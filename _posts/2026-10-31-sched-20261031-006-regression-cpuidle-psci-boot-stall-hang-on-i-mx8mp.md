---
id: sched-20261031-006
date: 2026-10-31
subject: '[REGRESSION] cpuidle: psci: boot stall/hang on i.MX8MP'
subsystem: sched
type: bug
status: rfc
severity: high
thread_root_msgid: <20261030171910.2822677-1-dario.binacchi@amarulasolutions.com>
lore_url: https://lore.kernel.org/all/20261030171910.2822677-1-dario.binacchi@amarulasolutions.com/
authors:
- Dario Binacchi
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 根因未定位（作者对 AMBA/CoreSight 早期探针的猜测未确认）
  - 需确认是否确由 65705b18162b 引入、是否波及其它平台
  next_action: 等 Ulf Hansson 或 cpuidle/arm 侧维护者回应定位根因
contribution_opportunities:
- kind: testing
  description: 在 i.MX8MP 或同类平台复现 65705b18162b 的启动 stall，提供第二数据点
- kind: discussion
  description: 分析 cpuidle 提前初始化与 AMBA 早期探针的时序交互以收敛根因
generated_at: '2026-11-01T09:00:00'
source_email_count: 1
related_articles: []
tags:
- idle
- hang
- regression
- arm64
title: '[REGRESSION] cpuidle: psci: boot stall/hang on i.MX8MP'
layout: article
---

## TL;DR
Dario Binacchi 报告一个 cpuidle/psci 的启动回归：i.MX8M Plus（Engicam i.Core MX8M Plus）在 mainline `c339f4010dea` 上，约 1/3 的启动在 `ledtrig-cpu` 注册后 stall ~0.9s 或直接 hang 到看门狗复位。`cpuidle.off=1` 或 revert `65705b18162b`（"cpuidle: psci: Move initialization a bit earlier in the boot sequence"）后 10/10 正常。已用 `#regzbot introduced: 65705b18162b` 挂进回归跟踪。当日无回复。

## 背景与问题
复现时序：正常启动在 `ledtrig-cpu: registered to indicate activity on CPUs` 之后约 11ms 即打印下一条消息；异常时在此处 stall ~0.9s 或 hang。作者未深挖，仅观察到 stall 似乎发生在 `pl330_driver_init()`，猜测与「CPU 已进入 `cpu_pd_wait` 时 AMBA 总线仍去读 CoreSight ETM 的 ID 寄存器」有关，但明确表示「我可能猜错」。已确认触发条件：仅在启用 cpuidle 时发生；`cpuidle.off=1` 或 revert `65705b18162b` 即消失。

## 技术方案
无补丁——这是回归报告。作者请求社区协助定位；线索指向 `65705b18162b` 将 psci cpuidle 初始化提前到 boot 序列更早位置，使其与 AMBA 总线早期探针（CoreSight ETM ID 寄存器读取）产生交互。

## 版本演进与当前进展
*current_version: null*。单封报告（`<20261030171910.2822677-1-dario.binacchi@amarulasolutions.com>`），致信 Ulf Hansson，当日无回复。

## Maintainer 意见与讨论焦点
当日无维护者表态。报告的切入点（`pl330_driver_init()` + AMBA/CoreSight 早期探针 vs cpuidle 提前初始化）尚未被确认，仍是作者猜想。

## 合入评估
*likelihood=unknown*。无修复方向、无维护者回应，属于刚挂进 regzbot 的回归报告。*blocking_issues*：根因未定位；需确认是否真是 `65705b18162b` 引入、以及是否影响其它平台。*next_action*：等 Ulf Hansson 或 cpuidle/arm 侧维护者回应定位根因。

## 效果评估
复现数据明确：约 1/3 启动 stall/hang；`cpuidle.off=1` 与 revert `65705b18162b` 均为 10/10 正常（作者实测）。

## 我可以参与的点
- **testing**：在 i.MX8MP（或其它带 CoreSight ETM + psci cpuidle 的平台）复现并确认 `65705b18162b` 是否稳定触发，为回归定位提供第二数据点。
- **discussion**：分析「cpuidle 提前初始化」与 AMBA 早期探针的时序交互，帮助收敛根因。

## 参考链接
- 报告: https://lore.kernel.org/all/20261030171910.2822677-1-dario.binacchi@amarulasolutions.com/
