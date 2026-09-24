# sched_ext: Fix CPU hotplug hang when a dying CPU's tasks sit in the BPF scheduler

## TL;DR
Tejun Heo（sched_ext 维护者）的 CPU 热插拔挂起修复（`sched_ext/for-7.3-fixes`）：正关机的 CPU 若还有任务停在 user DSQ 或被 BPF 调度器持有，`cpu_down()` 会永久挂起或直到 watchdog 弹掉调度器。补丁在 rq 下线时把非本地 DSQ 上的任务全部重新入队到本地 DSQ，并让 `ops.dispatch()` 一直运行到 rq 真正离线。带双 `Fixes:` 与 `Cc: stable # v6.12+`（30 insertions / 9 deletions），影响 sched_ext 的 CPU 热插拔正确性。

## 背景与问题
正在下线的 CPU 必须清空自己的 rq：热插拔线程在 `sched_cpu_wait_empty()` 等待，唯一能唤醒它的是 `balance_push()`（在 dying CPU 的 `__schedule()` 里运行，把可迁移任务推走）。sched_ext 打破了这个机制：

- 停在 user DSQ 上、或由 BPF 调度器持有的任务仍计在该 rq 上，但 inactive 的 CPU 不再调用 `ops.dispatch()`，无法把任务拉回来。
- dying CPU 进入 idle 时任务仍被计数，随后两种后果之一：
  1. 另一 CPU 消费该任务，rq 在没有 dying CPU 上的 `__schedule()` 的情况下被清空 → 热插拔线程永远不被唤醒，`cpu_down()` 挂着 `cpu_hotplug_lock` 死等；
  2. 任务只亲和 dying CPU，无法迁移 → offline 一直等到 watchdog 弹掉 BPF 调度器。

## 技术方案
两个修复点：

1. **rq 下线时重入队**（`rq_offline_scx()`）：当 rq 下线时，把其上所有「不在本地 DSQ」的任务重新入队。对 offline rq 的入队会落到本地 DSQ，于是 dying CPU 自己选中任务、`balance_push()` 把它们推走——与其它调度类行为一致。之后其它 CPU 上的任何 sched_ext 路径都无法再把任务从该 rq 拉走。并加了 `cpu_active(cpu_of(rq))` 短路（sched domain 重建调 `rq_offline` 时 CPU 仍存活，不应走此路径）。
2. **`ops.dispatch()` 运行到 rq 真正离线**（`scx_dispatch_sched()`）：此前 `ops.dispatch()` 在 CPU 进入 inactive 就停；但 CPU 热插拔要等一个 RCU grace period 才把 rq 下线，若一个只亲和 dying CPU、且被 preempt 进 RCU 读侧临界区的 BPF-held 任务，会阻塞该 grace period，导致 rq 永远下不了线。改为直接 `SCX_RQ_ONLINE` 测试（而非 `scx_rq_online()` 的 `cpu_active()` 测试），让 `ops.dispatch()` 持续运行直到 rq 下线；只有 dying CPU 自己的热插拔线程在 teardown 时清标志，`task_can_run_on_remote_rq()` 仍挡住其它 rq 的任务。

改动 30 insertions / 9 deletions（ext.c、inlines.h、sub.c、sched.h）。

## 版本演进与当前进展
v1 本日发出（`<20260923223825.734003-1-tj@kernel.org>`，`sched_ext/for-7.3-fixes`），暂无本日 review 回复。

## Maintainer 意见与讨论焦点
作者即 sched_ext 维护者 Tejun Heo，直接进入自家 `for-7.3-fixes` 分支。带 `Fixes: f0e1a0643a59` 与 `Fixes: 991ef53a4832`、`Cc: stable@vger.kernel.org # v6.12+`，`Reported-by: Alap Mohan <mohaalap@meta.com>` 与 `Joonwoo Park <joonwoo@meta.com>`（均 Meta）。无争议。

## 合入评估
*likelihood=high*。sched_ext 维护者自提的 CPU 热插拔挂起修复，定位精确、带双 Fixes 与 stable 标记，走自家 fixes 分支；挂起类是必须修的硬缺陷。*blocking_issues*：无明确项，待进入 `sched_ext/for-7.3` 及随后的 upstream/stable 回合。*next_action*：合入 `sched_ext/for-7.3-fixes`，后续回合 stable（v6.12+）。

## 效果评估
无性能数据；属正确性修复——避免 `cpu_down()` 挂起（`cpu_hotplug_lock` 死等）或 offline 被 watchdog 打断的硬故障，两个 Meta 报告者佐证了实际触发场景。

## 我可以参与的点
- kind=testing：在启用 sched_ext 调度器的机器上做 CPU 热插拔压力测试（尤其任务停在 user DSQ / 被 BPF 持有的场景），验证 `cpu_down()` 不再挂起。
- kind=review：核对 `rq_offline_scx()` 的重入队与 `cpu_active()` 短路分支在「sched domain 重建 vs 真正下线」两种路径下语义正确。

## 参考链接
- lore thread: https://lore.kernel.org/all/20260923223825.734003-1-tj@kernel.org/

---
id: sched-20260924-003
date: '2026-09-24'
subject: "sched_ext: Fix CPU hotplug hang when a dying CPU's tasks sit in the BPF scheduler"
subsystem: sched
type: fix
status: under_review
severity: critical
thread_root_msgid: '<20260923223825.734003-1-tj@kernel.org>'
lore_url: 'https://lore.kernel.org/all/20260923223825.734003-1-tj@kernel.org/'
authors:
  - 'Tejun Heo'
maintainers_involved:
  - 'Tejun Heo'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260923223825.734003-1-tj@kernel.org>'
    date: '2026-09-24'
    summary: 'rq 下线重入队 + ops.dispatch 运行到真正离线'
    review_outcome: '暂无 review 回复'
upstream_commit: null
fixes_commit: 'f0e1a0643a59'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: '合入 sched_ext/for-7.3-fixes 后回合 stable v6.12+'
contribution_opportunities:
  - kind: testing
    description: 'sched_ext 调度器下做 CPU 热插拔压力测试验证 cpu_down 不挂起'
  - kind: review
    description: '核对 rq_offline_scx 重入队与 cpu_active 短路分支语义'
generated_at: '2026-09-25T09:00:00'
source_email_count: 1
related_articles: []
tags:
  - sched_ext
  - hang
---