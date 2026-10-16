# sched/cputime: Don't account idle time twice after dyntick-idle

## TL;DR
Stian Halseth 修复 dyntick-idle 退出后 idle 时间被重复记账的问题：idle 退出时 dyntick-idle 已把当前时刻之前的时间记成 idle（或 IRQ time），但重启 tick 后第一个 tick 又把整段 TICK_NSEC 记给当前运行者，导致 `/proc/stat` 报告的 idle 时间超过 wall time。补丁记录 dyntick-idle 已记账的 tick period 部分，从结束该 period 的 tick 中扣除。已由 Peter 合入 tip sched/core（commit 96a494c9cfd8）。

## 背景与问题
idle 退出时，dyntick-idle 记账已把「到当前为止」的时间记入 idle（有 IRQ_TIME_ACCOUNTING 时记入 IRQ time），随后 tick 按其旧周期重启。第一个 tick 把一整段 TICK_NSEC 记给当时运行的任务，但这段 period 中 idle 退出之前的部分刚被记成 idle 时间——于是每次 idle 退出最多多记一个整 tick，`/proc/stat` 报出的 idle 时间超过 wall time。`Fixes: cf6444c3e1bb7 ("tick/sched: Unify idle cputime accounting")`。

## 技术方案
记录当前 tick period 中 dyntick-idle 已记账了多少，从结束该 period 的 tick 中扣除。改动涉及 `include/linux/kernel_stat.h`（新增 `idle_dyntick_entry`/`idle_tick_period`/`idle_tick_overlap` 三个字段）、`kernel/sched/cputime.c`（+39/−6）、`kernel/time/tick-sched.c`（+22/−5），共 +55/−13。

## 版本演进与当前进展
v1（提交于 2026-10-07，<20261007142950.547604-1-stian@itx.no>），获 Frederic Weisbecker Reviewed-by，2026-10-16 由 Peter 合入 tip sched/core（committer Peter Zijlstra）。

## Maintainer 意见与讨论焦点
Frederic Weisbecker（NO_HZ/tick 维护者）Reviewed-by；Peter Zijlstra 收取合入。无分歧。

## 合入评估
*likelihood=merged*。已合入 tip sched/core（commit `96a494c9cfd8`）。*blocking_issues*：无。*next_action*：无（已合入）。

## 效果评估
无量化数据；症状（idle 时间超过 wall time）为动机来源，属记账正确性修复。

## 我可以参与的点
当前阶段已合入，无明显参与空间。

## 参考链接
- tip 合入通知：https://lore.kernel.org/all/179213767779.2666988.12449783777877801435.tip-bot2@tip-bot2/
- 原始补丁：https://lore.kernel.org/all/20261007142950.547604-1-stian@itx.no/

---
id: sched-20261016-008
date: 2026-10-16
subject: "sched/cputime: Don't account idle time twice after dyntick-idle"
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: "<20261007142950.547604-1-stian@itx.no>"
lore_url: "https://lore.kernel.org/all/20261007142950.547604-1-stian@itx.no/"
authors: ["Stian Halseth"]
maintainers_involved: ["Frederic Weisbecker", "Peter Zijlstra"]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261007142950.547604-1-stian@itx.no>"
    date: 2026-10-07
    summary: "记录 dyntick-idle 已记账的 tick period 部分，从结束 tick 中扣除"
    review_outcome: "Frederic Reviewed-by；Peter 合入 tip sched/core"
upstream_commit: "96a494c9cfd8"
fixes_commit: "cf6444c3e1bb7"
merged_branch: "sched/core"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "无（已合入）"
contribution_opportunities: []
generated_at: "2026-10-17T01:30:00"
source_email_count: 1
related_articles: []
tags: [cfs, nohz]
---