---
id: sched-20261029-014
date: 2026-10-29
subject: 'ARM: omap: cpuidle34xx: Fix unbalanced cpu_pm_enter()/exit() and cleanup'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261028-susp2-v1-0-174b52857d89@kemnade.info>
lore_url: https://lore.kernel.org/all/20261028-susp2-v1-0-174b52857d89@kemnade.info/
authors:
- Andreas Kemnade
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261028-susp2-v1-0-174b52857d89@kemnade.info>
  date: 2026-10-28
  summary: 2 补丁：平衡 cpu_pm_enter/exit 恢复 vfp_pm_resume 调用；constify state info
  review_outcome: '作者自答补 Fixes: 1cd96478cf150；无外部 review'
upstream_commit: null
fixes_commit: 1cd96478cf150
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: 等 Tony Lindgren / Daniel Lezcano 之一 review 后合入
contribution_opportunities:
- kind: review
  description: 核对 __omap3_enter_idle() 各退出分支的 cpu_pm_enter/exit 配对是否完整
- kind: testing
  description: 在 OMAP3 硬件跑 suspend/idle 循环，观察 pm_debug/count 的 NEON/MPU 计数一致性
generated_at: '2026-10-30T09:30:00'
source_email_count: 4
related_articles: []
tags:
- idle
title: 'ARM: omap: cpuidle34xx: Fix unbalanced cpu_pm_enter()/exit() and cleanup'
layout: article
---

## TL;DR
Andreas Kemnade 发 2 补丁修 OMAP3 cpuidle 驱动（`arch/arm/mach-omap2/cpuidle34xx.c`）：① 平衡 `cpu_pm_enter()`/`cpu_pm_exit()` 调用——原代码在 idle 路径上 enter/exit 不对等，导致 `vfp_pm_resume()` 不会被调用来恢复 NEON/FPU 状态（作者在研究偶发 FPU 问题时发现，并援引 Sicelo 观察到 `pm_debug/count` 里 NEON off=1 但 MPU=0）；② 把 state info 声明为 `const`，把「cx 指针内容是否会变」交给编译器保证（清理）。作者在随后的自答里补上 `Fixes: 1cd96478cf150` 并确认「这确实是个被本补丁修掉的真问题」。

## 背景与问题
在研究一些偶发 FPU 问题时，作者发现 `cpuidle34xx` 的 idle 路径里 `cpu_pm_enter()`/`cpu_pm_exit()` 调用不平衡：一条路径 enter 了却没对应 exit（或反之）。后果是 PM 的 notifier 链（含 `vfp_pm_resume()`）在恢复时不触发，NEON/VFP 状态无法被恢复——这与 Sicelo 早先测试时看到的「`/sys/kernel/debug/pm_debug/count` 里 NEON off 计数 1 而 MPU 0」吻合。

## 技术方案
- **1/2** 平衡 `cpu_pm_enter()`/`cpu_pm_exit()`，使 PM 路径对称、`vfp_pm_resume()` 能在恢复时被调用（`arch/arm/mach-omap2/cpuidle34xx.c`）。
- **2/2** 把 state info 数组/指针 constify，把「cx 指针内容是否会变」的疑问交给编译器在编译期把关（清理）。

## 版本演进与当前进展
*current_version: v1*（2026-10-28，cover `<20261028-susp2-v1-0-174b52857d89@kemnade.info>`；base-commit `5fd8fdf561e0e6093305b6c993ee9b7c25bc8b51`）。作者当日自答补 `Fixes: 1cd96478cf150`（"ARM: OMAP3xxx: CPUIdle: optimize __omap3_enter_idle()"），并说明此前与 Sicelo 的测试讨论佐证了该缺陷的真实性。无外部 review 回帖。

## Maintainer 意见与讨论焦点
今日无维护者/外部回帖，唯一讨论是作者自答（补 Fixes 标签 + 解释与 Sicelo 的 `pm_debug/count` 观察一致）。无争议点。

## 合入评估
*likelihood=medium*。补丁 trivial、有明确 Fixes 标签与真实缺陷佐证；但 OMAP3 是较老的 ARM 平台、cpuidle 驱动由 ARM/OMAP maintainer（Tony Lindgren / Daniel Lezcano）收取，尚无人 review。*blocking_issues*：暂无，等 ARM OMAP 或 cpuidle maintainer 收取。*next_action*：等待 Tony Lindgren / Daniel Lezcano 之一 review 合入。

## 效果评估
作者自评「definitively a real problem fixed by this」——修复的是正确性（`vfp_pm_resume()` 不再被跳过），证据是 Sicelo 观察到的 NEON off / MPU 计数不一致；无性能数据。

## 我可以参与的点
- **review**：核对 `cpu_pm_enter()/exit()` 在 `__omap3_enter_idle()` 各退出分支上的配对是否完整（除作者修的那条，是否还有其它不配对分支）。
- **testing**：在 OMAP3 硬件（如 GTA04/BeagleBoard）上跑 suspend/idle 循环，观察 `pm_debug/count` 的 NEON/MPU 计数是否一致、FPU 偶发问题是否消失。

## 参考链接
- lore thread（0/2 cover）: https://lore.kernel.org/all/20261028-susp2-v1-0-174b52857d89@kemnade.info/
- 作者自答（补 Fixes 标签）: https://lore.kernel.org/all/20261028212302.75ec622e@kemnade.info/
