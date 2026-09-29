---
id: sched-20260929-008
date: '2026-09-29'
subject: 'sched_ext: Fix CPU hotplug hang when a dying CPU''s tasks sit in the BPF
  scheduler'
subsystem: sched
type: fix
status: merged_tip
severity: high
thread_root_msgid: <20260923223825.734003-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20260923223825.734003-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20260923223825.734003-1-tj@kernel.org>
  date: '2026-09-23'
  summary: rq 下线时重入队非本地 DSQ 任务 + ops.dispatch() 运行到 rq 真正离线
  review_outcome: 09-29 Tejun Applied to sched_ext/for-7.3-fixes
upstream_commit: null
fixes_commit: f0e1a0643a59
merged_branch: sched_ext/for-7.3-fixes
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 跟踪其经 sched_ext/for-7.3 进 mainline 及回合 stable（v6.12+）
contribution_opportunities:
- kind: testing
  description: 在 sched_ext + CPU 热插拔场景复现 dying CPU 有 BPF-held 任务的挂起并验证已消除
generated_at: '2026-09-30T01:15:00'
source_email_count: 1
related_articles:
- sched-20260924-003
tags:
- sched_ext
title: 'sched_ext: Fix CPU hotplug hang when a dying CPU''s tasks sit in the BPF scheduler'
layout: article
---

> **subject**：`sched_ext: Fix CPU hotplug hang when a dying CPU's tasks sit in the BPF scheduler`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/24/sched-20260924-003-sched-ext-fix-cpu-hotplug-hang-when-a-dying-cpu-s-tasks-sit.html">sched-20260924-003</a>：Tejun Heo（sched_ext 维护者）的 CPU 热插拔挂起修复——正关机的 CPU 若还有任务停在 user DSQ 或被 BPF 调度器持有，`cpu_down()` 会永久挂起或直到 watchdog 弹掉调度器；补丁在 rq 下线时把非本地 DSQ 任务全部重入队到本地 DSQ，并让 `ops.dispatch()` 一直运行到 rq 真正离线，带双 `Fixes:` 与 `Cc: stable # v6.12+`。
- <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-008-sched-ext-fix-cpu-hotplug-hang-when-a-dying-cpu-s-tasks-sit.html">sched-20260929-008</a>（今天）：Tejun Heo 回复「Applied to sched_ext/for-7.3-fixes」，本修复正式进入 sched_ext 的 7.3 修复分支，后续回合 stable。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/24/sched-20260924-003-sched-ext-fix-cpu-hotplug-hang-when-a-dying-cpu-s-tasks-sit.html">sched-20260924-003</a>）正下线的 CPU 必须清空自己的 rq：热插拔线程在 `sched_cpu_wait_empty()` 等待，唯一能唤醒它的是 dying CPU 的 `__schedule()` 里的 `balance_push()`。sched_ext 打破了这个机制——停在 user DSQ 或由 BPF 调度器持有的任务仍计在该 rq 上，但 inactive CPU 不再调用 `ops.dispatch()` 拉不回任务，导致 `cpu_down()` 挂着 `cpu_hotplug_lock` 死等，或任务只亲和 dying CPU 时 offline 等到 watchdog 弹掉调度器。今天无新背景，进展是合入。

## 技术方案

（承接 <a class="article-ref" href="/lkm/2026/09/24/sched-20260924-003-sched-ext-fix-cpu-hotplug-hang-when-a-dying-cpu-s-tasks-sit.html">sched-20260924-003</a>）两个修复点：1) `rq_offline_scx()` 在 rq 下线时把「不在本地 DSQ」的任务全部重入队，使其落到本地 DSQ、由 dying CPU 自己选中并 `balance_push()` 推走（并加 `cpu_active()` 短路）；2) `scx_dispatch_sched()` 改为直接 `SCX_RQ_ONLINE` 测试，让 `ops.dispatch()` 持续运行到 rq 真正离线。改动 30 insertions / 9 deletions（ext.c、inlines.h、sub.c、sched.h）。带 `Fixes: f0e1a0643a59` 与 `Fixes: 991ef53a4832`、`Cc: stable # v6.12+`。

## 版本演进与当前进展

v1（09-23，`<20260923223825.734003-1-tj@kernel.org>`）→ 09-29 Tejun Heo 收「Applied to sched_ext/for-7.3-fixes」。

## Maintainer 意见与讨论焦点

- **Tejun Heo**（作者即 sched_ext 维护者）：自提补丁、直接进自家 `for-7.3-fixes` 分支，09-29 确认「Applied to sched_ext/for-7.3-fixes」。`Reported-by: Alap Mohan`、`Joonwoo Park`（均 Meta）。无争议、无 NAK。

## 合入评估

*likelihood=merged*。已合入 `sched_ext/for-7.3-fixes`（挂起类是必须修的硬缺陷，双 `Fixes:` + `Cc: stable # v6.12+`）。*blocking_issues*：无。*next_action*：跟踪其经 `sched_ext/for-7.3` 进 mainline、以及回合 stable（v6.12+）的通告。

## 效果评估

无量化数据；效果是消除 sched_ext 场景下 dying CPU 有 BPF-held 任务时 `cpu_down()` 的永久挂起或 watchdog 弹调度器。

## 我可以参与的点

- `testing`：在 sched_ext + CPU 热插拔场景复现「dying CPU 上有 BPF-held/user-DSQ 任务」的挂起，验证 for-7.3-fixes 内核已消除挂起。

## 参考链接

- lore（补丁）: https://lore.kernel.org/all/20260923223825.734003-1-tj@kernel.org/
- Tejun 收取: https://lore.kernel.org/all/658555bf88cfc140f55ef862571be996@kernel.org/
