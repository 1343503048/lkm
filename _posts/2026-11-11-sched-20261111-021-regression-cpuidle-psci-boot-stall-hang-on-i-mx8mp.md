---
id: sched-20261111-021
date: '2026-11-11'
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
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 根因未明，65705b18162b 与 AMBA 早期探针的交互假设未验证
  next_action: 若再现则补 bisect 定位根因；否则按 regzbot inconclusive 关闭
contribution_opportunities:
- kind: testing
  description: 在 i.MX8M Plus 等平台复测，若仍复现则补 bisect
generated_at: '2026-11-12T09:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261031-006
tags:
- idle
- hang
- regression
- arm64
title: '[REGRESSION] cpuidle: psci: boot stall/hang on i.MX8MP'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/10/31/sched-20261031-006-regression-cpuidle-psci-boot-stall-hang-on-i-mx8mp.html">sched-20261031-006</a>：Dario Binacchi 报告一个 cpuidle/psci 的启动回归：i.MX8M Plus 在 mainline `c339f4010dea` 上约 1/3 的启动在 `ledtrig-cpu` 注册后 stall ~0.9s 或 hang 到看门狗复位；`cpuidle.off=1` 或 revert `65705b18162b`（"cpuidle: psci: Move initialization a bit earlier in the boot sequence"）后正常。已挂 `#regzbot introduced: 65705b18162b`。
- <a class="article-ref" href="/lkm/2026/11/11/sched-20261111-021-regression-cpuidle-psci-boot-stall-hang-on-i-mx8mp.html">sched-20261111-021</a>（今天）：**报告者改用 `#regzbot inconclusive: can't reproduce anymore` 收尾**——Dario 表示「抱歉没跟进；在 current mainline（`b3dfbde62cf1`，v7.4-rc2+）上已无法复现，不确定什么变了，后续测试中若再出现会报告」。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/10/31/sched-20261031-006-regression-cpuidle-psci-boot-stall-hang-on-i-mx8mp.html">sched-20261031-006</a>）原复现时序：正常启动在 `ledtrig-cpu: registered to indicate activity on CPUs` 后约 11ms 打印下一条；异常时在此 stall ~0.9s 或直接 hang。触发条件：仅启用 cpuidle 时发生，`cpuidle.off=1` 或 revert `65705b18162b` 即消失；线索指向 psci cpuidle 初始化被提前到 boot 序列更早位置，与 AMBA 总线早期探针（CoreSight ETM ID 寄存器读取）交互。

## 技术方案

无补丁——回归报告。今日报告者确认在 v7.4-rc2+ 上不再复现，将 regzbot 置为 inconclusive。

## 版本演进与当前进展

*current_version: 无（回归报告）*。状态从「open，等社区定位」转为「报告者无法复现、inconclusive」。

## Maintainer 意见与讨论焦点

当日无维护者回复。报告者单方面收尾：无法复现，原因未明（不排除被期间某个改动顺带修复，但未做 bisect 确认）。

## 合入评估

*likelihood=unknown*。回归未能定位根因也未被明确修复，仅因报告者无法复现而 inconclusive。*blocking_issues*：根因未明（`65705b18162b` 与 AMBA 早期探针的交互假设未验证）。*next_action*：若在后续测试或其它平台再现，补 bisect 定位根因；否则按 regzbot inconclusive 关闭。

## 效果评估

无可量化数据；复现与否的观察结果即全部证据。

## 我可以参与的点

- **testing**：在 i.MX8M Plus 或类似「psci cpuidle 提前初始化」的平台复测，若仍能触发 boot stall，补一个 bisect 定位到真正修复/回归 commit（这是当前缺失的关键一步）。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261030171910.2822677-1-dario.binacchi@amarulasolutions.com/
- 报告者的 inconclusive 收尾: https://lore.kernel.org/all/CABGWkvor=2AWC06iRvONAAPu6b8SS-JnJYmeALCYg_r4bh3wtQ@mail.gmail.com/
