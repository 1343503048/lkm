# sched/fair: Rework/fix task_h_load()

## TL;DR

Peter Zijlstra 8/28 发的 4 补丁系列中 `4/4` 重做 `task_h_load()`，8/31 当天只剩一处注释措辞的分歧：Vincent Guittot 要求为"两个参数可以为 NULL"补注释并说"rework 我看是好"（测试留到本周），Peter 立刻给出注释稿、Vincent 回 `s/then/when/`，Peter "Just so, typing hard :/" 接受。方向与实现均已无异议，属于接近收口的 cgroup 层级负载计算修复。

## 背景与问题

`task_h_load()` 在负载均衡时计算任务（及其 cfs_rq 所在层级）的**层级负载**，需要沿 cgroup 调度实体层级向上累加。`for_each_sched_entity()` 在遍历过程中会顺带设置 backlink，而有些调用方**不走层级遍历**——`__update_blocked_fair()` 就是遍历 `leaf_cfs_rq_list` 而不是逐级上溯。这类调用方拿不到遍历过程留下的状态，因此被重构的函数必须能接受"没有 backlink"的情形，这正是 `4/4` 里那两个允许为 NULL 的参数的用途。

本日线程中作者没有复述原始缺陷的具体触发路径（补丁本体不在当日缓存中），讨论完全集中在重构后的接口形态上，因此"修的是哪个可观测错误"这一点本日无新增信息。

## 技术方案

- `task_h_load()` 被 rework，签名上多出两个可为 NULL 的参数，用于在调用方**没有**通过 `for_each_sched_entity()` 建立 backlink 时（典型即 `__update_blocked_fair()` 走 `leaf_cfs_rq_list` 的路径）直接传入所需上下文。
- 设计取舍：不在 leaf 路径上补做层级遍历，而是把"层级遍历留下的信息"参数化，由调用方按自身可见的状态提供——代价是接口出现两个语义不自明的可空参数，这正是 Vincent 要求加注释的原因。

Peter 给出的注释稿（可直接当作设计说明读）：

```
/*
 * These last two arguments can be NULL then used outside of
 * the for_each_sched_entity() hierarchy iteration. Like in
 * __update_blocked_fair() where leaf_cfs_rq_list is iterated
 * instead.
 */
```

## 版本演进与当前进展

- 8/28：Peter Zijlstra 发出 4 补丁系列，`4/4` 为 "sched/fair: Rework/fix task_h_load()"（`<20260828075558.660152190@infradead.org>`）。
- 8/31 18:10：Vincent Guittot 提注释意见 + 表态"rework 我看着没问题，但还没跑测试，本周会跑"（`<CAKfTPtBuCgKjj_kM8zwihp7o10vBB7c9rmBtsJ5mVt3YxjXV0g@mail.gmail.com>`）。
- 8/31 18:37：Peter 直接给出注释文本（`<20260831103735.GW687043@noisy.programming.kicks-ass.net>`）。
- 8/31 20:06：Vincent "yes, looks good"，并挑一个语法 `s/then/when/`（`<CAKfTPtB5mpA0yGCwhv0wwdBj9xYWB+k+QL=daAu=qNCcBQexvA@mail.gmail.com>`）。
- 8/31 21:07：Peter "Just so, typing hard :/" 接受（`<20260831130705.GI4120091@noisy.programming.kicks-ass.net>`）。
- 当前版本仍是 v1（作者未重发），讨论已收敛到注释级别。

## Maintainer 意见与讨论焦点

- **Vincent Guittot（linaro，sched/fair 维护者之一）**：唯一实质意见是"应该加一条注释说明下面这两个参数是用在 `for_each_sched_entity` 未被调用、没有设置 backlink 的场景"；对方案本身给的是**有条件认可**——"I haven't run tests yet (I will during the week) but the rework looks good to me"。
- **Peter Zijlstra（作者）**：接受注释要求，接受 `then`→`when` 的措辞修改。
- 未解决问题：Vincent 承诺的测试尚未回帖；线程里没有出现 `Reviewed-by`/`Acked-by`。没有 NAK，也没有对语义正确性的质疑。

## 合入评估

**likely**。补丁出自 sched 核心维护者本人，另一位 sched/fair 维护者当场表示"看着好"，剩下的是注释与拼写级别的来回，且不存在备选方案之争。真正的收口条件是 Vincent 本周的功能/性能测试（负载均衡正确性类改动通常会过 kselftest 与 hackbench 一类回归），以及 `Fixes:` 标签是否需要（当日邮件未提及）。合入前应视作"已定稿待测"。

## 效果评估

暂无效果数据。当日线程内没有任何 benchmark 数字、迁移次数或负载均衡质量对比，全部讨论停留在接口形态与注释层面。Vincent 的"looks good to me"是代码审读判断，他自己明确说了尚未测试。

## 我可以参与的点

- **补上 Vincent 说要跑的那类测试**：cgroup 层级（多层组 + 权重差异）下的 load balance 正确性/性能回归，若发现异常直接回帖，这是该系列目前唯一缺的环节。
- **确认是否要 `Fixes:` 标签**：邮件里没写这是修哪个 commit 引入的问题；如果能在 6.6/6.12 一类长期分支上验证同一缺陷是否存在，对回合判断（以及是否该进 `sched/urgent`）有直接价值。
- **审阅系列另外 3 个补丁**：当日讨论只覆盖 `4/4`，其余补丁没被任何人提及。

## 参考链接

- lore thread（4/4 原始邮件）: https://lore.kernel.org/all/20260828075558.660152190@infradead.org/
- 本日讨论起点（Vincent Guittot）: https://lore.kernel.org/all/CAKfTPtBuCgKjj_kM8zwihp7o10vBB7c9rmBtsJ5mVt3YxjXV0g@mail.gmail.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260831-003
date: '2026-08-31'
subject: "sched/fair: Rework/fix task_h_load()"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20260828075558.660152190@infradead.org>"
lore_url: "https://lore.kernel.org/all/CAKfTPtBuCgKjj_kM8zwihp7o10vBB7c9rmBtsJ5mVt3YxjXV0g@mail.gmail.com/"
authors: [Peter Zijlstra, Vincent Guittot]
maintainers_involved: [Vincent Guittot, Peter Zijlstra]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260828075558.660152190@infradead.org>"
    date: 2026-08-28
    summary: "rework task_h_load()，为不走 for_each_sched_entity() 层级遍历的调用方（__update_blocked_fair()/leaf_cfs_rq_list）提供两个可空参数"
    review_outcome: "Vincent Guittot 要求补注释并表态方案 looks good（测试待做）；仅剩 then/when 措辞修正"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - "Vincent Guittot 承诺的功能/性能测试尚未回帖"
    - "线程内无 Reviewed-by/Acked-by，也未讨论是否需要 Fixes 标签"
  next_action: "Vincent 本周完成测试并回帖；必要时补 Fixes 标签"
contribution_opportunities:
  - kind: testing
    description: "在多层层级 cgroup + 权重差异场景跑 load balance 回归，补上目前唯一缺失的验证环节"
  - kind: review
    description: "确认该修复在长期分支上是否存在同样缺陷、是否应带 Fixes 标签进 sched/urgent"
generated_at: "2026-09-07T21:16:22"
source_email_count: 4
related_articles: []
tags: [cgroup, load_balance, cfs]
---
