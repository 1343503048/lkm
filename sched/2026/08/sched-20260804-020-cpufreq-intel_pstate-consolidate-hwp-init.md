# cpufreq: intel_pstate: Consolidate HWP P-states initialization

# cpufreq: intel_pstate 整合 HWP P-state 初始化

## TL;DR
Rafael 重构 intel_pstate 的 HWP P-state 初始化：引入 `intel_pstate_get_hwp_pstates()` 统一 HWP 专属初始化，移除冗余的 `intel_pstate_hybrid_hwp_adjust()` 及其 kerneldoc。声明无功能影响，低严重度清理，合入可能性 high。

## 背景与问题
intel_pstate 在 HWP 启用系统上的 P-state 初始化分散在 `intel_pstate_hybrid_hwp_adjust()` 与 `intel_pstate_get_cpu_pstates()` 的条件分支中，可读性差；且前者名称与 kerneldoc 已与实际行为不符（经先前改动后该函数所剩不多）。

## 技术方案
引入 `intel_pstate_get_hwp_pstates()` 承接全部 HWP 专属 P-state 初始化，把 `intel_pstate_hybrid_hwp_adjust()` 的代码移入其中并删除该函数及其不再必要的 kerneldoc。HWP 相关代码从 `intel_pstate_get_cpu_pstates()` 一并归集。

## 版本演进与当前进展
v1（2026-08-04），作者 Rafael J. Wysocki（cpufreq 维护者本人）。

## Maintainer 意见与讨论焦点
作者即 maintainer，预期顺利。Srinivas Pandruvada 等可能 ack。

## 合入评估
合入可能性 high。低风险重构，无功能影响。

## 效果评估
无基准；属代码可读性重构，效果以「初始化路径清晰、无行为回归」衡量。

## 我可以参与的点
可审阅重构后 HWP P-state 初始化在 hybrid/非 hybrid 机型上行为是否完全一致，回帖确认无回归。

## 参考链接
- lore thread: 未获取到

---
subject: "cpufreq: intel_pstate: Consolidate HWP P-states initialization"
id: sched-20260804-020
date: 2026-08-04
subsystem: cpufreq
type: cleanup
status: under_review
severity: low
thread_root_msgid: "<unknown>"
lore_url: "unknown"
authors: [Rafael J. Wysocki]
maintainers_involved: [Rafael J. Wysocki, Srinivas Pandruvada]
current_version: v1
patch_series:
  - version: v1
    msgid: "<unknown>"
    date: 2026-08-04
    summary: "intel_pstate 重构 HWP P-state 初始化：引入 intel_pstate_get_hwp_pstates() 统一 HWP 专属初始化，把 intel_pstate_hybrid_hwp_adjust() 的代码并入并移除其冗余 kerneldoc，使初始化路径更易读。声明无功能影响。"
    review_outcome: "v1 刚发，作者即 maintainer（Rafael），预期顺利合入 cpufreq 树。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待 Srinivas Pandruvada 等 ack 后进入 cpufreq-next。"
contribution_opportunities: []
generated_at: "2026-08-05T00:25:00"
source_email_count: 1
related_articles: []
tags: [cpufreq, intel_pstate]
---
