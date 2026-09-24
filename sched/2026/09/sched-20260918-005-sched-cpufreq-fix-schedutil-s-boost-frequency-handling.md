# sched/cpufreq: fix schedutil's boost frequency handling

## TL;DR
增量更新：Ananthu C V 的 schedutil boost 频率处理修复（v2）本日新增一轮 review 与实测——Oleg Keri 在 Lenovo Yoga Slim 7x（scmi-cpufreq）上验证通过并给出 Tested-by；Zhongqiu Han 质疑 Fixes 标签应指向 `6e39ba4e5a82`（cpufreq boost_freq_req QoS），并指出 acpi-cpufreq 场景下"是否有 freq 表"判断不足以覆盖 boost 频率，条件应改为"freq 表是否列有 boost 频率"。

## 背景与问题
背景见 sched-20260915-012：schedutil 在 boost 关闭后仍无法回到非 boost 频率上限。v2 为该 2-patch 系列（1/2 修负 pressure 处理，2/2 修 boost 关闭后 scaling_max_freq 不回落到非 boost 值）。

## 技术方案
沿用 v2 方案，本日关注点是 2/2 的判定条件：作者当前用"是否存在 freq 表"作为依据，但 acpi-cpufreq 有 freq 表却不设置 `CPUFREQ_BOOST_FREQ`，导致 `max_table_freq == max_base_freq == _PSS P0`，真正的 boost 上限（`cpuinfo.max_freq`）丢失。

## 版本演进与当前进展
- v2（09-08，`<20260908-schedutil-boost-frequency-handling-v2-0-25312a713699@oss.qualcomm.com>`）：当前版本，已获 Dietmar Eggemann 认可与 ARM64 Juno 实测、Oleg Keri 本日 Tested-by。

## Maintainer 意见与讨论焦点
- **Zhongqiu Han**：认为 issue 不止限于 schedutil，subject 过于狭窄；重申 Fixes 应为 `6e39ba4e5a82 ("cpufreq: Add boost_freq_req QoS request")`（v1 已提过）；建议区分"freq 表是否列出 boost 频率"（在 `cpufreq_table_validate_and_sort()` 表扫描时记录，类似 `boost_supported` 的推导方式）而非"是否存在 freq 表"。
- **Oleg Keri**：smoke test 通过，`echo 0/1 > boost` 后 scaling_max_freq 正确在 4032000/4723200 间切换；观察点：boost 关闭后 `cpuinfo_max_freq` 仍读 4723200。
- 分歧点：Fixes 标签与判定条件需作者确认/修正。

## 合入评估
*likelihood=high*。方案已获两位维护者/资深成员认可与多平台实测，方向确定；剩余 Zhongqiu 关于 Fixes 标签与判定条件的意见需作者回应。*blocking_issues*：Fixes 标签指向待确认；acpi-cpufreq 无 boost 表场景下的判定条件待修正。*next_action*：作者回应 Zhongqiu 意见，确认/修正 Fixes 与表扫描判定条件后即可推进。

## 效果评估
Oleg Keri 实测（Lenovo Yoga Slim 7x Gen 11，next-20260915）：workload 固定 CPU 在 boost 关/开下跑 4032000/4723200，3.14s vs 2.50s；`scaling_max_freq` 随 boost 开关在 4032000/4723200 间正确切换。另报 cpuinfo_max_freq 在 boost 关闭后仍为 4723200（未解决的次要观察，未见后续结论）。

## 我可以参与的点
- kind=review：确认 Zhongqiu 提出的 Fixes 标签（`6e39ba4e5a82`）与"表是否列 boost 频率"判定是否准确。
- kind=testing：在 acpi-cpufreq + 可 boost 平台复测 2/2，验证无 freq 表 boost 场景下 scaling_max_freq 的回落行为。

## 参考链接
- lore（v2 cover）: https://lore.kernel.org/all/20260908-schedutil-boost-frequency-handling-v2-0-25312a713699@oss.qualcomm.com/

---
id: sched-20260918-005
date: '2026-09-18'
subject: 'sched/cpufreq: fix schedutil''s boost frequency handling'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260908-schedutil-boost-frequency-handling-v2-0-25312a713699@oss.qualcomm.com>'
lore_url: 'https://lore.kernel.org/all/20260908-schedutil-boost-frequency-handling-v2-0-25312a713699@oss.qualcomm.com/'
authors:
  - 'Ananthu C V'
maintainers_involved:
  - 'Zhongqiu Han'
  - 'Oleg Keri'
current_version: v2
patch_series:
  - version: v2
    msgid: '<20260908-schedutil-boost-frequency-handling-v2-0-25312a713699@oss.qualcomm.com>'
    date: '2026-09-08'
    summary: '见 sched-20260915-012；修负 pressure 与 boost 关闭后频率回落'
    review_outcome: 'Dietmar 认可；Oleg Tested-by；Zhongqiu 提 Fixes 与判定条件意见'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - 'Fixes 标签指向（6e39ba4e5a82）待确认'
    - 'acpi-cpufreq 无 boost 表场景下的判定条件待修正'
  next_action: '作者回应 Zhongqiu 意见并修正判定条件'
contribution_opportunities:
  - kind: review
    description: '确认 Fixes 标签与表扫描判定是否准确'
  - kind: testing
    description: '在 acpi-cpufreq + 可 boost 平台复测 2/2 频率回落'
generated_at: '2026-09-19T09:00:00'
source_email_count: 2
related_articles:
  - sched-20260915-012
  - sched-20260908-006
tags:
  - schedutil
  - cpufreq
---