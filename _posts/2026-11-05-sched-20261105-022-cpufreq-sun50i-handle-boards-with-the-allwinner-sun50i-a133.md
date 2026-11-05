---
id: sched-20261105-022
date: 2026-11-05
subject: 'cpufreq: sun50i: Handle boards with the allwinner,sun50i-a133 compatible'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261104-a133-fix-v1-1-d0b5ad3d4c5d@gmail.com>
lore_url: https://lore.kernel.org/all/20261104-a133-fix-v1-1-d0b5ad3d4c5d@gmail.com/
authors:
- Rajan Yadav
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261104-a133-fix-v1-1-d0b5ad3d4c5d@gmail.com>
  date: 2026-11-04
  summary: 把 sun50i-a133 compatible 加进 sun50i 驱动与 cpufreq-dt-platdev blocklist。
  review_outcome: 刚发出，暂无 review。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: 等 sunxi/cpufreq 维护者评审；说明与 6 补丁系列关系
contribution_opportunities:
- kind: testing
  description: 在 A133 板验证 DVFS 与频率切换稳定
- kind: review
  description: 核对 blocklist 收录与配套系列是否冲突
generated_at: '2026-11-06T09:00:00+08:00'
source_email_count: 3
related_articles: []
tags:
- cpufreq
title: 'cpufreq: sun50i: Handle boards with the allwinner,sun50i-a133 compatible'
layout: article
---

## TL;DR

Rajan Yadav 修 sun50i cpufreq 对 A133 的支持：Teclast P80 只以 `allwinner,sun50i-a133` 作为 SoC compatible，但 sun50i 驱动与 cpufreq-dt-platdev blocklist 都没列它，导致 cpufreq-dt 自行 probe、只找到 `opp-microvolt-speedN` 属性而失败（OPP 表为空），整板无 CPU 变频。补丁把该 compatible 加进两处，已在本块 A133 板（KickPi K5C）验证。作者另有一份 6 补丁的 A133 速度分级系列（本窗口只到 2/6、3/6）在并行推进。

## 背景与问题

`allwinner,sun50i-a133` 出现在 arm/sunxi.yaml binding 中，但 sun50i cpufreq 驱动与 cpufreq-dt-platdev 的 blocklist 都未收录。于是 cpufreq-dt 通用驱动自己 probe，只能解析到 `opp-microvolt-speedN` 属性、缺 `opp-microvolt`，最终 `_of_add_opp_table_v2` 失败、OPP 表为空，整板失去 DVFS。

## 技术方案

把 `allwinner,sun50i-a133` 加进 sun50i cpufreq 驱动的兼容列表与 cpufreq-dt-platdev 的 blocklist。另有 6 补丁配套系列（`Add A133 speed grade detection`、`Move nvmem cell reading into a helper` 等）为 A133 引入更完整的速度分级支持。

## 版本演进与当前进展

*current_version: v1（独立修复，2026-11-04 发出）*。今日无回复。配套 6 补丁 A133 系列同窗口发出（仅 2/6、3/6 在缓存中）。

## Maintainer 意见与讨论焦点

暂无回复，本日无讨论。

## 合入评估

*likelihood=medium*。自包含的 compatible 补充 + 已实测，但无维护者表态，且与 6 补丁速度分级系列的关系需作者说明（避免两系列对同一驱动/设备树的改动冲突）。*blocking_issues*：暂无（等待评审）。*next_action*：等 sunxi/cpufreq 维护者评审；建议作者说明独立修复与 6 补丁系列的关系。

## 效果评估

作者在 KickPi K5C（A133，仅 `allwinner,sun50i-a133` compatible）上验证：修复前 cpufreq 如上失败，修复后 sun50i 驱动正常 probe 并建立 OPP 表、恢复变频。

## 我可以参与的点

- testing：在 A133 板验证修复后 DVFS 与热点的频率切换稳定。
- review：核对 blocklist 收录是否会与配套 6 补丁系列对 sun50i 驱动的改动冲突。

## 参考链接

- lore thread（独立修复）: https://lore.kernel.org/all/20261104-a133-fix-v1-1-d0b5ad3d4c5d@gmail.com/
- 配套 6 补丁系列 cover: https://lore.kernel.org/all/20261104-a133-series-v1-0-58217cb33a87@gmail.com/
