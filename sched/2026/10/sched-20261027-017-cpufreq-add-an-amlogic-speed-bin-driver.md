# cpufreq: add an Amlogic speed-bin driver

## TL;DR
Christian Köver-Draxl 提交的 Amlogic speed-bin cpufreq 驱动（系列 4/4）讨论继续：Christian Hewitt 提醒其 S4 相关工作（ramp-delay 是 OPP 切换稳定的关键），而 Amlogic 厂商侧 Chuan Liu 当众要求「先 hold off 不要在 S4 上提 cpufreq 驱动」，因 S4 的 clock 驱动尚不能设 CPU 时钟、regulator 缺电压稳定等待逻辑，贸然提升频率可能挂系统。方向暂缓。

## 背景与问题
为 Amlogic SoC 增加 speed-bin（芯片分档）感知的 cpufreq 驱动，以按芯片速度等级设置频率/电压。厂商侧指出 S4 平台当前有两个未解决前置：clock 驱动不能设置 CPU 时钟；CPU regulator 升压后需要时间稳定，现有逻辑缺少等待，可能在电压未到位时就抬升 CPU 频率导致系统挂起。

## 技术方案
讨论阶段为主：Christian Hewitt 给出其 S4 的 bindings/clock/driver 工作分支（`chewitt/linux amlogic-7.3.y`），并强调设置 ramp-delay 是 OPP 切换稳定的关键（相关 commit 链接）；Chuan Liu 说明从 C3 起 secure-clock 由 SMC 改走 SCMI，S4 因 SDK 发布较早多数客户固件仍用 SMC。

## 版本演进与当前进展
*current_version: v1*（4/4，`<20261025192219.209137-5-christian.koever-draxl@student.uibk.ac.at>`）。今日无新补丁，为厂商与社区的方案对齐讨论。

## Maintainer 意见与讨论焦点
无 cpufreq 维护者今日直接表态（Viresh 被 cc 未在当日缓存回复）。社区侧 Christian Hewitt 提供参考实现与关键经验（ramp-delay）；厂商侧 Chuan Liu 明确要求暂缓 S4 支持，等 clock/regulator 前置完成。

## 合入评估
*likelihood=low*。厂商主动要求 hold off，且存在会挂系统的硬件前置未解决。*blocking_issues*：S4 clock 驱动不能设 CPU 时钟、regulator 缺电压稳定等待逻辑。*next_action*：等厂商完成 clock/regulator 前置工作后再提驱动。

## 效果评估
无性能/功能数据。属新驱动引入前的方案讨论。

## 我可以参与的点
- *kind: discussion*：与厂商对齐 S4 的 SCMI/SMC 时钟路径选择及 regulator settle 时序需求。

## 参考链接
- 4/4 patch: https://lore.kernel.org/all/20261025192219.209137-5-christian.koever-draxl@student.uibk.ac.at/

---
id: sched-20261027-017
date: 2026-10-27
subject: 'cpufreq: add an Amlogic speed-bin driver'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20261025192219.209137-5-christian.koever-draxl@student.uibk.ac.at>'
lore_url: 'https://lore.kernel.org/all/20261025192219.209137-5-christian.koever-draxl@student.uibk.ac.at/'
authors:
  - 'Christian Köver-Draxl'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20261025192219.209137-5-christian.koever-draxl@student.uibk.ac.at>'
    date: 2026-10-26
    summary: 'Amlogic speed-bin cpufreq 驱动（4/4）'
    review_outcome: '厂商要求 hold off S4 支持'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - 'S4 clock 驱动不能设 CPU 时钟'
    - 'regulator 缺电压稳定等待逻辑'
  next_action: '等厂商完成 clock/regulator 前置后再提'
contribution_opportunities:
  - kind: discussion
    description: '对齐 S4 的 SCMI/SMC 时钟路径与 regulator settle 时序'
generated_at: '2026-10-28T09:00:00'
source_email_count: 3
related_articles: []
tags:
  - cpufreq
---