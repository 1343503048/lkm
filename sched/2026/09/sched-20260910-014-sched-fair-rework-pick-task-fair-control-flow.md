# sched/fair: Rework pick_task_fair() control flow

## TL;DR
Yury Norov 的单补丁清理：把 `pick_task_fair()` 里「从 rq 上挑任务」的那段抽成静态 helper `pick_task_fair_rq()`，并用 `while` / `do-while` 取代 `again:` / `idle:` 两个 goto 标签。自陈 "No functional changes intended"，GCC 15.2.0 + `x86_64_defconfig` 省 96 字节，加上 `CONFIG_SCHED_CORE` + `CONFIG_CFS_BANDWIDTH` 省 124 字节。09-10 缓存内**无人回帖**。改的是调度器最热的挑选路径，值得跟一眼；我对照 diff 逐条核过控制流，三条返回路径与原实现等价，未发现语义漂移。

## 背景与问题
`pick_task_fair()` 是公平类向 `__pick_next_task()` / core scheduling 交出候选任务的入口。改动前的形态（补丁上下文所示）是典型的 goto 循环：

```c
again:
	if (!cfs_rq->h_nr_queued)
		goto idle;

	/* Might not have done put_prev_entity() */
	if (cfs_rq->curr && cfs_rq->curr->on_rq)
		update_curr_eevdf(cfs_rq);

	se = pick_next_entity(rq, true);
	if (!se)
		goto again;

	p = task_of(se);
	return p;

idle:
	if (sched_core_enabled(rq))
		return NULL;

	new_tasks = sched_balance_newidle(rq, rf);
	if (new_tasks < 0)
		return RETRY_TASK;
	if (new_tasks > 0)
		goto again;
	return NULL;
```

痛点不是可读性口号，而是两个具体后果：一是 `again` 同时被「挑不到 entity」和「newidle 拉到了任务」两处回跳，一个标签承担两种语义，读者必须在脑子里维护「回到 again 后 `h_nr_queued` 会被重新检查」这个隐含前提；二是带后向 goto 的控制流会让编译器在该函数里保留更多活跃状态，`idle:` 段的入口条件被两条路径共享，难以单独优化——这也是为什么重构后能实测省出上百字节。

## 技术方案
拆成两层，边界正好落在「是否可能需要放开 rq lock」这条线上：

**内层 `pick_task_fair_rq()`（新增，static，不接收 `rf`）**——纯粹在当前 rq 上尝试挑一个任务，不涉及任何可能睡眠/解锁的操作：

```c
static struct task_struct *pick_task_fair_rq(struct rq *rq)
{
	struct cfs_rq *cfs_rq = &rq->cfs;
	struct sched_entity *se;

	while (cfs_rq->h_nr_queued) {
		/* Might not have done put_prev_entity() */
		if (cfs_rq->curr && cfs_rq->curr->on_rq)
			update_curr_eevdf(cfs_rq);

		se = pick_next_entity(rq, true);
		if (se)
			return task_of(se);
	}

	return NULL;
}
```

`goto again` 的回跳被写成 `while (cfs_rq->h_nr_queued)` 的循环条件——原来「跳回 again 后第一件事就是检查 h_nr_queued」的隐含语义被显式化成循环条件，挑不到 entity 时自然回到条件判断。

**外层 `pick_task_fair()`（保留 `rf`，因为 `sched_balance_newidle()` 会动 rq lock）**——只剩「挑不到就尝试均衡，均衡拉到了就再挑」这一层策略：

```c
	do {
		p = pick_task_fair_rq(rq);
		if (p)
			return p;

		if (sched_core_enabled(rq))
			return NULL;

		new_tasks = sched_balance_newidle(rq, rf);
	} while (new_tasks > 0);

	return new_tasks ? RETRY_TASK : NULL;
```

关键取舍是**把 `sched_core_enabled()` 的判断留在外层、放在 newidle 之前**，而不是塞进 helper：core scheduling 开启时不允许通过 newidle 拉任务（会破坏 core 内的同步挑选语义），这个约束与「在 rq 上挑任务」无关，因此属于外层职责。helper 不接 `rf` 也是同一逻辑的体现——只有 newidle 需要它。

最后 `return new_tasks ? RETRY_TASK : NULL;` 用三元表达式合并了原来的两个返回：循环退出时 `new_tasks <= 0`，`< 0` 对应 `RETRY_TASK`、`== 0` 对应 `NULL`，与原来的 `if (new_tasks < 0) return RETRY_TASK; ... return NULL;` 一一对应。

被放弃的备选方案邮件里没提；从 diff 看作者也没有尝试把 newidle 一并下沉到 helper（那样会把 `rf` 与解锁语义带进内层，反而更糟）。

## 版本演进与当前进展
- v1（2026-09-09 18:17 发出，本缓存收件时间 2026-09-10 02:17，`<20260909181712.1050224-1-ynorov@nvidia.com>`），单补丁，`kernel/sched/fair.c` 27 insertions / 24 deletions。
- 补丁基线 `kernel/sched/fair.c` index `ade1eceb39b8`；上下文显示基线已是 `h_nr_queued` + `update_curr_eevdf()` + `pick_next_entity(rq, true)`（层级下降已内聚到 `pick_next_entity()`）的形态。
- 截至 09-10 缓存结束：**v1 刚发出，暂无 review 意见**，无 Reviewed-by / Acked-by，无 NAK。
- 作者近况值得一提：同一天（09-10 01:19）Yury 给 steal_governor v13 的 07/13 补丁打了 Reviewed-by（见 sched-20260910-012），他此前多轮深度评审该系列，本补丁属于他在 `kernel/sched` 里顺手做的清理，而非某个系列的一部分。

## Maintainer 意见与讨论焦点
本日无任何维护者发言。需要如实标注的是：

- **Peter Zijlstra / Vincent Guittot / Ingo Molnar 均未表态**。`pick_task_fair()` 属于公平类最核心路径，这类「无功能变化」的重构最终能否进 tip，几乎完全取决于 core 维护者是否愿意接受一次纯结构性改动带来的 diff 噪音与潜在合并冲突。
- 作者身份是外部评审者（NVIDIA，长期维护 bitmap/cpumask），非 sched 维护者，因此没有「自己队列自己收」的便利。
- 我自己核对的等价性结论（供判断风险用，非邮件内容）：三条返回路径逐一对齐——(1) `pick_task_fair_rq()` 返回非 NULL 时直接返回，对应原 `p = task_of(se); return p;`；(2) `sched_core_enabled()` 为真返回 NULL，位置仍在 newidle 之前，与原 `idle:` 段一致；(3) 循环退出后 `new_tasks <= 0`，`< 0` → `RETRY_TASK`、`== 0` → `NULL`，与原两个 return 一致。`new_tasks` 在到达三元表达式前必然被赋值（do-while 至少执行一次），不存在未初始化读取。原实现中「`h_nr_queued` 为 0 时才走 idle 段」这一前提在新版中由 helper 返回 NULL 后紧接着的 core/newidle 分支承接，顺序未变。
- 一个**未被改动但被这次重构放大可见度**的既有风险：内层 `while` 若遇到 `h_nr_queued > 0` 而 `pick_next_entity()` 持续返回 NULL 的状态，会在持有 rq lock 的情况下空转（原 `goto again` 形态完全相同，不是本补丁引入）。重构后这段循环更紧凑，反而更容易被读者注意到这个前提。

## 合入评估
likelihood: unknown。

理由：证据面只有一封 v1 邮件、零回帖，没有任何维护者信号可供外推。倾向性判断（非邮件结论）：改动小、可验证、带实测代码体积数据，且 `pick_task_fair()` 近期本身就在被频繁重构，这类清理被接受的概率不低；但「No functional changes intended」用的是 *intended* 而非断言，核心路径的重构通常需要至少一位 fair 类维护者逐行确认等价性才会收。

blocking_issues：无人评审；核心热路径重构需要维护者确认语义等价；与 `kernel/sched/fair.c` 上其他在飞补丁（如 pick 路径相关的 EEVDF 改动）存在合并冲突风险。

next_action：等 Peter / Vincent 回复；若一周无回应，作者可在原线程 ping 一次并附上 objdump 对比（96/124 字节的数据已给出，但未见反汇编差异片段）。

## 效果评估
有具体数据，且是这类补丁唯一可量化的收益：

- GCC 15.2.0，`x86_64_defconfig`：`.text` **省 96 字节**。
- `x86_64_defconfig` + `CONFIG_SCHED_CORE` + `CONFIG_CFS_BANDWIDTH`：**省 124 字节**。

未见任何运行时 benchmark（schedbench / hackbench / 唤醒延迟等），作者也未声称有性能提升——`pick_task_fair()` 的分支结构变化对现代前端预测器的影响本就难以测出，只报代码体积是恰当的口径。需要标注：这两个数字只覆盖 x86_64 + GCC 15.2.0，其他架构/编译器组合下的效果未获取到。

## 我可以参与的点
- **等价性复核并回帖**（review）：本补丁唯一的合入门槛就是「确无功能变化」。可以把上面三条返回路径的逐条对齐、以及 `new_tasks` 不会未初始化使用这两点整理成简短分析回到线程，给维护者省一遍人工核对——这类回帖对纯清理补丁的推进作用很实际。
- **补其他架构/编译器的体积数据**（testing）：作者只给了 x86_64 + GCC 15.2.0。arm64（`defconfig` 与 `defconfig + SCHED_CORE + CFS_BANDWIDTH`）以及 clang 下的对比数据能直接加强这个补丁的说服力，成本低、无人做过。
- **顺带检查同类 goto 结构**（extend）：`pick_task_fair()` 的兄弟路径（如 `pick_next_task_fair()`、`put_prev_task_fair()` 以及 dl/rt 类的 pick 函数）是否存在同样「一个标签承担两种回跳语义」的结构，可作为后续独立清理系列——但应先等本补丁的评审结论，避免在维护者明确不欢迎此类重构时白发。

## 参考链接
- 补丁 v1（线程根）: https://lore.kernel.org/all/20260909181712.1050224-1-ynorov@nvidia.com/
- 同日作者对 steal_governor 07/13 的 Reviewed-by: https://lore.kernel.org/all/aqGVMR2m_NF76tv3@yury/
- tip-bot / upstream commit: 未获取到（尚未合入）

---
id: sched-20260910-014
date: 2026-09-10
subject: "sched/fair: Rework pick_task_fair() control flow"
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: "<20260909181712.1050224-1-ynorov@nvidia.com>"
lore_url: "https://lore.kernel.org/all/20260909181712.1050224-1-ynorov@nvidia.com/"
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: "2026-09-11T01:05:00"
authors:
  - "Yury Norov"
maintainers_involved: []
patch_series:
  - version: v1
    msgid: "<20260909181712.1050224-1-ynorov@nvidia.com>"
    date: "2026-09-09"
    summary: "抽出静态 helper pick_task_fair_rq() 承载 rq 内挑选逻辑，外层用 do-while 包住「挑不到则 sched_balance_newidle，拉到任务则重挑」，去掉 again:/idle: 两个 goto 标签；kernel/sched/fair.c 27 insertions / 24 deletions。"
    review_outcome: "v1 刚发出，暂无 review 意见。"
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - "无任何维护者表态，核心热路径重构需 fair 类维护者逐行确认语义等价"
    - "作者自陈用词是 No functional changes intended（intended 而非断言），等价性尚未被第三方确认"
    - "kernel/sched/fair.c 上其他在飞补丁可能与之冲突"
  next_action: "等 Peter Zijlstra / Vincent Guittot 回复；一周无回应可 ping 并附反汇编差异"
contribution_opportunities:
  - kind: review
    description: "回帖给出三条返回路径的逐条等价性分析（含 new_tasks 不会未初始化使用），替维护者省一遍人工核对"
  - kind: testing
    description: "补 arm64 defconfig（含/不含 SCHED_CORE + CFS_BANDWIDTH）与 clang 下的 .text 体积对比数据，作者只给了 x86_64 + GCC 15.2.0"
  - kind: extend
    description: "排查 pick_next_task_fair()/put_prev_task_fair() 及 dl、rt 类 pick 函数是否存在同样「一个 goto 标签承担两种回跳语义」的结构，作为后续清理（建议先等本补丁评审结论）"
source_email_count: 1
related_articles:
  - "sched-20260910-012"
tags:
  - cfs
  - eevdf
  - core_sched
---
