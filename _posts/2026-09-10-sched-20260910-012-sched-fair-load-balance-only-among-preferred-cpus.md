---
id: sched-20260910-012
date: 2026-09-10
subject: 'sched/fair: Load balance only among preferred CPUs'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260909135617.871006-8-sshegde@linux.ibm.com>
lore_url: https://lore.kernel.org/all/20260909135617.871006-8-sshegde@linux.ibm.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v13
generated_at: '2026-09-11T00:50:00'
authors:
- Shrikanth Hegde
maintainers_involved:
- Yury Norov
patch_series:
- version: v12
  msgid: <20260903063240.268775-8-sshegde@linux.ibm.com>
  date: '2026-09-03'
  summary: 本补丁实现自 v12 起定型：sched_balance_rq 的 cpumask_and 由 cpu_active_mask 改为 cpu_preferred_mask，sched_balance_newidle
    提前返回条件改为 !cpu_preferred(this_cpu)；3 insertions / 5 deletions。
  review_outcome: 09-03 当日无 reviewer 回帖。
- version: v13
  msgid: <20260909135617.871006-8-sshegde@linux.ibm.com>
  date: '2026-09-09'
  summary: 本补丁内容未变（v12→v13 的四条 changelog 全部落在 08/13 的 npc_push_work_pending 命名、rq
    字段位置与 CONFIG_PREFERRED_CPU 守卫、select_fallback_rq 后的 rq lock 注释）。
  review_outcome: '09-10 01:19 Yury Norov 给出 Reviewed-by: Yury Norov <ynorov@nvidia.com>，无附加意见；fair
    类维护者（Vincent Guittot）仍未表态。'
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Peter Zijlstra / Ingo Molnar 未回应封面提出的「排入 sched/core 冲 7.4」请求
  - 改的是 sched_balance_rq / sched_balance_newidle 主干，但公平类维护者 Vincent Guittot 未评审
  - 补丁依赖系列 04/13 引入的 cpu_preferred_mask，无法脱离系列单独合入，节奏由系列整体决定
  next_action: 等 Peter 表态排队时点；提请 Vincent Guittot 评审本补丁的 span 收窄与 NEWIDLE 提前返回
contribution_opportunities:
- kind: review
  description: 复核 sched_balance_rq 把 span 收窄到 cpu_preferred_mask 后与 sd->span 层级遍历、nohz.next_balance
    更新、find_new_ilb() 升序/降序不匹配的交互，把结论带回线程并提请 Vincent Guittot 关注
- kind: testing
  description: 构造「所有 idle CPU 均为 non-preferred」的场景（preferred 收缩到 1 个繁忙核），实测作者刻意放弃的
    find_new_ilb() 优化是否真的只造成一次无效迁移
source_email_count: 1
related_articles:
- sched-20260909-010
- sched-20260903-002
- sched-20260902-014
tags:
- load_balance
- affinity
- nohz
- idle
title: 'sched/fair: Load balance only among preferred CPUs'
layout: article
---

## TL;DR
本文为增量更新，完整背景见 related_articles 中的 sched-20260909-010（steal_governor 系列 v13 整体分析）与 sched-20260903-002。09-10 的唯一进展是 Yury Norov 给本补丁（v13 07/13）打了 `Reviewed-by: Yury Norov <ynorov@nvidia.com>`——他是该系列最严格的评审者，此前连续三轮提出实质意见（v11 的 steal 分母、v12 的 `cpumask_intersects_and`、v13 的 `npc_push_work_pending` 命名与 rq 字段位置），如今在负载均衡这一核心补丁上转为认可。Peter Zijlstra / Ingo Molnar 对封面「排入 sched/core 冲 7.4」的请求仍未回应。

## 背景与问题
steal_governor 系列把 CPU 超配场景下的 vCPU 抢占代价（锁持有者被抢占、临界区、TLB/cache miss）转化为一个协作式退让机制：guest 侧按 steal time 动态收缩「preferred CPU」集合，把负载折叠到更少的 vCPU 上。折叠动作有三条路径——唤醒选核（06/13）、tick 里用 stopper 推送 current（08/13）、以及本补丁负责的负载均衡。

本补丁要解决的具体矛盾在提交说明里写得很直白：一个 CPU 被标记为 non-preferred 之后，任何被拉到它上面的负载都是无意义的，因为下一个 tick 就会把它推走（"any load pulled towards it is pointless since the task will be pushed out again in the next tick"）。也就是说，如果负载均衡仍按 `cpu_active_mask` 计算 domain span，它会与 08/13 的 push 机制互相打架：均衡把任务拉过来，tick 又把它推回去，形成迁移抖动并浪费 active balance 的开销。

## 技术方案
改动极小，`kernel/sched/fair.c` 只有 3 insertions / 5 deletions，但落点都在公平类负载均衡的主干上：

1. `sched_balance_rq()` 的候选 CPU 集合从 active 掩码换成 preferred 掩码：

```c
-	cpumask_and(cpus, sched_domain_span(sd), cpu_active_mask);
+	cpumask_and(cpus, sched_domain_span(sd), cpu_preferred_mask);
```

由于 `cpu_preferred_mask` 被严格维护为 `cpu_active_mask` 的子集，这一步同时排除了 offline/inactive CPU，语义上是收窄而非替换；附带效果是 active balance 不会再选中一个 non-preferred CPU 去拉负载（"this stops active balancing from happening on a non-preferred CPU pulling the load"）。

2. `sched_balance_newidle()` 的提前返回条件同步改为 preferred 判断：

```c
-	/*
-	 * Do not pull tasks towards !active CPUs...
-	 */
-	if (!cpu_active(this_cpu))
+	/* Do not pull tasks towards !preferred CPUs */
+	if (!cpu_preferred(this_cpu))
 		return 0;
```

设计取舍有三条被作者显式记录下来，都是「宁可不优化，也不增加复杂度」的取向：

- **亲和契约优先**：只绑定到 non-preferred CPU 的任务不再被负载均衡移动，继续留在原地跑（"They will continue to run where they were previously running before the CPUs were marked as non-preferred"）。这与系列的整体约束一致——绝不破坏用户/任务亲和。
- **NEWIDLE 提前 bail out，但普通 idle balance 放行**：作者特别说明 idle balancing 仍然允许走下去，因为它会自然更新 `nohz.next_balance`——即使所有 idle CPU 都是 non-preferred，也需要这条路径维持 nohz 的下次均衡时间戳。
- **刻意不给 `find_new_ilb()` 加 preferred 过滤**：steal_governor 驱动是按 CPU 编号**降序**摘除 preferred 核，而 `find_new_ilb()` 是**升序**找 idle CPU，所以常见场景下它找到的第一个 idle CPU 本来就是 preferred；当所有 idle CPU 都 non-preferred 时反正也只能选第一个。作者认为为这种罕见边界加复杂度没有必要（"Adding additional complexity to it for rare edge cases is not necessary"）。

## 版本演进与当前进展
- 当前版本 v13（2026-09-09 21:56，thread root `<20260909135617.871006-1-sshegde@linux.ibm.com>`，本补丁为 07/13）。
- v12→v13 的 changelog 四条全部落在 08/13 与 rq 字段布局上（`push_task_work_done` → `npc_push_work_pending`、挪到 `steal_*` 字段旁并加 `CONFIG_PREFERRED_CPU` 守卫、`select_fallback_rq` 之后 rq lock 获取的注释更新），**本补丁 07/13 在 v13 中未作改动**，即 Yury 此次 R-b 针对的是 v12 就已定型的实现。
- 09-09 v13 发出当天无人回帖；09-10 01:19 Yury Norov 在本补丁线程给出 `Reviewed-by`（全文仅一行，无附加意见）。同日 Yury 尚未对系列其余补丁（尤其是他在 09-09 提过 rq 字段放置意见的 08/13）追加表态。
- 系列整体状态：13 个补丁、23 files changed、804 insertions(+) / 19 deletions(-)；封面已明确请求 Peter/Ingo 排队进 `sched/core` 冲 7.4，并希望能在 tip 树上跑一轮完整测试周期。

## Maintainer 意见与讨论焦点
- **Yury Norov（NVIDIA）**：本补丁 R-b（09-10）。他是系列的主要批评来源，此次转为认可，意味着「负载均衡 span 收窄到 preferred 掩码」这一最具侵入性的设计点已有一位长期评审者背书。本补丁线程内**无其他争议、无未决问题**。
- **Vincent Guittot / Dietmar Eggemann**：公平类与 Arm 侧维护者，对本补丁（改的是 `sched_balance_rq` / `sched_balance_newidle` 主干）至今**未表态**。这是本补丁目前最明显的评审缺口——Yury 的身份更接近长期评审者而非 fair 类维护者。
- **Peter Zijlstra / Ingo Molnar**：封面直接点名请求排队，09-09 至 09-10 仍无回应。
- 作者已声明的系列级遗留争议（与本补丁相关的部分）：机制只对 FAIR 类生效，RT/DL 与 sched_ext 明确推迟；stopper 只推 `rq->curr` 不推该 rq 上全部排队任务——本补丁让均衡与 push 不再打架，但 push 侧覆盖不全的问题依旧存在。

## 合入评估
likelihood: medium（就本补丁而言：实现只有 3+/5-，已获 Yury R-b，无未决技术分歧；但补丁不能脱离系列单独合入——`cpu_preferred_mask` 由系列 04/13 引入，缺了它本补丁无法编译，因此实际节奏由系列整体决定）。

blocking_issues：Peter/Ingo 未对「排入 sched/core 冲 7.4」表态；fair 类维护者（Vincent）未评审本补丁；系列横跨 driver core / drivers/virt / s390 / procfs 仍缺对应维护者 ack（见 sched-20260909-010）。

next_action：等 Peter 对排队时点的回应；本补丁可主动抄送/提请 Vincent Guittot 评审 `sched_balance_rq` 的 span 收窄与 `sched_balance_newidle` 的提前返回，补上公平类维护者的认可。

## 效果评估
本日邮件无任何新数据（Yury 的回帖只有一行 R-b）。

本补丁自身的收益是定性的：消除均衡与 tick push 之间的迁移抖动。系列级量化数据见 sched-20260903-002 / sched-20260909-010：PowerPC 实测 hackbench 无 `-p` 在 10/20/40 groups 下 5.20→4.65（+10.58%）、11.39→7.09（+37.75%）、20.32→11.31（+44.34%），kernbench 231→199（+14%）；x86/s390 数据作者已标注为基于 **v2** 由 Ilya Leoshkevich 在 OSPM26 期间所跑，实现此后已大幅变更，**不适用于当前版本**。`schbench` 无提升、纯 CPU-time 负载可能小幅回归，均为作者自陈。

## 我可以参与的点
- 本补丁已获 R-b、实现极小，直接的代码评审空间有限；但**公平类维护者的缺位是真实缺口**：可针对 `sched_balance_rq` 把 span 收窄到 `cpu_preferred_mask` 后，与 `sd->span` / `sched_domain` 层级遍历、`nohz.next_balance` 更新、以及 `find_new_ilb()` 升序/降序不匹配这几个交互点做一次专门复核，把结论带到线程里提请 Vincent 关注（review）。
- 作者明确放弃的 `find_new_ilb()` 优化是一个可验证的边界：构造「所有 idle CPU 均为 non-preferred」的场景（steal_governor 收缩到只剩 1 个 preferred 核且该核繁忙），实测 ILB 选到 non-preferred CPU 后是否真的只产生一次无效迁移，把数据回帖（testing）。
- 其余系列级参与点（用当前 v13 重跑 x86/s390 三列对照、push 覆盖全部排队任务的后续 patch、NUMA 感知裁剪）见 sched-20260909-010，不重复。

## 参考链接
- 本补丁（v13 07/13，线程根）: https://lore.kernel.org/all/20260909135617.871006-8-sshegde@linux.ibm.com/
- Yury Norov 的 Reviewed-by（09-10 本日邮件）: https://lore.kernel.org/all/aqGVMR2m_NF76tv3@yury/
- v13 系列封面: https://lore.kernel.org/all/20260909135617.871006-1-sshegde@linux.ibm.com/
- 同日 push 机制补丁（08/13，与本补丁配套）: https://lore.kernel.org/all/20260909135617.871006-9-sshegde@linux.ibm.com/
- tip-bot / upstream commit: 未获取到（尚未合入）
