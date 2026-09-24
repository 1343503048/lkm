# cpufreq: fix schedutil not returning to non-boost freq when boost is disabled

## TL;DR
本文为增量更新，完整背景见 sched-20260921-007（该系列 cover 标题为 sched/cpufreq: fix schedutil's boost frequency handling）。当天 Zhongqiu Han 在 SM8850（SCMI 驱动）上复测，给出精确定位：问题由 `db80ad776cd2`（"cpufreq: Remove driver default policy->min/max init"）引入，而 `538b0188da46`、`6e39ba4e5a82` 均未复现。测试结论与 v1 反馈一致，补丁方向获进一步佐证。

## 背景与问题
背景见 sched-20260921-007：schedutil 在 boost 关闭后不回落到非 boost 频率。该系列的 2/2 补丁修复此问题。

## 技术方案
方案见 sched-20260921-007（2/2）。当天无新代码。

## 版本演进与当前进展
系列 v2（cover `<20260908-schedutil-boost-frequency-handling-v2-0-25312a713699@oss.qualcomm.com>`）。当天 Zhongqiu Han 对 2/2 回复测试结果。

## Maintainer 意见与讨论焦点
- **Zhongqiu Han**（测试者）：在 SM8850 SCMI 驱动上复测，三个 commit 逐一验证——`538b0188da46`（cpufreq: ACPI 直接设 cpuinfo.max_freq）未复现、`6e39ba4e5a82`（boost_freq_req QoS）未复现、`db80ad776cd2`（移除驱动默认 policy->min/max init）**复现**。并解释了根因链条：`538b0188da46` 让 cpuinfo.max_freq 只增不减、boost 使能后钉在 boost 频率；因 `cpufreq_frequency_table_cpuinfo()` 同时把 policy->max 直接赋为 max_freq（每次按 boost 状态重算）故无伤；`6e39ba4e5a82` 把 boost QoS 更新移到 dirty 的 cpuinfo.max_freq 上但该值关闭时不变、`freq_qos_update_request()` 提前 bail、`cpufreq_set_policy()` 不触发，直接写入的 policy->max 幸存，问题仍不可见；`db80ad776cd2` 之后才暴露。结论与作者 v1 评论一致。
- 无反对意见。

## 合入评估
*likelihood=medium*（维持 sched-20260921-007 判断）。测试佐证补丁方向正确、问题 commit 已定位，但当日未见维护者最终合入表态。blocking_issues 见 sched-20260921-007；*next_action*：等待维护者基于定位结论收取或要求改版。

## 效果评估
无量化数字；Zhongqiu 给出问题引入 commit 的二分定位（`db80ad776cd2`）与因果链条，佐证修复必要性。

## 我可以参与的点
- **testing**：在其它 cpufreq driver（非 SCMI/ACPI）上复测，扩大修复覆盖验证。
- **review**：核对 2/2 修复是否在所有 driver default 初始化路径上覆盖 `db80ad776cd2` 引入的回归。

## 参考链接
- lore（v2 cover）: https://lore.kernel.org/all/20260908-schedutil-boost-frequency-handling-v2-0-25312a713699@oss.qualcomm.com/
- Zhongqiu 测试回复: https://lore.kernel.org/all/4f0915c0-5950-4e45-a72b-0db2942f00b5@oss.qualcomm.com/

---
id: sched-20260922-019
date: '2026-09-22'
subject: 'cpufreq: fix schedutil not returning to non-boost freq when boost is disabled'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<4f0915c0-5950-4e45-a72b-0db2942f00b5@oss.qualcomm.com>'
lore_url: 'https://lore.kernel.org/all/4f0915c0-5950-4e45-a72b-0db2942f00b5@oss.qualcomm.com/'
authors:
  - 'Ananthu C V'
maintainers_involved: []
current_version: v2
patch_series:
  - version: v2
    msgid: '<20260908-schedutil-boost-frequency-handling-v2-0-25312a713699@oss.qualcomm.com>'
    date: '2026-09-08'
    summary: '系列 v2（见 sched-20260921-007）'
    review_outcome: 'Zhongqiu 复测定位 db80ad776cd2 引入回归'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: '等待维护者基于定位结论收取或要求改版'
contribution_opportunities:
  - kind: testing
    description: '在其它 cpufreq driver 上复测，扩大修复覆盖验证'
  - kind: review
    description: '核对 2/2 是否覆盖 db80ad776cd2 引入回归的所有 driver 默认初始化路径'
generated_at: '2026-09-23T00:00:00'
source_email_count: 1
related_articles:
  - sched-20260921-007
tags:
  - cpufreq
---