---
id: sched-20260925-023
date: 2026-09-25
subject: 'sched_ext: Fixes for v7.3-rc4'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <be7ef09b8be82e9f0c5fb2bf197d7a44@kernel.org>
lore_url: https://lore.kernel.org/all/be7ef09b8be82e9f0c5fb2bf197d7a44@kernel.org/
upstream_commit: ee9c669f9bf5fd2c24206746ded9382fe810df89
fixes_commit: null
merged_branch: torvalds/linux.git
current_version: null
generated_at: '2026-09-26T01:15:00'
authors:
- Tejun Heo
- Liang Luo
maintainers_involved:
- Tejun Heo
patch_series:
- version: null
  msgid: <be7ef09b8be82e9f0c5fb2bf197d7a44@kernel.org>
  date: 2026-09-24
  summary: v7.3-rc4 fixes pull：UAF/死锁/丢唤醒/初始 mask/统计漏报 6 项 + selftests
  review_outcome: 09-25 已合入 torvalds/linux.git
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入主线，随 v7.3-rc4 发布
contribution_opportunities:
- kind: review
  description: UAF 与 mid-wakeup 状态修复涉及 rq 生命周期与卸载顺序，自家分支回合 sched_ext 相关提交时需确认一并带回
- kind: testing
  description: 在调度器 unload/re-home + 跨 CPU 唤醒压力下跑 sched_ext selftests，验证 rc4 修复无回归
source_email_count: 2
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Fixes for v7.3-rc4'
layout: article
---

## TL;DR

Tejun Heo 发起的 v7.3-rc4 sched_ext 修复 GIT PULL（tag `sched_ext-for-7.3-rc4-fixes`，6 项修复 + selftests）已被 Linus 合入 torvalds/linux.git（merge commit ee9c669f9bf5fd2c24206746ded9382fe810df89）。含一个 UAF 修复（跨 CPU 唤醒激活 + 调度器卸载顺序导致陈旧请求指向已释放内存）、一个死锁修复（`ops.dequeue()` 持源 DSQ 锁运行）、一个丢唤醒修复等。

## 背景与问题

sched_ext 在 v7.3-rc 周期暴露了一批真实缺陷，本 pull 集中修复：

- **丢唤醒（clobber）**：任务在其 dispatch 仍在进行中被重新入队时，dispatcher 会覆盖其 queued 状态，导致该任务后续所有 dispatch 被丢弃。修复为等待 in-flight dispatch 先 settle。
- **UAF**：另一 CPU 上的唤醒激活把目标 rq 标记为 mid-wakeup，使一个 pending 的本地 reenqueue 被滞留；若调度器先被卸载，陈旧请求指向已释放内存，被下一个调度器解引用。修复为等待/正确处理 mid-wakeup 状态。
- **死锁**：`ops.dequeue()` 在持源 dispatch 队列锁的情况下运行，调度器若在该回调里遍历该队列就会死锁 CPU。修复为不再持该锁调用 dequeue。
- **初始 CPU mask 无法获取**：有自定义 CPU ID 映射的调度器无从得知任务的初始 CPU mask、只能自行重建（在 sub-scheduler enable 与 re-home 场景下出错）。修复为把它传给 `ops.enable()`。
- **统计漏报**：bypass dispatch 事件计数器漏掉了 end-of-dispatch fallback 发出的 dispatch。修复补全计数。
- 另含针对 dequeue 锁与初始 mask 变更的 selftests。

## 技术方案

本 pull 为 6 项修复的集合（Liang Luo 1 项 + Tejun Heo 4 项 + selftests），changes up to `4409a85735cdca5c4c400c0dad1feee091872eee`。其中 `sched_ext: Count SCX_EV_SUB_BYPASS_DISPATCH in the dispatch fallback` 与当日另一枚独立统计补丁（<a class="article-ref" href="/lkm/2026/09/25/sched-20260925-019-sched-ext-count-cap-rejected-local-dsq-inserts-in-scx-ev-sub.html">sched-20260925-019</a>，SCX_EV_SUB_REJECT）是同一统计面补全的不同缺口。

## 版本演进与当前进展

- 09-24：Tejun 发出 GIT PULL（`<be7ef09b8be82e9f0c5fb2bf197d7a44@kernel.org>`），基线 `a9e3760b0838299649c0d57cca44daaf40ba3c33`。
- 09-25：pr-tracker-bot 确认已合入 torvalds/linux.git（merge commit ee9c669f9bf5fd2c24206746ded9382fe810df89）。

## Maintainer 意见与讨论焦点

Tejun Heo（sched_ext 维护者）直接向 Linus 发起 -rc4 fixes pull，Linus 合入。无分歧记录。

## 合入评估

已合入主线（*likelihood=merged*），merge commit ee9c669f9bf5fd2c24206746ded9382fe810df89，随 v7.3-rc4 发布。*blocking_issues* 无。

## 效果评估

修复类 pull，无 benchmark；正确性由缺陷描述静态可证（UAF/死锁/丢唤醒均为确定性路径）。暂无效果数据。

## 我可以参与的点

- `review`：UAF 与 mid-wakeup 状态的修复涉及 rq 生命周期与卸载顺序，自家分支若回合相关 sched_ext 提交，需确认这些修复一并回合，避免引入陈旧请求解引用。
- `testing`：在调度器 unload/re-home + 跨 CPU 唤醒的压力下跑 sched_ext selftests，验证 rc4 修复无回归。

## 参考链接

- GIT PULL: https://lore.kernel.org/all/be7ef09b8be82e9f0c5fb2bf197d7a44@kernel.org/
- 合入确认（pr-tracker）: https://lore.kernel.org/all/179028753357.2222164.10658990911294213165.pr-tracker-bot@kernel.org/
- torvalds merge: https://git.kernel.org/torvalds/c/ee9c669f9bf5fd2c24206746ded9382fe810df89
