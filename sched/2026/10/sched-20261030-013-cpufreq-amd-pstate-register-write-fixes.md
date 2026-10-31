# cpufreq/amd-pstate register write fixes

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261029-013：Christian Loehle（Arm）在把 AMD 机器纳入 acpi-cppc 测试时发现两个 amd-pstate 寄存器写值缺陷，发 2 补丁：① minimum 性能 hint 可超 policy 上限、旧逻辑反而把 `max_perf` 抬到 `min_perf`，改为把 `min_perf` 钳到 `max_limit_perf`；② resume 路径把 `policy->cur` 换算回 Desired 时向上取整可能超上限。
- sched-20261030-013（今天）：K Prateek Nayak（AMD）给整系列 **Reviewed-by + Tested-by**；amd-pstate 维护者 Mario Limonciello 回「Thanks for the fixes. I'll pick them up for 7.4-rc2.」并给 **Acked-by**——系列已定档进入 7.4-rc2。

## 背景与问题
（承接 20261029-013）两个 amd-pstate 寄存器写值缺陷不变：① minimum perf hint 可超过 policy 上限（如 schedutil 遇到要满容量的 RT 任务时），旧逻辑 `min_perf > max_perf` 时反过来抬 `max_perf`，突破 policy cap；② resume 时把 `policy->cur`（频率）换算回 Desired（性能值）因向上取整可能超出 `max_limit_perf`（实测 Ryzen 5 7430U 固定 1.2GHz policy：Desired=46 → cur=1216621 kHz → 换算回 Desired=47）。今日无新背景，为 AMD 侧 review/test 背书与合入定档。

## 技术方案
（承接 v1，2 补丁、1 文件 2 增 2 删）① 把 `min_perf` 钳到 `max_limit_perf`，避免反向抬 `max_perf`；② resume 换算时对 Desired 做上限钳制。今日无新代码；K Prateek 在 AMD 平台实测通过，Mario 决定 7.4-rc2 收取。

## 版本演进与当前进展
*current_version: v1*（2026-10-29 发出）。今日获 AMD 侧 Reviewed-by + Tested-by + Acked-by，定档 7.4-rc2 合入。

## Maintainer 意见与讨论焦点
- **Mario Limonciello（amd-pstate maintainer）**：Acked-by，明确「I'll pick them up for 7.4-rc2」。
- **K Prateek Nayak（AMD）**：全系列 Reviewed-by + Tested-by（实测背书）。
- 无遗留分歧。

## 合入评估
*likelihood=merged*（维护者已承诺 7.4-rc2 收取，带 Tested-by 实测）。*blocking_issues*：无。*next_action*：Mario 在 7.4-rc2 窗口提交至 Rafael 的 pm 树。

## 效果评估
K Prateek 未给出具体数值，仅「Tested-by」背书；此前作者的 Ryzen 5 7430U resume 换算 Desired 46→47 的越界为实测案例。

## 我可以参与的点
当前阶段已定档合入，暂无明显参与空间；可关注 7.4-rc2 落点与是否有 stable 回合需求。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261029121945.854675-1-christian.loehle@arm.com/

---
id: sched-20261030-013
date: 2026-10-30
subject: "cpufreq/amd-pstate register write fixes"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261029121945.854675-1-christian.loehle@arm.com>"
lore_url: "https://lore.kernel.org/all/20261029121945.854675-1-christian.loehle@arm.com/"
authors: [Christian Loehle]
maintainers_involved: [Mario Limonciello]
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "Mario 在 7.4-rc2 窗口提交至 Rafael 的 pm 树"
contribution_opportunities: []
generated_at: "2026-10-31T09:00:00"
source_email_count: 2
related_articles: [sched-20261029-013]
tags: [cpufreq]
---