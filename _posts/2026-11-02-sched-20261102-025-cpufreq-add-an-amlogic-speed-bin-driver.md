---
type: feature
status: under_review
severity: none
thread_root_msgid: <20261025192219.209137-1-christian.koever-draxl@student.uibk.ac.at>
authors:
- Christian Köver-Draxl
maintainers_involved: []
current_version: v1
patch_series: []
merge_assessment:
  likelihood: low
  blocking_issues:
  - 驱动命名/代码共享边界未与厂商、平台维护者达成一致
  next_action: 确定命名与边界后再推进
contribution_opportunities:
- kind: discussion
  description: 就 amlogic-s4-cpufreq vs 统一驱动给出意见
- kind: testing
  description: S4/C3 硬件验证 speed-bin 与 ramp-delay
upstream_commit: null
fixes_commit: null
merged_branch: null
source_email_count: 1
related_articles:
- sched-20261027-017
- sched-20261029-016
tags:
- cpufreq
- arm64
id: sched-20261102-025
subject: 'cpufreq: add an Amlogic speed-bin driver'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
title: 'cpufreq: add an Amlogic speed-bin driver'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/27/sched-20261027-017-cpufreq-add-an-amlogic-speed-bin-driver.html">sched-20261027-017</a>：Christian Köver-Draxl 的 Amlogic speed-bin cpufreq 驱动（4/4）讨论起。
- <a class="article-ref" href="/lkm/2026/10/29/sched-20261029-016-cpufreq-add-an-amlogic-speed-bin-driver.html">sched-20261029-016</a>：Amlogic 厂商 Chuan Liu 发长文澄清立场（统一 amlogic-cpufreq.c 规划、先整体评估再定）。
- sched-20261102（今天）：平台侧维护者 Martin Blumenstingl 回帖，给出对「代码在 SoC 代际间可共享多少」的细致回答（Meson8/8b/8m2 需 target_intermediate；GXBB/GXL/GXM 走 SCPI 无需新驱动；G12A/G12B/SM1 各自需 target_intermediate），建议本系列驱动命名为 `amlogic-s4-cpufreq`（C3/T7 可并入），并规划 32-bit 用 `amlogic-meson8-cpufreq`、后续 S7/S7D/S6/A9 由厂商判断合并。

## 背景与问题

（承接）为 Amlogic SoC 增加 speed-bin 分档感知的 cpufreq 驱动；今日收敛到「驱动命名与代码共享边界」的架构讨论。

## 技术方案

今日为架构建议：本系列改名 `amlogic-s4-cpufreq`（C3 乃至 T7 可并入同一驱动）；32-bit 与其它代际另立驱动或由厂商决定合并。

## 版本演进与当前进展

v1 系列；驱动命名/边界仍在上游平台维护者与厂商之间对齐。

## Maintainer 意见与讨论焦点

Martin（meson 平台维护者）给出清晰代际清单与命名建议；与厂商此前的「统一驱动」诉求存在张力（但 Martin 的「多驱动」与 Chuan 的「统一」已在不 named driver 方案上部分靠拢）。

## 合入评估

likelihood=low。驱动命名与代码共享边界尚未达成一致，且厂商起初希望 hold off。

## 效果评估

无性能数据。

## 我可以参与的点

- discussion：就命名（amlogic-s4-cpufreq vs 统一 amlogic-cpufreq）与代码共享边界提供意见。
- testing：在 S4/C3 硬件上验证 speed-bin 与 ramp-delay 行为。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261025192219.209137-1-christian.koever-draxl@student.uibk.ac.at/
