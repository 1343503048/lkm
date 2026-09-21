# sched/cpufreq: fix schedutil's boost frequency handling

## TL;DR
增量更新：Ananthu C V 的 schedutil boost 频率处理修复（v2）昨日有两则作者回复——回应 Oleg 关于 `cpuinfo->max_freq` 只升不降设计的疑问，并接受 Zhongqiu 建议、将在下一版给补丁补上 `Fixes: 538b0188da46` 标签，同时考虑把 `policy_has_boost_freq` 从 freq_table.c 导出复用。修复方向清晰，正按 review 意见迭代。

## 背景与问题
背景见 sched-20260918-005：schedutil 在关闭 boost 后频率无法回落到非 boost 值，根因是 commit 538b0188da46 给 `cpuinfo->max_freq` 加了"只向上更新"的 guard，导致该值降不回来，schedutil 随之持续停留在 boost 频率。

## 技术方案
v2 系列为两补丁：1/2 让 schedutil 的 boost 频率处理在运行时尽量不依赖 `cpuinfo_max_freq`；2/2 修复关闭 boost 后 schedutil 无法回到非 boost 频率。昨日讨论进一步明确：`cpuinfo->max_freq` 的向上 guard 是"为保留驱动设定值"的有意设计，故不能简单移除，需用补丁 1 的方式绕开，并计划复用/导出 `policy_has_boost_freq` 判断逻辑。

## 版本演进与当前进展
- v2（09-08，thread root `<20260908-schedutil-boost-frequency-handling-v2-0-25312a713699@oss.qualcomm.com>`）。
- 09-21：作者回帖两条——向 Oleg 解释 guard 设计；接受 Zhongqiu 的 Fixes 标签建议，明确下一版会更新，并欢迎对"导出 `policy_has_boost_freq`"方案的评论。

## Maintainer 意见与讨论焦点
- **Oleg（回帖者，原邮件不在本日缓存）**：质疑 `cpuinfo->max_freq` 为何无法回落。作者解释这是为保留驱动设定值的有意设计，补丁 2 正是绕过它。
- **Zhongqiu（回帖者）**：建议为该问题补 `Fixes: 538b0188da46`。作者同意，并将在下一版落实。
- 讨论焦点集中在 fix 归属（Fixes 标签）与 helper 复用（`policy_has_boost_freq` 的导出位置），无反对意见。

## 合入评估
likelihood=medium。修复逻辑清晰、有明确 Fixes 指向、作者积极响应 review；仍处 v2 迭代期（需落下一版补 Fixes 标签与 helper 复用），尚未见维护者最终 pickup。

## 效果评估
无新增性能数据。修复的预期效果是关闭 boost 后频率能正确回落到非 boost 值（Oleg 已帮忙测试补丁，作者致谢）。

## 我可以参与的点
- **review**：对"导出/移动 `policy_has_boost_freq` 到公共位置供 schedutil 复用"这一重构给出意见（作者明确欢迎评论）。
- **testing**：在带 boost 能力的 cpufreq 驱动（如 amd-pstate/intel_pstate）上验证关闭 boost 后频率回落的正确性与无回归。

## 参考链接
- lore thread: https://lore.kernel.org/all/20260908-schedutil-boost-frequency-handling-v2-0-25312a713699@oss.qualcomm.com/

---
id: sched-20260921-007
date: '2026-09-21'
subject: "sched/cpufreq: fix schedutil's boost frequency handling"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260908-schedutil-boost-frequency-handling-v2-0-25312a713699@oss.qualcomm.com>'
lore_url: 'https://lore.kernel.org/all/20260908-schedutil-boost-frequency-handling-v2-0-25312a713699@oss.qualcomm.com/'
authors:
  - 'Ananthu C V'
maintainers_involved: []
current_version: v2
patch_series:
  - version: v2
    msgid: '<20260908-schedutil-boost-frequency-handling-v2-0-25312a713699@oss.qualcomm.com>'
    date: '2026-09-08'
    summary: '运行时尽量不依赖 cpuinfo_max_freq 并修复关闭 boost 后频率无法回落'
    review_outcome: '作者回应 Oleg 疑问，接受 Zhongqiu 的 Fixes 标签建议并将在下一版落实'
upstream_commit: null
fixes_commit: '538b0188da46'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: '作者发下一版：补 Fixes 标签、导出并复用 policy_has_boost_freq'
contribution_opportunities:
  - kind: review
    description: '对导出/移动 policy_has_boost_freq 的重构给出意见（作者欢迎评论）'
  - kind: testing
    description: '在带 boost 能力的 cpufreq 驱动上验证关闭 boost 后频率回落正确性'
generated_at: '2026-09-22T01:10:00'
source_email_count: 2
related_articles:
  - sched-20260918-005
tags:
  - cpufreq
---