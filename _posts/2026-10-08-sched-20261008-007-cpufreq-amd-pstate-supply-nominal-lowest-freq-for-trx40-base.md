---
id: sched-20261008-007
subject: 'cpufreq/amd-pstate: Supply nominal/lowest freq for TRX40-based motherboards'
date: '2026-10-08'
subsystem: sched
type: discussion
status: superseded
severity: none
thread_root_msgid: null
lore_url: null
authors:
- Giovanni Gherdovich
maintainers_involved:
- Mario Limonciello
current_version: v1
patch_series:
- version: v1
  msgid: null
  date: null
  summary: 为 TRX40 主板缺 nominal/lowest 频率补 quirk（原补丁不在当日窗口）
  review_outcome: 最新 BIOS 修复了问题，结论 drop
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - 问题已由最新 BIOS 修复，quirk 无必要
  next_action: 作者 drop 补丁；若有无法升级固件的受困平台再评估三档核数 quirk
contribution_opportunities: []
generated_at: '2026-10-09T01:00:00'
source_email_count: 11
related_articles:
- sched-20261007-011
tags:
- cpufreq
- x86
title: 'cpufreq/amd-pstate: Supply nominal/lowest freq for TRX40-based motherboards'
layout: article
---

## TL;DR

这是一条以「补丁被放弃」收尾的 cpufreq 讨论：Giovanni Gherdovich 早前为 MSI TRX40 主板（Ryzen Threadripper 3960X）提的 quirk——在该类主板 ACPI `_CPC` 包缺失 nominal/lowest 频率、导致 amd-pstate 无法加载时硬补频率——在多名同平台用户升级最新 BIOS 后确认问题已由固件修复，作者与其他测试者均确认 amd-pstate 可正常加载、无性能问题。AMD 维护者 Mario Limonciello 明确「更希望不背这个 quirk」。结论：补丁将被 drop。原补丁不在当日窗口，本日全部为回复讨论。

## 背景与问题

TRX40 平台（AMD Ryzen Threadripper 3960X 等）早期 BIOS 的 ACPI `_CPC` 表不提供 nominal/lowest 频率，amd-pstate 因此无法在这些机器上加载，用户只能 `amd_pstate.enable=0` + `initcall_blacklist=amd-pstate` 禁用（Kyle 描述：不禁用则「系统开机要 15 分钟才到桌面」）。作者提出 quirk 补丁，按 family 0x17、model 0x30-0x3f 匹配，但 nominal 频率随核数不同（24 核 3800 MHz、32 核 3700 MHz、64 核 2900 MHz），故作者最终按 family+model+24 核约束匹配。

## 技术方案

方案本身即「匹配 family/model/核数、在缺失时注入 nominal/lowest 频率」的 quirk，本日无新代码。讨论的核心转向「是否还需要这个 quirk」——Kyle 与 Giovanni 分别在自家 MSI TRX40 主板上发现并升级了最新 BIOS（1.A4 / 2.94，均 2026-06 发布），升级后 `_CPC` 中 nominal/lowest 频率齐备、amd-pstate(-epp) 正常加载且无性能问题。Mario Limonciello 的观点成为结论：若有固件修复就不该背 quirk；若将来仍需 quirk，则应为三种核数各做一个（三档 nominal 不同）。

## 版本演进与当前进展

原补丁（v1）见 <a class="article-ref" href="/lkm/2026/10/07/sched-20261007-011-cpufreq-amd-pstate-supply-nominal-lowest-freq-for-trx40-base.html">sched-20261007-011</a>（10-07 发出并获 Mario 初审），本日全部为 `Re:` 讨论（11 封）。进展收敛到「drop」：Giovanni 明确「The patch can be dropped, as the latest BIOS release fixes the problem」，Mario 回复「Great news, thanks!」。

## Maintainer 意见与讨论焦点

- **Mario Limonciello**（AMD amd-pstate 维护者）：不愿为已被最新 BIOS 修复的问题背 quirk（「I would much rather not carry a quirk like this if it has been fixed in latest BIOS」）；并指出若真要做 quirk，应为 24/32/64 核三档各做一个。
- **Giovanni Gherdovich**（作者）：确认自家主板的 BIOS 更新修复了问题，决定 drop；总结了硬件与固件信息（MSI TRX40 PRO WIFI / 3960X / BIOS 2.94）。
- **Kyle Gospodnetich**（同平台用户）：确认最新 BIOS 修复、amd-pstate-epp 正常、无性能问题。
- 无 NAK 性质的反对；结论是「不需要这个补丁」。

## 合入评估

*likelihood=low*。补丁将被作者放弃，不会合入；这不是 review 上的分歧，而是外部条件（最新 BIOS 修复）消解了补丁的必要性。*blocking_issues*：问题本身已由固件修复，quirk 无必要。*next_action*：作者 drop 补丁；若未来出现仍受影响且无法升级固件的平台，再按 Mario 的「三档核数 quirk」建议评估是否重提。

## 效果评估

本日数据是「行为正确性」而非性能：Kyle 与 Giovanni 升级 BIOS 后 `cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_driver` 均显示 amd-pstate(-epp)，且「no performance issues」。未量化与 acpi-cpufreq 或禁用状态的性能差异。

## 我可以参与的点

当前阶段无明显参与空间——补丁方向已定（drop）。唯一可做的是：若手上有仍受该固件缺失影响、又无法升级 BIOS 的 TRX40 平台，可回帖告知，以判断是否仍需按「三档核数」方案重提 quirk。

## 参考链接

- 原补丁不在当日缓存，Message-ID 未获取到（`thread_root_msgid` 置 null）。
- Giovanni 的 drop 结论: https://lore.kernel.org/all/93ad2855-d876-4df3-a105-f08d93dc7d7d@suse.cz/
- Kyle 的 BIOS 修复确认: https://lore.kernel.org/all/bK7n7j4SGpNNcHzUh7I63T_Ozbd5u6wVHdVlpa3Ym76UQs2PhQDtaREPYuFsHMKZku0B9v2-d8A9PdeBRx_0l0xUZ9gt--wxwyI4-sTKfyM=@kylegospodneti.ch/
