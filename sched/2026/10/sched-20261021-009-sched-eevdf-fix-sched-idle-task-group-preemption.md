# sched/eevdf: Fix sched idle task group preemption

## TL;DR
本文为增量更新，完整脉络见下。

- sched-20261020-001：Vincent Guittot 发往 sched 的单补丁修复——EEVDF「单运行队列」改动（`85570f10a4c6`）后，扁平层级把全部 runnable 任务放进同一 cfs_rq，wakeup 抢占时仍需向上遍历 task group 层级才能判断是否存在 sched_idle 任务组，否则 idle 组任务不会被正确抢占。当日 v1→v2 连发，Jakub Okoński 实测修复了其 `cpu.idle` 用例，但指出「同 cgroup 下 nice 19 spinner 相对 7.2.9 仍回退」；作者明确本补丁只覆盖 sched_idle 组场景、nice 19 另行排查。
- sched-20261021-009（今天）：Kayra Cizmeci 走查层级示例后给出 Reviewed-by；但 Peter Zijlstra 对修复依赖的 `cpu.idle` **语义本身**提出质疑——「为什么要在乎这个共同祖先？能否在 `sched_group_set_idle()` 里把 idle 传播到所有子组，或让 `se_is_idle()` 向上走、任一祖先 idle 即算 idle」，并直言「我痛恨 `find_matching_se()`，当初删除它时别提多开心」。Vincent 回应 `cpu.idle` 只作用于一层，Peter 倾向**改变该语义**（把 T{AB} 在 idle 组内的差异也算进来），并请 Google 侧说明 `cpu.idle` 的实际用法。修复方向因此面临是否被语义变更取代的不确定性。

## 背景与问题
（承接 sched-20261020-001）「sched/eevdf: Move to a single runqueue」落地 v7.3 后，Jakub Okoński 报告 `cpu.idle` cgroup 用例的 wakeup 抢占语义被破坏：单运行队列下扁平层级把所有 runnable 任务放进同一 cfs_rq，`wakeup_preempt_fair()` 直接比较 `se_is_idle(se/pse)`，未沿 task group 层级找「共同父级的兄弟实体」，导致 sched_idle 任务组不被正确抢占。今日无新背景补充，焦点从「补丁是否正确」转向「`cpu.idle` 的语义到底该是什么」。

## 技术方案
（承接 sched-20261020-001）修复新增 `find_matching_se()` 把两个 sched_entity 对齐到「共同父级的兄弟实体」层级，再以 `se_is_idle()` 判定，据此决定抢占走向（idle 让位非 idle→RESCHED；非 idle 让位 idle→NONE；两侧同类→原 EEVDF 判定）。今日无新补丁，仅有对方案语义根基的质疑：Peter 提出两条替代——(1) 在 `sched_group_set_idle()` 把 idle 传播给所有子组；(2) 让 `se_is_idle()` 向上遍历、任一祖先 idle 即返回真。二者都会改变现有行为。

## 版本演进与当前进展
*current_version: v2*（无新版本，今日为 v2 评审与语义讨论）。

## Maintainer 意见与讨论焦点
- Kayra Cizmeci（RB）：在 GA idle/GB 非 idle、GC idle/GD 非 idle 的层级示例里走查了 `find_matching_se()` 的上下对齐路径，认为「只改变我们看哪里、不改变对结果的用法」，给出 Reviewed-by。
- Peter Zijlstra（核心分歧）：「我 F'ing 讨厌 cgroups」；质疑为何要关心共同祖先、`cpu.idle` 实际语义是什么；提出传播 idle 或 `se_is_idle()` 向上遍历两条路；并指出「在 T{AB} vs TC 场景下，T{AB} 处于 idle 组内这一点不应被丢掉」——想**改变语义**而非按现有语义修。
- Vincent Guittot：`cpu.idle` 应用于一层、对同层实体起效；两条替代路径都行但都会改变行为。
- Kayra 补充 TB/TA/TC 相对关系，说明现有语义下 idle 只改变组对其兄弟的地位。
- Peter 已把 Josh（`cpu.idle` 原实现者）加入 Cc，请 Google 侧说明实际用法。

## 合入评估
*likelihood=medium*。补丁本身已有 Kayra Reviewed-by，但 Peter 对 `cpu.idle` 语义的质疑动摇了 `find_matching_se()` 这一修复根基——如果采纳「传播 idle / 向上遍历」的语义变更，本补丁可能被取代。*blocking_issues*：`cpu.idle` 语义待澄清（Google/Josh 尚未回应）；nice 19 回退仍待作者另行修复。*next_action*：等 Josh/Google 说明 `cpu.idle` 用法后再定语义与修复方向。

## 效果评估
无新增 benchmark。昨日功能验证结论延续：修复 `cpu.idle` 用例有效，但 nice 19 同 cgroup 场景仍回退。

## 我可以参与的点
- `discussion`：Peter 抛出的 `cpu.idle` 语义问题（传播 vs 向上遍历 vs 维持单层）目前无定论，可结合 cgroup v2 `cpu.idle` 的实际生产用法提供输入，帮收敛语义方向。

## 参考链接
- v2 patch：https://lore.kernel.org/all/20261019182622.1584454-1-vincent.guittot@linaro.org/
- Peter 语义质疑：https://lore.kernel.org/all/20261021131313.GM2823843@noisy.programming.kicks-ass.net/
- Peter 进一步主张改变语义：https://lore.kernel.org/all/20261021145042.GQ2823843@noisy.programming.kicks-ass.net/

---
id: sched-20261021-009
date: 2026-10-21
subject: "sched/eevdf: Fix sched idle task group preemption"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261019182622.1584454-1-vincent.guittot@linaro.org>"
lore_url: "https://lore.kernel.org/all/20261019182622.1584454-1-vincent.guittot@linaro.org/"
authors: ["Vincent Guittot"]
maintainers_involved: ["Vincent Guittot", "Peter Zijlstra"]
current_version: v2
patch_series:
  - version: v2
    msgid: "<20261019182622.1584454-1-vincent.guittot@linaro.org>"
    date: 2026-10-20
    summary: "find_matching_se() 对齐层级 + wakeup_preempt_sched_idle() 三路判定"
    review_outcome: "Kayra RB；Peter 质疑 cpu.idle 语义、倾向改变语义"
upstream_commit: null
fixes_commit: "85570f10a4c6"
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["cpu.idle 语义待澄清（Peter 倾向改变语义）", "nice 19 同 cgroup 回退另行修复"]
  next_action: "等 Josh/Google 说明 cpu.idle 用法后再定语义与修复方向"
contribution_opportunities:
  - kind: discussion
    description: "结合 cgroup v2 cpu.idle 生产用法，输入 Peter 提出的语义问题"
generated_at: "2026-10-22T01:30:00"
source_email_count: 6
related_articles: ["sched-20261020-001"]
tags: [eevdf, cgroup, regression]
---