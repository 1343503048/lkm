---
id: sched-20261022-006
date: 2026-10-22
subject: 'cpufreq: CPPC: Preserve OSPM-set registers across hotplug and unload'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261020121846.691218-1-sumitg@nvidia.com>
lore_url: https://lore.kernel.org/all/20261020121846.691218-1-sumitg@nvidia.com/
authors:
- Sumit Gupta
maintainers_involved: []
current_version: v6
patch_series:
- version: v6
  msgid: <20261020121846.691218-1-sumitg@nvidia.com>
  date: 2026-10-20
  summary: CPPC 保存/恢复 OSPM 设置的寄存器以跨 hotplug/unload
  review_outcome: Christian 建议 store 时保存；Sumit 拟定合并方案并 respin
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: Sumit 按合并方案 respin，Christian 在 AMD 平台验证后确认
contribution_opportunities:
- kind: testing
  description: 在 x86 CPPC 平台验证热插拔/卸载后 OSPM 寄存器保持
- kind: review
  description: 审读 respin 后 store 时保存 + offline 恢复固件值的覆盖完整性
generated_at: '2026-10-23T01:20:00'
source_email_count: 2
related_articles:
- sched-20261021-015
tags:
- cpufreq
title: 'cpufreq: CPPC: Preserve OSPM-set registers across hotplug and unload'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/08/27/sched-20260827-007-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20260827-007</a>：Sumit Gupta 的 CPPC 系列（CPU 热插拔与驱动卸载时保留 OSPM 设置的寄存器值）经 v1–v5 演进，以 arm64 PCC 为主要验证路径。
- <a class="article-ref" href="/lkm/2026/09/17/sched-20260917-006-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20260917-006</a>：v5 获 K Prateek Nayak 的 x86 实测 Tested-by。
- <a class="article-ref" href="/lkm/2026/09/26/sched-20260926-009-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20260926-009</a>：cpufreq 维护者 Rafael Wysocki 催评审——「没有其他输入我不会应用这个系列」。
- <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-015-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20261021-015</a>：Christian Loehle（Arm）补充建议——所有 ospm-set 寄存器可以在 `sysfs_store` 时就保存下来，从而不必处理 offline/suspend 期间可能发生的读错误。
- <a class="article-ref" href="/lkm/2026/10/22/sched-20261022-006-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20261022-006</a>（今天）：Christian 进一步认可「store 时保存 + 读取初始值」方案，并提议「若 init() 读不到初始值就不初始化（或不允许 autosel）」。Sumit 拟定合并方案——保留 v2 的 offline 固件恢复语义 + v1 的 store 时保存请求值，宣布将据此 respin。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/08/27/sched-20260827-007-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20260827-007</a> → <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-015-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20261021-015</a>）CPPC 驱动在 CPU 热插拔与驱动卸载时丢失 OSPM 设置的寄存器值，导致离线-上线周期后电源管理配置失效。今日新增实现层面的收敛：offline()/suspend() 时读这些寄存器**可能失败**，失败的读会丢掉请求；线上 reapply 失败也可能让寄存器跌回固件/复位值，随后被下一次 offline 保存覆盖。因此「store 时保存请求值」成为共识方向。

## 技术方案
（承接前序版本 + 今日收敛）把 OSPM 设置的寄存器（如 `auto_select`、`energy_performance_preference_val`）纳入 save/restore 表，跨 hotplug/unload 保留。Sumit 提出的合并方案：`init()` 保存固件值作为初始请求值；每次 `sysfs_store` 成功后更新请求值（boot 参数系列同样处理）；`offline()/suspend()` 恢复固件值（不现读寄存器）；`online()/resume()` 重放请求值，失败则保留请求待下次。Christian 补充：若 init()（或首次 autosel 使能）读不到初始值，则干脆不让驱动初始化/不允许 autosel=1。

## 版本演进与当前进展
*current_version: v6*（`<20261020121846.691218-1-sumitg@nvidia.com>`）。当日无新版本发出；作者宣布将按合并方案 respin。Christian 表示其配套的 1/5 也有一版更新，将在 AMD 平台验证后发出。

## Maintainer 意见与讨论焦点
Christian Loehle（Arm）认可「store 时保存」更合理，并就「读不到初始值」给出「不初始化/不允许 autosel」的建议。Sumit 回帖确认方案可行且保留前序讨论意图，将据此改版。未见反对意见。

## 合入评估
*likelihood=high*。作者与评审已就实现方向达成一致，只待改版后重新收取；*blocking_issues*：无实质分歧，缺乏的是最终 respin 版本；*next_action*：Sumit 按合并方案 respin，Christian 验证其 1/5 后在 AMD 平台确认。

## 效果评估
无新量化数据；此前已有 K Prateek Nayak 的 x86 Tested-by。

## 我可以参与的点
- *kind: testing*：在 ARM PCC 之外（尤其 x86 CPPC）验证热插拔/卸载后 OSPM 寄存器保持情况。
- *kind: review*：审读 respin 后「store 时保存 + offline 恢复固件值」的实现是否覆盖所有寄存器类型。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261020121846.691218-1-sumitg@nvidia.com/
- Sumit 今日回帖：https://lore.kernel.org/all/51747329-abe1-406a-aeae-94ebb7a35bf4@nvidia.com/
- Christian 今日回帖：https://lore.kernel.org/all/85da866f-4fbb-4cf2-9376-3f7405e049ef@arm.com/
