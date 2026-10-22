---
id: sched-20261022-004
date: 2026-10-22
subject: 'cpufreq: Avoid fallback values in cpuinfo_avg_freq'
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: <20261019065358.66115-1-liu.yun@linux.dev>
lore_url: https://lore.kernel.org/all/202610221936.40b4334f-lkp@intel.com/
authors:
- Jackie Liu
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261019065358.66115-1-liu.yun@linux.dev>
  date: 2026-10-19
  summary: cpuinfo_avg_freq 避免 fallback 值（本体未进入缓存）
  review_outcome: 0-day 报 ltp.runpwtests03.fail
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - ltp.runpwtests03.fail on Haswell
  next_action: 作者核查 cpuinfo_avg_freq 改动为何导致 runpwtests03 失败
contribution_opportunities:
- kind: testing
  description: 在其它平台复现 runpwtests03 失败，协助定位
- kind: review
  description: 核查去 fallback 对 LTP 功率管理测试的预期影响
generated_at: '2026-10-23T01:20:00'
source_email_count: 1
related_articles: []
tags:
- cpufreq
- regression
title: 'cpufreq: Avoid fallback values in cpuinfo_avg_freq'
layout: article
---

## TL;DR
Jackie Liu（liu.yun@linux.dev）10-19 发出的 cpufreq 补丁，当日被 0-day 内核测试机器人（kernel test robot）报出 LTP 功能测试回退：`ltp.runpwtests03.fail`。该补丁的意图是「cpuinfo_avg_freq 不再使用 fallback 值」，但 0-day 在 Haswell i7-4790T 上跑 LTP `power_management_tests` 时 `runpwtests03` 失败。补丁尚未见维护者回帖。

## 背景与问题
`cpuinfo_avg_freq` 在部分平台下会落到 fallback（兜底）频率值，补丁试图去掉这些 fallback 路径。0-day 在 `commit e5f9d99762e2` 上运行 LTP（ltp-x86_64-1255a3be5-1_20261017，x86_64-rhel-9.4-ltp，gcc-14，Haswell i7-4790T 8 线程 1 socket）时，`power_management_tests` 套件中的 `runpwtests03` 失败（`cpufreq_intel` 通过、`runpwtests04/06` 通过）。0-day 建议修复以独立补丁提交时带上 `Reported-by` 与 `Closes` 标签。

## 技术方案
补丁本体未进入当日缓存（只有 0-day 的回帖），具体实现未获取到；仅能确认其目标是「`cpuinfo_avg_freq` 避免 fallback 值」。

## 版本演进与当前进展
*current_version: v1*（thread root `<20261019065358.66115-1-liu.yun@linux.dev>`）。当日新增内容即 0-day 的失败报告，无作者回应。

## Maintainer 意见与讨论焦点
未获取到维护者意见；仅 0-day 自动化 CI 报告一个测试失败。

## 合入评估
*likelihood=low*。补丁触发了 0-day 的 LTP 功能测试失败，合入前需作者定位并修复或解释该回退；*blocking_issues*：`ltp.runpwtests03.fail`（Haswell 上 `power_management_tests`）；*next_action*：作者核查 `cpuinfo_avg_freq` 改动为何导致 `runpwtests03` 失败。

## 效果评估
0-day 报出 `runpwtests03` 失败（0.532s，taited），未见量化性能数据；失败根因未获取到。

## 我可以参与的点
- *kind: testing*：在其它平台/内核版本复现 `runpwtests03` 失败，帮助作者定位是否与 `cpuinfo_avg_freq` 改动相关。
- *kind: review*：核查 `cpuinfo_avg_freq` 去掉 fallback 后对 LTP 功率管理测试的预期影响。

## 参考链接
- 0-day 报告：https://lore.kernel.org/all/202610221936.40b4334f-lkp@intel.com/
- 补丁原贴：https://lore.kernel.org/all/20261019065358.66115-1-liu.yun@linux.dev/
