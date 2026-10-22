# sched: fix stale get_pref_llc() stub for !CONFIG_SCHED_CACHE

## TL;DR
本文为增量更新，完整脉络见下。

- sched-20261021-017：Yafang Shao 的 bpf-next RFC v3 系列（per-cgroup NUMA balancing 模式选择）中的 1/5 补丁：修正 `!CONFIG_SCHED_CACHE` 构建下 `get_pref_llc()` 桩函数已过期（与实际签名不符）的问题。当日获 Gregory Price 与 Chen Yu 双 Reviewed-by，两人均建议这类修复应**从系列中拆出单独提交**；作者已回应会单独发送。
- sched-20261022-014（今天）：Tim Chen 追加 Reviewed-by，并建议 `Cc: stable@vger.kernel.org #v7.2.x`——因为该补丁所修的 commit `b636fef85bda` 已被回合到 7.2.x stable，此修复也应同步回合。

## 背景与问题
（承接 sched-20261021-017）`get_pref_llc()` 的 `!CONFIG_SCHED_CACHE` 桩实现与其新签名失配（stale），在关闭 SCHED_CACHE 的构建下会编译/语义异常。该修复混在 Yafang 的 bpf-next RFC 系列里，评审一致认为应作为独立修复提交。今日补充：因被修 commit `b636fef85bda` 已进 stable，本修复需跟随回合 stable。

## 技术方案
（承接前序）单补丁：把 `!CONFIG_SCHED_CACHE` 下过期的 `get_pref_llc()` 桩更新到与实际函数签名一致。具体 diff 未完整进入当日缓存。今日仅新增 stable 回合建议（`Cc: stable@vger.kernel.org #v7.2.x`）。

## 版本演进与当前进展
*current_version: v3*（thread root `<20261019064157.29885-1-laoar.shao@gmail.com>`，属 bpf-next RFC v3 系列 1/5）。当日无新版本，为评审背书与 stable 回合建议。

## Maintainer 意见与讨论焦点
Tim Chen 追加 Reviewed-by，并明确「该补丁修的 commit `b636fef85bda` 已回 stable，应 `Cc: stable #v7.2.x`」。此前 Gregory Price、Chen Yu 已 Reviewed-by 且建议拆出单独提交。无反对意见。

## 合入评估
*likelihood=high*。已累计三位 Reviewed-by，方向明确（拆出单独提交 + stable 回合）；*blocking_issues*：无实质卡点；*next_action*：作者单独发送该修复并带 stable 标签。

## 效果评估
编译正确性修复，无性能数据。

## 我可以参与的点
- *kind: review*：确认拆分后的单补丁签名与 stable 回合版本号无误。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261019064157.29885-1-laoar.shao@gmail.com/
- Tim Chen 今日回帖：https://lore.kernel.org/all/cbf93381e02861620b012ace93c816f2c0822fea.camel@linux.intel.com/

---
id: sched-20261022-014
date: 2026-10-22
subject: "sched: fix stale get_pref_llc() stub for !CONFIG_SCHED_CACHE"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261019064157.29885-1-laoar.shao@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261019064157.29885-1-laoar.shao@gmail.com/"
authors: ["Yafang Shao"]
maintainers_involved: []
current_version: v3
patch_series:
  - version: v3
    msgid: "<20261019064157.29885-2-laoar.shao@gmail.com>"
    date: 2026-10-19
    summary: "更新 !CONFIG_SCHED_CACHE 下过期的 get_pref_llc() 桩"
    review_outcome: "Gregory Price / Chen Yu / Tim Chen 三 Reviewed-by，建议拆出单独提交 + stable 回合"
upstream_commit: null
fixes_commit: "b636fef85bda"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "作者单独发送该修复并带 stable 标签"
contribution_opportunities:
  - kind: review
    description: "确认拆分后的单补丁签名与 stable 回合版本号"
generated_at: "2026-10-23T01:20:00"
source_email_count: 1
related_articles: ["sched-20261021-017"]
tags: [cfs]
---