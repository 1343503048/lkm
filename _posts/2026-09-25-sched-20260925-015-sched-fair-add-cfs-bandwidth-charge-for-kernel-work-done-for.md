---
id: sched-20260925-015
date: 2026-09-25
subject: 'sched/fair: add cfs_bandwidth_charge() for kernel work done for a cgroup'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20260924184714.912181-5-shakeel.butt@linux.dev>
lore_url: https://lore.kernel.org/all/20260924184714.912181-5-shakeel.butt@linux.dev/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: '2026-09-26T01:15:00'
authors:
- Shakeel Butt
maintainers_involved: []
patch_series:
- version: v1
  msgid: <20260924184714.912181-5-shakeel.butt@linux.dev>
  date: 2026-09-24
  summary: 新增 cfs_bandwidth_charge()，把内核为 cgroup 干的活计费到其 cpu.max 池并可转 debt
  review_outcome: 无回帖
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 纯 RFC，无 review 无维护者表态
  next_action: 等 cgroup/sched 维护者对 debt 语义与 quota 扣减路径的 review
contribution_opportunities:
- kind: review
  description: 审读 debt 计费在多层祖先配额、burst、cpu.max 运行时修改下的正确性，以及 __refill_cfs_bandwidth_runtime
    里 debt 归还的锁上下文
- kind: discussion
  description: 直接 throttle 当事线程 vs 记 debt 让 group 后续任务买单，两种方案对延迟敏感内核线程的影响值得讨论
source_email_count: 1
related_articles: []
tags:
- cgroup
- cfs
title: 'sched/fair: add cfs_bandwidth_charge() for kernel work done for a cgroup'
layout: article
---

## TL;DR

Shakeel Butt 的 RFC 系列（7 补丁，「把内核为某 cgroup 做的活计费到该 cgroup」）中的 4/7：新增 `cfs_bandwidth_charge()`，让内核线程经 `set_active_cgroup()` 为某 cgroup 做的 CPU 活不仅体现在 cpu.stat，还能真正扣减该 cgroup 的 `cpu.max` 配额池。纯 RFC、无人回帖，合入走向未知。

## 背景与问题

`set_active_cgroup()` 让内核线程（如 kworker、内存回收路径）为某个 cgroup 干活时，把它的 CPU 时间计到该 cgroup——但**只体现在 `cpu.stat`**。这份活并没有计入该 cgroup 的 `cpu.max` 限额：cgroup 自己的任务用完配额被节流时，内核替它做的活却「白嫖」了 CPU 时间，绕过带宽控制。

## 技术方案

新增 `cfs_bandwidth_charge(cgrp, delta)`：与 cgroup 自身 runtime 被扣除的同一路径类似，把 `delta` 从该 cgroup task group 及每个有限额祖先的 `cpu.max` 池中扣除。关键语义：这份活**本身不节流**（它已经跑完了），而是让它之后该 group 自己的任务少拿时间。池子当前不够扣的部分记为 debt，从下一轮 refill 里还；debt 上限为一个 period 的 quota，避免一次性突发活让 group 长时间饿死；修改 `cpu.max` 会清零 debt。built-in 上 patch 位于 kernel/sched/core.c +1、kernel/sched/fair.c +43、kernel/sched/sched.h +8，共 52 insertions。

## 版本演进与当前进展

- RFC v1（2026-09-24，封面 `<20260924184714.912181-1-shakeel.butt@linux.dev>`，7 补丁）：本枚 4/7，msgid `<20260924184714.912181-5-shakeel.butt@linux.dev>`。
- 09-25：补丁落盘缓存，无任何回帖。

## Maintainer 意见与讨论焦点

RFC 刚发出，今日无人回帖、无维护者表态。唯一可参考的信号是语义取舍：作者明确选择「不计费到正在干活的线程、而是记到被服务 cgroup 的池并转为 debt」——这是与「直接 throttle 当事线程」对立的方案，可能在后续 review 中被讨论。

## 合入评估

*likelihood=unknown*。纯 RFC、无回帖，机制涉及 cgroup 带宽控制核心路径，需 cgroup/sched 维护者 trade-off 后才有方向。*blocking_issues*：无 review、无表态。*next_action*：等 cgroup/sched 维护者对 debt 语义与 quota 扣减路径的 review。

## 效果评估

暂无效果数据；RFC 邮件未附 benchmark。

## 我可以参与的点

- `review`：审读 debt 计费语义在多层祖先配额、burst、以及 `cpu.max` 运行时修改下的正确性，尤其是 `__refill_cfs_bandwidth_runtime()` 里 debt 归还的锁上下文。
- `discussion`：直接 throttle 当事线程 vs 记 debt 让 group 后续任务买单，两种方案对延迟敏感内核线程的影响值得讨论。

## 参考链接

- RFC 4/7 补丁: https://lore.kernel.org/all/20260924184714.912181-5-shakeel.butt@linux.dev/
- RFC 封面: https://lore.kernel.org/all/20260924184714.912181-1-shakeel.butt@linux.dev/
