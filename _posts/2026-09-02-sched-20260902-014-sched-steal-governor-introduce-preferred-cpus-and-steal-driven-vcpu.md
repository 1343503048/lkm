---
id: sched-20260902-014
date: '2026-09-02'
subject: 'sched, steal_governor: Introduce preferred CPUs and steal-driven vCPU backoff'
subsystem: sched
type: feature
status: under_review
severity: medium
thread_root_msgid: <20260903063240.268775-1-sshegde@linux.ibm.com>
lore_url: https://lore.kernel.org/all/20260903063240.268775-1-sshegde@linux.ibm.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v12
generated_at: '2026-09-07'
authors:
- Shrikanth Hegde
maintainers_involved:
- Yury Norov
- Vincent Guittot
- Dietmar Eggemann
- Frederic Weisbecker
- Mete Durlu
patch_series:
- '[PATCH v12 00/13] sched, steal_governor: Introduce preferred CPUs and steal-driven
  vCPU backoff'
- '[PATCH v12 01/13] sched/cputime: Add kcpustat_field_total helper'
- '[PATCH v12 02/13] cpumask: Introduce cpumask_intersects_and'
- '[PATCH v12 04/13] cpumask: Introduce cpu_preferred_mask'
- '[PATCH v12 05/13] sysfs: Add preferred CPU file'
- '[PATCH v12 06/13] sched/core: Try to use a preferred CPU in is_cpu_allowed'
- '[PATCH v12 07/13] sched/fair: Load balance only among preferred CPUs'
- '[PATCH v12 08/13] sched/core: Push current task from non preferred CPU'
- '[PATCH v12 09/13] sched/debug: Add migration stats due to non preferred CPUs'
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 封面两次点名请求 Peter/Ingo 排进 sched/core 目标 7.4，调度维护者到 9/7 仍无任何表态
  - 唯一第三方独立复测（Yury，v10）为吞吐 -3.1%；作者要求的 hackbench/pgbench 重测尚无结果，x86/s390 数据停留在 v2
  - 没有任何 arch/hypervisor 侧启用者，arch specific interface 被列为合入后的工作；合入后默认 CONFIG_STEAL_GOVERNOR=m
    且不加载
  - 系列仍在变大（12→13 补丁、21→23 文件）且改的是 is_cpu_allowed() 与 sched_tick() 的 stopper push，与同期
    PE/task_h_load/core-sched 改动有 rebase 冲突风险
  next_action: 等 v13 或在 v12 上补两件事：Yury 的 -3.1% 用锁密集负载复测；preferred 收缩与 cpuset 分区/隔离核的交叉行为
contribution_opportunities:
- 在 cpuset 分区/隔离核场景测 preferred 收缩与 cgroup 允许 CPU 集合的交叉行为，这是本系列目前完全没覆盖的评审面
- 用作者的 virtme/vng 脚本在 KVM/Xen + 超卖宿主上以 hackbench/pgbench 复现或推翻 -3.1% 回退
- 验证 is_cpu_allowed() 的 fair-only 早退是否完全隔离 RT/DL 落点（叠加热插拔与 cpuset）
- 整理 arch x hypervisor x 阈值 x steal% x 吞吐 的差异表，替代目前只有 PowerPC 是当前实现的证据缺口
source_email_count: 18
related_articles:
- sched-20260825-008-sched-steal-governor-v11.md
tags:
- sched/core
- sched/fair
- preempt
title: 'sched, steal_governor: Introduce preferred CPUs and steal-driven vCPU backoff'
layout: article
---

## TL;DR

9/2 这条回帖（UID 73311）是 v11 `05/12` 分歧线的**收口**：arm64 32-bit 任务的 cpumask 正确性之争，
用作者新提的 `cpumask_intersects_and()` 三掩码求交解决，同时按 Vincent Guittot 的意见**放弃 arch Kconfig
gating**、保持通用实现；作者在帖尾预告 v12，9/3 发出 **v12 00/13**（+798/-19，23 文件）。争议层次已经从
「该不该往 `is_cpu_allowed()` 塞 preferred CPU」降到 helper 写法与字段摆放。封面把请求写得很明确：
"Could this series be considered for queuing in sched/core, targeting inclusion in 7.4?"
但 Peter Zijlstra / Ingo 到 9/7 仍未表态，而唯一一次第三方独立测试（Yury，v10）给出的是
**吞吐 -3.1%（steal 75%→6%）**。原稿说「缓存内无可引用的效果数据」不成立——数据一直在封面里。

## 背景与问题

问题不是「steal 高所以少跑」这么简单。作者的定位是：vCPU 被抢占的代价超出损失的 CPU 时间本身——
锁持有者被抢占（LHP）、临界区、TLB/cache miss，数据库这类 OLTP/OLAP 混合负载受害最重。宿主超卖时，
guest 主动把工作折叠到更少 vCPU 上（少要 pCPU）会降低宿主争抢，从而提升**整体**吞吐；作者同时承认
纯 CPU 时间型负载可能轻微回退。现有手段都不合适：CPU 热插拔/cpuset 隔离要重建拓扑且**破坏用户态亲和性**，
显式任务亲和性用户管不过来。所以需要一个内核内、协作式、且不违反 affinity 契约的快速 backoff。

方案分两层：

- **A 层（调度器机制，`CONFIG_PREFERRED_CPU`）**：新增 CPU 状态 preferred，
  `cpu_preferred_mask` 严格维持为 `cpu_active_mask` 的子集，在三个入口当提示用——唤醒
  （`is_cpu_allowed()` → `select_fallback_rq()`）、tick push（`sched_tick()` 里用 stopper 把当前任务
  推离非 preferred CPU）、负载均衡（`sched_balance_rq` 把 domain span 限制在 preferred 内）。
  硬约束是尊重用户亲和性：只被 pin 在非 preferred CPU 上的任务就留在原地。目前**只作用于 FAIR 类**，
  RT/DL/sched_ext 明确 deferred（v3→v4 时就砍掉了 RT 补丁）。
- **B 层（策略引擎，`drivers/virt/steal_governor.c`，`CONFIG_STEAL_GOVERNOR=m`）**：周期采样 steal
  time，超过 high_threshold（默认 5%）就少一个 core，低于 low_threshold（默认 2%）就多一个 core，
  形成一个自维护的阶梯。推荐 `interval_ms` 500–5000，且建议 low 阈值不要设 0。
  设计约束：至少保留一个 core preferred，preferred 永远是 active 子集。跨 VM 之间不需要通信。

## 技术方案

本补丁（`is_cpu_allowed()` 那一刀）的演进正好是整个系列的缩影。v11 形态为了 arm64 32-bit 任务
（`allow_mismatched_32bit_el0`）里 `p->cpus_ptr` 可能含架构上不可能的 CPU，写了一段分支 +
`for_each_cpu_and()` 循环，`kernel/sched/core.c` +39/-2；Dietmar Eggemann 主张不需要
（`p->cpus_ptr` 本来就是 `task_cpu_possible_mask(p)` 的子集，交集里不可能出现非法 CPU），
作者 8/27 反驳说 `task_allowed_on_cpu()` 里还额外查了 `task_cpu_possible()`，所以他保留了防御性检查。
Vincent Guittot 的两句是决定性的："It's always better to support all arch by default, unless something
is missing which is not the case here."（不要加 arch gating）以及 "But the cpumask is already available
not like if you need to create a new one"（掩码现成，别怕查）。最终 9/2 的解法把三方意见折成一个 O(N)
三掩码求交，v12 里 `task_can_sched_on_preferred()` 缩成 4 个 early-out + 1 个 return：

```c
+	return cpumask_intersects_and(p->cpus_ptr, cpu_preferred_mask,
+				      task_cpu_possible_mask(p));
```

配套新增 `__bitmap_intersects_and()` / `bitmap_intersects_and()` / `cpumask_intersects_and()`
（v12 的 02/13，也是 12→13 个补丁的原因）。作者在同一封里给出两个附带结论：
`cpumask_intersects()` 与 `cpumask_intersects_and()` 在他跑的负载下无可测差异；`cpumask_intersects_and()`
还可用于 `drivers/cpuidle/coupled.c:cpuidle_coupled_any_pokes_pending()`，会单独发补丁。
`is_cpu_allowed()` 是全调度类共用的可运行性判断，所以「只有 FAIR 类认 preferred」这条
（`p->sched_class != &fair_sched_class` 早退）是它不被 RT/DL 语义污染的边界，review 时应盯这一行。

## 版本演进与当前进展

12 个版本的骨架（取自封面 revision history）：RFC v1 只有 push 机制 + 手工 sysfs 提示；v2 改名
Preferred CPUs 并做成架构无关；v3 引入 `CONFIG_PREFERRED_CPU`；v4 把 preferred 改为 active 子集、
砍掉 RT、deferred sched_ext；v5 把 steal 计算挪进驱动（STEAL_MONITOR）；v6 放弃在
`select_fallback_rq()` 里缓存 preferred 状态、放弃 wakeup 补丁；v7 收敛驱动补丁数、可能 CPU 改为
active 计算 steal；v8 改名 STEAL_GOVERNOR、强制设计约束并在不满足时恢复状态、`interval_ms` 下限
10ms→100ms；v9 全部并入 `drivers/virt/steal_governor.c`；v10 引入 `kcpustat_field_total()`、
删掉 idle balancing 里的 `cpu_preferred` 检查（顺带自洽地处理 `nohz.next_balance`）、文档挪到
`sched-paravirt.rst`；**v11（8/25）** steal 比例分母从 possible 改回 active（避免阈值被稀释，Yury +
Ionut Nechita）、加 XEN dom0 阻塞检查、修 arm64 32-bit 任务可能崩溃与 `__migrate_task()` abort 导致的
亲和性竞态（多来自 Sashiko 自动评审）；**v12（9/3）** 只做 arm64 简化 + `cpumask_intersects_and` +
去掉 arch gating。基线也从 `68e37487810a ("sched/fair: Fix flat hierarchy")` 换到
`ef9293b3b797 ("sched: dynamic: Fix preemption model strings")`——说明作者在跟 tip/sched/core 前进。
其余进展：9/4 Frederic Weisbecker 给 `01/13` `Acked-by`；9/5 Yury 在 `v12 08/13`（tick push）上开新一轮
意见；9/7 作者逐条回复并承诺再改一版。

## Maintainer 意见与讨论焦点

- **Yury Norov（NVIDIA，本系列最强评审者，封面专门为致谢）**：9/1 一句 "ARM64 testing is obviously
  missed." 把 arm64 支持问题钉住；9/5 转到 `v12 08/13` 的具体问题：`select_fallback_rq()` 拿锁又放锁
  之后与别的进程存在竞态窗口、新增字段应被 `CONFIG_PREFERRED_CPU` 保护、变量命名（设 true 的时机在调用
  stopper 之前，建议 `need_push_to_npc`）、字段为什么放在 `cfs_tasks` 与 `avg_rt` 之间、以及
  "What about pahole?"。作者 9/7 的答复值得记：正常不会拿 rq 锁，即使任务被负载均衡抢走，
  `task_rq(p) == rq` 检查会兜住所以安全；命名与 CONFIG 保护接受；pahole 只在 powerpc 128B cacheline
  上看过（那里是 64 字节空洞），64B 行上不最优，会挪到 `balance_callback/nohz_idle_balance/idle_balance`
  后面那个 6 字节空洞或 `ttwu_local` 后面的 4 字节空洞。
- **Vincent Guittot（Linaro）**：两条意见直接改变了实现形态——不加 arch gating、不做多余的掩码构造。
- **Dietmar Eggemann（ARM）**：认为 `allow_mismatched_32bit_el0` 主要是 Android 13 以前的 32-bit
  userspace 场景，arm64 上启用 steal_governor 时预期与其它已测架构无显著差异。他没有给 NAK，但他是
  「这个特例值不值得存在」的质疑方。
- **Ionut Nechita（Sunlight Labs）**：XEN dom0 阻塞检查的来源（v11）。
- **Frederic Weisbecker**：`01/13 kcpustat_field_total` `Acked-by`（9/4）——外围 helper 已被接受。
- **Mete Durlu（IBM）**：`01/13` `Reviewed-by`（与 Yury 并列）。
- **Peter Zijlstra / Ingo Molnar**：对封面的排队请求**沉默**（9/3 至今）。这是唯一的真卡点。
- 无 NAK。跨 8/27、8/31、9/1、9/2 的四分歧线以作者吸收意见告终。

## 合入评估

**likelihood: unclear**。有利面：12 轮迭代、争议已降级为局部实现细节、`01/13` 拿到 1 个 Ack + 2 个
Reviewed、作者对每条意见都在 1–2 天内给出可验证的答复并落到 changelog、体积仅 +798/-19 且策略层完整
隔离在 `drivers/virt/` 下（核心侧只有 `kernel/sched/core.c` 120 行、`fair.c` 8 行）。不利面更实质：

1. **调度维护者从未表态**，而封面两次点名请求排进 sched/core、目标 7.4；作者自己也说 v11 是"在合并窗口
   发以收集意见"。没有 Peter 的排队答复，就没有可判断的进展。
2. **收益证据不闭环**：PowerPC 是主力数据（作者自测），x86/s390 那份是 Ilya Leoshkevich 在 OSPM26 期间
   基于 **v2** 测的，作者自己注明"implementation has changed and some overhead has been removed since
   then"；唯一第三方独立复测（Yury，v10）是 -3.1%。作者对回退的解释（payload 无锁无临界区、每任务仍被
   抢占 75% 只是换了共享对象、外加上下文切换开销）在机制上讲得通，但要求换 hackbench/pgbench 重测的请求
   到 9/7 没有得到结果。
3. **启用面仍是空档**：arm64 现在无 gating 地进来了，但没有任何 arch/hypervisor 侧的启用者；作者明确把
   "arch specific interface 以拿到额外收益"列为 merge 之后的工作。也就是说合入后短期内它对主线用户是
   默认关闭的死代码（`CONFIG_STEAL_GOVERNOR=m` 且不默认加载）。
4. 系列规模仍在长（12→13 补丁、21→23 文件），且 `is_cpu_allowed()` 与 `sched_tick()` 里的 stopper push
   属高关注面；同时 09-02 当天 PE 批合并、`task_h_load()` 重做、core-sched 7/7 系列都在动
   `pick_next_task()`/`sched_tick()` 附近，rebase 冲突风险不低（v12 已因此换过一次基线）。

## 效果评估

封面给的数字（PowerPC，VM1 60VP/30EC + VM2 30VP/20EC，共享池 50×SMT8，两 VM 跑同一负载，报总吞吐）：
hackbench 20 groups 11.39→7.09（+37.75%）、40 groups 20.32→11.31（+44.34%）、10 groups +10.58%；
kernbench 耗时 231→199（+14%）；Daytrader（db2 交易代理）30% 负载 1x→1.53x、60% 负载 1x→1.41x。
反面同样在封面里：schbench 三种配置只在 +1.71%~+5.90% 间晃、作者自己的批注是
"Effectively means no-improvements or regressions"；10 groups(-p)/20 groups(-p) 里
governor 编进来但**未启用**的列相对基线就是 -3.85%/-8.30% 的噪声级回退。作者声明无 steal 时
（dedicated LPAR 或只跑一个 VM）开关无差异，`STEAL_GOVERNOR=n` 开销可忽略。
第三方：Yury 的 v10 笔记本测试（4 VM × 8 vCPU / 8 pCPU，2 分钟，纯数学 payload）总吞吐
49460 → 47941（-3.1%），steal 从 ~75% 收敛到 ~6%——**收敛机制有效，收益未复现**，
他同时要求系列自带测试（附了 541 行 virtme/vng 脚本）。鲁棒性测试清单（作者自述）覆盖热插拔、
nohz_full housekeeping 组合、pin 在非 preferred 的任务保持不动、`taskset -cp` 亲和性迁移、
480 CPU 机器上 4800 个 stress-ng 线程仍能折叠。已知限制作者自己写了：stopper 只推当前任务不推整条 rq、
不做 NUMA 感知的核心挑选（按 CPU 号砍最后一个 active core）、只支持 FAIR 类。

## 我可以参与的点

- **cpuset/cgroup 视角是这条线最缺的评审意见**（与用户主线直接相关）：`cpu_preferred_mask` 被定义为
  `cpu_active_mask` 子集、且驱动承诺不破用户 affinity，但二者与 cpuset 的交叉只被作者的手工清单覆盖。
  值得直接测并回帖的是：cpuset 分区（含 `cpuset.cpus.partition` root/isolated）叠加 steal 收缩时，
  被砍掉的 core 是否一定落在该 cgroup 允许集合外？封面写的是"steal_governor 按 CPU 号砍最后一个
  active core，不做 NUMA 感知拼接"，以及极端情况下"限制到第一个 housekeeping core"——这两条对
  隔离核/大内存 NUMA 机器的落点判断是可以直接给数据的。
- **补上 Yury 要的那次复测**：他的 `-3.1%` 用的是无锁纯数学 payload，作者已解释为什么不合适；
  在 KVM/Xen guest + 超卖宿主上用 hackbench/pgbench 复刻他的 virtme 脚本，是收敛这条线最省力的贡献，
  目前线程里没人做。
- **`is_cpu_allowed()` 改动的非 FAIR 影响面**：现在靠 `p->sched_class != &fair_sched_class` 早退隔离，
  可以做一次 RT/DL + cpuset + 热插拔的组合验证，确认 preferred 状态不会经由
  `select_fallback_rq()`/stopper push 影响 RT/DL 落点；这也是 Peter 最可能问的点。
- **arch 差异表**：现有数据只有 PowerPC 是当前实现，x86/s390 停在 v2、arm64 完全无数据（Dietmar 只给了
  预期，没测）。一张「arch × hypervisor × 阈值 × steal% × 吞吐」的表比再多一轮 code review 更有说服力。
- **回合判断**：+798 行、新 CPU 状态、新驱动、tick 里加 stopper push，**不是**回合候选；但如果它进 tip，
  值得同步关注的是 `include/linux/cpumask.h`(+42) 与 `kernel/cpu.c`(+6) 这两处基础设施，
  它们比策略驱动更可能被 cpuset 相关改动复用。

## 参考链接

- 9/2 收口回帖（UID 73311，含 v11→v12 完整 diff）：https://lore.kernel.org/all/8de8d33f-b3e5-407c-98bb-65e8ebe3e100@linux.ibm.com/
- v11 封面（8/25，含 benchmark 与 12 版 revision history）：https://lore.kernel.org/all/20260825103855.721013-1-sshegde@linux.ibm.com/
- v11 05/12 补丁本体：https://lore.kernel.org/all/20260825103855.721013-6-sshegde@linux.ibm.com/
- v12 封面（9/3，00/13）：https://lore.kernel.org/all/20260903063240.268775-1-sshegde@linux.ibm.com/
- v12 06/13（最终形态的 task_can_sched_on_preferred）：https://lore.kernel.org/all/20260903063240.268775-7-sshegde@linux.ibm.com/
- Dietmar Eggemann 的 32-bit EL0 论证（8/27）：https://lore.kernel.org/all/2e1085f1-82f2-42dc-ae72-0bedffb414f3@arm.com/
- 作者保留防御性检查的反问（8/27）：https://lore.kernel.org/all/0a62143d-6d8d-46a4-ac92-f8ca7268e555@linux.ibm.com/
- 作者询问是否现在就启用 arm64（8/31）：https://lore.kernel.org/all/53035ba4-53ec-4907-93b8-c8b957d1fa61@linux.ibm.com/
- Vincent Guittot「默认支持所有 arch」：https://lore.kernel.org/all/CAKfTPtA5Bdw89hezn1wi_p0m0dJgJJ1GYg8H93PsvsMC4bVJxA@mail.gmail.com/
- Yury Norov「ARM64 testing is obviously missed」：https://lore.kernel.org/all/apWxmL_brfi4fa4z@yury/
- Vincent Guittot「cpumask 是现成的」：https://lore.kernel.org/all/CAKfTPtA4zmD=0Es2cXSHAodTZGLJPvv88s0_4QScp745PxFVMw@mail.gmail.com/
- Dietmar Eggemann 关于 allow_mismatched_32bit_el0 的实际影响面：https://lore.kernel.org/all/3368b089-32ce-4521-ab19-e37c9f029b8b@arm.com/
- Yury Norov 的 v10 独立复测（-3.1% 与测试脚本）：https://lore.kernel.org/all/aojOp7KNsVGGb2CX@yury/
- 作者对回退的解释与换 benchmark 的请求：https://lore.kernel.org/all/4158c891-85d8-492c-be19-157cb0f6100a@linux.ibm.com/
- Frederic Weisbecker 对 01/13 的 Acked-by：https://lore.kernel.org/all/apmfne3iBct7oNTp@localhost.localdomain/
- Yury Norov 在 v12 08/13 上的新一轮意见（9/5）：https://lore.kernel.org/all/aptiJP_8SWwZWju6@yury/
- 作者对 pahole/命名/竞态的逐条答复（9/7）：https://lore.kernel.org/all/7d88a3c4-a7e4-4814-9e29-84955b69a5b3@linux.ibm.com/
- v10 封面（第三方测试所针对的版本）：https://lore.kernel.org/all/20260812054033.95658-1-sshegde@linux.ibm.com/
- 相关：[[sched-20260825-001]]（v11 主文）、[[sched-20260822-003]]（Yury 独立测试与回退）、[[sched-20260902-001]]（同期 guest/steal 方向的 PE 批合并）
