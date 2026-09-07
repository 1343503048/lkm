# sched_clock: Add option to use absolute time against hardware clock reset

## TL;DR

Feng Tang（阿里）给 `kernel/time/sched_clock.c` 加一个 `abs_sched_clock` 启动选项：注册新时钟源时
不再以旧时钟为锚做 epoch 换算，而是直接把硬件计数器自复位以来的值换算成 ns，好让 kernel / SCP 固件 /
ATF 三方日志对齐到同一条时间轴。这条线到 9/7 已经**终结**：Marc Zyngier 两轮质疑（所谓 absolute
并不绝对、EL2 可以任意偏移、且会破坏 `sched_clock()` handover），计时维护者 Thomas Gleixner 9/6 直接拒绝
（"we don't care about your bug chasing war stories at all... stop pestering us with your firmware
debug hacks"），作者 9/7 退化成「只在 `pr_info` 里多打一个 reset 相对值」仍被 Marc 挡回，作者回
"I see your point now, thanks!" 收场。原稿把它记成 `under_review`、并称 Thomas 未表态，两处都需要纠正。

## 背景与问题

`sched_clock()` 表示的是内核启动起算的相对时间；硬件计数器（arm64 arch timer）自复位以来的绝对值里还
包含很长时间的固件阶段。作者的动机是跨软件栈调试：现代服务器平台上 SCP（System Control Processor）
固件、ATF（Arm Trusted Firmware）与 Linux 并行运行，排查 RAS 类问题需要把三方日志的事件排到一条时间轴上，
而三方都能读同一个硬件计数器，所以「自硬件定时器复位起算」是唯一公共基准。作者自述
"Locally, it did help on chasing some RAS issues which needed cooperation between kernel, SCP firmware
and ATF." 需求本身真实，但它改变的是**所有** `sched_clock()` 消费者的时间语义。

## 技术方案

只有一个文件、+11/-3，且是运行时开关而非编译期选项：

```c
+static bool abs_sched_clock;
+core_param(abs_sched_clock, abs_sched_clock, bool, 0400);
```

在 `sched_clock_register()` 里，注册新计数器时改写 epoch 的算法：

```c
 	new_epoch = read();
-	cyc = cd.actual_read_sched_clock();
-	ns = rd.epoch_ns + cyc_to_ns((cyc - rd.epoch_cyc) & rd.sched_clock_mask, rd.mult, rd.shift);
+	if (abs_sched_clock) {
+		ns = cyc_to_ns(new_epoch & new_mask, new_mult, new_shift);
+	} else { ... }
```

作者自己在 commit message 里加了使用前提：用户必须确认自己的 `sched_clock` 硬件计数器支持绝对计数；
回帖里他把前提列成三条——不因 cpuidle/suspend 停止、不随 cpufreq 变频、回绕周期足够大，并说明本想用
`CLOCK_SOURCE_SUSPEND_NONSTOP` 做能力检查但 `sched_clock.c` 里拿不到。另外他承认 Sashiko（自动评审）
指出一处问题：`epoch_ns` 不该用 `cyc_to_ns()` 算，应改用 `mul_u64_u64_div_u64()`——即这个 epoch 换算
本身还有溢出精度缺陷。

## 版本演进与当前进展

- 9/2 16:21 v1 单补丁（UID 73291），无版本号后缀，**全程未重发**。
- 9/2 23:32 Marc Zyngier 第一轮（UID 74431）：先问为什么不做成一次性采样 + 离线对齐日志，再指出
  "your 'absolute' clock isn't absolute at all. This doesn't consider SW running at EL2 that could
  happily offset thing by an arbitrary value."，并表态 "I'm somewhat reluctant to burden the kernel
  with something that is, by definition, unreliable."
- 9/3 14:51 Yao Yuan 追问是否指 VM 场景；9/3 15:38 Marc 第二轮（UID 76312）补齐三条技术理由：EL2
  同时控制虚拟与物理 offset（且不必是 hypervisor，很多"保护内核"的 EL2 软件也会偏移计数器以隐藏行为）；
  以及**新时钟不是从旧时钟结束处开始，会破坏 `sched_clock()` handover**——arm64 只有一个真时间源所以不受影响，
  其它 arch 会受害。
- 9/3 15:45 / 16:07 作者回应（UID 76264/76356）：强调这只是 debug 选项、主要面向裸机，承认 guest 场景
  不成立，并主动类比 x86 TSC 的运行时改值问题（"There used to be similar things happened for TSC on
  x86 platforms, which Thomas has mentioned several times"）。
- 9/6 04:39 Thomas Gleixner（计时维护者，UID 82105）：断然拒绝，并要求把问题留在固件团队。
- 9/7 17:05 作者提出退化方案（UID 84107）：不改语义，只在 `sched_clock_register()` 已有的
  `pr_info` 里多打一个 `has run %lluns since counter reset`（用 `mul_u64_u64_div_u64(new_epoch,
  NSEC_PER_SEC, rate)`）。
- 9/7 17:37 Marc（UID 84197）仍然反对进主线："the only time this is actually useful is when bringing
  up new HW/FW that is broken. So why the need to put that in an upstream kernel, instead of being as
  part of your debug toolbox?"
- 9/7 18:57 作者接受（UID 84469）。线程到此结束，无 v2。

## Maintainer 意见与讨论焦点

- **Marc Zyngier（arm64 计时/KVM）**：三轮发言，是实质反对者，且给出的是**语义层**反驳而不是风格意见：
  绝对性依赖 EL2 不自干计数器（他明确点出不只 VM，还包括"以保护为名占住 EL2"的固件），以及
  `sched_clock()` handover 在跨时钟源切换时的连续性。
- **Thomas Gleixner（计时子系统维护者）**：立场比 Marc 更硬——不是要求改版，而是认为这个需求不属于内核
  该管的范围（"Educate your firmware people"）。维护者层面已经没有讨论空间。
- **作者 Feng Tang 与 Yao Yuan（阿里）**：从「需要选项」退到「需要一条打印」，再退到接受不出线；
  过程中没有出现任何调度侧的人替这个需求说话。
- 调度侧（Peter Zijlstra / John Stultz）与 tracing 侧全程**沉默**——考虑到这会改变所有
  `sched_clock()` 消费者的起点，这本身就是信号：没人愿意为它背书。
- 无 `Acked-by`/`Reviewed-by`，无 NAK 标签但等同于被拒。

## 合入评估

**likelihood: unlikely**。三条依据：计时维护者明确拒绝且给了「不要再来」的措辞；唯一的软着陆方案
（9/7 的 `pr_info` 一行）也被 Marc 以「这属于本地 debug 工具箱」挡回；作者已表示接受，且 5 天内没有 v2。
即使将来复活，前置条件也很重：要有人论证为何不能在 boot 阶段一次性暴露绝对时间戳，如何解决 handover
连续性（Marc 认为其它 arch 会坏），以及 EL2 偏移使绝对性不成立这个物理限制——后者无解，只能限定裸机场景。

## 效果评估

零数据。线程里没有人给出「开启选项后时间跳变消失」的实测，也没有人量化过固件阶段到底有多长、
跨栈日志对齐误差有多大；作者只有「本地确实帮助定位了 RAS 问题」的定性陈述。反过来关心成本的人也没有：
没有人在真机上验证过多时钟源注册 arch（handover）下时间轴会偏多少。唯一可量化的产出是 9/7 那个退化
patch 的形态——它在 `sched_clock_register()` 里加一次除法，运行时代价为 0。

## 我可以参与的点

- **对调度侧最有价值的补位（本线程确实缺）**：整理一份「依赖 `sched_clock()` 自 boot 从 0 起算且跨
  注册连续」的消费者清单——`sched_clock_irqtime`/`psi_account_irqtime`、cputime、PELT 起点、
  watchdog、tracing 时钟同步。Marc 的 handover 论点只有他自己一句话，没人把它落成清单；
  这条清单对以后任何同类提案（包括 OLK 内部私有分支的时钟改动）都复用得上。
- **私有分支的可行做法**：上游不会要这个特性，但需求（多固件栈日志对齐）在服务器上真实存在。可以直接
  拿作者 9/7 的形态作为本地 debug 补丁（只在 `sched_clock_register()` 打印 reset 相对 ns，
  并用 `mul_u64_u64_div_u64()` 而非 `cyc_to_ns()`），零语义风险；这比维护一个 `abs_sched_clock`
  开关安全得多。
- **如果仍想推上游**：正确的切面是 clocksource/boot 时间戳侧（一次性把「自计数器复位以来的 ns」暴露到
  用户态可读位置），而不是给 `sched_clock()` 加分支语义——线程里这个方案是 Marc 提的（一次性采样 +
  离线处理），作者反驳的理由只有「boot 期可能 panic 所以 debugfs 不可用」+「dmesg 也能做但麻烦」，
  这个反驳不够硬，值得替他补完或彻底放弃。
- 相关：[[sched-20260902-011]] 里 `rq_clock()`/`idle_stamp` 那类「时钟起点假设」的回归，正好说明
  动 `sched_clock` 语义的风险不是抽象的。

## 参考链接

- v1 补丁（UID 73291）：https://lore.kernel.org/all/20260902082123.95770-1-feng.tang@linux.alibaba.com/
- Marc Zyngier 第一轮质疑（UID 74431）：https://lore.kernel.org/all/87h5k7mzxy.wl-maz@kernel.org/
- Yao Yuan 的 VM 场景追问：https://lore.kernel.org/all/ayvjcnerxbgffnpv6j2kxs2vxfu54gynu6oxv3j2u44he55o4p@pq42xsh4qkrg/
- Marc Zyngier 第二轮（EL2 offset 与 handover 破坏）：https://lore.kernel.org/all/878q5i6ay6.wl-maz@kernel.org/
- 作者回应（三条硬件前提 + Sashiko 的 mul_u64_u64_div_u64）：https://lore.kernel.org/all/apkli5dC8z3rcXBy@U-2FWC9VHC-2323.local/
- 作者关于运行时改时间计数器的自我保留：https://lore.kernel.org/all/apkqtgN3c3LUTmy-@U-2FWC9VHC-2323.local/
- Thomas Gleixner 拒绝（9/6）：https://lore.kernel.org/all/8733vn5t6p.ffs@fw13/
- 作者退化为 pr_info 一行（9/7）：https://lore.kernel.org/all/ap5-ZM-2RMih3iQ7@U-2FWC9VHC-2323.local/
- Marc 最终反对（9/7）：https://lore.kernel.org/all/86h5k14d34.wl-maz@kernel.org/
- 作者接受收尾（9/7）：https://lore.kernel.org/all/ap6Ypbz4wkftPgBa@U-2FWC9VHC-2323.local/
- 相关：[[sched-20260902-002]]（同期调度核心改动）、[[sched-20260902-011]]（rq_clock/idle_stamp 起点假设）

---
id: sched-20260902-013
date: '2026-09-02'
subject: 'sched_clock: Add option to use absolute time against hardware clock reset'
subsystem: sched
type: feature
status: stalled
severity: low
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
- Marc Zyngier
- Thomas Gleixner
patch_series:
- '[PATCH] sched_clock: Add option to use absolute time against hardware clock reset'
merge_assessment:
  likelihood: low
  blocking_issues:
  - 'Thomas Gleixner 明确拒绝该需求进入内核，并要求问题留在固件侧解决'
  - 'Marc Zyngier 指出 absolute 语义不成立（EL2 可任意偏移虚拟/物理计数器）且破坏 sched_clock() handover 连续性'
  - '作者 9/7 的退化方案（仅在 pr_info 打印 reset 相对 ns）仍被 Marc 以属本地 debug 工具为由挡回，作者已接受'
  - '调度侧与 tracing 侧全程无人支持，也无 Acked-by/Reviewed-by'
  next_action: '不再等待 v2；如需该能力，按 9/7 形态做本地 debug 补丁，或改到 clocksource/boot 时间戳侧一次性暴露'
contribution_opportunities:
- '整理依赖 sched_clock() 从 0 起算且跨时钟源注册连续的内核消费者清单（irqtime/cputime/PELT/watchdog/tracing）'
- '把绝对时间需求改到 clocksource / boot 时间戳侧：启动时一次性暴露自计数器复位的 ns，不动 sched_clock 语义'
- '在裸机上量化固件长时间运行 + 计数器复位造成的 sched_clock 与真实时间偏差，为同类提案补上目前完全缺失的实测'
- '复用 9/7 的 pr_info 形态作为 OLK 私有 debug 补丁（改用 mul_u64_u64_div_u64 避免 epoch_ns 溢出）'
source_email_count: 11
related_articles: []
tags:
- sched/core
---
