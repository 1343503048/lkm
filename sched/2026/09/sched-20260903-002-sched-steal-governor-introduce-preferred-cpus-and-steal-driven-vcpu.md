# sched, steal_governor: Introduce preferred CPUs and steal-driven vCPU backoff

## TL;DR

这不是「过载 CPU 偷空闲 CPU 的任务」，而是反向的协作式退让：在 CPU 超配的共享池（PowerPC SPLPAR、KVM 等）上，宿主抢占 vCPU 的代价远不止丢失的 CPU 时间（锁持有者被抢占、临界区、TLB/cache miss），所以让 guest 在 steal time 升高时**主动把负载折叠到更少的 vCPU 上**，降低宿主争用。Shrikanth Hegde 的 v12 分两层：调度器侧新增 preferred CPU 状态（`cpu_preferred_mask`），策略侧新增 `drivers/virt/steal_governor.c` 按 steal time 增减 preferred 核数。v12 于本日发出并已明确请求 Peter/Ingo 排队到 sched/core  targeting 7.4；本日无新回帖，v12 只按 v11 的复审意见做了 ARM64 与 Kconfig 层面的收敛。

## 背景与问题

大机 pCPU 密度上升后，企业负载普遍采用 CPU 超配：给 VM 配远多于物理核的 vCPU。多 VM 同时高负载时共享 pCPU 池饱和，hypervisor 为公平性必须抢占 vCPU；若被抢占时正持锁或关中断，全系统前进能力崩塌。传统缓解（向锁持有者 yield）覆盖不全，且还有 cache/TLB miss、vCPU 抢占本身与宿主调度开销等隐性成本。

现有手段的不足被明确列出：CPU 热插拔与 cpuset 隔离是重量级管理操作，需要重建拓扑并**破坏用户态 CPU 亲和**；显式任务亲和对用户几乎不可维护。因此需要内核内一个快速、协作式的退让机制，在不违反亲和契约的前提下随争用动态伸缩：争用高时折叠到少量 vCPU，争用消失后重新铺开。

## 技术方案

**Layer A — 调度器机制（preferred CPUs）**：新增 CPU 状态 preferred，表示该 vCPU 可安全使用且使用它不会加剧 pCPU 争用；通过 `cpu_preferred_mask` 暴露，严格保持为 `cpu_active_mask` 的子集。调度器把它当 hint 用三条路径折叠负载：

1. 唤醒：`is_cpu_allowed()` 判断目标 CPU 是否 preferred，否则 `select_fallback_rq()` 在亲和允许时选一个 preferred CPU（v12 patch 06/13）。
2. tick 推送：`sched_tick()` 中若当前 CPU 非 preferred，用 stopper 线程把运行中任务推到 preferred CPU（patch 08/13）。
3. 负载均衡：`sched_balance_rq` 把 domain span 限制在 `cpu_preferred_mask` 内，避免任务被拉向非 preferred CPU（patch 07/13）。

设计约束是**绝不破坏用户/任务亲和**：独占绑定到非 preferred CPU 的任务原地不动。可观测性由 patch 09/13（非 preferred CPU 引发的迁移统计）与 sysfs `preferred` 文件提供；文档为 `Documentation/scheduler/sched-paravirt.rst` 与 `Documentation/driver-api/steal-governor.rst`。

**Layer B — 策略引擎 `steal_governor`**（`CONFIG_STEAL_GOVERNOR=m`）：核心调度器不应内置虚拟化策略，故周期采样全系统 steal time；超过 high_threshold（默认 5%）就把 preferred 减 1 核，低于 low_threshold（默认 2%）就加 1 核，形成阶梯式自维护收缩/扩张，且**无需任何跨 VM 通信**。约束为至少保留 1 个 preferred 核、preferred ⊆ active；建议 `interval_ms` 取 500~5000。

辅助机制：v12 另引入 `cpumask_intersects_and` 以简化 ARM64 32 位任务 `p->cpus_ptr` 含架构上不可用 CPU 的情况；`kcpustat_field_total` helper 供 steal 比例计算使用。

## 版本演进与当前进展

- 系列自 RFC 起已迭代 12 版，从 arch 专用 RFC 收敛为「通用调度器机制 + 可插拔虚拟化驱动」；v11 为 12 patch，v12 扩到 13 patch。
- v11 → v12（本日）：简化 ARM64 32 位任务分支（采纳 Dietmar Eggemann、Vincent Guittot）；为之上移引入 `cpumask_intersects_and`（采纳 Yury Norov）；**暂不做任何 arch 级 Kconfig gating**，保持对所有支持 paravirt + steal time 记账的 arch 通用（采纳 Vincent Guittot）。
- v10 → v11 的要点仍在生效：steal 比例分母改用 active 而非 possible CPU 以免阈值被稀释（Yury Norov、Ionut Nechita）、加 XEN dom0 blocking 检查、多架构框架推迟到合入后再设计、并修掉 sashiko 报的 arm64 32 位任务潜在崩溃、`__migrate_task` abort 引入的亲和竞态等问题。
- 基线：`tip/sched/core` 的 `ef9293b3b797`（"sched: dynamic: Fix preemption model strings"）。
- 作者在封面明确判断"the series has now converged and is ready for merge consideration"，并请求以 7.4 为目标排队。
- 本日 09-03 缓存内只有作者自己发的 cover 与 6 个 patch，**无 reviewer 回帖**。

## Maintainer 意见与讨论焦点

本日的实质进展是「吸收 v11 意见后的定稿」，封面 changelog 直接点名了三位维护者/评审者的意见落点：

- **Vincent Guittot（Linaro）**：两点被采纳——去掉 arch 特定的 Kconfig gating（"Keep the feature without any arch specific kconfig gating for now ... If a need arises, it can be brought in"），以及 ARM64 32 位任务 `p->cpus_ptr` 含架构上不可能出现的 CPU 这一简化。
- **Dietmar Eggemann（Arm）**：与上条同源的平台侧正确性意见，v12 一并吸收。
- **Yury Norov**：系列最强的批评者（封面致谢其"rigorous reviews"），`cpumask_intersects_and`、`kcpustat_field_total`、steal 分母改用 active CPU、代码全部收拢到 `drivers/virt/steal_governor.c`、`CONFIG_PREFERRED_CPU` 与 sysfs 可见性的耦合等多处均出自他。
- 待表态方：**Peter Zijlstra / Ingo Molnar**。封面直接点名询问是否可排队进 `sched/core`  targeting 7.4，并希望该特性在 tip 树上获得一轮完整测试周期。09-03 尚无回帖、无 `Acked-by`。
- 已声明的遗留争议点：仅支持 FAIR 类（RT 与 sched_ext 明确推迟）；stopper 只推 current 任务，不迁移该 rq 上全部排队任务；steal_governor 按 CPU 编号去掉最后一个 active 核，**尚不做 NUMA 感知的核裁剪**；纯 CPU-time 负载可能小幅回归。

## 合入评估

likelihood: **possible**。

依据：v12 已把 v8 之后所有评审意见逐条落到 changelog 里并点名提出者，作者自认收敛且主动请求排队；实现刻意保持简单（作者原话 "deliberately kept simple"），基线就是当日 `tip/sched/core`；有跨三种架构的真实收益数据；测试矩阵覆盖热插拔、housekeeping/`nohz_full` 组合、用户亲和、`taskset -cp` 迁移、极端负载（480 CPU 上 4800 个 stress-ng 线程）。

卡点：一是 Peter Zijlstra/Ingo Molnar 至今（09-03）未对该系列表态，13 个 patch 里调度器核心只占 3 个，真正的争议面（tick 里起 stopper 推送、把 sched_domain span 收窄到 preferred 掩码）还没得到公平类维护者的正式认可；二是仅 FAIR 类生效 + 只推 current 任务，会让「preferred CPU 掩码」成为一个语义不完整的通用机制，容易被要求先补齐 RT/DL 或先明确边界；三是协作前提是所有 VM 都打该补丁，属策略而非机制问题；四是作者自承纯 CPU-time 负载会小幅回归，`schbench` 数据也确实没有提升。

## 效果评估

数据充分（PowerPC 为 v12 实测，x86/s390 为 Ilya Leoshkevich 在 OSPM26 期间基于 **v2** 的 KVM 数据，实现已变更，只能作方向性参考）：

PowerPC（VM1 60VP/30EC + VM2 30VP/20EC，共享池 50 核 SMT8，两 VM 同负载，取总吞吐）：
- hackbench 无 `-p`：10/20/40 groups 分别 5.20→4.65（+10.58%）、11.39→7.09（+37.75%）、20.32→11.31（+44.34%）。
- kernbench（`-j nr_cpus` 耗时）：231→199，+14%。
- Daytrader（DB2 交易代理）：30% 负载 1x→1.53x，60% 负载 1x→1.41x。
- schbench：作者自评"no improvements or regressions"（+1.71%~+2.11%）。
- 无 steal time 场景（dedicated LPAR 或单 VM）吞吐持平，说明机制本身开销可忽略；`STEAL_GOVERNOR=n` 开销亦可忽略。

x86（cascade-lake，16C/32T，ΔRPS）最好为 hackbench 8VM×16CPU **+90.73%±9.97%**，pgbench 16VM×4CPU +31.77%；尾部为 sysbench 16VM×4CPU -3.22%、pgbench 4VM×32CPU -3.21%。
s390（z16，8C/16T SMT2）pgbench 2VM×8CPU +73.50%±35.91%（标准差极大）、pgbench 16VM×4CPU +61.30%；尾部 hackbench 2VM×24CPU -4.99%。

结论与作者一致：真实业务型负载收益显著、纯 CPU-time 负载小幅回归、无争用时近零开销。

## 我可以参与的点

1. **回合价值最高的一点**：OLK-6.6 若要跟进，Layer A 的三处入口（`is_cpu_allowed()`/`select_fallback_rq()`、`sched_tick()` 里的 stopper 推送、`sched_balance_rq` 的 span 收窄）与 `cpu_preferred_mask` 与 `cpu_active_mask` 的子集不变式，是全部依赖面；v12 去掉 arch Kconfig gating 后，回合时需要自行加回平台开关，这一点可以直接回帖提出。
2. cpuset/cgroup 视角的空白点：目前设计与 `cpusets` 的交互只写了「不破坏用户亲和」，但 preferred 掩码与 cpuset 独占分区、`sched_setaffinity` 竞争时的行为在封面里没有量化说明。可在超配 VM 上用 `cpuset` 绑核 + `steal_governor` 组合跑一轮，把冲突场景的表现贴回线程。
3. 可帮跑的验证：v12 的 x86 数据基于 v2，作者明确说"the implementation has changed and some overhead has been removed since then"。在 x86 KVM 上用 v12 复现一组 hackbench/pgbench/sysbench 的 ΔRPS，是目前线程里最缺的一块证据。
4. 代码点复核：patch 09/13 的迁移统计是否覆盖 `select_fallback_rq` 与 ALB 两条路径；`sched_tick()` 中取 rq 锁后队列 stopper 的中断关闭窗口（v11 由 sashiko 提出）在 v12 是否仍然成立。

## 参考链接

- v12 封面：https://lore.kernel.org/all/20260903063240.268775-1-sshegde@linux.ibm.com/
  - patch 06/13（is_cpu_allowed 使用 preferred CPU）：https://lore.kernel.org/all/20260903063240.268775-7-sshegde@linux.ibm.com/
  - patch 07/13（仅在 preferred CPU 间负载均衡）：https://lore.kernel.org/all/20260903063240.268775-8-sshegde@linux.ibm.com/
  - patch 08/13（把 current 任务从非 preferred CPU 推出）：https://lore.kernel.org/all/20260903063240.268775-9-sshegde@linux.ibm.com/
  - patch 09/13（非 preferred CPU 引发的迁移统计）：https://lore.kernel.org/all/20260903063240.268775-10-sshegde@linux.ibm.com/
- 上一版对照：v11 封面 https://lore.kernel.org/all/20260825103855.721013-1-sshegde@linux.ibm.com/
- 相关文章/系列：
  - [[sched-20260902-014]] steal_governor v11 preferred（讨论版）。
- 相关代码：
  - `kernel/sched/core.c` `is_cpu_allowed()` / `sched_tick()` 推送；`kernel/sched/fair.c` `sched_balance_rq`
  - `drivers/virt/steal_governor.c`；`Documentation/scheduler/sched-paravirt.rst`

---
id: sched-20260903-002
date: '2026-09-03'
subject: 'sched, steal_governor: Introduce preferred CPUs and steal-driven vCPU backoff'
subsystem: sched
type: feature
status: under_review
severity: medium
thread_root_msgid: '<20260903063240.268775-1-sshegde@linux.ibm.com>'
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
- Dietmar Eggemann
- Vincent Guittot
patch_series:
- "sched/cputime: Add kcpustat_field_total helper"
- "cpumask: Introduce cpumask_intersects_and"
- "sched/docs: Document cpu_preferred_mask and Preferred CPU concept"
- "cpumask: Introduce cpu_preferred_mask"
- "sysfs: Add preferred CPU file"
- "sched/core: Try to use a preferred CPU in is_cpu_allowed"
- "sched/fair: Load balance only among preferred CPUs"
- "sched/core: Push current task from non preferred CPU"
- "sched/debug: Add migration stats due to non preferred CPUs"
- "virt: Introduce steal governor driver"
- "virt/steal_governor: Add control knobs for handling steal values"
- "virt/steal_governor: Implement steal_governor policy loop"
- "virt/steal_governor: Enable the driver"
merge_assessment:
  likelihood: possible
  blocking_issues:
  - "Peter Zijlstra / Ingo Molnar 截至 09-03 未表态，13 patch 中无 Acked-by"
  - "仅 FAIR 类生效且 stopper 只推 current 任务，机制语义不完整"
  - "协作前提是所有 VM 都打补丁；纯 CPU-time 负载作者自认会小幅回归"
  - "x86/s390 收益数据仍基于 v2，v12 未复测"
  next_action: "等 sched/core 维护者回应是否排队进 7.4；社区侧补 v12 的 x86/s390 复测数据"
contribution_opportunities:
- "在 x86 KVM 上用 v12 复现 hackbench/pgbench/sysbench 的 ΔRPS（现有数据基于 v2）"
- "量化 preferred CPU 掩码与 cpuset 独占分区/taskset 绑核冲突时的行为"
- "复核 patch 09/13 迁移统计是否覆盖 select_fallback_rq 与 ALB 两条路径"
- "评估 OLK-6.6 回合面：cpu_preferred_mask 子集不变式与三处调度器入口"
source_email_count: 7
related_articles:
- sched-20260902-014
tags:
- sched/core
- sched/fair
- sched/cache
- topology
---
