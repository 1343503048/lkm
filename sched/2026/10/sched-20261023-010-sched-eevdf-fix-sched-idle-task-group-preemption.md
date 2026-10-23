# sched/eevdf: Fix sched idle task group preemption

## TL;DR
本文为增量更新，完整脉络见下。

- sched-20261020-001：Vincent Guittot 发往 sched 的单补丁修复——EEVDF「单运行队列」改动（`85570f10a4c6`）后，扁平层级把全部 runnable 任务放进同一 cfs_rq，wakeup 抢占时仍需向上遍历 task group 层级才能判断是否存在 sched_idle 任务组，否则 idle 组任务不会被正确抢占。当日 v1→v2 连发，Jakub Okoński 实测修复了其 `cpu.idle` 用例，但指出「同 cgroup 下 nice 19 spinner 相对 7.2.9 仍回退」；作者明确本补丁只覆盖 sched_idle 组场景、nice 19 另行排查。
- sched-20261021-009：Kayra Cizmeci 走查层级示例后给出 Reviewed-by；但 Peter Zijlstra 对 `cpu.idle` **语义本身**提出质疑（能否把 idle 传播到所有子组，或让 `se_is_idle()` 向上走、任一祖先 idle 即算 idle），并直言「我痛恨 `find_matching_se()`，当初删除它时别提多开心」。
- sched-20261022-005：Josh Don（Google，`cpu.idle` 原实现者）写长文支持保留 `find_matching_se()`——「让 TB 抢占 TA」才是理想判定，避免破坏「在自身 cgroup 层级内部委派 cpu.idle」的用户；Peter 进一步给出把 idle 传播到所有子组的草稿补丁 `tg_set_idle_up()`，但仍认为「TA/TB 都标记 idle、只不过层级不同」的语义很怪。
- sched-20261023-010（今天）：Peter 再发**第二版传播草稿**——`init_cfs_rq()` 增加 parent 参数、新建 `tg_set_idle_up()` 沿 `walk_tg_tree_from()` 向上累加 `h_nr_idle`，并称「顺带修了你说的 init 那处」；但 Josh Don 立即指出 clear 侧的双重遍历是坏的（会让 `h_nr_idle` 变负），Kayra Cizmeci 也构造 ROOT→A(3)→B(2) 示例证明新版本「把 A 设 idle 时 ROOT 应为 5 却算出 3」仍不对。焦点从「是否用 find_matching_se」进一步收窄到「Peter 传播方案的具体实现正确性」。

## 背景与问题
（承接 sched-20261020-001 → sched-20261021-009 → sched-20261022-005）「sched/eevdf: Move to a single runqueue」落地 v7.3 后，Jakub Okoński 报告 `cpu.idle` cgroup 用例的 wakeup 抢占语义被破坏：单运行队列下扁平层级把所有 runnable 任务放进同一 cfs_rq，`wakeup_preempt_fair()` 直接比较 `se_is_idle(se/pse)`，未沿 task group 层级找「共同父级的兄弟实体」，导致 sched_idle 任务组不被正确抢占。近日焦点持续从「补丁是否正确」转向「`cpu.idle` 的语义到底该是什么」——组间抢占是否应尊重 cgroup 层级。今天 Peter 的传播方案第二次落地为具体 diff，进入实现正确性讨论。

## 技术方案
（承接 sched-20261020-001）原始修复新增 `find_matching_se()` 把两个 sched_entity 对齐到「共同父级的兄弟实体」层级，再以 `se_is_idle()` 判定抢占走向（idle 让位非 idle→RESCHED；非 idle 让位 idle→NONE；两侧同类→原 EEVDF 判定）。今日 Peter 的传播替代方案（第二版 diff）：

- `init_cfs_rq(struct cfs_rq *cfs_rq, struct cfs_rq *parent)`：有 parent 时 `cfs_rq->idle = parent->idle`——**回应 Josh 上日「sum of ancestors 需要在 cgroup 创建时也设置」**；`sched_init()` 里 `init_cfs_rq(&rq->cfs, NULL)`。
- `cfs_rq->idle` 语义从「本组 tg->idle 的本地缓存」改为「所有祖先 tg->idle 之和」。
- 新增 `tg_set_idle_up()`：`sched_group_set_idle()` 里用 `walk_tg_tree_from(tg, tg_nop, tg_set_idle_up, &tsi)` 从该组向上对每个祖先组累加/递减 `h_nr_idle`（增量按 `h_nr_queued - h_nr_idle`），取代原来「逐 se 沿 `for_each_sched_entity` 向上」的双重遍历；`guard(mutex)`/`guard(rq_lock_irqsave)` 替代显式加解锁。
- `print_cfs_rq()` 顺带多打一行 `idle`。

Josh Don 与 Kayra Cizmeci 当日即指出这版实现仍有 bug（见下）。

## 版本演进与当前进展
*current_version: v2*（原始补丁 `sched-20261020-001` 的 v2，作者 Vincent 的 `find_matching_se()` 方案）；Peter 的「idle 传播」替代方案当日演进到第二版草稿（非正式补丁号）。当日无作者 Vincent 的新版本发出。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**（维护者，当日主力）：承认上日版本错（「Argh. Yes, I seem to have gotten it wrong. I'll try again in the morning.」），次日给出第二版传播 diff，仍坚持替代 `find_matching_se()` 的方向（「是的，我们还能把它用作 find_matching_se() 的优化——虽然我仍觉得那套语义很怪，但算了，如果大家真要这样」）。
- **Josh Don**（`cpu.idle` 原实现者）：指出第二版 clear 侧的双重遍历是坏的——「从 A(2 tasks)/B(3 tasks)、A 先 idle 的状态出发，clear 时先处理 B 减 3、再处理 A 试图减 5，会让 root 的 `h_nr_idle` 变成 -3」；并建议「分层计数 idle 之后，可保留 find_matching_se() 做精确抢占检查，但只在两任务中至少一个有 idle 祖先时才调用」。
- **Kayra Cizmeci**：构造 ROOT→A(3 tasks)→B(2 tasks) 例，把 A 设 idle 时「应得 B=0、A=2、ROOT=5，但新版本算出 ROOT=3」，认为仍不对。

三方（Peter/Josh/Kayra）对「传播方案」的实现正确性尚未达成一致，作者 Vincent 的原始 `find_matching_se()` 方案当日无新动作。

## 合入评估
*likelihood=medium*。原始补丁有 Kayra Reviewed-by，但主维护者 Peter 持续主张以「idle 传播到子组」的语义变更取代 `find_matching_se()`，而该替代方案两版草稿都被 Josh/Kayra 指出实现 bug，语义与实现均未收敛。*blocking_issues*：`cpu.idle` 是否传播到子组/`se_is_idle()` 是否向上走的语义分歧未解决；Peter 传播草稿的 clear 侧计数（h_nr_idle 变负）与 set-idle 汇总（ROOT 少算）bug 待修。*next_action*：Peter 或作者给出语义论证 + 修正实现，或 Josh/Google 明确 `cpu.idle` 官方用法后定案。

## 效果评估
无新量化数据。既有结论延续：`find_matching_se()` 方案修复 `cpu.idle` 用例有效（Jakub 实测），nice 19 同 cgroup 回退属另一线索、不在本补丁范围。

## 我可以参与的点
- *kind: review*：就 Peter 传播方案的 `tg_set_idle_up()` 累计方向（set 与 clear 两路径是否对称、避免 `h_nr_idle` 为负）给出走查。
- *kind: discussion*：结合 cgroup v2 `cpu.idle` 的实际生产用法，就「组间抢占是否应尊重 cpu.idle 层级」提供输入，帮收敛语义方向。

## 参考链接
- Peter 第二版传播草稿: https://lore.kernel.org/all/20261023132956.GD409038@noisy.programming.kicks-ass.net/
- Josh Don 回帖: https://lore.kernel.org/all/CABk29NviVUAK6B_deQ7qah8eABiCikbFpTwDEO2hdproGLdLwQ@mail.gmail.com/
- Kayra 回帖: https://lore.kernel.org/all/attitenhAXB86seS@scheduler.schedules/
- Peter 承认上版错误: https://lore.kernel.org/all/20261022212150.GW2823843@noisy.programming.kicks-ass.net/
- 前文: sched-20261020-001 / sched-20261021-009 / sched-20261022-005

---
id: sched-20261023-010
date: 2026-10-23
subject: "sched/eevdf: Fix sched idle task group preemption"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261019182622.1584454-1-vincent.guittot@linaro.org>"
lore_url: "https://lore.kernel.org/all/20261019182622.1584454-1-vincent.guittot@linaro.org/"
authors: ["Vincent Guittot"]
maintainers_involved: ["Peter Zijlstra", "Josh Don", "Kayra Cizmeci"]
current_version: v2
patch_series:
  - version: v2
    msgid: "<20261019182622.1584454-1-vincent.guittot@linaro.org>"
    date: 2026-10-19
    summary: "find_matching_se() 对齐层级 + se_is_idle() 判定抢占"
    review_outcome: "Kayra Reviewed-by；Peter 主张以 idle 传播语义变更取代"
upstream_commit: null
fixes_commit: "85570f10a4c6"
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["cpu.idle 语义（传播/向上遍历/单层）未收敛", "Peter 传播草稿 clear 侧 h_nr_idle 变负、set-idle 汇总少算"]
  next_action: "语义论证 + 修正传播实现，或 Josh/Google 明确 cpu.idle 官方用法后定案"
contribution_opportunities:
  - kind: review
    description: "走查 tg_set_idle_up 的 set/clear 对称性，避免 h_nr_idle 为负"
  - kind: discussion
    description: "就组间抢占是否尊重 cpu.idle 层级提供生产用法输入"
generated_at: "2026-10-24T09:09:00"
source_email_count: 4
related_articles: ["sched-20261020-001", "sched-20261021-009", "sched-20261022-005"]
tags: [eevdf, cgroup, preempt]
---