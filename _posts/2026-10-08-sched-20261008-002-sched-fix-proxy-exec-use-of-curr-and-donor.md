---
id: sched-20261008-002
subject: 'sched: Fix proxy-exec use of curr and donor'
date: '2026-10-08'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261008132604.98242-1-jemmywong512@gmail.com>
lore_url: https://lore.kernel.org/all/20261008132604.98242-1-jemmywong512@gmail.com/
authors:
- Jemmy Wong
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261008132604.98242-1-jemmywong512@gmail.com>
  date: '2026-10-08'
  summary: NUMA/cache tick、task_sched_runtime flush、CFS 带宽检查改指向正确上下文
  review_outcome: Kayra 提示与 Hui Su 早前补丁疑似重复，作者尚未回应
upstream_commit: null
fixes_commit: aa4f74dfd42b
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 与 Hui Su 早前补丁（20260913）的重叠待澄清
  - 无 proxy-exec 维护者（John Stultz）或 Peter/Ingo review
  next_action: 回应 Kayra 重叠提醒并说明差异/合并，等待维护者审阅
contribution_opportunities:
- kind: review
  description: 核对三枚补丁对 rq->donor/rq->curr 语义与边界场景的假设
- kind: discussion
  description: 澄清与 Hui Su 补丁的重叠范围，判断合并或取舍
- kind: testing
  description: CONFIG_SCHED_PROXY_EXEC=y 下验证 NUMA 周期/runtime 读数/nohz 带宽行为
generated_at: '2026-10-09T01:00:00'
source_email_count: 5
related_articles: []
tags:
- proxy_execution
- cfs
title: 'sched: Fix proxy-exec use of curr and donor'
layout: article
---

## TL;DR

Jemmy Wong 发 3 枚修复，收掉 proxy execution（拆分调度上下文 `rq->donor` 与执行上下文 `rq->curr`）下的三处记账不一致：NUMA/cache tick 钩子、`task_sched_runtime()` 的运行时 flush、`sched_can_stop_tick()` 的 CFS 带宽检查在拆分后仍错误地以 donor 为「在 CPU 上的任务」。三枚均带 `Fixes:` 标签（第 3 枚明确无功能变化、无 Fixes）。Kayra Cizmeci 提醒作者这可能与 Hui Su 早前的一枚补丁重复。属修复性质、尚无维护者 review。

## 背景与问题

proxy execution 把调度上下文（`rq->donor`，真正被调度的 waiter）与执行上下文（`rq->curr`，在 CPU 上跑的锁持有者）拆开后，`update_se()` 已把 open run interval 记到 `rq->curr`，但 tick 路径与运行时采样仍把 donor 当成「CPU 上的任务」：

- NUMA/cache tick 钩子用 donor，而 donor 被 mutex 阻塞、其运行时被冻结 → `node_stamp`/`numa_scan_period` 永远不跨过、`TWA_RESUME` 的 task_work 被排到一个阻塞任务上。
- `task_sched_runtime()` 只在 `@p` 是 donor 时才 commit 未结算区间，但区间其实由 `update_se()` 记到 `rq->curr`；读锁持有者的运行时时漏掉 flush，丢掉上次更新以来的时间。
- `sched_can_stop_tick()` 用 `rq->curr` 测 CFS 带宽，但配额由 donor 消耗（`account_cfs_rq_runtime()` 记到 `rq->donor` 的 cfs_rq）。

未开启 `CONFIG_SCHED_PROXY_EXEC` 时 `curr`/`donor` 是 union、指向同一任务，故这些 bug 只在 proxy-exec 下暴露。

## 技术方案

- patch 1（`sched/fair`）：`task_tick_fair()` 的 NUMA 与 cache tick 钩子改传 `rq->curr`（与 `psi_account_irqtime()`、`wq_worker_tick()` 一致），并把参数从 `curr` 改名为 `donor` 以免混淆；仅当 `rq->curr` 属 fair 类时才跑钩子，保持 NUMA 扫描不落到非 fair 任务上、与 `account_mm_sched()` 一致。`Fixes: aa4f74dfd42b`（runtime accounting w/ split contexts）、`Fixes: df0d98475954`（cache-aware infra）。
- patch 2（`sched/core`）：`task_sched_runtime()` 改为当 `@p` 是 `rq->curr` 时通过 donor 类的 `update_curr()` 结算区间（delta 仍取自 donor 的 `exec_start`、仍作用于 `@p`）。`Fixes: aa4f74dfd42b`。
- patch 3（`sched/core`）：`sched_can_stop_tick()` 的带宽检查指向 `rq->donor`，与 `sched_fair_update_stop_tick()` 一致。两处调用都在 `nr_running == 1` 之前返回，proxy 期间 tick 决策不变，故无 `Fixes:`、无功能变化。

## 版本演进与当前进展

v1 刚发出（cover `<20261008132604.98242-1-jemmywong512@gmail.com>`），尚无维护者 review。Kayra Cizmeci 回复指出与 Hui Su 早前一枚补丁（`https://lore.kernel.org/lkml/20260913064722.1534766-1-sh_def@163.com/`）疑似修同一问题，建议作者协调合并，并 CC 了 Hui 与 John（Stultz）。

## Maintainer 意见与讨论焦点

暂无 mainline sched 维护者表态。唯一实质回帖来自 Kayra Cizmeci（活跃 sched reviewer，非维护者）：指出本系列与 Hui Su 早前补丁的重复，要求说明差异/合并。这是当前最重要的待澄清点——proxy-exec 记账补丁若与既有补丁重叠，作者需确认谁是上游基线、避免重复劳动。

## 合入评估

*likelihood=medium*。方向正确（修复拆分上下文后的记账不一致）、三枚均明确 `Fixes:` 指向既有 proxy-exec/cache-aware 提交，逻辑自洽且声明在非 proxy-exec 下无功能变化；但 ① 与 Hui Su 早前补丁疑似重复、需协调；② 尚无 John Stultz 或 Peter/Ingo 等维护者 review；③ 补丁署名 `Assisted-by: LLM`，社区对 LLM 辅助补丁仍需人工核验。*blocking_issues*：与 Hui Su 补丁的重叠待澄清；无维护者 review。*next_action*：作者回应 Kayra、说明与 Hui Su 补丁的差异或合并方案，等 proxy-exec 系列维护者（John Stultz）审阅。

## 效果评估

纯记账正确性修复，无性能数据；作者自述三枚补丁在未开 `CONFIG_SCHED_PROXY_EXEC` 时行为不变（union 下 curr/donor 同任务），第 3 枚明确无功能变化。效果属「消除 proxy-exec 下的记账偏差」这一类正确性问题，无 benchmark。

## 我可以参与的点

- `review`：核对三枚补丁对 `rq->donor`/`rq->curr` 语义的假设（尤其是 patch 2 中「通过 donor 类 `update_curr()` 但 delta 作用于 `@p`」在各类切换/远程 tick 场景下是否完备）。
- `discussion`：协助澄清本系列与 Hui Su 补丁（20260913）的重叠范围，判断应合并、取舍还是 rebase。
- `testing`：在 `CONFIG_SCHED_PROXY_EXEC=y` + `CONFIG_CACHE_AWARE_SCHED` 的环境下验证 NUMA 扫描周期、`clock_gettime`/`getrusage` 读数、CFS 带宽 nohz 停止 tick 行为。

## 参考链接

- 系列封面: https://lore.kernel.org/all/20261008132604.98242-1-jemmywong512@gmail.com/
- Kayra 的重叠提醒: https://lore.kernel.org/all/20261008153348.92684-1-kayracizmeci@gmail.com/
