---
id: sched-20260905-005
date: '2026-09-05'
subject: 'sched/core: Push current task from non preferred CPU'
subsystem: sched
type: discussion
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
- Tim Chen
- Chen Yu
patch_series:
- 'sched/cputime: Add kcpustat_field_total helper'
- 'cpumask: Introduce cpumask_intersects_and'
- 'sched/docs: Document cpu_preferred_mask and Preferred CPU concept'
- 'cpumask: Introduce cpu_preferred_mask'
- 'sysfs: Add preferred CPU file'
- 'sched/core: Try to use a preferred CPU in is_cpu_allowed'
- 'sched/fair: Load balance only among preferred CPUs'
- 'sched/core: Push current task from non preferred CPU'
- 'sched/debug: Add migration stats due to non preferred CPUs'
- 'virt: Introduce steal governor driver'
- 'virt/steal_governor: Add control knobs for handling steal values'
- 'virt/steal_governor: Implement steal_governor policy loop'
- 'virt/steal_governor: Enable the driver'
merge_assessment:
  likelihood: possible
  blocking_issues:
  - 缓存正文里没有 Peter Zijlstra / Ingo Molnar 对 v12 的表态，也没有 tip-bot 收树迹象
  - 08/13 的 4 条意见要到 09-07 才有回应，字段位置与命名仍未定，预计需要 v13
  - 作者自承纯 CPU-time 负载可能小幅回退
  - 只支持 FAIR 类，且不做 NUMA 感知的核裁剪
  next_action: 看是否出现 v13 及 Peter/Ingo 是否排队进 sched/core（目标 7.4）
contribution_opportunities:
- 在 arm64/x86 KVM 超配环境跑 hackbench/schbench/pgbench 并给 tip 周期补测试反馈
- 复核 push_task_work_done 取锁顺序与 stopper 竞争，以及 PREEMPT_RT 下的安全性
- 就 cpuset/housekeeping 集合与 cpu_preferred_mask 重叠的语义回帖
- 回合前确认 kcpustat_field_total / cpumask_intersects_and 等前置 helper
source_email_count: 2
related_articles:
- sched-20260904-012
- sched-20260903-002
tags:
- sched/core
- sched/fair
- sched/cache
- topology
title: 'sched/core: Push current task from non preferred CPU'
layout: article
---

## TL;DR

Steal governor v12（13 补丁，Shrikanth Hegde / IBM）把「非偏好 CPU 上主动用 stopper 把当前任务推走」作为 tick 侧的执行手段，作者明确请求 Peter/Ingo 把它排进 `sched/core`、目标合并窗口 **7.4**。本日两件事：Yury Norov 对 08/13 提了 4 条具体意见（锁竞争窗口、per-CPU 变量命名、`struct rq` 字段摆放、pahole），Tim Chen 则在同一天贴出**另一条独立修复** `sched/cache: Keep nr_pref_llc_running in the runnable domain` 的 v3——那是 cache-aware 均衡的误迁移 bug，不属于本系列。

## 背景与问题

高密度 pCPU 服务器上普遍做 vCPU 超配，hypervisor 为公平会抢占 vCPU；如果 vCPU 在持锁或关中断段被抢占，代价远超损失的那段 CPU 时间（锁持有者抢占、TLB/cache 失效）。Guest 侧的缓解办法是在竞争严重时把工作「折叠」到更少 vCPU 上，但现有手段各有缺陷：CPU 热插拔 / isolated cpusets 是重量级管理操作、需要重建拓扑且**破坏用户态亲和性**，显式任务亲和性几乎不可维护。

v12 的架构分两层：A 层是通用调度器机制 `cpu_preferred_mask`（严格保持为 `cpu_active_mask` 的子集），通过三条路径折叠负载——wakeup 时 `is_cpu_allowed()` 检查偏好、tick 时把非偏好 CPU 上的运行任务推走、`sched_balance_rq()` 把均衡域限制在偏好掩码内；B 层是策略引擎 `drivers/virt/steal_governor`（`CONFIG_STEAL_GOVERNOR=m`），按 steal time 高低阈值（默认高 5% / 低 2%，`interval_ms` 建议 500–5000）每次增减一个核。设计约束是**绝不违反用户/任务亲和性**：只被绑到非偏好 CPU 的任务就留在那里。

08/13 负责的是 tick 推送这一条。

## 技术方案

- `sched_tick()` 开头加 `if (!cpu_preferred(cpu)) sched_push_current_non_preferred_cpu(rq);`。
- 推送函数在 `scoped_guard(rq_lock, rq)` 内做三重检查：`task_can_sched_on_preferred()`（显式亲和性只允许非偏好 CPU 时直接放弃）、`rq->push_task_work_done`（已有 stopper 就不重复排队）、`is_migration_disabled()`；然后把 `push_task_work_done = true`、`get_task_struct()`，用 per-CPU `struct cpu_stop_work npc_push_task_work` 调 `stop_one_cpu_nowait()`。
- stopper `sched_non_preferred_cpu_push_stop()`：先重新判 `cpu_preferred(rq->cpu)`（已变偏好就清标志退出）；取 `p->pi_lock` 后**在拿 rq 锁之前**调 `select_fallback_rq(rq->cpu, p)`（注释明确「This could take rq lock. So call it before rq lock is taken」），再 `rq_lock()`、清 `push_task_work_done`、`update_rq_clock()`、`context_unsafe_alias(rq)`，最后 `task_rq(p) == rq && task_on_rq_queued(p) && !is_migration_disabled(p)` 才 `__migrate_task()`。
- 有意与 `__balance_push_cpu_stop()` / `push_cpu_stop` 保持分离，理由是 `CONFIG_PREFERRED_CPU` 下实现更干净；仅支持 FAIR 类；只推当前运行任务，「把 rq 上全部排队任务搬走」列为后续优化。
- `struct rq` 新增 `bool push_task_work_done`，作者当前放在 `cfs_tasks` 与 `avg_rt` 之间。

## 版本演进与当前进展

- 09-03 发出 v12（v11→v12 只有两项实质变化：按 Dietmar Eggemann / Vincent Guittot 的意见简化 arm64 32-bit 任务下 `p->cpus_ptr` 含架构上不可能 CPU 的情况，并为此引入 `cpumask_intersects_and()`（Yury Norov）；同时按 Vincent 的意见暂不做 arch kconfig gating）。
- 更早的版本轨迹：v10→v11 把 steal ratio 分母从 possible 改为 active CPU 以避免阈值被稀释（Yury Norov、Ionut Nechita）、加 XEN dom0 阻塞检查、把多架构框架推迟到合并后、并按 sashiko 的自查修了 arm64 32-bit 可能崩溃、`__migrate_task` 中断路径竞争、rq 锁小窗口关中断、仅 migration enabled 时排 stopper 等问题。v8→v9 大改布局，把驱动收敛回 `drivers/virt/steal_governor.c`。v7→v8 才改名 STEAL_GOVERNOR（原 STEAL_MONITOR）。
- 09-05 Yury Norov 对 08/13 提 4 条意见；09-07 Shrikanth 逐条回应（见下节）。截至 09-07 未见 v13。
- v12 的 rebase 基线写得很明确：`tip/sched/core at commit 'ef9293b3b797 ("sched: dynamic: Fix preemption model strings")'`（即当天已入 tip 的 `ef9293b3b797`）。
- 作者自陈「系列已收敛、可按合入考虑」，并主动希望「在 tip 树里获得一轮好的测试周期」；合并后的计划是 arch 专属接口设计与测试框架。

## Maintainer 意见与讨论焦点

- **Yury Norov（NVIDIA，09-05，对 08/13）** 四条：
  1. `select_fallback_rq()` 若拿锁，则释放锁到后续 `rq_lock()` 之间存在与其他进程竞争的窗口——「Or I misunderstand it?」；
  2. `push_task_work_done` 应由 `CONFIG_PREFERRED_CPU` 保护，且**命名不正确**：变量在调用 stopper 之前就被置 true，建议 `need_push_to_npc` 之类；
  3. 字段为什么放在 `cfs_tasks` 与 `avg_rt` 之间，若无特殊原因建议挪到 `CONFIG_PARAVIRT` 保护字段旁边；
  4. 「What about pahole?」——即 `struct rq` 尺寸/空洞影响。
- **Shrikanth Hegde（09-07）逐条接受或解释**：竞争问题他认为大部分情况根本不会拿到 rq 锁，且即便任务在拿锁前被负载均衡器拉走，`task_rq(p) == rq` 判断会兜住并 bail out，「So it is safe」；命名接受，倾向 `npc_push_work_pending`；pahole 方面他在 powerpc（128 字节 cache line）上确认过 `cfs_tasks` 之后本来就是 64 字节空洞，但换成 64 字节 line 后可能不是最优，列出两个候选打包位置（`balance_callback/nohz_idle_balance/idle_balance` 后的 6 字节空洞，以及 `ttwu_count/ttwu_local` 后的 4 字节空洞），倾向第一个；并同意用 `CONFIG_PREFERRED_CPU` 包住该字段（原先为免 ifdef 才没加）。
- **同日另一条独立线程（不属于 v12）**：`nr_pref_llc_running` 应与哪些任务比较。这条线由 Tim Chen 09-02 提出 v2 并点名「Chen Yu 和 Xusheng，看着没问题请加 reviewed-by」；Chen Yu 09-03 建议把四处相似逻辑合成一个带 delta 的 helper；Tim Chen 09-05 采纳为 v3——引入成员谓词 `task_pref_llc_runnable()`（`p->pref_llc_queued && !p->se.sched_delayed`）与 `pref_llc_running_inc()/dec()` 包装，删掉 `account_llc_delayed()` 与 `account_llc_requeue_delayed()`，并强调两处易错点：`set_delayed()` 里的 dec **必须**排在 `se->sched_delayed = 1` 之前、以及 `account_llc_dequeue()` 要跳过仍 delayed 的任务以免二次递减。该补丁带 `Reported-by: Zhan Xusheng`、`Suggested-by: Chen Yu`、`Closes:` 指向 `20260827135000.735138-1-zhanxusheng@xiaomi.com`，基于 v7.3-rc1。
- 该 bug 的实际后果值得单独记：`alb_break_llc()` 用 `nr_pref_llc_running == cfs.h_nr_runnable` 判断是否打破 LLC 偏好，但前者跟「queued」语义、后者跟「runnable」语义；在 DELAY_DEQUEUE 下一个偏好任务去睡眠就会让等式破坏、`alb_break_llc()` 返回 false，而 active balance 唯一查的就是这个 LLC 检查（stopper 跑起来后 `LBF_ACTIVE_LB` 会跳过 `can_migrate_task()` 的逐任务判断），于是可能把任务从它偏好的 LLC 上拉走。`nr_llc_running` 与 `sd->llc_counts` 保持 queued 语义不动。

## 合入评估

**likelihood: possible。**

正面依据：12 轮迭代后作者直接请求 Peter/Ingo 排队进 `sched/core` 并点名目标窗口 7.4；机制保持通用（所有支持 paravirt + steal time 统计的架构都能用，不做 arch gating）；驱动刻意放 `drivers/virt/` 且 `=m`，`STEAL_GOVERNOR=n` 时开销可忽略；PowerPC/s390/x86 都有实测；Yury Norov 被作者致谢为「rigorous reviews that greatly improved the series」，08/13 的 4 条意见在 09-07 已全部得到可执行的回应（改名、加 config 保护、换字段位置、给出 pahole 证据）。

卡点：
1. **这批缓存正文里没有 Peter Zijlstra 或 Ingo Molnar 对 v12 的任何表态**，也没有 tip-bot 收树迹象——是否排队仍完全未定。
2. 08/13 的 4 条意见虽有答复，但答复本身还带着未定项（「I will pick one after little bit of probing」），意味着至少还要一轮 v13。
3. 纯 CPU-time 负载作者自己承认会小幅回退（cover 明确写「It may regress slightly for pure CPU-time workloads」），新机制默认关闭，收益依赖所有 VM 都 honor steal hint 的协作前提。
4. 已知限制：只支持 FAIR 类（RT/dl/sched_ext 推迟）、只推当前任务、steal_governor 按 CPU 编号剔核而不做 NUMA 感知的拼接——最后一条与同日 Yury 自己的 fallback NUMA-aware 补丁是同一区域。

## 效果评估

有完整数据（作者自测 PowerPC + Ilya Leoshkevich 在 OSPM26 期间的 x86/s390 KVM 数据，注意后者基于 v2，实现此后已变且去掉了一些开销）：

- PowerPC SPLPAR（VM1 60VP/30EC + VM2 30VP/20EC，共享池 50 核 SMT8，默认 1000ms/低 200/高 500）：hackbench 20 groups 11.39 → 7.09（**+37.75%**）、40 groups 20.32 → 11.31（**+44.34%**）、10 groups +10.58%；`-p` 组 +4.19%~+13.08%（40 groups `-p` 打开时 -8.30%）；kernbench 耗时 231 → 199（+14%）；Daytrader（db2 交易代理负载）Load@30% 1x → **1.53x**、Load@60% → **1.41x**；schbench 三档在 +0.18%~+5.90% 间波动，作者自评「effectively means no improvement or regression」。无 steal time 场景（dedicated LPAR 或只跑 VM2）吞吐与开关无关，即自身开销极小。
- x86（cascade-lake 16C/32T）：最好 hackbench 8VM×16CPU **+90.73% ± 9.97%**、4VM×24 +52.67%、pgbench 16VM×4CPU +31.77%；最差 sysbench 16×4 -3.22%、pgbench 4×32 -3.21%。
- s390（z16 8C/16T SMT-2）：pgbench 2VM×8 **+73.50% ± 35.91%**（方差大）、pgbench 16×4 +61.30%、hackbench 16×4 +54.11%；最差 hackbench 2×24 -4.99%、sysbench 12×4 -2.91%。
- 鲁棒性验证覆盖 CPU 热插拔、`nohz_full` 各种 housekeeping 组合、taskset 显式钉非偏好 CPU、affinity move、4800 个 stress-ng 线程压在 480 CPU 系统上仍能折叠到偏好 CPU。

## 我可以参与的点

- 现在正是「tip 树测试周期」的空窗：作者明说希望这个特性在 tip 里被充分测试，任何非 PowerPC 平台（尤其 arm64 服务器 + KVM 超配）的实测回帖都有增量价值。可跑的：hackbench（含 `-p`）、schbench、pgbench/sysbench 作为「纯 CPU 时间可能回退」的反例验证，以及 `CONFIG_STEAL_GOVERNOR=n` 的开销基线。
- 可直接复核的代码点：`push_task_work_done` 的语义（作者同意改名 `npc_push_work_pending`，但它覆盖的是「已排队 stopper」而非「需要推送」，命名与 Yury 建议方向相反，值得看一眼最终 v13）；stopper 里 `select_fallback_rq()` 与 `p->pi_lock` / `rq_lock` 的取锁顺序在 PREEMPT_RT 下是否安全；以及 `context_unsafe_alias(rq)` 的必要性。
- 与 cpuset/cgroup 主线的交叉点最值得回帖：`cpu_preferred_mask` 被定义为 `cpu_active_mask` 的子集，且机制刻意不破用户亲和性，那么 **cpuset 划分的 CPU 集合与非偏好 CPU 重叠时策略引擎该不该越界收缩**、以及 `housekeeping_cpu()` 与折叠交互（cover 只说验证过 nohz_full 组合）都是设计层面尚未收口的地方。
- 回合视角：`CONFIG_PREFERRED_CPU` + `CONFIG_STEAL_GOVERNOR` 对虚拟化管理面很有吸引力，但它依赖 steal time 统计、`cpumask_intersects_and()`、`kcpustat_field_total()` 等前置改动（v12 01/13、02/13），OLK-6.6 回合要先补这些 helper；且 `nr_pref_llc_running` 那条 cache-aware 误迁移 bug 与推送逻辑无关，但同期 tip/sched/core 的 cache-aware 改动本身也在这个 rebase 基线上，回合时要一起看。

## 参考链接

- 相关文章/系列：
  - [[sched-20260904-012]] steal_governor v12 kcpustat_field_total helper（01/13）。
  - [[sched-20260903-002]] steal_governor v12 偏好 CPU + vCPU 回退。
- v12 cover letter：https://lore.kernel.org/all/20260903063240.268775-1-sshegde@linux.ibm.com/
- v12 08/13 补丁本体：https://lore.kernel.org/all/20260903063240.268775-9-sshegde@linux.ibm.com/
- Yury Norov 的 4 条意见：https://lore.kernel.org/all/aptiJP_8SWwZWju6@yury/
- Shrikanth 09-07 的逐条回应：https://lore.kernel.org/all/7d88a3c4-a7e4-4814-9e29-84955b69a5b3@linux.ibm.com/
- `nr_pref_llc_running` 讨论线（独立于 v12）：v3 https://lore.kernel.org/all/2b0a35122ee615c6fa51076e5d79330e633755ac.camel@linux.intel.com/ 、v2 https://lore.kernel.org/all/06ed8af87506f858176a81a4c29acf92d24b6dc7.camel@linux.intel.com/ 、Chen Yu 的 helper 建议 https://lore.kernel.org/all/apmQaelH5Y7czrOM@fengwei-dev/
- 相关代码：
  - `kernel/sched/core.c` `sched_tick()` / `sched_push_current_non_preferred_cpu()` / `sched_non_preferred_cpu_push_stop()` / `select_fallback_rq()`
  - `kernel/sched/fair.c` `nr_pref_llc_running` / `alb_break_llc()` / `set_delayed()` / `clear_delayed()`
  - `drivers/virt/steal_governor.c`、`Documentation/scheduler/sched-paravirt.rst`
