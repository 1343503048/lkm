---
id: sched-20261007-012
date: '2026-10-07'
subject: 'cpufreq: qcom-nvmem: Add IPQ9650 support'
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: <20261007-ipq9650_cpufreq-v1-1-bb808da4ab2c@oss.qualcomm.com>
lore_url: https://lore.kernel.org/all/20261007-ipq9650_cpufreq-v1-1-bb808da4ab2c@oss.qualcomm.com/
authors:
- Kathiravan Thirumoorthy
maintainers_involved:
- Dmitry Baryshkov
- Viresh Kumar
current_version: v1
patch_series:
- version: v1
  msgid: <20261007-ipq9650_cpufreq-v1-1-bb808da4ab2c@oss.qualcomm.com>
  date: '2026-10-07'
  summary: IPQ9650 加 blocklist + QCOM_ID speedbin 版本映射
  review_outcome: Dmitry R-b；Viresh 当日 Applied
upstream_commit: null
fixes_commit: null
merged_branch: cpufreq tree (Viresh)
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 随下个合并窗口进主线
generated_at: '2026-10-08T01:00:00'
contribution_opportunities: []
source_email_count: 3
related_articles: []
tags:
- cpufreq
title: 'cpufreq: qcom-nvmem: Add IPQ9650 support'
layout: article
---

> **subject**：`cpufreq: qcom-nvmem: Add IPQ9650 support`

## TL;DR

Kathiravan Thirumoorthy（Qualcomm）的 +10 行 SoC 使能补丁：给 Qualcomm NVMEM cpufreq 驱动加 IPQ9650 支持——用 eFuse speedbin 值在运行时选出受支持的 OPP（`opp-supported-hw` 属性），并把 IPQ9650 加进 cpufreq-dt 平台设备的 blocklist，确保走 NVMEM 驱动而非通用 dt 驱动。Qualcomm 的 Dmitry Baryshkov 当日给 `Reviewed-by`，cpufreq 维护者 Viresh Kumar **6 分钟后即 Applied**——当天闭环收取。

## 背景与问题

Qualcomm IPQ 系 SoC 的可用频率集由 eFuse 里烧录的 speedbin（版本/丝印分级）决定：同一 SoC 不同 bin 支持不同 OPP 上限。通用 `cpufreq-dt` 平台设备不解析 speedbin，会在这些 SoC 上选错 OPP；`qcom-cpufreq-nvmem` 驱动负责读 eFuse 并与 DT 里各 OPP 的 `opp-supported-hw` 匹配。IPQ9650 此前两处都缺：驱动版本表没有它的 QCOM_ID，cpufreq-dt blocklist 也没有它的 compatible，导致驱动不绑定。

## 技术方案

`drivers/cpufreq/cpufreq-dt-platdev.c` +1、`drivers/cpufreq/qcom-cpufreq-nvmem.c` +9：

- blocklist 增 `{ .compatible = "qcom,ipq9650" }`（与既有 ipq8064/8074/9574 并列）。
- 驱动的版本映射 switch 增加对应 QCOM_ID case，按 `*speedbin` 值设置 `drv->versions` 位（供 `opp-supported-hw` 匹配）。

## 版本演进与当前进展

- v1（10-07 15:01，`<20261007-ipq9650_cpufreq-v1-1-bb808da4ab2c@oss.qualcomm.com>`）。
- 15:07 Dmitry Baryshkov `Reviewed-by`；15:09 Viresh Kumar「Applied. Thanks.」——从发出到收取 8 分钟。

## Maintainer 意见与讨论焦点

无技术讨论：Dmitry 的回帖只有 R-b tag，Viresh 只确认收取。焦点为零——纯 SoC 使能，模式与此前 ipq9574 等条目完全同构。

## 合入评估

*likelihood=merged*。Viresh 已 Applied（cpufreq 树），随下个合并窗口进主线。*blocking_issues*：无。

## 效果评估

无 benchmark；效果是使能性的——IPQ9650 设备上 cpufreq 正确按 speedbin 选 OPP、避免越 bin 跑不支持的最高频。

## 我可以参与的点

- 无实质参与空间（已收取）；若维护 IPQ 类平台的发行版内核，回合时注意 blocklist 与驱动两侧需成对出现，只回合一侧会导致驱动不绑定或 OPP 误选。

## 参考链接

- 补丁: https://lore.kernel.org/all/20261007-ipq9650_cpufreq-v1-1-bb808da4ab2c@oss.qualcomm.com/
- Dmitry 的 R-b: https://lore.kernel.org/all/tnmm2misly3wct7out4gybimrql42si47trcoygaquan2gm2w7@rzqqkefwdmvh/
- Viresh 的收取: https://lore.kernel.org/all/asXwHVcEyf0fpvhP@vireshk-B250M-D3H/
