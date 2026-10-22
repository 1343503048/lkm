---
id: sched-20261022-002
date: 2026-10-22
subject: 'cpuidle: psci: Allow skipping the suspend mode switch'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261022-psci-fix-v3-0-9ce2133c5659@gmail.com>
lore_url: https://lore.kernel.org/all/20261022-psci-fix-v3-2-9ce2133c5659@gmail.com/
authors:
- Alejandro Tafalla
- Reza Kurniawan
maintainers_involved: []
current_version: v3
patch_series:
- version: v3
  msgid: <20261022-psci-fix-v3-2-9ce2133c5659@gmail.com>
  date: 2026-10-22
  summary: 新增 skip-suspend-mode-switch 属性，跳过 psci_set_osi_mode()
  review_outcome: 当日无回帖
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: 等待 cpuidle/PSCI 维护者评审
contribution_opportunities:
- kind: testing
  description: 在受影响 SoC 上验证 skip-suspend-mode-switch 能通过 probe
generated_at: '2026-10-23T01:20:00'
source_email_count: 1
related_articles: []
tags:
- idle
title: 'cpuidle: psci: Allow skipping the suspend mode switch'
layout: article
---

## TL;DR
Reza Kurniawan（与 Alejandro Tafalla 合著）v3 系列的 2/4 补丁：部分 SoC（如高通 MSM8917/MSM8937）报 OSI 模式受支持、却对 `PSCI_SET_SUSPEND_MODE` 返回 NOT_SUPPORTED，导致 `psci_set_osi_mode()` 失败、驱动 probe 直接中止。新增 `skip-suspend-mode-switch` 设备树属性，命中时跳过模式切换、沿用已构建的拓扑继续。当日无回帖。

## 背景与问题
`psci-cpuidle-domain` 挂载时，若固件声称支持 OSI 却又拒绝设置 suspend mode，会得到 `-95 (-EOPNOTSUPP)` 并使 probe 失败，输出「probe with driver psci-cpuidle-domain failed with error -95」。高通 MSM8917/MSM8937 等 SoC 即属此类：PSCI 报 OSI 支持但拒绝任何 `PSCI_SET_SUSPEND_MODE` 调用。

## 技术方案
v3 2/4，改 `drivers/cpuidle/cpuidle-psci-domain.c`（+16/-6，含日志）与 `drivers/firmware/psci/psci.c`（+6/-2）：当设备树含 `skip-suspend-mode-switch` 属性时，不调用 `psci_set_osi_mode()`，直接沿用已构建的 PM domain 拓扑，并在 PSCI 初始化路径同样跳过默认「切到 PC 模式」的调用，日志区分「keeping firmware-set mode」与「using OSI/PC mode」。此前版本已在属性命名、日志与属性检查时机上随评审迭代。

## 版本演进与当前进展
*current_version: v3*（`<20261022-psci-fix-v3-2-9ce2133c5659@gmail.com>`）。当日仅缓存到 2/4 一封，封面（0/4）与其余补丁未进入缓存；无当日评审回帖。v1/v2 演进细节未获取到。

## Maintainer 意见与讨论焦点
未获取到当日维护者或评审意见。

## 合入评估
*likelihood=unknown*。属 cpuidle/firmware 设备树扩展，当日无任何回帖；*blocking_issues*：是否被接受未可知；*next_action*：等待 cpuidle/PSCI 维护者评审。

## 效果评估
无量化数据；修复目标是让受影响 SoC 能正常挂载 psci-cpuidle-domain 而不是 probe 失败。

## 我可以参与的点
- *kind: testing*：在受影响 SoC（MSM8917/8937 或其它「报 OSI 支持却拒绝 SET_SUSPEND_MODE」的平台）验证 `skip-suspend-mode-switch` 属性能通过 probe。

## 参考链接
- lore patch: https://lore.kernel.org/all/20261022-psci-fix-v3-2-9ce2133c5659@gmail.com/
- 封面 0/4：https://lore.kernel.org/all/20261022-psci-fix-v3-0-9ce2133c5659@gmail.com/
