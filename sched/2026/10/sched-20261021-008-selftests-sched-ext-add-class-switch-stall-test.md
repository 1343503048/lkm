# selftests/sched_ext: Add class_switch_stall test

## TL;DR
Michal Blaszczyk（Google）发往 sched_ext 的 v2 独立补丁：新增 `class_switch_stall` selftest，验证任务在等待中离开 SCHED_EXT 后 `runnable_at` 不会被 watchdog 误判为 stall。当日 Tejun Heo 已将其收取到 `sched_ext/for-7.5`。

## 背景与问题
该测试配套 `sched_ext: Reset runnable_at when a task leaves its scheduler` 修复（见 related_articles）：任务在 SCHED_EXT 之外等待的时间不应计入 crash watchdog 的「等待时长」，否则会误报 stall 并中止调度器。本补丁把该场景固化为可回归的 selftest。

## 技术方案
新增 `selftests/sched_ext/class_switch_stall` 测试：构造任务在 SCHED_EXT 与其它 sched_class 之间切换的时序，断言其不会触发 stall 判定。

## 版本演进与当前进展
*current_version: v2*。v2（`<20261020075029.330343-1-michalblk@google.com>`）当日获 Tejun 收取。

## Maintainer 意见与讨论焦点
Tejun Heo（sched_ext 维护者）直接收取到 `sched_ext/for-7.5`，无额外意见。

## 合入评估
*likelihood=merged*。已由 Tejun 收取到 `sched_ext/for-7.5`。

## 效果评估
属回归测试补丁，无性能数字。

## 我可以参与的点
当前无即时参与点。

## 参考链接
- v2 补丁：https://lore.kernel.org/all/20261020075029.330343-1-michalblk@google.com/
- Tejun 收取回帖：https://lore.kernel.org/all/3438e7928ab1bda677019ee77f40e3dc@kernel.org/

---
id: sched-20261021-008
date: 2026-10-21
subject: "selftests/sched_ext: Add class_switch_stall test"
subsystem: sched
type: fix
status: merged_tip
severity: none
thread_root_msgid: "<20261020075029.330343-1-michalblk@google.com>"
lore_url: "https://lore.kernel.org/all/20261020075029.330343-1-michalblk@google.com/"
authors: ["Michal Blaszczyk"]
maintainers_involved: ["Tejun Heo"]
current_version: v2
patch_series:
  - version: v2
    msgid: "<20261020075029.330343-1-michalblk@google.com>"
    date: 2026-10-21
    summary: "新增 class_switch_stall selftest 覆盖 runnable_at 误判 stall 场景"
    review_outcome: "Tejun 收取到 sched_ext/for-7.5"
upstream_commit: null
fixes_commit: null
merged_branch: "sched_ext/for-7.5"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已收取，无需进一步动作"
contribution_opportunities: []
generated_at: "2026-10-22T01:30:00"
source_email_count: 1
related_articles: ["sched-20261019-012"]
tags: [sched_ext]
---