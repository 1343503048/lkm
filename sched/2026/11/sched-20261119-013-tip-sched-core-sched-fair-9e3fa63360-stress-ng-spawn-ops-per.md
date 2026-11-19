# [tip:sched/core] [sched/fair]  9e3fa63360: stress-ng.spawn.ops_per_sec 12.8% regression

## TL;DR

Intel 0day（kernel test robot）报告：已进入 tip/sched/core 的 `9e3fa63360`（"sched/fair: Rework/fix task_h_load()"）在 Sapphire Rapids（224 线程、2 socket）上造成 **stress-ng `spawn` 用例 12.8% 的性能回退**（ops_per_sec 17811→15528）。同一报告还列出相邻提交 `e0aeaebb8a`（"sched/fair: Extend for_each_sched_entity() with a back-link"）一并纳入对比基线。当日无维护者回应；`task_h_load()` 重写在 9 月已作为系列讨论过，此为其合入后的首次回归告警。

## 背景与问题

`task_h_load()`（任务层级负载计算）在 9 月经 Mathieu Desnoyers 重写/修复（"sched/fair: Rework/fix task_h_load()"），并于近期进入 tip/sched/core。0day 的 stress-ng 基准发现其合入后，`spawn` 子测试吞吐下降 12.8%。stg-ng `spawn` 高频 fork/exec，对调度路径（含 `task_h_load`、`for_each_sched_entity` 遍历）很敏感，回退指向这两个相邻提交引入的层级遍历/负载计算变化。

## 技术方案

本日仅为回归报告、无补丁。报告给出了精确基线与责任 commit 序（`e0aeaebb8a` → `9e3fa63360`），并把责任 commit 的完整 hash、config（x86_64-rhel-9.4、cpufreq_governor=performance、100% 线程、60s）与复现材料 URL 一并给出，供作者/维护者定位。

## 版本演进与当前进展

*current_version: 无（resgression 报告）*。`9e3fa63360` 已于 tip/sched/core 落地，此为合入后的回归告警，尚无修复。

## Maintainer 意见与讨论焦点

当日无维护者回应。报告按惯例提示「若在单独补丁/commit 修复，请加 `Reported-by: kernel test robot` 与 `Closes` 链接」。

## 合入评估

*likelihood=unknown*。刚报出、无任何人（作者/维护者）回应，无法判断是否会回退该 commit 还是出修复。*blocking_issues*：需作者/维护者确认回退是否真由 `task_h_load()` 引起、并定位具体误差来源。*next_action*：作者复核 `9e3fa63360`/`e0aeaebb8a` 对 fork/exec 路径的层级遍历开销，回帖或出修复。

## 效果评估

0day 实测：stress-ng `spawn` ops_per_sec 由 17811（±stddev）降至 15528，**-12.8%**（ops 绝对值 1067726→930818）；机器为 Sapphire Rapids 224 线程、60s、performance governor。单一用例的单一平台回退，尚无更大范围数据。

## 我可以参与的点

- **testing**：在其他平台/负载（fork/exec 密集类，如 hackbench、lat_syscall fork、unixbench spawn）复测 `9e3fa63360` 相对 `e0aeaebb8a` 的回退，判断是否为普适回退。
- **review**：分析 `task_h_load()` 重写与 `for_each_sched_entity()` back-link 在 spawn 场景下的额外遍历/粒度变化，定位 12.8% 的来源。

## 参考链接

- lore thread（LKP 报告）: https://lore.kernel.org/all/202611191526.fc8f4ad6-lkp@intel.com/
- 复现材料: https://download.01.org/0day-ci/archive/20261119/202611191526.fc8f4ad6-lkp@intel.com

---
id: sched-20261119-013
date: '2026-11-19'
subject: "[tip:sched/core] [sched/fair]  9e3fa63360: stress-ng.spawn.ops_per_sec 12.8% regression"
subsystem: sched
type: regression
status: under_review
severity: high
thread_root_msgid: "<202611191526.fc8f4ad6-lkp@intel.com>"
lore_url: "https://lore.kernel.org/all/202611191526.fc8f4ad6-lkp@intel.com/"
authors: []
maintainers_involved: []
current_version: v1
patch_series: []
upstream_commit: "9e3fa63360bc9ac17619ff076d38d29f57edeb0e"
fixes_commit: null
merged_branch: "sched/core"
merge_assessment:
  likelihood: unknown
  blocking_issues: ["需确认回退来源并定位误差来源"]
  next_action: "作者复核 9e3fa63360/e0aeaebb8a 对 fork/exec 路径开销，回帖或出修复"
contribution_opportunities:
  - kind: testing
    description: "其他平台复测 9e3fa63360 相对 e0aeaebb8a 的回退是否普适"
  - kind: review
    description: "分析 task_h_load 重写与 for_each_sched_entity back-link 在 spawn 场景的开销来源"
generated_at: "2026-11-20T09:00:00+08:00"
source_email_count: 1
related_articles: []
tags: [cfs, load_balance, regression]
---