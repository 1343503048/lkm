---
id: sched-20260906-005
date: '2026-09-06'
subject: 'sched_clock: Add option to use absolute time against hardware clock reset'
subsystem: sched
type: discussion
status: stalled
severity: none
thread_root_msgid: <20260902082123.95770-1-feng.tang@linux.alibaba.com>
lore_url: https://lore.kernel.org/all/20260902082123.95770-1-feng.tang@linux.alibaba.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: '2026-09-07'
authors:
- Feng Tang
maintainers_involved:
- Thomas Gleixner
- Marc Zyngier
patch_series:
- version: v1
  msgid: <20260902082123.95770-1-feng.tang@linux.alibaba.com>
  date: '2026-09-02'
  summary: kernel/time/sched_clock.c 新增 abs_sched_clock core_param(bool, 0400)；sched_clock_register()
    在该参数开启时把 epoch 直接用 ns = cyc_to_ns(new_epoch & new_mask, new_mult, new_shift) 表示自硬件计数器复位起的绝对时间，不再累加旧
    clock 的 epoch_ns。动机是把 kernel/SCP firmware/ATF 的日志对到同一时间线以追 RAS 问题。+11/-3。
  review_outcome: Marc Zyngier 质疑（一次性采样+后处理即可、EL2 可任意偏移所以并不绝对、不愿内核承担定义上不可靠之物、破坏 sched_clock
    handover）；09-06 Thomas Gleixner 明确 NAK，称其为 firmware debug hack。本日无 v2。
merge_assessment:
  likelihood: unlikely
  blocking_issues:
  - timekeeping/clocksource 维护者 Thomas Gleixner 明确 NAK，且未给出可操作的修改方向
  - Marc Zyngier 的两条实质反对：EL2 软件可任意偏移使「绝对」不成立；该改动破坏 sched_clock handover（新时钟不从旧时钟结束处继续），非
    arm64 的 arch 会受影响
  - 定位问题：服务特定固件调试场景，作者已自行降级为 debug-only option 并承认 runtime 操纵 sched_clock 不太好
  next_action: 不再跟进该线程；若有同类内部需求，按 out-of-tree debug 补丁或「启动早期采样 + 日志后处理对齐」自行实现；要上游则需在
    timekeeping 层重新设计（能力检查 + handover 连续性）并先与维护者沟通
contribution_opportunities:
- kind: design
  description: 补齐邮件里被指出但未解决的两块：arch 能声明计数器「自复位连续、恒定频率、wrap 足够长」的能力检查接口（作者称 sched_clock.c
    里拿不到 CLOCK_SOURCE_SUSPEND_NONSTOP），以及 abs 模式下 clocksource 中途切换时 epoch 跳变的处理
- kind: review
  description: Sashiko 指出的 cyc_to_ns() 精度/溢出问题应改用 mul_u64_u64_div_u64()；自有分支中涉及高频计数器到
    ns 的换算处可对照检查
source_email_count: 8
related_articles:
- sched-20260903-015
tags:
- sched_clock
title: 'sched_clock: Add option to use absolute time against hardware clock reset'
layout: article
---

## TL;DR

Feng Tang（09-02）给 `kernel/time/sched_clock.c` 加了个 `abs_sched_clock` core_param，让注册新 clocksource 时将 `epoch_ns` 直接算成「自硬件计数器复位以来的绝对时间」，以便 kernel / SCP firmware / ATF 的日志落在同一条时间线上追 RAS 问题。09-06 04:39 Thomas Gleixner 给出明确 NAK（原文称这是 firmware debug hack）。本日无 v2、无支持意见，方向在上游基本关闭。

## 背景与问题

作者的问题陈述：`sched_clock` 显示的是相对本 kernel boot 起点的相对时间，而硬件复位到 kernel 启动之间可能有很长的 firmware 阶段。现代服务器平台上并行跑着多份软件（arm64 上 SCP 固件跑在 SCP 处理器、ATF 与 Linux 跑在主处理器），追这类跨方问题时需要把各自日志对到同一参考时间线；这些软件都能读同一个硬件 timer，而它正是 Linux `sched_clock` 的基础，因此「用自硬件复位起的绝对计数器」就能给大家同一个时间基。作者称本地确实靠它对齐过需要 kernel、SCP、ATF 协作分析的 RAS 问题。

需要强调：这补丁改的是 timekeeping 侧的通用 `sched_clock` 框架（`kernel/time/sched_clock.c`），不是 `kernel/sched/clock.c`，所以回帖的是 timers/clocksource 维护者与 arm64 时间源维护者，而不是调度器维护者。

## 技术方案

新增 `static bool abs_sched_clock` + `core_param(abs_sched_clock, abs_sched_clock, bool, 0400)`；在 `sched_clock_register()` 里，原本「旧计数器算出 ns 累加进 epoch_ns」的分支被替换为：开启该参数时 `ns = cyc_to_ns(new_epoch & new_mask, new_mult, new_shift)`，即直接把新计数器的绝对值当作 epoch。改动量 `kernel/time/sched_clock.c` +11/-3。

## 版本演进与当前进展

- 09-02 16:21 Feng Tang 发出 v1（`<20260902082123.95770-1-feng.tang@linux.alibaba.com>`）。
- 09-02 23:32 Marc Zyngier 提出三点质疑（见下节）。
- 09-03 14:51 / 18:20 Yao Yuan 就 EL2 偏移场景追问并确认理解；15:38 Marc 补充：这不只是 VM 问题，很多非 hypervisor 软件也占着 EL2、offset 计数器值以隐藏自己的行为；且该改动破坏 `sched_clock()` handover——新时钟不是从旧时钟结束处接着走，arm64 只有一个真正时间源所以不受影响，其它 arch 大概会受害。
- 09-03 15:45 Feng Tang 承认这（大意）「只是一个 debug option，主要用于追 bug」：场景是 baremetal，可能在 boot 期就 panic 所以 debugfs 不可用；列出硬件计数器需满足的三个前提（一直运行、不因 cpuidle/suspend 停止、不随 cpufreq 变频、wrap 周期足够大）；说想用 `CLOCK_SOURCE_SUSPEND_NONSTOP` 做能力检查但 `sched_clock.c` 里拿不到，因此只能在 commit log 里要求用户自行确认；并转述 Sashiko（自动 review）指出不该用 `cyc_to_ns()` 算 `epoch_ns`、应改用 `mul_u64_u64_div_u64()`。
- 09-03 16:07 Feng Tang 进一步让步：「Manipulating time counter(sched_clock) runtimely doesn't sound like a good thing」，并举 x86 TSC 上发生过类似事情、Thomas 已多次提到。
- 09-06 04:39 Thomas Gleixner 给出 NAK；本日邮件中没有 v2，也没有任何支持该方向的回帖。

## Maintainer 意见与讨论焦点

- **Marc Zyngier（arm64/时间源）**：核心质疑（以下为大意）是：为什么这不是一次性采样计数器、放到某个用户可访问的位置（debugfs 或其它）、最后做后处理来对齐日志——大家一直这么做，而且够用了；其次，你所谓的 absolute 一点都不 absolute，它没有考虑跑在 EL2 的软件可以随意偏移；结论是他相当不愿意让内核背上一种定义上就不可靠的东西。
- **Thomas Gleixner（timers/clocksource 维护者，09-06）**：不是技术评审而是明确拒绝，原文：「I told you before that we don't care about your bug chasing war stories at all. Educate your firmware people and stop pestering us with your firmware debug hacks.」措辞里的 “I told you before” 说明此前已有过同类沟通（具体在何处邮件中未提及）。没有留下可操作的修改建议，等于把「为固件调试往通用时钟里塞开关」这条路堵死。
- **作者侧**：Feng Tang 已主动把定位降级为 debug-only 并承认设计上的顾虑，但没有提出替代方案（例如 Marc 建议的采样+后处理路线）；未见其他维护者或用户支持该方向。

## 合入评估

`likelihood=unlikely`。依据：clocksource/timekeeping 维护者明确 NAK，arm64 时间源维护者此前已给出「定义上不可靠」+「破坏 sched_clock handover」两条实质性反对，作者本人也承认这不是好的做法，本日无 v2、无第三方救援。卡点不是代码质量而是定位：它服务的是特定固件调试场景，且要跨 arch 定义「硬件计数器复位绝对时间」的能力与语义。若非要往上游推，必须先重新定位为 timekeeping 层的通用能力（能力检查 + handover 连续性语义），而不是一个 `core_param` 开关——但按 tglx 的表态，这种重写也不会由这个线程承接。

## 效果评估

邮件中未提供效果数据：既没有开启前后的时间线对齐样例，也没有开销数字。作者给的唯一「收益」证据是主观陈述（本地靠它追过需要 kernel/SCP/ATF 协作的 RAS 问题），而这一理由正是 tglx 拒绝的点。Marc 提出的替代路线（一次性采样 + 后处理）在邮件中被作者否掉的理由只有「boot 期 panic 时 debugfs 不可用」与「这个选项更方便」，未见量化对比。

## 我可以参与的点

- 结论先行的实用建议：这个方向上游已关闭，若要满足同样的「跨 kernel/固件统一时间线」需求，在 OLK 内部按 out-of-tree debug 补丁维护（或直接实现 Marc 说的「启动早期采样一次硬件计数器 + 打进日志 + 事后脚本对齐」）成本更低，也不要按调度器补丁的路子去 review——真正的语义风险都在 timekeeping 侧。
- 如果想认真推上游，可以先补上邮件里被指出但没解决的两块，再去找 tglx 谈：一是能力检查（作者承认 `sched_clock.c` 里拿不到 `CLOCK_SOURCE_SUSPEND_NONSTOP`，需要一个 arch 能声明「计数器自复位起连续、恒定频率、wrap 足够长」的接口）；二是 handover 连续性（`abs_sched_clock` 分支下 `epoch_ns` 不再累加，按代码推断在 clocksource 中途切换时会发生跳变，这对依赖 `sched_clock()` 做时间戳的调度统计与 cgroup CPU 记账都不安全——邮件中未展开，属于可以替他论证的方向）。
- 精度点可直接复核：Sashiko 指出的 `cyc_to_ns()` 计算 `epoch_ns` 溢出问题应改用 `mul_u64_u64_div_u64()`，这类高精度绝对时间换算在时钟/记账代码里是通病，自己分支里有类似换算时可以一并对照检查。

## 参考链接

- v1 原始提案: https://lore.kernel.org/all/20260902082123.95770-1-feng.tang@linux.alibaba.com/
- Marc Zyngier 首条质疑: https://lore.kernel.org/all/87h5k7mzxy.wl-maz@kernel.org/
- Marc Zyngier 关于 EL2 与 handover 的补充: https://lore.kernel.org/all/878q5i6ay6.wl-maz@kernel.org/
- Feng Tang 关于 debug-only 与硬件前提的回应: https://lore.kernel.org/all/apkli5dC8z3rcXBy@U-2FWC9VHC-2323.local/
- Thomas Gleixner 的 NAK（本日）: https://lore.kernel.org/all/8733vn5t6p.ffs@fw13/
- tip-bot commit: 未获取到
- stable backport: 未获取到
- 相关：[[sched-20260903-015]]
