# sched_clock: Add option to use absolute time against hardware clock reset

## TL;DR

这不是「时钟复位后补偿跳变」的功能，而是一个纯调试用途的启动选项：arm64 服务器上一次 nasty bug 往往要同时对齐 SCP 固件、ATF 与 Linux 三方日志，而三方都能读同一个硬件定时器，于是 Feng Tang 增加 `core_param(abs_sched_clock, ...)`，让 `sched_clock_register()` 在建立 epoch 时直接把计数器当前值换算成 ns（`cyc_to_ns(new_epoch & new_mask, new_mult, new_shift)`）而不是相对 boot 归零，从而把三方日志放到同一条以硬件定时器复位为原点的时间轴上。Marc Zyngier 的反对分两层：所谓「绝对」并不绝对（EL2 软件可以任意 offset 计数器，且这不需要虚拟机），而且这会打破 `sched_clock()` 的 handover（新时钟不从旧时钟结束处开始）。作者本日回应承认 guest 场景可能失效、列出硬件计数器需满足的三条能力要求，并把定位收窄为「baremetal 调试选项」。

## 背景与问题

`sched_clock()` 显示的是相对内核 boot 起点的相对时间，而硬件定时器在固件阶段（SCP 上的系统控制处理器固件、主核上的 ATF）早已在跑，从硬件复位到内核注册时钟之间可能有很长的固件时间。调试跨固件的问题时需要一个所有软件都能读到的统一时间基准，而 `sched_clock` 本身就建立在这个硬件定时器上，所以「用自硬件定时器复位起的绝对计数值」是唯一三方都认同的时间轴。作者说明这套做法在其本地的 RAS 问题排查中已经实际发挥作用（把 kernel / SCP / ATF 各自日志里的时间戳映射到同一条时间轴）。

因此它要解决的不是计数器回绕或复位造成的时间跳变（那是 `sched_clock` 现有 epoch 机制负责的事），而是**跨软件层的时间轴对齐**。作者的定位很明确：这是一个 debug option，主要用于追 bug；而且因为可能是 boot 期 panic，debugfs 不一定可用，所以才需要 cmdline 形态。

## 技术方案

`kernel/time/sched_clock.c` 11 增 3 删，两个改动点：

- 在已有的 `core_param(irqtime, irqtime, int, 0400)` 旁新增 `static bool abs_sched_clock;` 与 `core_param(abs_sched_clock, abs_sched_clock, bool, 0400)`，注释写明含义是「是否使用自时钟硬件复位起的绝对计数值」。
- `sched_clock_register()` 里建立 epoch 的分支：原本无条件执行 `cyc = cd.actual_read_sched_clock(); ns = rd.epoch_ns + cyc_to_ns((cyc - rd.epoch_cyc) & rd.sched_clock_mask, rd.mult, rd.shift);`（新计数器的 epoch 要接上旧计数器的 ns），改为在 `abs_sched_clock` 为真时直接 `ns = cyc_to_ns(new_epoch & new_mask, new_mult, new_shift)`，即新 clock 的 ns 起点就是硬件计数器的绝对值。

作者在 09-03 补了三条「用户需自行保证硬件计数器满足」的能力要求（因为没有现成的能力检测）：

- 一直运行，进入 cpuidle 或系统 suspend 时不停；
- 频率不随 cpufreq 变化；
- 回绕周期足够大。

他还提到本来想用 `CLOCK_SOURCE_SUSPEND_NONSTOP` 做能力检查，但该标志在 `sched_clock.c` 里拿不到，所以只能在提交说明里要求使用者自行确认。另外他承认一处来自自动评审（Sashiko）的有效意见：计算 `epoch_ns` 不该用 `cyc_to_ns()`，应改用 `mul_u64_u64_div_u64()`。

## 版本演进与当前进展

- 09-02 16:21 Feng Tang（`feng.tang@linux.alibaba.com`）首发单补丁（无版本号），动机与 RAS 排查背景写在提交说明里；23:32 Marc Zyngier 回帖，提出「为什么不做成一次性采样 + 日志后处理」、「你的绝对时钟其实不绝对（EL2 可 offset）」、「不愿意让内核背负一个定义上就不可靠的东西」三点。
- 本日（09-03）4 封往返：14:51 Yao Yuan 替 EL2 那条追问「是指 hypervisor 在 EL2 改 vcounter 的情形吗」；15:38 Marc 确认并把它推广到非 VM 场景，同时抛出第二层新问题——**打破 `sched_clock()` handover**；15:45 Feng Tang 逐条回应，把用途收窄为 baremetal 调试、承认 guest 下可能失效、给出上面三条硬件要求与 `CLOCK_SOURCE_SUSPEND_NONSTOP` 拿不到的现实约束；16:07 Feng Tang 认同「运行时操纵时间计数器不是好事」，举 x86 TSC 的前例（Thomas 多次提过），并坦言自己只熟 x86/arm64，不清楚是否真有架构会切换 `sched_clock`；18:20 Yao Yuan 总结 EL2 offset 相当于「hypervisor 对 guest 隐藏自己的处理时间」。
- 尚无 v2，无 tag，未收到 timekeeping 侧维护者的表态；本日全部讨论仍是问题而非结论。

## Maintainer 意见与讨论焦点

- **Marc Zyngier（timekeeping/架构侧的高影响力评审者）** 的两条反对意见有明确层次差别：
  - 方法论层面：「I really have to ask: why isn't this just a one-off sampling of the counter, kept in some user accessible location (debugfs or something else), and ultimately post-processed to align your logs? People have been doing this... forever, and that has been "good enough" so far.」
  - 正确性层面：「your "absolute" clock isn't absolute at all. This doesn't consider SW running at EL2 that could happily offset thing by an arbitrary value.」并在 09-03 展开：「EL2 controls both virtual and physical offsets, and therefore provides the kernel with a different view of time. This doesn't even have to be a VM. There is a lot of non-hypervisor SW out there that just hogs EL2 for more or less nefarious purposes (such as "protecting" the kernel), and offsetting the counter values is one of thing they could do to hide what they are doing.」
  - 结构性层面（本日新增，比前两条更难绕开）：「this change seems to break the `sched_clock()` handover, since the new clock doesn't start where the old one ends. This doesn't affect arm64, which can only have one true source of time, but other archs would probably suffer from this.」
  - 结论性表态：「I appreciate this is not what your case, but I'm somewhat reluctant to burden the kernel with something that is, by definition, unreliable.」
- **Feng Tang（作者）** 本日的应对策略是收窄声明面而不是扩代码：强调只是 debug 选项、主要面向 baremetal、由使用者保证计数器能力；对 handover 问题没有给出技术回应，只是承认「don't know whether there is other architecture that really switches `sched_clock`」——这一条目前处于**未解决**状态。对 debugfs 替代方案他给出了唯一实质抗辩：目标场景可能在 boot 期 panic，debugfs 未必能用，但同时接受「用 dmesg 打印也能达到目的」。
- **Yao Yuan（同厂，未署名为作者）**：在本日承担提问与澄清角色，并主动提出「we can discuss this more in Feng's reply」。
- 焦点收敛为两问：一是**功能是否必要**（一次性采样 + 后处理/dmesg 打印能否完全替代，作者已部分承认）；二是**是否会破坏架构无关的 `sched_clock` 语义**（handover 连续性），后者比 EL2 更硬。

## 合入评估

likelihood: **unlikely**（以当前形态）。

依据：本 thread 唯一的维护者级意见是明确保留态度的（「... reluctant to burden the kernel with something that is, by definition, unreliable.」），而且第二封回帖又追加了一个作者尚未回答的结构性问题（`sched_clock()` handover 在新旧时钟切换点不再连续）；作者的定位是「只在特定 baremetal 平台上、由使用者自证硬件能力」的调试开关，这类「依赖平台前提、无能力检测、语义为 debug」的 cmdline 参数在内核里本就少见；`kernel/time/sched_clock.c` 属于 timekeeping 维护范围，本 thread 中 timekeeping 维护者尚未发言，缺少最关键的支持者；此外 `0400` 权限的 `core_param` 只影响启动期，覆盖面有限，收益却只在单一厂商的 RAS 调试场景中被提及。

可能存活的最小变体（也是讨论已经指向的方向）：把「以绝对计数为原点的 epoch」作为一次性信息打印到 dmesg（而非改变 `sched_clock()` 的语义），既满足跨固件对齐需求，也不动 handover 与可靠性边界。卡点：需要作者接受这个降级形态，或给出 handover 连续性的具体处理与「哪些架构真的会切换 `sched_clock`」的证据。

## 效果评估

邮件中未提供效果数据（本补丁也不需要性能数据）。作者给的是用例层面的证据：「Locally, it did help on chasing some RAS issues which needed cooperation between kernel, SCP firmware and ATF, by mapping the actions from each players into one timeline based on the timestamps in their logs.」——即已在真实问题上验证了可用性，但没有给出具体日志片段、平台型号或问题描述，无法被他人复现。

需要标注的证据缺口：没有说明 `abs_sched_clock` 打开后时间戳偏移量的实际范围（固件阶段究竟占多少秒），也没有说明多核/多 CPU 上 `sched_clock` 是否仍满足各自 monotonic 的既有约束（handover 问题之外的一点）；对 Marc 提出的 EL2 offset 场景与 handover 场景，双方都只有定性论断，没有任何一台机器上的实测。

## 我可以参与的点

1. 直接回答 handover 这个未决问题：把 `abs_sched_clock` 打开后在真正会注册第二个 `sched_clock` 源的平台（典型是早期 jiffy 时钟 → 硬件时钟的切换点，以及支持 hotplug/切换的架构）打印切换前后的 `sched_clock()` 值，量化跳变量。目前全线程只有 Marc 的一句论断和作者「不熟悉其它架构」的坦白，一份实测就能决定这条反对意见是否成立。
2. 帮作者把「能力要求」变成检测：他已说明 `CLOCK_SOURCE_SUSPEND_NONSTOP` 在 `sched_clock.c` 里拿不到。可行的讨论方向是把这三条要求（suspend 不停、频率不随 cpufreq 变、回绕周期足够）在注册时做成一次性 warning 或在 `struct clocksource`/`sched_clock_data` 上暴露一个能力位，避免「用户自行保证」。这是一个具体、小体积、社区容易接受的改法。
3. 提出或验证被讨论指向的降级方案：boot 期把「硬件计数器绝对值 ↔ 内核时间」的换算关系打印一行到 dmesg，日志后处理即可对齐 SCP/ATF 时间轴。若自研平台已有类似需求，这条实现成本远低于维护一个 cmdline 语义开关，也更容易拿到 Ack。
4. 回合视角：这是本周期少见的「调度时间基准与固件日志对齐」需求，OLK 类服务器内核同样要跨 BMC/SCP 日志定位 RAS 与热插拔问题。即便不合本补丁，也值得评估自研内核里以「dmesg 打印 epoch 换算」的形态满足同一需求；若真要回合，必须先确认自家 `sched_clock` 是否存在第二注册点（虚拟化宿主、ARM arch timer 与早期 jiffy 时钟的交接），否则 handover 跳变会直接污染调度统计与 trace 时间戳。

## 参考链接

- 本补丁线程：
  - 补丁本体（09-02）：https://lore.kernel.org/all/20260902082123.95770-1-feng.tang@linux.alibaba.com/
  - Marc Zyngier 的首轮三点质疑（09-02）：https://lore.kernel.org/all/87h5k7mzxy.wl-maz@kernel.org/
  - Yao Yuan 关于 EL2 vcounter 的追问（本日）：https://lore.kernel.org/all/ayvjcnerxbgffnpv6j2kxs2vxfu54gynu6oxv3j2u44he55o4p@pq42xsh4qkrg/
  - Marc Zyngier 的 EL2 展开 + handover 新反对（本日）：https://lore.kernel.org/all/878q5i6ay6.wl-maz@kernel.org/
  - 作者逐条回应与硬件能力要求（本日）：https://lore.kernel.org/all/apkli5dC8z3rcXBy@U-2FWC9VHC-2323.local/
  - 作者关于 TSC 前例与其它架构的坦白（本日）：https://lore.kernel.org/all/apkqtgN3c3LUTmy-@U-2FWC9VHC-2323.local/
- 相关文章：[[sched-20260902-013]]（同一补丁在 09-02 的首发记录）。

---
id: sched-20260903-015
date: '2026-09-03'
subject: 'sched_clock: Add option to use absolute time against hardware clock reset'
subsystem: sched
type: discussion
status: under_review
severity: low
thread_root_msgid: '<20260902082123.95770-1-feng.tang@linux.alibaba.com>'
lore_url: https://lore.kernel.org/all/20260902082123.95770-1-feng.tang@linux.alibaba.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: '2026-09-07'
authors:
- Feng Tang
maintainers_involved:
- Marc Zyngier
- Yao Yuan
patch_series:
- "sched_clock: Add option to use absolute time against hardware clock reset"
merge_assessment:
  likelihood: low
  blocking_issues:
  - "Marc 认为该时钟定义上不可靠，且 EL2 软件可任意 offset 计数器"
  - "abs_sched_clock 打破 sched_clock() handover 连续性，作者本日仍未回应"
  - "无法用 CLOCK_SOURCE_SUSPEND_NONSTOP 做能力检测，只能依赖使用者自证硬件满足三条要求"
  - "kernel/time/ 属 timekeeping 维护范围，本 thread 未见 timekeeping 维护者表态"
  next_action: "评估降级为 dmesg 一次性打印绝对 epoch 换算，并实测是否存在真的切换 sched_clock 的架构"
contribution_opportunities:
- "实测 abs_sched_clock 下 jiffy→硬件时钟切换点的 sched_clock() 跳变量"
- "把三条硬件计数器能力要求做成注册期检测或 warning"
- "验证 dmesg 打印绝对 epoch 是否足以替代语义开关这一降级方案"
- "回合前排查自研内核 sched_clock 注册点数量，避免污染调度统计与 trace 时间戳"
source_email_count: 5
related_articles:
- sched-20260902-013
tags:
- sched_clock
---
