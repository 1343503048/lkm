---
id: sched-20260909-010
date: '2026-09-09'
subject: 'sched, steal_governor: Introduce preferred CPUs and steal-driven vCPU backoff'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: 20260909135617.871006-1-sshegde@linux.ibm.com
lore_url: https://lore.kernel.org/all/20260909135617.871006-1-sshegde@linux.ibm.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v13
generated_at: '2026-09-10T00:55:00'
authors:
- Shrikanth Hegde
maintainers_involved:
- Yury Norov
patch_series:
- version: v11
  msgid: 20260825103855.721013-1-sshegde@linux.ibm.com
  date: '2026-08-25'
  summary: steal 比例分母改为返回 active CPU 而非 possible CPU，避免阈值被稀释（Yury Norov、Ionut Nechita）；加入
    XEN dom0 阻塞检查；多架构框架推迟到合并后再设计。
  review_outcome: Yury Norov 与 Ionut Nechita 的意见被采纳。
- version: v12
  msgid: 20260903063240.268775-1-sshegde@linux.ibm.com
  date: '2026-09-03'
  summary: 简化 ARM64 32 位任务 p->cpus_ptr 可能包含架构上不可能 CPU 的情形（Dietmar Eggemann、Vincent
    Guittot），为此新增 cpumask_intersects_and；按 Vincent 意见暂不做架构 kconfig gating。
  review_outcome: 09-09 06:58 Yury Norov 就该系列 08/13 的 struct rq 字段放置再提意见：不应依赖 hole
    优化，应放到逻辑相关字段旁，并建议放 prev_steal_time* 或 active balancing 段。
- version: v13
  msgid: 20260909135617.871006-1-sshegde@linux.ibm.com
  date: '2026-09-09'
  summary: 改名 push_task_work_done → npc_push_work_pending、按 Yury 意见挪到 steal_* 字段旁并加
    CONFIG_PREFERRED_CPU 守卫、更新 select_fallback_rq 之后 rq lock 的注释；13 补丁，23 files changed,
    804 insertions(+), 19 deletions(-)。封面请求 Peter/Ingo 考虑排入 sched/core、目标 7.4。
  review_outcome: v13 发出当天（21:56 之后）无人回帖；Yury 的三条意见已在本轮全部落地。
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Peter Zijlstra 尚未回应「入队 sched/core 冲 7.4」的请求，v13 发出当天无人回帖
  - 横跨多子系统的改动缺对应维护者 ack：drivers/base/cpu.c 与 kernel/cpu.c 的 preferred CPU sysfs、drivers/virt
    新目录、arch/s390/hiperdispatch.c、fs/proc/uptime.c、MAINTAINERS 新增条目
  - x86 与 s390 的量化数据由作者明确标注为基于 v2 由 Ilya Leoshkevich 在 OSPM26 期间所跑，实现此后已变，非 PowerPC
    证据不适用于当前版本
  - 作者自陈依赖 steal time 记账准确性，PowerVM 在单 VM 场景下报出异常 steal time 仍在等 hypervisor 团队排查
  next_action: 等 Peter 对排队时点表态；补齐 driver core / drivers/virt / s390 / procfs 侧维护者
    ack；用当前版本重跑 x86 与 s390 的三列对照数据
contribution_opportunities:
- kind: review
  description: preferred CPU 的 sysfs（drivers/base/cpu.c、kernel/cpu.c）、drivers/virt
    新目录、fs/proc/uptime.c 与 MAINTAINERS 条目当天均无对应维护者表态，可逐条提请相应维护者评审
- kind: testing
  description: 用当前 v13 重跑 x86 KVM 的 pgbench/hackbench/sysbench 三列对照（baseline/disabled/enabled），替换作者自陈已过期的
    v2 数据，并验证 schbench 上无收益是否成立
- kind: extend
  description: 封面明列的 deferred 项中，把 push 从只推 rq->curr 扩展到推该 rq 上全部排队任务、以及把机制从 FAIR
    扩到 RT，都是可独立推进的后续 patch
- kind: discussion
  description: NUMA splicing 目前仅按 CPU 编号去掉最后活跃核、假定 CPU 在节点间均匀分布，可给出不均衡拓扑下的具体失败场景并讨论折叠目标
- kind: new_patch
  description: 若自家分支需要显式关闭该特性，可重提架构级 gating——作者在 v11→v12 采纳 Vincent 意见去掉了 gating 但留了口子「If
    a need arises, arch specific gating could be introduced」；回合时 Fixes 需引用自家分支 commit
source_email_count: 9
related_articles:
- sched-20260907-011
- sched-20260905-005
- sched-20260903-002
- sched-20260902-014
tags:
- load_balance
- affinity
- sched_debug
- arm64
title: 'sched, steal_governor: Introduce preferred CPUs and steal-driven vCPU backoff'
layout: article
---

## TL;DR

本文为增量更新，问题建模与 v8..v12 的演进见 related_articles 中的 sched-20260907-011 / sched-20260903-002 / sched-20260902-014 / sched-20260831-007。09-09 是这个系列**正式请求排队**的一天：Shrikanth Hegde 21:56 发出 v13（13 补丁），封面直接问 Peter/Ingo「能否考虑进 sched/core、目标 7.4」，并把上一轮 Yury Norov 的三条评审意见全部收掉（字段改名 `npc_push_work_pending`、挪到 `steal_*` 旁边、加 `CONFIG_PREFERRED_CPU` 守卫）。同一天上午还有 Yury 与作者关于 `struct rq` 布局的收尾对话，作者用 pahole 数据证明改动不增加 cacheline 数。

## 背景与问题

大规模机器上客户普遍用 CPU 超配：给 VM 配很多 vCPU、背后是更小的共享 pCPU 池。多个 VM 同时高负载时 pCPU 池被争抢，hypervisor 必须为了公平 preempt 某个 vCPU；如果被 preempt 的 vCPU 正持锁或关中断，整体前进能力就崩了——除了丢失的 CPU 时间，还有锁持有者被抢占、TLB/cache miss、host 调度开销这些隐性成本。有效的缓解手段是让 guest **主动把负载折叠到更少的 vCPU 上**：少要一些 pCPU，降低 host 侧争抢，反而提高整机吞吐。

已有的做法都不合适：CPU 热插拔与隔离 cpuset 是重量级、需要管理动作且要重建拓扑，还会破坏用户态的 CPU 亲和性；显式任务亲和性对用户几乎不可管理。所以需要的是一种**快的、协作式的、在内核里的**退让机制，并且不违反用户/任务的亲和性契约。

建模选择：用 guest 已看到的 steal time 作为争抢程度的量化——它在 paravirt 世界是既有构造，主流架构都支持，量级随争抢程度自然缩放，今天已被管理员用来调整 VM 配置。

## 技术方案

分两层，刻意把策略与机制切开。

**Layer A：调度器机制（preferred CPUs）**。引入一个新的 CPU 状态 preferred，表示「这个 vCPU 可以安全使用、用它不会加剧底层 pCPU 争抢」，通过 `cpu_preferred_mask` 暴露，并严格维持为 `cpu_active_mask` 的子集。调度器把它当提示用，三个介入点：

1. **唤醒**：`is_cpu_allowed()` 检查目标 CPU 是否 preferred，否则走 `select_fallback_rq` 选一个 preferred CPU（前提是任务亲和性允许）。
2. **tick 推送**：`sched_tick()` 里如果当前 CPU 非 preferred，用 stopper 线程把正在跑的任务主动推到一个 preferred CPU。
3. **负载均衡**：`sched_balance_rq` 把域 span 限制在 `cpu_preferred_mask` 内，避免把任务往非 preferred CPU 上拉。

硬约束：**绝不破坏用户亲和性**——如果任务被独占钉在非 preferred CPU 上，它就留在那里。

**Layer B：策略引擎（`drivers/virt/steal_governor.c`）**。核心调度器不应该规定虚拟化策略，因此策略独立成一个可加载驱动（`CONFIG_STEAL_GOVERNOR`），带 sysfs 控制接口（`Documentation/driver-api/steal-governor.rst` 151 行 + ABI 文档 14 行），依据 steal 比例的低/高阈值（默认 1000ms 周期、200/500 阈值）在 vCPU 之间做折叠/展开决策。s390 的 `arch/s390/kernel/hiperdispatch.c` 也做了适配。

规模：23 files changed, 804 insertions(+), 19 deletions(-)，其中 `kernel/sched/core.c` +125、`kernel/sched/fair.c` 8 行、`kernel/sched/sched.h` +9、`drivers/virt/steal_governor.c` 新文件 296 行，另有 `cpumask`/`bitmap` 侧新增 `cpumask_intersects_and`。特性对支持 paravirt + steal time 记账的所有架构通用，作者明确「如有需要再引入架构级 gate」（这是 v11→v12 时 Vincent Guittot 要求去掉架构 kconfig gating 的结果）。

## 版本演进与当前进展

v13 的改动全部是 Yury Norov 的收尾意见（v12→v13 changelog 原文四条）：把 `push_task_work_done` 改名为 `npc_push_work_pending`；按 Yury 要求在 `struct rq` 里挪位置；给它加 `CONFIG_PREFERRED_CPU` 守卫；更新 `select_fallback_rq()` 之后关于 rq lock 获取的注释。

这场对话发生在当天上午：06:58 Yury 提出（`<aqCTMREUoCmbtygK@yury>`）

> The struct rq is highly configurable. Depending on your config, the holes will migrate to different places. I'd not rely on just 'optimizing holes' problem. Just put the new field next to logically related existing fields. You've got paravirt-related prev_steal_time and prev_steal_time_rq, and you've got the /* For active balancing */ section. Maybe one of them?

作者 11:21 用 pahole 回了一组对照数据（`<ee949902-1158-456e-af4d-b1fe6c42ac61@linux.ibm.com>`）：把字段放到 `#ifdef CONFIG_PARAVIRT_TIME_ACCOUNTING / u64 prev_steal_time_rq / #endif` 之后并加 `#ifdef CONFIG_PREFERRED_CPU` 守卫，128 字节 cacheline 下 `struct rq` 前后都是 `size: 5632, cachelines: 44`，成员 104→105、holes 15→17、sum holes 502→533；64 字节 cacheline 下 `prev_steal_time_rq` 之后本来就有 "XXX 16 bytes hole, try to pack"，也能吸收。并当场承诺 "I will make this change and send out v13 today." —— v13 确实在 21:56 发出。

版本节奏：v10（08-12）→ v11（08-25）→ v12（09-03）→ v13（09-09）。更早它是一个架构相关的 RFC，现在演化成「调度器机制 + 虚拟化驱动」的组合。当天 v13 之内收到的 8 封邮件里**没有任何新回帖**（v13 是 21:56 发的，当天结束）。

## Maintainer 意见与讨论焦点

- **Yury Norov（cpumask/bitmap 维护者）本日唯一的技术意见是布局论证方法学**，而且被完全接受。关键点值得记下来：在 `struct rq` 这种高度可配置的 structs 里，用「正好填进某个 hole」作为放置理由是站不住的，因为换一份配置 hole 就搬家了；正确做法是放到逻辑相关的字段旁边。作者的回应不是辩解而是直接给 pahole 双 cacheline 尺寸的对照，这也是意见能被快速关闭的原因。
- **作者主动请求排队**："Could this series be considered for queuing in sched/core, targeting inclusion in 7.4? The feature could also benefit from a good testing cycle in the tip tree." 这是本系列第一次明确请求入队时机。
- **作者自己列出的、期待被质疑的点**："If there are any remaining design or implementation concerns, please let me know." 封面同时主动承认了三项限制：依赖 steal time 记账准确（架构给错值会导致次优决策甚至性能回退）；纯 CPU 时间型负载（如 `stress-ng --cpu=N`）可能不受益甚至小幅回退。
- **已推到合并之后的工作**（封面明列）：架构相关接口的设计、一个自测框架（至少在 KVM 环境）、把推送从「只推 curr」扩展到「推该 rq 上全部排队任务」、RT 与 sched_ext 类（当前只覆盖 FAIR）、NUMA 感知的 splicing（现在只是按 CPU 编号去掉最后活跃核）。
- 历史分歧的沉淀：v11→v12 采纳了 Dietmar/Vincent 的 ARM64 32 位任务 `p->cpus_ptr` 可能包含架构上不可能 CPU 的简化（并因此新增 `cpumask_intersects_and`），以及 Vincent 要求的「暂不做架构 kconfig gating」；v10→v11 采纳了 Yury 与 Ionut Nechita 的 steal 比例分母应返回 active CPU 而非 possible CPU（避免阈值被稀释）、以及 XEN dom0 阻塞检查。

## 合入评估

`likelihood=medium`，且这是我看到过的该系列最接近可合入的状态——但仍有实质不确定性。

有利：13 个版本迭代，评审意见到 v13 已经收敛为命名/位置/注释级别的收尾（Yury 的四条全部落地）；跨三个架构（PowerPC 主测 + x86/s390 KVM 数据）；文档与 ABI 齐备；机制与策略分层清楚，通用性上有明确边界（不动用户亲和性、只覆盖 FAIR）；作者自陈「I believe the series has now converged and can be considered for merging」。

不确定：本日以 `steal_governor`/`preferred CPU` 命名的**内核改动横跨 7 个子系统**——`kernel/sched/`、`lib/bitmap.c`+`include/linux/bitmap.h`、`include/linux/cpumask.h`、`drivers/base/cpu.c`（sysfs）、`kernel/cpu.c`、`drivers/virt/`、`arch/s390/`、`fs/proc/uptime.c`、`Documentation/ABI/`。到目前为止只有 Yury（cpumask 侧）明确在 review，**cpufreq 无关但 `kernel/cpu.c` 与 `drivers/base/cpu.c` 需要 Greg/热插拔侧、`drivers/virt/` 需要该树维护者、s390 需要 IBM 侧表态**，这些 ack 当天一个都没有。作者请求 Peter 排队的诉求本身也还没有任何回复。另外作者自己承认 x86/s390 的数据是 **基于 v2** 由 Ilya Leoshkevich 在 OSPM26 期间跑的，虽然核心想法一致但实现已变、"some overhead has been removed since then"——严格说，非 PowerPC 的量化证据已经不适用于当前代码。

`next_action`：需要 Peter 对「入队 sched/core 冲 7.4」明确表态，需要跨子系统 maintainer 的 ack（bitmap/cpumask 已有 Yury 的评审脉络，但 driver core / drivers/virt / s390 / procfs 侧仍是空白），以及一份用当前版本重跑的 x86/s390 数据。

## 效果评估

封面给了三架构的数据表，其中 PowerPC 是**当前实现**的实测，且提供了难得的三列对照（baseline / steal_governor disabled / enabled）——中间那一列正是回答「开销是否来自框架本身还是策略生效」的关键：

PowerPC（VM1 60VP/30EC + VM2 30VP/20EC，共享池 50 核 SMT8，默认参数 1000ms/200/500，两 VM 跑同一负载、报总和）：

- hackbench：10 groups 5.20 → disabled 5.40(-3.85%) → **enabled 4.65 (+10.58%)**；20 groups 11.39 → 12.01(-5.44%) → **7.09 (+37.75%)**；40 groups 20.32 → 19.80(+2.56%) → **11.31 (+44.34%)**；带 `-p` 的三档为 +13.08% / +4.19% / +4.48%。
- schbench（-L -n 0 -r 30 -s 0，-m 1 / t=128,256,512）：enabled 分别 +2.11% / +1.71% / +2.04%，disabled 分别 +5.90% / +0.18% / +3.26%。作者的批注很诚实："Effectively means no-improvements or regressions"——schbench 上确实没有可信收益（disabled 列的 +5.90% 比 enabled 还高，说明在噪声内）。
- kernbench（elapsed，-j nr_cpus）：231 → 235(-1.7%) → **199 (+14%)**。
- Daytrader（DB2 的真实交易系统代理负载）：30% 负载 1x → 0.96x → **1.53x**；60% 负载 1x → 0.94x → **1.41x**。
- phoronix/memcached GET 1:1000（1 写 1000 读）：1x → 0.99x → **1.2x**。
- 无 steal time 的独占 LPAR 下 enabled/disabled 吞吐相同 → 框架自身开销可忽略。

x86（cascade-lake，32 线程=16 核）与 s390（z16，16 线程=8 核 SMT-2）是 ΔRPS 表，最好与最差若干档：x86 hackbench 8VM×16CPU +90.73%±9.97%、pgbench 16VM×4CPU +31.77%±2.44%，最差 sysbench 16/4 -3.22%±1.09%、pgbench 4/32 -3.21%±0.79%；s390 pgbench 2VM×8CPU +73.50%±35.91%（注意这个 ±35.91% 的标准差意味着该数字几乎不可用）、pgbench 16/4 +61.30%±4.09%、hackbench 16/4 +54.11%±4.38%，最差端 -4.99%±3.31%。**但这两组数据作者明确标注是基于 v2 的**，不能当作当前实现的证据。

作者的总结（我认为与数据相符）：多数真实负载有改善；无 steal time 时开销可忽略；纯 CPU 时间型负载可能小幅回退。需要指出的薄弱处：s390/x86 数据版本过旧、PowerPC 的 schbench 一行实际上不成立、以及 memcached 里 GET 1:1 有小幅回退——作者把这一条归因于 PowerVM 在单 VM 情况下报告的 steal time 本身不对（已交 hypervisor 团队查），并因此专门写了「本特性假定 steal time 准确」的限制条款。这个归因目前没有数据支撑，属作者的现场判断。

## 我可以参与的点

- `review`：**跨子系统 ack 现状**是这组补丁最实际的缺口。`kernel/cpu.c`、`drivers/base/cpu.c` 的 preferred CPU sysfs 文件、`fs/proc/uptime.c`（steal 显示）、`drivers/virt/` 新目录与 MAINTAINERS 的 9 行，当天都还没有对应维护者说话。帮忙把这些点逐条 @ 到相应维护者并追问，比再提一个代码细节更有价值。
- `testing`：用**当前 v13** 重跑 x86 KVM 的 pgbench/hackbench/sysbench 对照（baseline / disabled / enabled 三列），补上作者承认已经过期的那份证据；顺手确认 schbench 上「无收益」是否成立。这正好落在作者请求的 "a good testing cycle in the tip tree" 之前。
- `extend`：封面明列的 deferred 项中有两项是纯调度器侧、独立可做的——把 push 从「只推 `rq->curr`」扩展到推该 rq 上全部排队任务，以及把该机制从 FAIR 扩到 RT。作者认为"there is no need for it"，如果自家场景需要 RT 或大量排队任务的折叠，这是能直接提 PR 的方向。
- `new_patch`：`CONFIG_PREFERRED_CPU` 目前不做任何架构 gating，任何支持 paravirt + steal 记账的架构都会编入这段代码。若自家分支需要显式关闭，可以按 v11→v12 时 Vincent 的那次意见被推翻的路径重提「架构级 gating」——注意作者留了口子："If a need arises, arch specific gating could be introduced." 回合到自家分支时按 OLK 规范 `Fixes` 需指向自家 commit。
- `discussion`：NUMA splicing 现在只是按 CPU 编号去掉最后活跃核，作者假定 CPU 在节点间均匀分布。在 NUMA 机器上这条假设常不成立，而这个问题当天没有任何人提。可以先给出一个具体的失败场景（例如跨节点不均衡时折叠到哪个节点）来讨论。

## 参考链接

- v13 cover letter（含 v12→v13 changelog、三架构数据表、限制与后续工作）: https://lore.kernel.org/all/20260909135617.871006-1-sshegde@linux.ibm.com/
- v13 08/13（push current task）: https://lore.kernel.org/all/20260909135617.871006-9-sshegde@linux.ibm.com/
- Yury Norov 关于 struct rq 布局的意见: https://lore.kernel.org/all/aqCTMREUoCmbtygK@yury/
- 作者的 pahole 对照与「今天发 v13」承诺: https://lore.kernel.org/all/ee949902-1158-456e-af4d-b1fe6c42ac61@linux.ibm.com/
- v12: https://lore.kernel.org/all/20260903063240.268775-1-sshegde@linux.ibm.com/
- v11: https://lore.kernel.org/all/20260825103855.721013-1-sshegde@linux.ibm.com/
- v10: https://lore.kernel.org/all/20260812054033.95658-1-sshegde@linux.ibm.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到
