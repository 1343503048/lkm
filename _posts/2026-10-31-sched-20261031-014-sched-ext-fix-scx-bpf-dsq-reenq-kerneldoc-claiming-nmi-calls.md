---
id: sched-20261031-014
date: 2026-10-31
subject: 'sched_ext: Fix scx_bpf_dsq_reenq() kerneldoc claiming NMI calls are allowed'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <20261029235251.3235814-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20261029235251.3235814-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Andrea Righi
- Tejun Heo
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.4-fixes
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 随 sched_ext 的 v7.4 fixes pull 合入 tip
contribution_opportunities: []
generated_at: '2026-11-01T09:00:00'
source_email_count: 1
related_articles:
- sched-20261030-011
tags:
- sched_ext
title: 'sched_ext: Fix scx_bpf_dsq_reenq() kerneldoc claiming NMI calls are allowed'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/30/sched-20261030-011-sched-ext-fix-scx-bpf-dsq-reenq-kerneldoc-claiming-nmi-calls.html">sched-20261030-011</a>：Tejun Heo 修 sched_ext kerneldoc 与实现不符——`scx_bpf_dsq_reenq()` 在 NMI 会 abort 调度器但文档仍写「Can be called from anywhere」，改为「任意上下文除 NMI」，并顺带修 wrapper 的 DSQ 描述与 `SCX_RENQ_*`→`SCX_REENQ_*` 拼写（纯文档）。当日已获 Andrea Righi Acked-by。
- <a class="article-ref" href="/lkm/2026/10/31/sched-20261031-014-sched-ext-fix-scx-bpf-dsq-reenq-kerneldoc-claiming-nmi-calls.html">sched-20261031-014</a>（今天）：Tejun 标注 **Applied to sched_ext/for-7.4-fixes**，正式进入维护者 fixes 分支。

## 背景与问题
（承接）纯文档一致性修复，无功能风险。今日为合入状态变更，无新增技术信息。

## 技术方案
（承接 20261030-011）`kernel/sched/ext/ext.c` 两处 kerneldoc 修正，无功能性改动。

## 版本演进与当前进展
*current_version: v1*（2026-10-29 发出）。今日合入 `sched_ext/for-7.4-fixes`，附 `Acked-by: Andrea Righi <arighi@nvidia.com>`。

## Maintainer 意见与讨论焦点
Andrea Righi 已 Acked-by（前一版）；Tejun 今日 Applied，无遗留分歧。

## 合入评估
*likelihood=high*。已进维护者 `sched_ext/for-7.4-fixes` 分支。*blocking_issues*：暂无。*next_action*：随 sched_ext 的 v7.4 fixes pull 合入 tip。

## 效果评估
无性能数据；纯文档一致性修复，无运行时影响。

## 我可以参与的点
当前阶段暂无明显参与空间（已进维护者分支）。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261029235251.3235814-1-tj@kernel.org/
