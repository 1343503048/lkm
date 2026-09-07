# sched/fair: which tasks should nr_pref_llc_running be compared against?

## TL;DR

本文为增量更新：这条线程从 8/27 Zhan Xusheng（小米）读 `alb_break_llc()` 时的一个语义疑问开始，8/28 Tim Chen 承认 DELAY_DEQUEUE 会破坏该判据并**在回帖里内联给了修复**（把 `nr_pref_llc_running` 拉回 runnable 语义），同一帖拿到 Zhan 的 `Reviewed-by`。**8/30 Chen Yu 又指出同一计数器的第二个漏洞：负载均衡迁移路径上 `attach_tasks() → enqueue_entity() → account_llc_enqueue()` 会给一个仍处于 delayed 状态、并不 runnable 的任务加计数**——因为迁移时 `se->on_rq == false`，`requeue_delayed_entity()` 不会清 `sched_delayed`。也就是说 8/28 那版修复只补了睡眠侧，迁移侧还没人动。这是 CAS 判据正确性问题，本地主线树（截至 2026-08-31）尚未见任何一处修复。

## 背景与问题

CAS 的 active balance 入口 `alb_break_llc()` 用一个等式判断"源 rq 上所有可运行的 fair 任务都偏好源 LLC"，从而拒绝为了均衡而破坏局部性：

```c
	if (env->src_rq->nr_pref_llc_running &&
	    env->src_rq->nr_pref_llc_running == env->src_rq->cfs.h_nr_runnable) {
		...
		if (env->src_rq->nr_running <= 1)
			return true;
```

Zhan Xusheng 的原始发现（8/27）：两个计数器覆盖的集合不同。

- `nr_pref_llc_running` 在 `account_entity_enqueue()/account_entity_dequeue()` 旁边维护（主线 `kernel/sched/fair.c:1513`、`1547`，与 `cfs_rq->nr_queued++/--` 同步）→ **queued 语义**。
- `h_nr_runnable` 由 `set_delayed()`/`clear_delayed()` 增减，delay-dequeued 的实体仍然 queued 但被它排除 → **runnable 语义**。

后果：开了 DELAY_DEQUEUE 时，一个刚睡下去的任务会让 `nr_pref_llc_running` 停在 `h_nr_runnable` 之上，等式不成立 → `alb_break_llc()` 返回 false → active load balance 不再尊重 LLC 偏好。错误是**单向**的（计数器是另一个的超集，所以只会"该保护时没保护"，不会"错误地保护"）。

Zhan 同时诚实交代了他**没能在两台 socket 的 qemu 客户机里跑出这条路径**：CAS 打开、一个 6 busy + 10 sleeping 线程的进程，`p->preferred_llc` 从未被赋值，`nr_pref_llc_running` 始终为 0，而 `alb_break_llc()` 本身跑了 21 次；他怀疑 `update_se()` 在模拟环境下因 `delta_exec <= 0` 提前返回，导致 `account_mm_sched()` 大多在 `sc_stat` 检查前就返回——并指出"如果虚拟机都测不出这类问题，这件事本身就值得知道，因为这正是不一致能长期隐藏的原因"。

## 技术方案

**Tim Chen 的修法（8/28，内联补丁 `sched/cache: Keep nr_pref_llc_running in the runnable domain`）**：在计数器一侧对齐语义，即"让 `nr_pref_llc_running` 和 `h_nr_runnable` 一样排除 delayed 任务"，而不是把比较对象换成 `cfs.h_nr_queued`（Zhan 提出的另一个候选，被放弃）：

- 新增 `account_llc_delayed()` / `account_llc_requeue_delayed()`，分别在 `set_delayed()`、`clear_delayed()` 里按 `p->pref_llc_queued` 减/加计数。
- 防止重复扣减：任务真正被 dequeue 时 `dequeue_entity()` 会先 `account_llc_dequeue()` 再 `clear_delayed()`，所以 `account_llc_dequeue()` 在 `p->se.sched_delayed` 仍置位时**跳过**减计数，并清掉 `pref_llc_queued`，使随后的 `clear_delayed()` 也不再加回。
- `nr_llc_running` 与 `sd->llc_counts` **保持 queued 语义不动**。
- commit message 里强调 "Active balance only moves runnable tasks, and this is the only LLC check it consults: once the stopper runs, `LBF_ACTIVE_LB` skips the per-task test in `can_migrate_task()`"——即这条判据是 active balance 唯一的 LLC 闸门，所以它错一次就漏一次。

**Zhan Xusheng 的 `Reviewed-by`（8/28）附带的顺序证明**（这段是判据能否信的关键）：`dequeue_hierarchy()`（fair.c:8148）经 `dequeue_entity()` 到 `account_llc_dequeue()`，而 `clear_delayed()` 要到 8164 才执行，所以测试 `se->sched_delayed` 时标志仍然有效；四组序列（enqueue/dequeue、enqueue/sleep/wake/dequeue、enqueue/sleep/真实 dequeue、负载均衡搬走 delayed 任务）收支平衡；`requeue_delayed_entity()` 只做 `__enqueue_entity()` + `clear_delayed()`，不经过 `account_entity_enqueue()`，因此唤醒路径不会重复计数；`account_mm_sched()` 也看不到 delayed 任务，因为 `task_running_on_cpu()`（fair.c:12245）要求 `task_on_rq_queued()`；`sd->llc_counts` 的两个读者（fair.c:11895、13228）都是拿它与另一个 `llc_counts` 比，delayed 任务两边同时偏移。

**8/29 Tim Chen 收尾**：确认 "sd->llc_counts do not need to change as you pointed out"。

**8/30 Chen Yu 指出漏掉的迁移路径**（本日的实质新增）：负载均衡迁移靠 `detach_tasks()/attach_tasks()` 搬任务，期间 `p->se.sched_delayed` **保持不变**；`enqueue_task_fair()` 只有在 `se->on_rq && se->sched_delayed` 时才经 `requeue_delayed_entity()` 清标志，而迁移途中 `se->on_rq == false`。于是

```
attach_tasks → enqueue_hierarchy → enqueue_entity → account_llc_enqueue(rq, p)
```

会在目的 rq 上给一个 delayed（不 runnable）的任务**错误地加 `nr_pref_llc_running`**。Chen Yu 并追问：既然比较对象已经改成 runnable 语义，`alb_break_llc()` 里那段是不是也该一起动——他引用的片段把那条"唯一任务"判据写作 `env->src_rq->cfs.h_nr_runnable <= 1`，而主线该处目前是 `nr_running <= 1`（我的判断：他是在建议把这条也统一到 runnable 语义，邮件里没有展开，属未定论）。

## 版本演进与当前进展

- 8/27：Zhan Xusheng 发出疑问帖（非补丁），点明"读代码所得、未观测到失败、qemu 里也跑不出该路径"。
- 8/27–8/28：Tim Chen 回复承认 DELAY_DEQUEUE 会破坏判据，内联给出修复（`<59e2b8265fc650266b93d8f523c366edfa912428.camel@linux.intel.com>`），带 `Reported-by: Zhan Xusheng`。
- 8/28：Zhan Xusheng 回 `Reviewed-by` + 顺序与收支证明。
- 8/29：Tim Chen 致谢并确认 `sd->llc_counts` 不改。
- 8/30：**Chen Yu 提出迁移路径的第二个漏洞，无人回应，未发新 revision**。
- 本地主线树核对（`/home/zq/code/linux`，树时间 2026-08-31）：`account_llc_delayed()`/`account_llc_requeue_delayed()` 均不存在，`account_llc_enqueue/dequeue` 仍是 queued 语义 → 两处问题都还在。

## Maintainer 意见与讨论焦点

- **Tim Chen（CAS 主作者）**：接受判据有缺陷，选择"改计数器语义"而非"改比较对象"；明确 `sd->llc_counts` 保持 queued 语义（这条有 Zhan 的论证支撑，双方一致）。
- **Chen Yu（CAS 另一位核心作者）**：不满足于只补睡眠侧，指出 `sched_delayed` 在迁移期间不变这一事实会让 enqueue 侧重新跑偏——**这正是当前线程未解决的分歧**：语义对齐要覆盖 `set_delayed/clear_delayed` **和** 迁移的 attach/detach 两条路径，而内联补丁只做了前者。
- 形式问题：修复是以"回复里内联补丁"的方式发的（subject 为 `Re: [PATCH] ...`），没有独立的 `[PATCH]` msgid 链条，这类改法对 tip 侧接手不友好。
- 未解决：①迁移路径怎么修（在 `account_llc_enqueue()` 里也判 `p->se.sched_delayed`？还是让 attach 路径把 delayed 状态正确落地）；②`alb_break_llc()` 里 `nr_running <= 1` 是否改成 `h_nr_runnable <= 1`；③这些都还没有任何 benchmark/实测，且提出者自己承认在 qemu 里无法构造出条件。

## 合入评估

**possible**，但当前不宜直接收：内联修复已有一枚 `Reviewed-by`（来自报告者本人），方向也由 CAS 作者认可；问题是 CAS 的另一位作者在同日指出方案不完整，合理走向是带迁移侧修法的新版本，而它尚未出现。另一个现实障碍是**这条判据在真实硬件上无法验证**——`preferred_llc` 在测试环境里根本没被赋值，因此社区既拿不到"修复有效"的证据，也难以回归测试。

## 效果评估

**没有任何效果数据**，且这是本线程最实质性的空白：

- 原始发现是纯读代码推理，报告者明确说"This is from reading the code rather than an observed failure"，并给出他尝试复现失败的细节（`preferred_llc` 从未赋值、`nr_pref_llc_running` 恒为 0、`alb_break_llc()` 执行 21 次、疑似 `delta_exec <= 0` 早退）。
- 修复侧（Tim Chen）与追加问题侧（Chen Yu）都没有提供实测、benchmark 或 schedstat 前后对比。
- 结论方向上"该判据在 DELAY_DEQUEUE 下会漏保护"有代码依据支撑，但**实际影响幅度未知**。

## 我可以参与的点

- **最有价值的一件事：给出能触发这条路径的真实环境数据**。Zhan 在 qemu 里测不出来（`preferred_llc` 压根不分配），任何能在实体 2-socket/多 LLC 机器上把 `nr_pref_llc_running`、`h_nr_runnable`、`nr_running` 三个值同时采出来（`/proc/sched_debug` 或 tracepoint）并展示"delayed 任务导致等式失效"的回帖，都会直接推动这个补丁定型。
- **把迁移路径的修法写实**：可以顺着 Chen Yu 的分析给出具体方案（例如 `account_llc_enqueue()` 同样跳过 `p->se.sched_delayed` 的任务），并核对 `attach_tasks()/detach_tasks()` 期间 `pref_llc_queued` 的取值是否已成对；这是当前**没人给出代码**的空白点。
- **回答 `nr_running <= 1` 那条判据是否应改为 runnable 语义**：Chen Yu 提了但没展开，无人回应，适合给出结论性分析。
- **回合判断**：OLK-6.6 若带 CAS，这条属于"判据正确性"级别的问题，且和 `DELAY_DEQUEUE` 是否开启直接相关——可以先确认本地分支的 `DELAY_DEQUEUE`/CAS 组合是否会命中同一等式；上游修复未定型前不建议回合。

## 参考链接

- lore（8/27 原始疑问帖，线程根）: https://lore.kernel.org/all/20260827135000.735138-1-zhanxusheng@xiaomi.com/
- lore（8/28 Tim Chen 内联修复）: https://lore.kernel.org/all/59e2b8265fc650266b93d8f523c366edfa912428.camel@linux.intel.com/
- lore（8/28 Zhan Xusheng Reviewed-by 与顺序证明）: https://lore.kernel.org/all/20260828022012.936112-1-zhanxusheng1024@gmail.com/
- lore（8/29 Tim Chen 确认 sd->llc_counts 不改）: https://lore.kernel.org/all/a2b5c308fcb9487dc04d80f57b3e3ed606410ac8.camel@linux.intel.com/
- lore（8/30 Chen Yu 指出迁移路径漏洞）: https://lore.kernel.org/all/apPnJaUS5vq2f85J@three-body/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260830-003
date: '2026-08-30'
subject: "sched/fair: which tasks should nr_pref_llc_running be compared against?"
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: "<20260827135000.735138-1-zhanxusheng@xiaomi.com>"
lore_url: "https://lore.kernel.org/all/apPnJaUS5vq2f85J@three-body/"
authors: [Zhan Xusheng, Tim Chen, Chen Yu]
maintainers_involved: [Tim Chen, Chen Yu]
current_version: v1
patch_series:
  - version: v1
    msgid: "<59e2b8265fc650266b93d8f523c366edfa912428.camel@linux.intel.com>"
    date: 2026-08-28
    summary: "内联补丁 sched/cache: Keep nr_pref_llc_running in the runnable domain：在 set_delayed()/clear_delayed() 同步调整 nr_pref_llc_running，并让 account_llc_dequeue() 在 sched_delayed 仍置位时跳过减计数"
    review_outcome: "报告者 Zhan Xusheng 给出 Reviewed-by 与收支证明，确认 sd->llc_counts 保持 queued 语义；8/30 Chen Yu 指出迁移 attach 路径仍会错误加计数，未发新 revision"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "Chen Yu 指出的负载均衡迁移路径漏洞未修，当前方案只覆盖睡眠侧"
    - "修复以回帖内联补丁形式发出，缺独立 [PATCH] msgid 链，不利于 tip 接手"
    - "无真实硬件实测：qemu 环境下 preferred_llc 从未赋值，无法证明修复效果"
    - "alb_break_llc() 中 nr_running <= 1 判据是否改为 h_nr_runnable 语义未有结论"
  next_action: "作者需覆盖迁移路径并作为独立补丁重发，社区需要提供能触发该等式的实体机数据"
contribution_opportunities:
  - kind: testing
    description: "在实体多 LLC 机器上采集 nr_pref_llc_running/h_nr_runnable/nr_running，复现 delayed 任务导致 alb_break_llc() 漏保护"
  - kind: extend
    description: "给出 account_llc_enqueue() 侧对 p->se.sched_delayed 的处理方案，补齐 Chen Yu 指出的迁移路径"
  - kind: discussion
    description: "回答 alb_break_llc() 里 nr_running <= 1 是否应统一为 runnable 语义，目前无人回应"
generated_at: "2026-09-07T22:06:23"
source_email_count: 1
related_articles: [sched-20260826-010]
tags: [cfs, load_balance]
---
