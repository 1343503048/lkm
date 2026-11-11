# ARM: omap: cpuidle34xx: balance cpu_pm_enter/exit()

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261029-014：Andreas Kemnade 发 2 补丁修 OMAP3 cpuidle 驱动：① 平衡 `cpu_pm_enter()`/`cpu_pm_exit()` 调用——原 idle 路径 enter/exit 不对等，导致 `vfp_pm_resume()` 不被调用、NEON/FPU 状态无法恢复（与 Sicelo 观察到的「pm_debug/count 里 NEON off=1 而 MPU=0」吻合）；② state info 声明为 `const` 作清理。`Fixes: 1cd96478cf150`。
- sched-20261111-022（今天）：**Kevin Hilman（OMAP 维护者）实测后发现仍有偶发 VFP 崩溃**——「即便打了这个修复，beagle/beagle-xm 上仍有间歇失败，NEON 与 MPU 计数不匹配是个好线索」；他提出根因应在 clockdomain 允许 idle 之前先建立 `neon_clkdm → mpu_clkdm` 的唤醒依赖，否则 NEON 会立即 idle、MPU 继续运行时 VFP 指令 trap 为未定义。附 `pm34xx.c` 的修复 diff，称早期测试中「不再看到间歇 VFP 崩溃」。作者 Andreas 认可其分析并计划重跑自己的自动测试、再做 omapdrm 相关 bisect。

## 背景与问题

（承接 sched-20261029-014）cpuidle34xx 的 idle 路径 `cpu_pm_enter()`/`cpu_pm_exit()` 不平衡，导致 PM notifier 链（含 `vfp_pm_resume()`）在恢复时不触发、NEON/VFP 状态无法恢复。今日 Kevin Hilman 在自测中复现到「即便修了 enter/exit 平衡，仍有间歇 VFP 崩溃」，并把线索收敛到 NEON clockdomain 的 wakeup 依赖缺失。

## 技术方案

今日 Kevin Hilman 给出一个追加 diff（`arch/arm/mach-omap2/pm34xx.c`）：把 `neon_clkdm`/`mpu_clkdm`/`per_clkdm`/`wkup_clkdm` 的 `clkdm_lookup()` 提前，在 `pwrdms_setup()` 编程 NEON 为 OFF/RET 之前，先 `clkdm_add_wkdep(neon_clkdm, mpu_clkdm)` 建立 NEON→MPU 唤醒依赖；否则 idle 的 NEON clockdomain 会让 NEON 在 MPU 仍运行时掉电，VFP 指令 trap 为未定义直到 NEON 被唤醒。原 patch 1/2（平衡 `cpu_pm_enter/exit`）仍是必要修复，此 diff 为其之上的补充，Kevin 称「再多测几轮后用带 changelog 的正式补丁发送」。

## 版本演进与当前进展

*current_version: v1（2026-10-28，`<20261028-susp2-v1-0-174b52857d89@kemnade.info>`）*。今日无新版本；Kevin Hilman 计划在补充测试后另发一个独立的 NEON wakeup-dependency 补丁。

## Maintainer 意见与讨论焦点

- **Kevin Hilman（OMAP 维护者）**：认可原修复，但指出其不完整——NEON vs MPU 计数不匹配指向 `neon_clkdm → mpu_clkdm` wakeup 依赖缺失，附修复 diff 并计划正式发送。
- **Andreas Kemnade（作者）**：认可分析，称「这桩事就此收尾」，并计划重跑自动测试、再做 omapdrm/8250_DMA 的 bisect。
- 无 NAK；结论是「原修复必要但不足，需追加 wakeup 依赖补丁」。

## 合入评估

*likelihood=medium*。原 2 补丁方向正确，但 Kevin 的实测表明还差一个 NEON wakeup 依赖补丁；两者合并后才能完整消除间歇 VFP 崩溃。*blocking_issues*：Kevin 的 NEON wakeup 依赖补丁尚未正式发出并完成测试。*next_action*：Kevin 补充测试后发送 NEON wakeup 依赖的正式补丁；与 Andreas 的原补丁一并评审合入。

## 效果评估

Kevin 报告「加了下述 diff 后，早期测试中不再看到间歇 VFP 崩溃」，属定性验证；原补丁的 enter/exit 平衡也有 `pm_debug/count` 的计数佐证。无量化 benchmark。

## 我可以参与的点

- **testing**：在 N900 / GTA04 / beagle-xm 等 OMAP3 设备上复测「原补丁 + Kevin 的 NEON wakeup 依赖」组合，重点观测 MPU 卡在 INA 不 OFF 与 VFP crash 是否都消失。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261028-susp2-v1-0-174b52857d89@kemnade.info/
- Kevin Hilman 的补充分析: https://lore.kernel.org/all/7ha4ngv55s.fsf@baylibre.com/
- Andreas 的回应: https://lore.kernel.org/all/20261110212306.39327765@kemnade.info/

---
id: sched-20261111-022
date: '2026-11-11'
subject: "ARM: omap: cpuidle34xx: balance cpu_pm_enter/exit()"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261028-susp2-v1-0-174b52857d89@kemnade.info>"
lore_url: "https://lore.kernel.org/all/20261028-susp2-v1-0-174b52857d89@kemnade.info/"
authors: [Andreas Kemnade]
maintainers_involved: [Kevin Hilman]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261028-susp2-v1-0-174b52857d89@kemnade.info>"
    date: '2026-10-28'
    summary: "平衡 cpu_pm_enter/exit 使 vfp_pm_resume 被调用；state info const 化"
    review_outcome: "Kevin 认可但不完整，需追加 NEON wakeup 依赖补丁"
upstream_commit: null
fixes_commit: "1cd96478cf150"
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["Kevin 的 NEON wakeup 依赖补丁尚未正式发出"]
  next_action: "Kevin 补测后发 NEON wakeup 依赖正式补丁，与原补丁一并评审"
contribution_opportunities:
  - kind: testing
    description: "在 N900/GTA04/beagle-xm 上复测原补丁 + NEON wakeup 依赖组合"
generated_at: "2026-11-12T09:00:00+08:00"
source_email_count: 2
related_articles: [sched-20261029-014]
tags: [idle]
---