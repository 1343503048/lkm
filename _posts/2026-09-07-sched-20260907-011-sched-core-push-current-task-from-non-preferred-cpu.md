---
id: sched-20260907-011
date: '2026-09-07'
subject: 'sched/core: Push current task from non preferred CPU'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260903063240.268775-9-sshegde@linux.ibm.com>
lore_url: https://lore.kernel.org/all/7d88a3c4-a7e4-4814-9e29-84955b69a5b3@linux.ibm.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v12
generated_at: '2026-09-07'
authors:
- Shrikanth Hegde
maintainers_involved:
- Yury Norov
patch_series:
- version: v12
  msgid: <20260903063240.268775-9-sshegde@linux.ibm.com>
  date: '2026-09-03'
  summary: steal governor v12 第 08/13 片：sched_tick() 中若 !cpu_preferred(cpu)，用 stop_one_cpu_nowait()
    把当前任务推走；struct rq 新增 bool push_task_work_done 做去重。本日无新版本，作者就 09-05 Yury Norov
    的 4 条意见逐条回应：主张 select_fallback_rq() 与 rq_lock() 之间的窗口由 task_rq(p) == rq 兜住故安全；接受改名
    npc_push_work_pending；承认字段位置只在 powerpc(128B line) 上 pahole 过，给出两个对 64B/128B 都合适的候选（idle_balance
    后 6 字节空洞 / ttwu_local 后 4 字节空洞），倾向第一个；同意加 CONFIG_PREFERRED_CPU 保护。
  review_outcome: Yury Norov 4 条意见中 3 条被采纳、1 条由作者以既有兜底检查论证为安全；无第三方支持或反对意见；Peter Zijlstra
    / Ingo Molnar 仍未表态；截至本日无 v13。
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 缓存正文里没有 Peter Zijlstra / Ingo Molnar 对 v12 的表态，也没有 tip-bot 收树迹象，是否排队进 sched/core（目标
    7.4）仍定不下来
  - struct rq 字段位置未定（作者称要 probe 后再选），预计至少还有一轮 v13
  - 竞争窗口那条只有作者的定性论证，没有 no-op 比例的实测数据
  next_action: 看是否出现 v13（关注最终命名与字段落位、CONFIG_PREFERRED_CPU 保护是否加上）以及 Peter/Ingo 是否在
    sched/core 侧接话
contribution_opportunities:
- kind: review
  description: 在 arm64/x86（64B cacheline）上用 pahole 复核作者给出的两个 struct rq 候选位置是否真不增大结构体、不与热字段产生
    false sharing，并给出意见
- kind: testing
  description: 给 task_rq(p) != rq / !task_on_rq_queued / is_migration_disabled 三个
    bail-out 分支加统计，实测超配场景下 tick 推送退化为 no-op 的比例
- kind: review
  description: 确认最终命名（npc_push_work_pending 描述的是已排队状态，与 Yury 建议的意图导向命名 need_push_to_npc
    方向相反）以及 CONFIG_PREFERRED_CPU 保护后 config=n 时 struct rq 是否缩回去
- kind: discussion
  description: 就 cpuset 划分集合 / housekeeping_cpu() 与 cpu_preferred_mask 重叠时的收缩语义回帖，这块设计至今未收口
source_email_count: 1
related_articles:
- sched-20260905-005
- sched-20260903-002
- sched-20260904-012
tags:
- cfs
- affinity
- topology
- perf
title: 'sched/core: Push current task from non preferred CPU'
layout: article
---

## TL;DR

本文为增量更新，完整背景见 sched-20260905-005（steal governor v12 的第 08/13 片：tick 上用 stopper 把非偏好 CPU 上的当前任务推走）。本日只有一封邮件，但把 Yury Norov 09-05 对 08/13 提的 4 条意见**全部**给出了可执行答复：Shrikanth Hegde 论证 `select_fallback_rq()` 与后续 `rq_lock()` 之间的窗口是安全的（绝大多数情况根本不会拿 rq 锁，即使任务在拿锁前被负载均衡拉走，`task_rq(p) == rq` 会兜住并 bail out）；接受改名 `npc_push_work_pending`；承认 `struct rq` 新字段当初只在 powerpc（128B cacheline）上 pahole 过、那里正好是 64 字节空洞，但在 64B cacheline 上可能不是最优，并给出两个对两种 cacheline 都合适的候选位置；同时同意用 `CONFIG_PREFERRED_CPU` 包住该字段。截至本日仍是 v12，没有 v13——作者的原话是「I will pick one after little bit of probing.」

## 背景与问题

v12 的整体架构、动机（vCPU 超配下持锁/关中断段被 host 抢占的代价、`cpu_preferred_mask` 三条折叠路径、只推 FAIR 类当前任务等）与 08/13 的实现细节见 [[sched-20260905-005]]，此处只留一句定位：08/13 在 `sched_tick()` 开头判 `!cpu_preferred(cpu)`，把非偏好 CPU 上正在跑的任务用 `stop_one_cpu_nowait()` 排队推走，`struct rq` 为此新增一个 bool 字段做「已排队 stopper」的去重标记。

本日讨论全部围绕 Yury 09-05 那 4 条评审意见的落地，不涉及新增功能。

## 技术方案

作者本日给出的三处改动方向（均为对 v12 代码的收敛，尚未见 v13 实体）：

1. **竞争窗口的安全性论证**。Yury 的疑问是 stopper 里 `select_fallback_rq()` 可能自己拿 rq 锁、放锁之后到后续 `rq_lock()` 之间有与其他上下文竞争的窗口。作者的回答分两层：`Most of the time it won't grab the rq lock.`（只有走到需要改掩码的兜底分支，例如 fallback 到 possible CPUs 之类情形才会拿），更关键的是**兜底检查在后**——`Even if the task got pulled by load balancer before grabbing the lock, Below (task_rq(p) == rq) will catch that, and it bails out. So it is safe.` 也就是取 rq 锁之后先确认「任务还在我以为的那把 rq 上、还在 queued、且没被 migration-disable」，任何一条不成立就放弃，因此窗口内任务被负载均衡搬走只会导致推送变成 no-op，不会双重迁移或状态错乱。这与 v12 里既有的 `task_rq(p) == rq && task_on_rq_queued(p) && !is_migration_disabled(p)` 三条件正是同一道防线。
2. **字段命名与 config 保护**。接受 Yury 的意见（该字段是在调 stopper **之前**就置 true，所以 `push_task_work_done` 语义不准），倾向 `npc_push_work_pending`；并同意用 `CONFIG_PREFERRED_CPU` 包住该字段——作者解释当初为避免一堆 ifdef 才没加，但既然它只在该 config 下被使用，加保护「makes sense too」。
3. **`struct rq` 字段摆放**。这是本日最有信息量的部分。作者承认原始依据只是 powerpc（128B cacheline）上的一次 pahole：

   ```
   	int                        online;               /*  4524     4 */
   	struct list_head           cfs_tasks;            /*  4528    16 */

   	/* XXX 64 bytes hole, try to pack */
   ```

   放在 `cfs_tasks` 之后正好落进空洞。但他也承认：`Now, that i check 64 byte cachelines it may not be the optimal one.` 于是列出**两处对 64B 与 128B cacheline 都合适**的候选，并强调这两处「It won't increase the size or cause any existing fields to misalign」：
   - 候选 1：`balance_callback`(3608,8) / `nohz_idle_balance`(3616,1) / `idle_balance`(3617,1) 之后的 6 字节空洞，紧挨着 `misfit_task_load`(3624,8)；
   - 候选 2：`ttwu_count`(5276,4) / `ttwu_local`(5280,4) 之后的 4 字节空洞，紧挨着 `idle_state`(5288,8)。

   作者当前偏好候选 1（与 `nohz_idle_balance` / `idle_balance` / `misfit_task_load` 这批「均衡/推送意图」标志同处一段，语义上也更聚合），但最终决定留给实测：`I will pick one after little bit of probing. My preference so far is first one.`

## 版本演进与当前进展

- 09-03 v12（13 片）发出，作者请求 Peter/Ingo 排进 `sched/core`、目标窗口 **7.4**；v11→v12 的实质变化与更早的版本轨迹见 [[sched-20260905-005]]。
- 09-05 08:28 Yury Norov 对 08/13 提 4 条意见（竞争窗口、命名 + config 保护、字段摆放、pahole）。
- 09-07 11:23 Shrikanth Hegde 逐条回应（本日唯一邮件）：4 条中 3 条直接采纳（改名、加 `CONFIG_PREFERRED_CPU`、挪字段位置），1 条给出安全性论证（竞争窗口）。
- 截至本日**没有 v13**，本邮件中也没有出现新的 patchset 或维护者表态。字段位置仍是未定项（等作者的 probe 结果）。

## Maintainer 意见与讨论焦点

- **Yury Norov（NVIDIA）**：本日的焦点仍是他那 4 条。值得注意的是他的意见层次很清楚——1 条是潜在正确性问题（要求作者论证），3 条是工程整洁度（命名、config 保护、结构体布局 + pahole）。作者对正确性那条是「解释并主张安全」，对另外三条全部接受，这通常意味着下一版会带上这些改动而不产生新的争论。
- **Shrikanth Hegde（作者）**：应对方式是「能接受的全接受，安全论证靠既有兜底检查」。他的安全论证有一个隐含前提值得 reviewer 盯一下：`task_rq(p) == rq` 只能保证「任务不在我不知情情况下被搬走」，它依赖取到 rq 锁后读到的 `task_rq(p)` 与 `p->on_rq` 是稳定一致的视图（此时锁已持有）；而**推送退化为 no-op 的概率**本身没有量化——也就是说，如果这个窗口在实践中不罕见，特性收益会打折，但正确性不受影响。邮件中没有给出这方面的统计。
- **无人反驳，也无人加意见**：Peter Zijlstra、Ingo Molnar 在本线程（含本日）仍未对 v12 表态，因此「是否排队进 sched/core」依旧未定，与 [[sched-20260905-005]] 记录的判断一致。

## 合入评估

`likelihood=medium`（维持前作判断）。

正面：08/13 的评审意见已经全部闭环到「可执行改动」的程度，作者对 4 条无一拒绝，只剩字段位置这类收尾细节；机制保持通用（不做 arch gating）、驱动侧 `=m`、x86/s390/PowerPC 均已有实测（数据见前作）。

卡点：
1. **缺 Peter/Ingo 的表态**，也没有 tip-bot 收树迹象——12 轮迭代后作者请求排队，本日邮件里仍没有任何维护者接话。
2. 字段摆放「等 probe 后再定」本身就意味着还会有 v13；v13 之后理论上还要一轮 review。
3. 作者自己承认纯 CPU-time 负载会小幅回退，收益依赖 VM 侧 honor steal hint 的协作前提（前作已记录）。

## 效果评估

本日邮件是评审往返，不含任何新数据；08/13 单独也没有 benchmark（系列级数据见 [[sched-20260905-005]] 的 hackbench/schbench/pgbench/sysbench/Daytrader 表格）。本日唯一带「数字」的内容是 `struct rq` 的 pahole 偏移：字段挪到候选 1 时利用 `idle_balance` 之后的 6 字节空洞、挪到候选 2 时利用 `ttwu_local` 之后的 4 字节空洞，作者主张两者都不增加 `struct rq` 总大小、也不让现有字段错位——这是他给出的唯一可验证主张，且他人可以用 pahole 直接复算。

## 我可以参与的点

- **现在正缺的输入就是别的架构上的 pahole 证据**，这条对本用户几乎零成本：作者只在 powerpc（128B line）上确认过当前位置，并明说「换成 64B cacheline 可能不是最优」。在 arm64（64B line，含 Kunpeng 类机型）与 x86 上分别 `makepahole`/`pahole` 出 `struct rq`，看他的两个候选在自家 config（`CONFIG_CFS_BANDWIDTH`、`CONFIG_SCHED_ACPU`、RT 组等开关组合会显著改变 `struct rq` 布局）下是否真的既不掉进新空洞又不错开热字段，回帖就是实质贡献；尤其可以检查候选 2（`ttwu_count/ttwu_local` 之后）是否与 wakeup 路径热字段同 cacheline 而带来额外 false sharing——这恰好是作者主张「不会 misalign」之外更需要论证的点。
- **命名与 config 保护值得顺手确认**：`npc_push_work_pending` 描述的是「已排队 stopper」而非「需要推送」，与 Yury 建议的 `need_push_to_npc`（意图导向）方向相反，最终 v13 落在哪个名字上可以盯一下；另外加 `CONFIG_PREFERRED_CPU` 保护后，config=n 时 `struct rq` 是否真的缩回去也值得用 pahole 对比。
- **安全论证可以被验证而不是被接受**：如果想在 v13 前给作者一个数据点，可在 `task_rq(p) != rq` / `!task_on_rq_queued()` / `is_migration_disabled()` 三个 bail-out 分支各加一次统计（或 tracepoint），跑超配场景看 no-op 比例；若比例可观，说明 tick 推送与负载均衡在互相抢活，这既影响特性收益也影响 `sched_balance_rq()` 侧的掩码收敛策略。这是本线程里目前只有定性论断、最容易用一份实测推进的点。
- **与 cpuset/cgroup 的交叉语义仍未收口**（前作已提出、本日没有新进展）：`cpu_preferred_mask` 是 `cpu_active_mask` 的子集，而折叠决策由 `steal_governor` 驱动，那么与非偏好 CPU 重叠的 cpuset 划分、`housekeeping_cpu()`/`nohz_full` 组合该不该被越界收缩，仍是设计层面的空白；目标窗口是 7.4，还有时间回帖。
- 回合侧：目标 7.4 意味着主线最早在 7.4 出现，OLK-6.6 若想吃这个能力要准备 out-of-tree 维护，并先补齐前置 helper（`kcpustat_field_total()`、`cpumask_intersects_and()`）；本日字段位置未定，也顺带说明 `struct rq` 布局还会动，回合时不要按 v12 的偏移做任何硬编码假设。

## 参考链接

- 相关文章/系列：
  - [[sched-20260905-005]] 前作：v12 全架构、08/13 实现细节与 Yury 的 4 条意见原文。
  - [[sched-20260903-002]] steal governor v12 的偏好 CPU + vCPU 回退主体。
  - [[sched-20260904-012]] 系列 01/13 的 `kcpustat_field_total()` helper。
- 本日作者的逐条回应: https://lore.kernel.org/all/7d88a3c4-a7e4-4814-9e29-84955b69a5b3@linux.ibm.com/
- Yury Norov 的 4 条意见（09-05）: https://lore.kernel.org/all/aptiJP_8SWwZWju6@yury/
- v12 08/13 补丁本体: https://lore.kernel.org/all/20260903063240.268775-9-sshegde@linux.ibm.com/
- v12 cover letter: https://lore.kernel.org/all/20260903063240.268775-1-sshegde@linux.ibm.com/
- tip-bot commit: 未获取到（本线程尚未入 tip）
- stable backport: 未获取到
