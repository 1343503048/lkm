---
id: sched-20261030-015
date: 2026-10-30
subject: 'cpufreq: CPPC: Preserve OSPM-set registers across hotplug and unload'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261030092416.1993889-1-sumitg@nvidia.com>
lore_url: https://lore.kernel.org/all/20261030092416.1993889-1-sumitg@nvidia.com/
authors:
- Sumit Gupta
- Christian Loehle
maintainers_involved: []
current_version: v7
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 等 Rafael 对 v7 的最终 review/收取
  next_action: Rafael 收取 v7，或在 AMD 平台补充验证
contribution_opportunities:
- kind: testing
  description: 在 AMD/arm64 平台验证 v7 热插拔与 suspend-resume 后 EPP/Auto Select 不丢
- kind: review
  description: 核对 patch 1 的 Desired clamp 写序在平台复位后不会发出非法性能请求
generated_at: '2026-10-31T09:00:00'
source_email_count: 4
related_articles:
- sched-20260827-007
- sched-20260917-006
- sched-20260926-009
- sched-20261021-015
- sched-20261022-006
tags:
- cpufreq
title: 'cpufreq: CPPC: Preserve OSPM-set registers across hotplug and unload'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/08/27/sched-20260827-007-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20260827-007</a>：Sumit Gupta 的 CPPC 系列（CPU 热插拔与驱动卸载时保留 OSPM 设置的寄存器值）经 v1–v5 演进，以 arm64 PCC 为主要验证路径。
- <a class="article-ref" href="/lkm/2026/09/17/sched-20260917-006-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20260917-006</a>：v5 获 K Prateek Nayak 的 x86 实测 Tested-by。
- <a class="article-ref" href="/lkm/2026/09/26/sched-20260926-009-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20260926-009</a>：cpufreq 维护者 Rafael Wysocki 催评审——「没有其他输入我不会应用这个系列」。
- <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-015-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20261021-015</a>：Christian Loehle 建议在 `sysfs_store` 时保存 ospm-set 寄存器，避免 offline/suspend 时读错误。
- <a class="article-ref" href="/lkm/2026/10/22/sched-20261022-006-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20261022-006</a>：Christian 补充「init() 读不到初始值就不初始化」；Sumit 拟定合并方案（offline 恢复固件值 + store 时保存请求值），宣布将据此 respin。
- <a class="article-ref" href="/lkm/2026/10/30/sched-20261030-015-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20261030-015</a>（今天）：Sumit 发 **v7**（0/5 封面 + 5 补丁），吸收 Sashiko/Christian/Rafael 意见：patch 1 把 Desired 钳进 MIN/MAX 而非拒绝、`store_auto_select()` 仅成功才更新缓存；patch 2 `exit()` 只释放驱动数据、`online()` 使能失败继续；patch 4 改为每次成功 sysfs 写都保存请求值、`init()` 读不到固件值即失败、拆分 auto_act_window store；patch 5 `suspend()` 不再现读/保存寄存器。

## 背景与问题
（承接 v1–v6）CPPC 驱动在 CPU 热插拔与驱动卸载时丢失 OSPM 设置的寄存器值（EPP/Auto Select/Auto Activity Window），导致离线-上线周期后电源管理配置失效。此前已收敛的共识：offline/suspend 期间读寄存器可能失败，故「store 时保存请求值 + init() 保存固件值」成为方向。今日为 v7 落地该共识，无新背景。

## 技术方案
（承接 v6，v7 按评审意见落地）5 补丁结构：

- **patch 1**（Christian）：`ACPI: CPPC: Order performance-control updates`——重排 cppc_set_perf() 的 Desired/MIN/MAX 写序，使平台永不看到非法请求；v7 把「Desired 超界即拒绝」改为「clamp 进 MIN/MAX」。
- **patch 2**：加 `online()/offline()` 回调，让 policy 跨热插拔存活（不再 teardown/rebuild）；`exit()` 只释放数据；`online()` 使能失败仅记录不返回。
- **patch 3**：autonomous selection 寄存器 helper 改用 u64。
- **patch 4**：init() 存固件值作为初始请求值、每次成功 sysfs 写更新请求值、offline() 恢复固件值、online() 重放请求值；拆分 auto_act_window store。
- **patch 5**：把 restore/reapply 扩展到 suspend/resume（suspend() 不再现读寄存器，改由标志位协调 offline/resume）。

## 版本演进与当前进展
*current_version: v7*（2026-10-30 发出）。v6→v7 按 Sashiko（clamp 而非拒绝、store 仅成功更新、exit 只释放数据）、Christian（store 保存、init 失败即失败、拆 auto_act_window）、Rafael（store 保存）逐条吸收。当日无回复。

## Maintainer 意见与讨论焦点
当日无新回复。此前 Rafael Wysocki（cpufreq maintainer）的态度是「无其他输入不应用」——v7 已把此前积累的评审意见（Sashiko/Christian/Rafael）尽数吸收，下一步主要看 Rafael 是否接受 v7 并收取。

## 合入评估
*likelihood=high*。系列经 v1–v7 长期打磨、已获 x86 Tested-by 与多位 reviewer 背书、v7 落地全部收敛意见；唯一变量是 Rafael 的最终收取。*blocking_issues*：等 Rafael 对 v7 的最终 review/收取。*next_action*：Rafael 收取 v7（或在 AMD 平台补充 Christian 的验证）。

## 效果评估
无 v7 新增性能数据；此前 v5 有 K Prateek 的 x86 实测 Tested-by。功能价值在「热插拔/suspend 后 OSPM 寄存器配置不丢失」。

## 我可以参与的点
- **testing**：在 AMD/arm64 平台验证 v7 热插拔与 suspend-resume 后 EPP/Auto Select 等寄存器值不丢。
- **review**：核对 patch 1 的 Desired clamp 写序在平台复位后不会发出非法性能请求。

## 参考链接
- lore thread（v7 封面）: https://lore.kernel.org/all/20261030092416.1993889-1-sumitg@nvidia.com/
