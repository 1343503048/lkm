# sched: Replace nr_iowait_cpu() with a bool accessor

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261014-004：Christian Loehle 发清理补丁——menu governor 已不再消费 per-CPU iowait 计数的大小，剩余调用方只关心「零/非零」，故把 `nr_iowait_cpu()` 改成返回 `bool` 的 `cpu_has_iowait()`，纯重构、无行为变更，当日无 review。
- sched-20261015-014：Peter Zijlstra 回「So I like this」，但困惑为何把 coccinelle 脚本写进 commit message；Christian 发 v2，把 cocci 片段从 commit message 挪走。
- sched-20261016-004（今天）：Prateek 建议把剩余 open-coded 检查也一并换成 `cpu_has_iowait()`，Christian 发 v3（转更多调用点 + 收 Kayra/Prateek 的 R-B 与 Prateek 的 T-B），**当日即被 Peter 合入 tip sched/core（commit b99b7f60c5b4）**。

## 背景与问题
（承接 20261014-004）`nr_iowait_cpu()` 返回 per-CPU iowait 计数的大小，其唯一需要大小值的消费者（menu governor）已删除（`38f83090f515`）。所有 per-CPU 调用方如今只做零/非零判定，却仍拿着一个「大小」接口。今日无新的背景变化，进入收尾合入阶段。

## 技术方案
（承接 v2）`nr_iowait_cpu()` → `bool cpu_has_iowait(int cpu)`，`nr_iowait()` 直接求和保留全局总量，更新 generic 与 s390 idle 记账调用方。v3 新增：把 `account_idle_time()`、`kcpustat_field_vtime()` 等仍 open-coded 的 `atomic_read(&rq->nr_iowait)` 检查也换成 `cpu_has_iowait()`（Prateek 的建议），并收下 tags。合入的 commit 保留 coccinelle 转换规则说明。

## 版本演进与当前进展
- v2（2026-10-15）：按 Peter 意见把 cocci 片段移出 commit message。
- v3（2026-10-16，<20261016073341.575472-1-christian.loehle@arm.com>）：转更多 open-coded 调用点、收 R-B/T-B。
- 当天 Peter 合入 tip sched/core：`b99b7f60c5b4`。

## Maintainer 意见与讨论焦点
Peter Zijlstra 在 v1 就表示「So I like this」，仅对 commit message 里的 cocci 脚本有疑问（v2 已解决）；Prateek 建议扩大转换范围（v3 已采纳）；Kayra、Prateek 给 R-B，Prateek 给 T-B。无分歧。

## 合入评估
*likelihood=merged*。已合入 tip sched/core（commit `b99b7f60c5b4`）。*blocking_issues*：无。*next_action*：无（已合入）。

## 效果评估
无行为/性能变化（纯接口重构）。无量化数据。

## 我可以参与的点
当前阶段已合入，无明显参与空间。

## 参考链接
- tip 合入通知：https://lore.kernel.org/all/179213767317.2666988.5842328125477460793.tip-bot2@tip-bot2/
- v3 patch：https://lore.kernel.org/all/20261016073341.575472-1-christian.loehle@arm.com/

---
id: sched-20261016-004
date: 2026-10-16
subject: "sched: Replace nr_iowait_cpu() with a bool accessor"
subsystem: sched
type: fix
status: merged_tip
severity: none
thread_root_msgid: "<20261016073341.575472-1-christian.loehle@arm.com>"
lore_url: "https://lore.kernel.org/all/20261016073341.575472-1-christian.loehle@arm.com/"
authors: ["Christian Loehle"]
maintainers_involved: ["Peter Zijlstra"]
current_version: v3
patch_series:
  - version: v3
    msgid: "<20261016073341.575472-1-christian.loehle@arm.com>"
    date: 2026-10-16
    summary: "转更多 open-coded 调用点、收 Kayra/Prateek R-B 与 Prateek T-B"
    review_outcome: "当日被 Peter 合入 tip sched/core"
upstream_commit: "b99b7f60c5b4"
fixes_commit: null
merged_branch: "sched/core"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "无（已合入）"
contribution_opportunities: []
generated_at: "2026-10-17T01:30:00"
source_email_count: 4
related_articles: ["sched-20261014-004", "sched-20261015-014"]
tags: [cfs, cpufreq]
---
