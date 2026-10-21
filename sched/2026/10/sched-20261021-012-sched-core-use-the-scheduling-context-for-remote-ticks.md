# sched/core: Use the scheduling context for remote ticks

## TL;DR
本文为增量更新，完整脉络见下。

- sched-20261017-005：Shubhang Kaushik（Ampere）单补丁——full-nohz 远程 tick `sched_tick_remote()` 对 `rq->curr` 调 `task_tick()`，但 proxy execution 下 `rq->curr` 是 mutex-owner 执行上下文、`rq->donor` 才是调度上下文；改为对 `rq->donor` 调 `task_tick()` 并移除 `WARN_ON_ONCE(curr!=donor)`。带 `Fixes: 7de9d4f94638`。
- sched-20261019-010：Christian Loehle（Arm）回帖一个排版 NIT + 提示可参考 sashiko 的审查页。
- sched-20261021-012（今天）：作者 Shubhang 回复 Christian——确认「full-nohz 区间 sanity check 同样假设 `rq->curr` 是调度上下文」，并宣布 v2 将统一用 `rq->donor` 做 idle 检查与 `exec_start` 计算，同时吸收 NIT 修正。

## 背景与问题
（承接 sched-20261017-005）proxy execution 下 `rq->curr`（mutex owner 执行上下文）与 `rq->donor`（真正被代理执行的调度上下文）分离；远程 tick 落在 `rq->curr` 上做调度记账，与真正该记账的 `rq->donor` 不一致，且原 `WARN_ON_ONCE(rq->curr != rq->donor)` 假设被 proxy execution 打破。今日补充：Christian 指出 full-nohz 的区间 sanity check 也假设 `rq->curr` 是调度上下文——`curr->se.exec_start` 在 proxy execution 下、记账路径更新它之前可能是 stale 的。

## 技术方案
（承接 v1，今日为 v2 方向确认，无新补丁）v1 把 `task_tick()` 改挂 `rq->donor`、`rq->curr` 仅做执行时间 sanity check。v2 将扩展为：idle 检查与 `exec_start` 计算都用 `rq->donor`，并吸收 Christian 的 NIT（排版）与 sashiko 审查意见。

## 版本演进与当前进展
*current_version: v1*（v2 待发）。

## Maintainer 意见与讨论焦点
Christian Loehle（Arm）：上一轮的排版 NIT 之外，本轮指出 full-nohz 区间 sanity check 的同类假设问题。作者 Shubhang 完全采纳，确认 v2 统一走 `rq->donor`。无分歧。

## 合入评估
*likelihood=high*。proxy execution 语义下的正确性修复，`Fixes:` 明确，作者与 reviewer 方向一致，只差 v2 落地。*blocking_issues*：v2 尚未发出。*next_action*：作者发 v2（`rq->donor` 统一 idle 检查与 exec_start + NIT 修正）。

## 效果评估
无 benchmark 数据。属 proxy execution 下远程 tick 记账正确性修复。

## 我可以参与的点
- `review`：v2 发出后核对 idle 检查与 `exec_start` 是否都正确改用 `rq->donor`，及 full-nohz 区间 sanity check 是否一并修复。

## 参考链接
- Shubhang 的 v2 计划回帖：https://lore.kernel.org/all/6acc6595-60aa-94b7-6316-f82ab635f985@gentwo.org/
- v1 patch：未获取到（v1 发出日期在当日缓存窗口之外）

---
id: sched-20261021-012
date: 2026-10-21
subject: "sched/core: Use the scheduling context for remote ticks"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: null
lore_url: "https://lore.kernel.org/all/6acc6595-60aa-94b7-6316-f82ab635f985@gentwo.org/"
authors: ["Shubhang Kaushik"]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: null
    date: 2026-10-17
    summary: "sched_tick_remote 改对 rq->donor 调 task_tick()，移除 WARN_ON_ONCE(curr!=donor)"
    review_outcome: "Christian 提示 full-nohz sanity check 同类问题，作者确认 v2 统一 rq->donor"
upstream_commit: null
fixes_commit: "7de9d4f94638"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["v2 尚未发出"]
  next_action: "作者发 v2（rq->donor 统一 idle 检查与 exec_start）"
contribution_opportunities:
  - kind: review
    description: "v2 发出后核对 idle 检查与 exec_start 的 rq->donor 改法"
generated_at: "2026-10-22T01:30:00"
source_email_count: 1
related_articles: ["sched-20261019-010"]
tags: [nohz, proxy_execution]
---