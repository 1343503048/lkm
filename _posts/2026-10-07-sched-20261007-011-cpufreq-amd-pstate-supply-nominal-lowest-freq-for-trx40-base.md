---
id: sched-20261007-011
date: '2026-10-07'
subject: 'cpufreq/amd-pstate: Supply nominal/lowest freq for TRX40-based motherboards'
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: <20261007144150.15113-1-ggherdovich@suse.cz>
lore_url: https://lore.kernel.org/all/20261007144150.15113-1-ggherdovich@suse.cz/
authors:
- Giovanni Gherdovich
maintainers_involved:
- Mario Limonciello
current_version: v1
patch_series:
- version: v1
  msgid: <20261007144150.15113-1-ggherdovich@suse.cz>
  date: '2026-10-07'
  summary: TRX40 24 核 SKU quirk：注入 nominal 3800/lowest 550
  review_outcome: Mario 方向认可 + 三追问（核数匹配/缺值语义/系统明细）
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 核数参与匹配的合理性待论证
  - 受影响系统明细未补齐
  next_action: 回答追问并补信息（次日实际以 BIOS 已修复为由放弃）
generated_at: '2026-10-08T01:00:00'
contribution_opportunities:
- kind: discussion
  detail: 回答 TRX40 三档核数 nominal freq 差异下的匹配拆分问题
source_email_count: 4
related_articles: []
tags:
- cpufreq
- x86
title: 'cpufreq/amd-pstate: Supply nominal/lowest freq for TRX40-based motherboards'
layout: article
---

> **subject**：`cpufreq/amd-pstate: Supply nominal/lowest freq for TRX40-based motherboards`

## TL;DR

Giovanni Gherdovich（SUSE）为 TRX40 芯片组主板（AMD Ryzen Threadripper 3000 系）补 amd-pstate 加载失败的固件缺口：部分该类主板的 ACPI `_CPC` 包**缺失 lowest 与 nominal frequency 字段**（支持 CPPC V2 而非 V3），且无固件更新可用；amd-pstate 必须知道 nominal frequency 才能加载，于是这些机器上驱动直接不可用。补丁走 amd-pstate 既有的 quirks 机制——按 CPU family（0x17）、model（0x30-0x3F）、**每包核数==24** 匹配后注入 `nominal_freq=3800`/`lowest_freq=550`，+31 行。AMD 维护者 Mario Limonciello 当日介入：确认这正是 Kyle Gospodnetich 线下找过他的同款问题、认可「BIOS 不会再修的老硬件」正是 quirk 的适用场景，但对「为什么核数参与匹配」连续追问（换 CPU 到其它型号 CPPC 就正常吗？BIOS bug 是缺值而非错值对吧？），并要求补充主板厂商/型号/BIOS 信息。次日该线以「最新 BIOS 已修复、补丁放弃」收尾（<a class="article-ref" href="/lkm/2026/10/08/sched-20261008-007-cpufreq-amd-pstate-supply-nominal-lowest-freq-for-trx40-base.html">sched-20261008-007</a>）。

## 背景与问题

TRX40 平台早期 BIOS 的 `_CPC` 表不提供 nominal/lowest frequency（CPPC V2 形态）；amd-pstate 的 `freq_to_perf()` 等换算依赖显式 nominal freq，缺值即无法加载，用户只能 `amd_pstate.enable=0` + initcall 黑名单禁用（Kyle 描述不禁用时开机异常缓慢）。驱动已有 quirk 机制处理「ACPI 表缺 nominal freq」的先例（`quirk_amd_7k62`），本补丁为 TRX40 增加第二个 quirk 条目。难点在匹配条件：同 family/model 下 24 核与 32/64 核 SKU 的 nominal 频率不同（3800/3700/2900 MHz），作者选择按「family+model+24 核」收窄到单一已知 SKU。

## 技术方案

`drivers/cpufreq/amd-pstate.c` +31：

- 新增 `quirk_amd_ryzen_threadripper_3000_24c`：`nominal_freq = 3800`、`lowest_freq = 550`。
- 新增 `dmi_matched_trx40_bios_bug()`：`x86 == 0x17 && x86_model ∈ [0x30, 0x3F] && topology_num_cores_per_package() == 24` 时启用 quirk 并打 `pr_info`。
- 注册进 `amd_pstate_quirks_table[]`（DMI 匹配表）。

Mario 的三个 review 追问（待答）：

1. **核数为何参与匹配**：换一颗不同核数的 CPU（同 family/model 区间）CPPC 是否就正常？若 BIOS bug 与核数无关，匹配面收窄可能漏掉 32/64 核受害机。
2. **bug 语义确认**：BIOS bug 是「缺值」（lack of values）而非「错值」（invalid values），对吧——这决定 quirk 注入值是「补缺」还是「覆盖」。
3. **信息补全**：要求作者/报告者补主板厂商、型号、BIOS 版本/厂商、CPU 型号。

## 版本演进与当前进展

- v1（10-07 22:41，`<20261007144150.15113-1-ggherdovich@suse.cz>`）：如上方案。
- 当日：Mario 22:56 介入（+Kyle 并确认同款问题、三个追问）；Kyle 23:04 确认「same problem」；Mario 23:05 向 Kyle 要系统明细。
- 次日（<a class="article-ref" href="/lkm/2026/10/08/sched-20261008-007-cpufreq-amd-pstate-supply-nominal-lowest-freq-for-trx40-base.html">sched-20261008-007</a>）：多名同平台用户升级最新 BIOS 后问题消失，Mario 表态不愿背 quirk，补丁被放弃。

## Maintainer 意见与讨论焦点

**Mario Limonciello**（AMD，amd-pstate 维护者）：方向性认可（「really old hardware that the BIOS isn't going to fix」正是 quirk 的场景）+ 三个实质性追问（核数匹配、缺值/错值语义、系统信息）。**Kyle Gospodnetich**（报告者）：确认与线下讨论同款问题。焦点：quirk 的匹配面是否过窄/过宽——nominal freq 按 SKU 核数三档不同，单一 24 核 quirk 是否够用是后续若保留 quirk 时必须解决的问题（Mario 次日明说「若将来仍需 quirk，应为三种核数各做一个」）。

## 合入评估

*likelihood=medium*（次日实际走向为放弃，见 <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-007-cpufreq-amd-pstate-supply-nominal-lowest-freq-for-trx40-base.html">sched-20261008-007</a>；本篇按 10-07 当日状态评估）。维护者当日介入且方向认可，但三个追问未答、系统信息未补齐。*blocking_issues*：核数参与匹配的合理性待论证；受影响系统明细未提供。*next_action*：作者回答追问、补信息——或如次日实际发生的那样，确认最新 BIOS 已修复后撤补丁。

## 效果评估

无 benchmark。效果是二元的：quirk 生效后 amd-pstate 可在缺值固件的 TRX40 主板上加载。次日数据显示根因（BIOS 缺值）已被 2026-06 发布的固件更新修复（1.A4/2.94），quirk 的必要性随之消失。

## 我可以参与的点

- `discussion`：Mario 的核数之问可以直接回答——TRX40 同代 24/32/64 核 nominal freq 分别为 3800/3700/2900 MHz，若 BIOS bug 与核数无关则匹配应拆三档；这个答案在次日讨论中被 Mario 采纳为「若需 quirk 则三档各一」。
- 回合视角：无回合价值（次日即放弃）。

## 参考链接

- 补丁: https://lore.kernel.org/all/20261007144150.15113-1-ggherdovich@suse.cz/
- Mario 的 review: https://lore.kernel.org/all/27b226c7-f30b-4863-96e6-6798232863c5@amd.com/
- Kyle 的确认: https://lore.kernel.org/all/nfzkXrDTHHjIW_SUzjPg0gOHamPmFkMiNw8Xyzu1ET_un0fM-tmdI3ChdnOkXAkrh_nX4jiwmzCK6GgWwOsfDti3ta-vlRMihfH4dGUgBCU=@kylegospodneti.ch/
- Mario 向 Kyle 要明细: https://lore.kernel.org/all/a387ee24-ef09-4983-865c-47ef43fa0964@amd.com/
- 相关文章：<a class="article-ref" href="/lkm/2026/10/08/sched-20261008-007-cpufreq-amd-pstate-supply-nominal-lowest-freq-for-trx40-base.html">sched-20261008-007</a>（次日的放弃收尾）
