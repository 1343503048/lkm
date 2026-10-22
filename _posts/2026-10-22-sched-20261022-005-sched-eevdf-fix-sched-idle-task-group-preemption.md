---
id: sched-20261022-005
date: 2026-10-22
subject: 'sched/eevdf: Fix sched idle task group preemption'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261019182622.1584454-1-vincent.guittot@linaro.org>
lore_url: https://lore.kernel.org/all/20261019182622.1584454-1-vincent.guittot@linaro.org/
authors:
- Vincent Guittot
maintainers_involved:
- Peter Zijlstra
current_version: v2
patch_series:
- version: v2
  msgid: <20261019182622.1584454-1-vincent.guittot@linaro.org>
  date: 2026-10-19
  summary: find_matching_se() 对齐共同父级兄弟实体判定 idle 抢占
  review_outcome: Kayra Reviewed-by；Peter 质疑 cpu.idle 语义，番外传播方案讨论
upstream_commit: null
fixes_commit: 85570f10a4c6
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - cpu.idle 是否应传播到子组/向上遍历的语义分歧未解决
  next_action: 收敛 cpu.idle 语义后决定是否保留 find_matching_se()
contribution_opportunities:
- kind: review
  description: 就组间抢占是否尊重 cpu.idle 层级给出用例与观点
- kind: testing
  description: 对比 find_matching_se() 与 idle 传播方案在多层 cpu.idle 拓扑下的行为
generated_at: '2026-10-23T01:20:00'
source_email_count: 3
related_articles:
- sched-20261021-009
tags:
- eevdf
- cgroup
- regression
title: 'sched/eevdf: Fix sched idle task group preemption'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/10/20/sched-20261020-001-sched-eevdf-fix-sched-idle-task-group-preemption.html">sched-20261020-001</a>：Vincent Guittot 发往 sched 的单补丁修复——EEVDF「单运行队列」改动（`85570f10a4c6`）后，扁平层级把全部 runnable 任务放进同一 cfs_rq，wakeup 抢占时仍需向上遍历 task group 层级才能判断是否存在 sched_idle 任务组，否则 idle 组任务不会被正确抢占。当日 v1→v2 连发，Jakub Okoński 实测修复了其 `cpu.idle` 用例，但指出「同 cgroup 下 nice 19 spinner 相对 7.2.9 仍回退」；作者明确本补丁只覆盖 sched_idle 组场景、nice 19 另行排查。
- <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-009-sched-eevdf-fix-sched-idle-task-group-preemption.html">sched-20261021-009</a>：Kayra Cizmeci 走查层级示例后给出 Reviewed-by；但 Peter Zijlstra 对修复依赖的 `cpu.idle` **语义本身**提出质疑——「能否在 `sched_group_set_idle()` 里把 idle 传播到所有子组，或让 `se_is_idle()` 向上走、任一祖先 idle 即算 idle」，并直言「我痛恨 `find_matching_se()`，当初删除它时别提多开心」。
- <a class="article-ref" href="/lkm/2026/10/22/sched-20261022-005-sched-eevdf-fix-sched-idle-task-group-preemption.html">sched-20261022-005</a>（今天）：Josh Don（Google）写长文支持保留 `find_matching_se()`——认为「让 TB 抢占 TA」才是理想判定，避免破坏「在自身 cgroup 层级内部委派 cpu.idle」的用户；Peter 进一步给出把 idle 传播到所有子组的草稿补丁 `tg_set_idle_up()`，但仍认为「TA/TB 都标记 idle、只不过层级不同」的语义很怪。焦点仍是 `cpu.idle` 语义，而非补丁正确性与否。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/10/20/sched-20261020-001-sched-eevdf-fix-sched-idle-task-group-preemption.html">sched-20261020-001</a>）「sched/eevdf: Move to a single runqueue」落地 v7.3 后，Jakub Okoński 报告 `cpu.idle` cgroup 用例的 wakeup 抢占语义被破坏：单运行队列下扁平层级把所有 runnable 任务放进同一 cfs_rq，`wakeup_preempt_fair()` 直接比较 `se_is_idle(se/pse)`，未沿 task group 层级找「共同父级的兄弟实体」，导致 sched_idle 任务组不被正确抢占。今日焦点进一步从「补丁是否正确」转向「`cpu.idle` 的语义到底该是什么」——是否应在组间抢占上尊重 cgroup 层级。

## 技术方案
（承接 <a class="article-ref" href="/lkm/2026/10/20/sched-20261020-001-sched-eevdf-fix-sched-idle-task-group-preemption.html">sched-20261020-001</a>）修复新增 `find_matching_se()` 把两个 sched_entity 对齐到「共同父级的兄弟实体」层级，再以 `se_is_idle()` 判定，据此决定抢占走向（idle 让位非 idle→RESCHED；非 idle 让位 idle→NONE；两侧同类→原 EEVDF 判定）。今日无正式新补丁，仅两套替代语义被摆上台面：Josh Don 主张保留 `find_matching_se()`（精确但 wakeup 时较贵，与既有的 `sched_idle_rq` imprecise 特性一脉相承）；Peter 主张(1) 在 `sched_group_set_idle()` 把 idle 传播给所有子组（并附 `tg_set_idle_up()` 草稿 diff，利用 `h_nr_queued - h_nr_idle` 增量对每个 `for_each_sched_entity(se)` 累加 `h_nr_idle`），或 (2) 让 `se_is_idle()` 向上遍历、任一祖先 idle 即真。Kayra 则建议「先判两任务是否同一子树、再沿子树向上找 idle 祖先」。

## 版本演进与当前进展
*current_version: v2*（`<20261019182622.1584454-1-vincent.guittot@linaro.org>`）。当日无新补丁版本，进展为语义之争与 Peter 的传播方案草稿。

## Maintainer 意见与讨论焦点
Peter Zijlstra 认为现语义「weird」：TA/TB 都标记为 idle（只是层级不同），老代码会让 TB 抢占 TA，但他「看不出这有什么好」；并构造了一个 ROOT→{GA\*,GB→{GC\*,GD→GE→{TC,TD},TB}} 的用例，说明严格 LCA 规则下 TC/TD 会互相抢占，尽管它们同属一个 idle 子树。Josh Don 反驳：GB 非 idle 而 GA idle，TB 应抢占 TA；cpu.idle 是「权重」与「抢占」双重概念，权重天然被层级尊重，抢占部分也应尽量尊重层级，且「imprecise placement 比 imprecise preemption 更可接受」。Kayra Cizmeci 认为 Peter 的用例也很怪，提出子树+向上找 idle 的折中，并质疑「丢掉 TA 与 T{C,D} 的区别是否可接受」。

## 合入评估
*likelihood=medium*。补丁本身有 Kayra 的 Reviewed-by，但主打方向被主维护者 Peter 质疑，语义需要先收敛；*blocking_issues*：`cpu.idle` 是否传播到子组/`se_is_idle()` 是否向上走的语义分歧未解决；*next_action*：等待作者或 Peter 给出「idle 传播」方案实测与语义论证后再定。

## 效果评估
无新量化数据；上一日已确认 `cpu.idle` 用例修复有效（Jakub 实测），nice 19 回退属另一线索，不在本补丁范围。

## 我可以参与的点
- *kind: review*：就「组间抢占是否应尊重 cpu.idle 层级」给出用例与观点。
- *kind: testing*：在多层 cpu.idle cgroup 拓扑下对比 `find_matching_se()` 与 Peter 的传播方案行为差异。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261019182622.1584454-1-vincent.guittot@linaro.org/
- Peter 今日回帖：https://lore.kernel.org/all/20261022114705.GW88198@noisy.programming.kicks-ass.net/
- Josh Don 今日回帖：https://lore.kernel.org/all/CABk29Nv2ZzB1KGEuPmx4VmxTJ6pKmikGMr8cvzzDhHZSKpkgvg@mail.gmail.com/
