---
id: sched-20260910-002
date: 2026-09-10
subject: 'sched: Make proxy execution compatible with sched_ext'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260831134338.1531664-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260831134338.1531664-1-arighi@nvidia.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v13
generated_at: '2026-09-11T09:50:00'
authors:
- Andrea Righi
maintainers_involved:
- Peter Zijlstra
patch_series:
- version: v13
  msgid: <20260831134338.1531664-1-arighi@nvidia.com>
  date: '2026-08-31'
  summary: 18 补丁解除 CONFIG_SCHED_PROXY_EXEC 与 !SCHED_CLASS_EXT 的互斥：sched_ext 全面改用 rq->donor
    记账，引入 SCX_OPS_ENQ_BLOCKED 与准入委托，最后删除 Kconfig 互斥。09-10 收到 Peter Zijlstra 对 03/04/05/07/08/09/14/15
    共 10 条正式评审意见。
  review_outcome: Peter 给出 09/18（switching_to_scx 内 gate 调用 sched_proxy_block_task）与
    15/18（inline + scx_enabled、准入总是执行）的具体改法；质疑 03/18 FAIR donor+RT curr、05/18 类不变假设、14/18
    组合 3/4 的前提不成立；08/18 WF_ON_RQ 被要求说清到底要区分什么；04/18 需解释主线为何未触发该警告。
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 08/18 WF_ON_RQ 的语义被 Peter 指出与 wakeup_preempt() 的既有约束矛盾，需重新论证或撤回
  - 09/18 在每次调度类转换都调用 sched_proxy_block_task 且未被 scx_allow_proxy_exec() gate，被明确要求重构
  - 03/18、14/18 的若干前提场景被指按 pick 优先级不可能发生，补丁需相应收敛
  - 04/18 修复的必要性取决于能否解释主线为何从未触发该 false migration warning
  next_action: 作者按 Peter 的逐条意见出 v14（含 switching_to_scx gate 方案与 15/18 inline 化），继续走
    sched_ext/for-7.4
contribution_opportunities:
- kind: testing
  description: 在开启 CONFIG_SCHED_PROXY_EXEC 的环境按 Peter 的 switching_to_scx() 建议试改 09/18，验证
    ext 相关类转换路径的 donor 阻塞行为并回报列表
- kind: review
  description: 梳理 wakeup_preempt()/move_queued_task()/ttwu 的调用矩阵，帮助回答 WF_ON_RQ 到底需要区分什么
- kind: extend
  description: sched_ext BPF 调度器作者可预研 14/18 donor/curr 引用拆分语义对自家调度器记账的影响，准备 v14 落地后的适配
source_email_count: 10
related_articles:
- sched-20260908-003
- sched-20260904-007
- sched-20260831-001
tags:
- sched_ext
- preempt
- proxy_execution
title: 'sched: Make proxy execution compatible with sched_ext'
layout: article
---

## TL;DR
本文为增量更新，完整背景见 related_articles 中的 sched-20260908-003 / sched-20260904-007 / sched-20260831-001。09-10 是 Peter Zijlstra 对 18 补丁 v13 系列承诺的正式评审落地的一天：他在 03、04、05、07、08、09、14、15 共 8 个补丁上留下 10 条意见，其中 08/18（WF_ON_RQ）与 09/18（跨调度类转换阻塞 donor）的设计被直接质疑，03/18、14/18 的前提被指「不可能发生」，但 15/18 他给出了明确可接受的改法。v14 的工作量已经清晰。

## 背景与问题
代理执行把调度上下文（`rq->donor`）与执行上下文（`rq->curr`）拆开以缓解优先级反转；本系列（PATCHSET v13 sched_ext/for-7.4）目标是解除 `CONFIG_SCHED_PROXY_EXEC` 对 `!SCHED_CLASS_EXT` 的依赖，让 BPF 调度器全面接管 donor/curr 拆分后的策略与记账。09-08 时技术争议面已基本清零，瓶颈只剩 Peter 的正式评审——本日评审到达。

## 技术方案
本日无新版本代码，全部是 Peter 对既有 v13 补丁的设计反馈（按补丁归纳）：

- **03/18（NOHZ CFS bandwidth checks follow proxy donor）**：Peter 质疑补丁假设的场景本身不成立——"how can we ever have rq->donor be FAIR and rq->curr be RT? That makes no sense. If an RT task is runnable, pick should just straight up pick that." 并要求把所有 proxy 特有逻辑收进上方单一的 `sched_proxy_exec()` 分支。
- **04/18（Avoid false migration warning for proxy donors）**："I'm not sure why we're not hitting this upstream?"——即如果该警告是真实问题，为什么主线没有触发过，需要解释。
- **05/18（Pass next class to sched_change_begin()）**：针对补丁里「类不会变」的假设，Peter 反问 "Uh, yes it can. That's what {EN,DE}QUEUE_CLASS are for, no?"。
- **07/18（sched_ext hooks for proxy execution）**：三个 hook 里他理解另外两个，要求展开说明 `scx_proxy_resolved()` 的必要性。
- **08/18（WF_ON_RQ wake flag）**：Peter 表示困惑——`wakeup_preempt()` 只会被调用在已在 runqueue 上的任务，这正是 wake-preemption 的意义；连 already-runnable 的区分都成立的话，`move_queued_task()` 之类也该带上这个 flag。"What actual distinction are you needing?"
- **09/18（Block proxy donors across scheduler transitions）**：判定补丁中 DEQUEUE_CLASS 条件是同义反复（有 DEQUEUE_CLASS 就意味着 next_class != ->sched_class）；明确表示不喜欢现状："We most certainly don't want to do this on every sched class change. It isn't even gated by scx_allow_proxy_exec()." 他期望 `sched_proxy_block_task()` 在加载 ext 调度器的「大切换」函数（scx_root_enable_ 之类）里被调用，并在第二封邮件中给出具体改法：`switching_to_scx()` 中 `if (!scx_allow_proxy_exec(p)) sched_proxy_block_task(rq, p);`。
- **14/18（Split curr|donor references properly）**：作者穷举的 donor/curr 组合里，"I don't see how 3,4 can happen. If there is a runnable FAIR task, then pick will pick that directly."——按 pick 优先级，donor class 必须始终高于 owner class，两个组合应删掉。
- **15/18（Delegate proxy donor admission to BPF schedulers）**：两条具体改法——入口封装成带 `scx_enabled()` 判断的 inline；并参照另一处的写法 "Just have it be always instead of for ext-ext only"（准入检查应总是执行，而不是只在 ext→ext 场景）。

## 版本演进与当前进展
current_version: v13（2026-08-31 发出，msgid `<20260831134338.1531664-1-arighi@nvidia.com>`）。09-08 作者集中回应了 Prateek/Tejun/Richard 的遗留意见；09-10 Peter 的正式评审到达，v13 尚未有作者对这些意见的公开回应（当天 Andrea 在另一线程对 Hui Su 表示两个系列「很快会兼容」，见 sched-20260910-003）。v14 需要落实：03/18 收敛进 sched_proxy_exec() 分支并论证 FAIR donor + RT curr 场景是否真实存在、04/18 解释主线为何未触发、05/18 处理 {EN,DE}QUEUE_CLASS 引起的类变化、07/18 说明 scx_proxy_resolved()、08/18 重新定义 WF_ON_RQ 想表达的区分（或撤回）、09/18 按 Peter 给出的 switching_to_scx() 方案重构、14/18 删除组合 3/4、15/18 inline 化并改为总是检查。

## Maintainer 意见与讨论焦点
Peter Zijlstra 一人留下全部 10 条意见，性质分三档：
- 直接可执行的改法：09/18（switching_to_scx 内 gate 后调用）、15/18（inline + always）、03/18（收进单一分支）。
- 前提性质疑（补丁假设的场景可能不存在）：03/18 的 FAIR donor + RT curr、05/18 的「类不会变」、14/18 的组合 3/4、04/18 的「主线为何没踩到」。
- 要求作者解释动机：07/18 的 scx_proxy_resolved()、08/18 的 WF_ON_RQ 到底想区分什么。
分歧焦点在 08/18 与 09/18：两者都是 Peter 明确表示不喜欢/困惑的设计，作者需要在 v14 里给出实质性重构而不只是辩护。没有出现 NAK 整个系列的信号——评审细到给出具体代码建议，说明方向被接受。

## 合入评估
likelihood: medium（较 09-08 的评估持平略降：评审落地暴露出 8 个补丁需要修改，但全部意见都是可操作的，且 Peter 给出了 09/18、15/18 的具体改法）。blocking_issues：08/18 WF_ON_RQ 的语义站不住，需要重新论证或撤回；09/18 必须重构为只在切入 scx 时 gate 调用；03/18、14/18 中「不可能发生」的场景需要从补丁前提中移除；04/18 需要解释主线未触发的原因，否则该修复的必要性存疑。next_action：作者按上述清单出 v14，仍走 sched_ext/for-7.4（Tejun 树），由 Peter 复核后收取。

## 效果评估
本日邮件均为设计评审，无新的 benchmark 或复现数据。暂无效果数据。

## 我可以参与的点
- 在自己维护的开启 CONFIG_SCHED_PROXY_EXEC 的分支上，按 Peter 的 switching_to_scx() 建议预先试改 09/18 并验证 ext→ext、FAIR→ext 转换路径的 donor 阻塞行为，把结果带到列表（testing）。
- 08/18 的 WF_ON_RQ：梳理 wakeup_preempt()/move_queued_task()/ttwu 路径中「已在 rq」与「新到 rq」的实际调用矩阵，帮助回答 Peter 的 "what actual distinction are you needing"（review）。
- 关注 v14 发出后 14/18 组合穷举的更新——做 sched_ext BPF 调度器的话，donor/curr 引用拆分语义直接影响自家调度器的记账实现（extend）。

## 参考链接
- lore thread（v13 封面）: https://lore.kernel.org/all/20260831134338.1531664-1-arighi@nvidia.com/
- Peter 对 09/18 的改法建议: https://lore.kernel.org/all/20260910114158.GS788244@noisy.programming.kicks-ass.net/
- Peter 对 08/18 的质疑: https://lore.kernel.org/all/20260910104528.GI4120091@noisy.programming.kicks-ass.net/
- Peter 对 15/18 的两条意见: https://lore.kernel.org/all/20260910133900.GT776954@noisy.programming.kicks-ass.net/ 、 https://lore.kernel.org/all/20260910134142.GU776954@noisy.programming.kicks-ass.net/
- Peter 对 03/18 的质疑: https://lore.kernel.org/all/20260910095448.GE4120091@noisy.programming.kicks-ass.net/
