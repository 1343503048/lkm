---
id: sched-20261012-017
date: '2026-10-12'
subject: 'sched/autogroup: Make nice rate-limit updates atomic'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261012133155.86480-1-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20261012133155.86480-1-sh_def@163.com/
authors:
- Hui Su
maintainers_involved:
- K Prateek Nayak
- Mike Galbraith
current_version: v2
patch_series:
- version: v1
  msgid: <20261008064440.240528-1-sh_def@163.com>
  date: '2026-10-08'
  summary: 用专用 spinlock 串行化时间戳查/改
  review_outcome: Prateek 认为 spinlock 过重，建议 try_cmpxchg + 失败者 -EAGAIN
- version: v2
  msgid: <20261012133155.86480-1-sh_def@163.com>
  date: '2026-10-12'
  summary: 非特权用 try_cmpxchg、特权用 xchg 保留绕过行为
  review_outcome: 当日新发，待 Prateek re-review
fixes_commit: 5091faa449ee
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 待 Prateek 对 v2（try_cmpxchg+xchg）的 re-review
  next_action: 等 Prateek 确认 v2 方案，必要时补并发 CAP_SYS_ADMIN 测试后交 Peter
contribution_opportunities:
- kind: testing
  description: 验证并发非特权 + CAP_SYS_ADMIN 混合写 /proc/sched_autogroup 的 nice 时限流与 xchg
    竞争无 -EAGAIN 泄漏
generated_at: '2026-10-13T01:40:00'
source_email_count: 3
related_articles:
- sched-20261008-003
tags:
- autogroup
title: 'sched/autogroup: Make nice rate-limit updates atomic'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-003-sched-autogroup-serialize-nice-rate-limit-updates.html">sched-20261008-003</a>：Hui Su 修 `proc_sched_autogroup_set_nice()` 的 check-then-act 竞态——函数级静态时间戳的检查/更新非原子，两个并发非特权写者可同时进入 `sched_group_set_shares()` 击穿限流；v1 用专用 spinlock 串行化。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-017-sched-autogroup-make-nice-rate-limit-updates-atomic.html">sched-20261012-017</a>（今天）：作者发 v2——按 Prateek 建议改用 `try_cmpxchg()`（非特权，失败者返回 -EAGAIN）+ `xchg()`（特权，保留绕过限流行为并原子更新时间戳），并重跑 KCSAN/限流测试。

## 背景与问题

（承接 20261008-003）`proc_sched_autogroup_set_nice()` 用函数级静态时间戳做 100ms 限流，但检查与更新不是原子的：并发非特权写者可能同时看到过期时间戳、都进入重活 `sched_group_set_shares()`，削弱限流。

## 技术方案

（承接 20261008-003）v1 用 spinlock；Prateek 认为 spinlock 过重（注释本就「不想取全局锁」），建议 `try_cmpxchg()`、失败者直接 -EAGAIN。v2 落实：`capable(CAP_SYS_ADMIN)` 分支用 `xchg(&next, HZ/10 + jiffies)`（保留特权绕过 + 原子更新）；非特权分支 `READ_ONCE(next)` 后 `time_before(jiffies, old) || !try_cmpxchg(...)` 则 -EAGAIN（`kernel/sched/autogroup.c` +9/-5）。

## 版本演进与当前进展

- v1（10-08，spinlock；Prateek 建议 try_cmpxchg）→ v2（10-12，try_cmpxchg + xchg，`Fixes: 5091faa449ee`）。
- 作者自测：x86_64 KVM 功能限流 oracle「8 个同步非特权写者只放 1 个、其余 -EAGAIN」；特权与混合竞争测试无 -EAGAIN/错误；KCSAN 强制重叠测试放 1 个、无 `proc_sched_autogroup_set_nice` 报告。

## Maintainer 意见与讨论焦点

K Prateek Nayak（v1 时）质疑 spinlock 过重、建议 try_cmpxchg；作者采纳并保留 CAP_SYS_ADMIN 的绕过语义。Mike Galbraith（autogroup 原作者，v1 时）此前已认可方向。今日 v2 待 Prateek re-review。

## 合入评估

*likelihood=medium*。方案收敛到 reviewer 建议的 try_cmpxchg，方向正确。*blocking_issues*：待 Prateek 对 v2 的 re-review。*next_action*：等 Prateek 确认，交 Peter 收取。

## 效果评估

作者 v2 自测（KVM/KCSAN）：8 个并发非特权写者仅 1 个通过限流、其余 -EAGAIN；特权/混合竞争无 -EAGAIN 泄漏。属功能正确性验证，无性能数字。

## 我可以参与的点

- `testing`：验证并发非特权 + CAP_SYS_ADMIN 混合写 `/proc/sched_autogroup` 时，`xchg` 竞争不会让特权调用者误收 -EAGAIN（作者已测，可复测更大并发）。

## 参考链接

- lore（v2）: https://lore.kernel.org/all/20261012133155.86480-1-sh_def@163.com/
- lore（Prateek 对 v1 的意见）: https://lore.kernel.org/all/19b982f8-f4a0-4d47-8f56-0779e691f0eb@amd.com/
