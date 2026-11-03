# cpufreq: add an Amlogic speed-bin driver

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261027-017：Christian Köver-Draxl 的 Amlogic speed-bin cpufreq 驱动（4/4）讨论起。
- sched-20261029-016：Amlogic 厂商 Chuan Liu 发长文澄清立场（统一 amlogic-cpufreq.c 规划）。
- sched-20261102-025：平台侧维护者 Martin Blumenstingl 给出代际清单与命名建议（`amlogic-s4-cpufreq`）。
- sched-20261103-020（今天）：Chuan Liu 回帖表示不再反对驱动实现（基于 pm_opp + cpufreq-dt 即可适配 A9 等），并问能否把 CPU 时钟处理放进 clock 驱动以复用 cpufreq-dt——厂商与平台维护者就命名/共享边界进一步靠拢。

## 背景与问题

（承接 sched-20261102-025）为 Amlogic SoC 增加 speed-bin 分档感知的 cpufreq 驱动；此前焦点是「统一驱动 vs 多驱动」的命名与代码共享边界。

## 技术方案

（承接）今日厂商给出新结论：基于 `amlogic-cpufreq.c` 已能较好适配 A9（此前担心 cpufreq-dt 处理不了多 cluster 的复杂时钟/电源逻辑，现认为可经 `dev_pm_opp_set_config()` 的 `config_clks()`/`config_regulators()` 回调解决），对驱动实现无异议。Chuan Liu 进一步问：能否把 CPU 时钟处理逻辑放进 clock 驱动（如 G12A 那样），从而完全复用 cpufreq-dt；并对 SM1（需额外管理 DSU 时钟）给出 CPU/DSU 频率映射关系（≤1GHz 同步、1-1.2GHz DSU=1GHz、>1.2GHz DSU=cpu×80%），总结各代际特征（G12B 及之前=1 clock+1 supply；SM1=+DSU；S4/C3/T7=+binning 电压；S7/S7D/S6=两者兼具）。

## 版本演进与当前进展

*current_version: v1 系列*。驱动命名/共享边界仍在厂商与平台维护者之间对齐，但已从「hold off」转向「无异议、探讨复用」。

## Maintainer 意见与讨论焦点

厂商 Chuan Liu 收回了对驱动实现的顾虑，与 Martin 的「多驱动」建议部分靠拢（复用 cpufreq-dt 可减少独立 cpufreq_driver 的需要）。命名与时钟归属问题仍开放。

## 合入评估

*likelihood=low*。命名（amlogic-s4-cpufreq vs 统一 amlogic-cpufreq）与时钟处理落点（clock 驱动 vs cpufreq 驱动）仍未定，但厂商态度转积极。

## 效果评估

无性能数据。

## 我可以参与的点

- discussion：就时钟处理落点（clock 驱动 vs cpufreq 驱动）与命名给出意见。
- testing：在 S4/C3 或 DSU 平台（SM1）上验证 speed-bin 与频率映射。

## 参考链接

- lore thread（今日 Chuan Liu 回帖）: https://lore.kernel.org/all/48b333a3-ef88-4739-a087-3ed9d8ec60a4@amlogic.com/

---
id: sched-20261103-020
date: 2026-11-03
subject: "cpufreq: add an Amlogic speed-bin driver"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: null
lore_url: "https://lore.kernel.org/all/48b333a3-ef88-4739-a087-3ed9d8ec60a4@amlogic.com/"
authors: ["Christian Köver-Draxl"]
maintainers_involved: []
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues: ["命名与时钟处理落点未定"]
  next_action: "厂商与平台维护者就命名/时钟归属达成一致。"
contribution_opportunities:
  - kind: discussion
    description: "就时钟处理落点与驱动命名给出意见。"
  - kind: testing
    description: "在 S4/C3 或 DSU 平台上验证 speed-bin 与频率映射。"
generated_at: "2026-11-04T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261102-025]
tags: [cpufreq]
---