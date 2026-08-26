---
id: sched-20260826-001
date: 2026-08-26
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: unknown
lore_url: unknown
authors:
- K Prateek Nayak
maintainers_involved:
- Andrea Righi
current_version: v1
patch_series:
- version: v1
  msgid: unknown
  date: 2026-08-26
  summary: 16 篇 RFC，提出 proxy exec sleeping-owner 的替代处理方案，引入 is_linked 状态和 __task_rq_lock()
    方案
  review_outcome: Andrea Righi 对 PELT 注释和 owner-NULL 自旋提出修改建议
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - RFC PoC 不可 bisect
  - spurious wakeup 开销未量化
  - 与原方案关系待厘清
  next_action: 等待社区对整体方向的反馈，需使系列可 bisect
contribution_opportunities:
- kind: testing
  description: 在高并发 mutex 竞争场景下 benchmark 新旧方案的锁竞争开销
- kind: review
  description: 帮助测试中间构建的编译正确性并反馈
generated_at: '2026-08-27T01:10:00'
source_email_count: 17
related_articles: []
tags:
- core_sched
- preempt
title: 'sched/core: Alternate approach to sleeping-owner handling in PROXY_EXEC'
layout: article
---

## TL;DR

K Prateek Nayak (AMD) 提交了一套 16 篇的 RFC，提出 proxy exec 中 sleeping-owner 处理的替代方案。核心思路是将 John Stultz 的大补丁拆分为更小的模块，引入 `p->is_linked` 状态 + `__task_rq_lock()` 方案来减少锁弹跳，并为不需要 chain-wakeup 的任务提供无额外锁的快路径。Andrea Righi (NVIDIA) 已对 Patch 03/04 给出 review 意见。这是 PoC 阶段，尚未 bisectible。

## 背景与问题

Proxy exec 中，当 owner 进入睡眠时，blocked donor 需要排队在 owner 上并在 owner 唤醒时执行 chain-wakeup。当前方案在 `ttwu_runnable()` 路径中处理 enqueued donor wakeup vs owner chain-wakeup 竞争时，激活路径需要额外获取 `p->blocked_lock`，导致所有 wakeup 都要承担锁开销——即使大多数任务根本不需要 chain-wakeup。

当前的锁嵌套规则为：`p->pi_lock → __task_rq_lock() → lock->wait_lock → p->blocked_lock`，chain-wakeup 路径在 `p->pi_lock` 和 `p->blocked_lock` 之间来回切换以防止并发 wakeup 修改链。

## 技术方案

RFC 引入以下关键设计：

1. **`p->is_linked` 状态**：与 `p->on_rq` 联合为 `needs_rq_sync`（u16），可在 `rq_lock` 外原子检查，用于判断是否需要走 `ttwu_runnable()` 路径
2. **`__task_rq_lock()` 方案**：只需 `__task_rq_lock()`（始终持有）+ `p->blocked_lock`（按链中每个 owner 切换），检测到排队任务时才获取，减少锁弹跳
3. **主动移除 blocked donor**：在 `proxy_enqueue_on_owner()` 中，若 `owner->on_rq` 转为非零，主动移除 blocked donor，确保 owner 不必关心此后进入的 donor
4. **MIGRATING 标记迁移**：blocked donor 在 blocking 前迁移到确定性 CPU，确保整条链由单个 CPU 拥有
5. **消除 delayed tasks 干扰**：链上的 delayed tasks 在 blocking 前完全阻塞，保证链解析到单 CPU 的条件成立
6. **快路径优化**：`p->lock_nesting` 为 0 的任务（不可能解析到 `__mutex_owner()`）直接走 `__activate_task()`，跳过所有 proxy 逻辑

## 版本演进与当前进展

这是该方案的首个 RFC（v1），基于 John Stultz 在 lore 上的大补丁（`20260807035232.1881495-9-jstultz@google.com`）进行拆分重构。RFC 明确声明"not bisectible in any way at the moment"，相关代码在不同 patch 间引入，中间构建可能失败。Patch 1-4 被标注为独立 fix，可以在不依赖其余 RFC 的情况下讨论。

## Maintainer 意见与讨论焦点

**Andrea Righi (NVIDIA, sched_ext maintainer)** 对 Patch 03/16 提出：
- 注释仍引用旧的 `!last_update_time` 逻辑，应更新为描述 `DO_ATTACH` 的新语义
- 建议用 `DO_ATTACH` 替代 `se->avg.last_update_time` 作为迁移指示器，并加 `WARN_ON_ONCE()` 防御

对 Patch 04/16，Andrea 指出 `proxy_resched_idle()` 在 owner 出现前可能自旋较长时间，因为 owner 可能一直为 NULL 直到被 `mutex_unlock()` 选中的 waiter 获得 CPU 并获取 mutex。

Prateek 自己也标注了 `XXX: Is there a better way to handle this?`，承认当前方案在无 owner 时对每个任务做 spurious wakeup 并不理想。

## 合入评估

- **likelihood**: low（RFC 阶段，PoC 性质，16 篇大改动，需要大量 review 和测试）
- **blocking_issues**: 不可 bisect、spurious wakeup 开销未量化、与 John Stultz 原方案的关系需厘清
- **next_action**: 等待社区对整体方向的反馈，尤其是 Andrea 指出的 owner 为 NULL 时的自旋问题；需要使系列可 bisect

## 效果评估

暂无性能数据。RFC 明确为 PoC，主要目标是验证方案可行性和获取社区反馈。

## 我可以参与的点

- 该 RFC 不可 bisect，可以帮助测试中间构建的编译正确性并反馈
- proxy exec 的 sleeping-owner 处理是活跃开发区域，可以帮忙在特定负载（高并发 mutex 竞争）下跑 benchmark 对比新旧方案的锁竞争开销
- Patch 04/16 的 spurious wakeup 问题可以用 ftrace 量化 owner 为 NULL 时的 wakeup 频率

## 参考链接

- lore thread: 未获取到（RFC 首发，需从 sched/.state/emails/20260826/58515.json 获取 msgid）
- 关联的 John Stultz 原补丁: https://lore.kernel.org/lkml/20260807035232.1881495-9-jstultz@google.com/
