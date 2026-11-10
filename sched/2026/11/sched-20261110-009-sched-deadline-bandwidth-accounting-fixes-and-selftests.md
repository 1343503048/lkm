# sched/deadline: bandwidth accounting fixes and selftests

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261105-001：Mathieu Desnoyers 的 v2 系列（21 补丁）在 Juri Lelli 此前 4 个 sched/urgent 修复之上再修 17 个 SCHED_DEADLINE 带宽记账 bug（其中 3 个可直接打死内核），带自测与 sched_debug。Juri 已对多数补丁给 Reviewed-by/Acked-by，Marek Szyprowski 实测修复了 CPU hotplug 崩溃并给 Tested-by；Ingo 要求「严格只含 -stable 可回退修复的子集」。
- sched-20261106-001：v3 发出，扩到 24 补丁，把 Juri 被 Ingo 丢弃的 4 个 sched/urgent 修复全部吸收，新增 patch 5/7/13/16 四个新修复。
- sched-20261107-002：v4 发出，扩到 26 补丁（22 修复 + sched_debug + 3 自测），新增 replenishment timer 跨 class 往返残留与 boosted 任务设 SCHED_DEADLINE 缺账两个修复。
- sched-20261108-003：作者逐条回应 sashiko-bot 对 9 个补丁的评审，并密集披露 v5 计划。
- sched-20261109-001：v5 发出（29 补丁，25 修复 + sched_debug + 3 自测）。Juri 当日评审 patch 03/04/06 并给 Reviewed-by，Mathieu 承诺下一版采纳注释意见并补 `unlikely()`。
- sched-20261110-009（今天）：**Juri 进一步评审 patch 07/08/09**——07 与 09 给 Acked-by（07「take it，re-entry 边角另案处理」、09「nit 后 Ack」）；08（deadline boost 从 waiter's rt_mutex node 取参数）Juri 明确表示「不确定想要这套额外机制」，给出两个更简单的 bandaid 备选。Mathieu 逐条回应 08 的机制必要性，并披露 v6 计划：新增 patch 28/29 修「0-lag 前带新参数返回」的既定缺陷（Fixes `a649f237db18`/`40767b0dc768`）+ 3 个 `deadline_bw_test` 用例。

## 背景与问题

（承接 sched-20261105-001 / 20261106-001 / 20261107-002 / 20261108-003 / 20261109-001）Juri Lelli 前一轮 4 个 SCHED_DEADLINE 带宽记账修复被 Ingo 从 tip/sched/urgent 移除，Mathieu Desnoyers 系统梳理 dl_bw/total_bw/this_bw 记账边界缺陷，按 Ingo「修复在前、stable 可截取」推到 v5（29 补丁）。今日评审焦点从「记账修复」转向「deadline boost / 参数复位」这组带 PI 纠缠的补丁（patch 07/08/09），它们正是最容易出 hang 的那部分。

## 技术方案

今日围绕三个补丁：

- **07/29 `Do not lose a throttled task switched out and back`**：Juri Ack（「still fixes the hang，v2 意见仍算数：take it，re-entry 边角另案处理」）。
- **08/29 `Take a deadline boost from the waiter's rt_mutex node`**：Juri 不确信要这套机制（「PI with DEADLINE 本来就是坏的，这又加一个坏点；hang 是真的，但要更简单的 stop-gap 直到 proxy execution 修好」），给两个 bandaid 备选：① 不清除 blocked waiter 的参数（用 `p->pi_blocked_on` 守卫 `__dl_clear_params()` 调用，带宽释放照旧在 0-lag 时刻、只把参数 wipe 推迟到任务不再 blocked）；② `replenish_dl_entity()` 对 `pi_of(dl_se)->dl_runtime <= 0` 的 WARN 改为直接 bail（deboost 已在飞行中、释放 rq lock 打断死循环、owner 限流到 walk 落地再退回 fair）。Mathieu 回应：deadline boost 本是临时方案、他的补丁让 donor 参数副本正确、代价在 stable；并指出 Juri 的两个问题——`__dl_clear_params()` 也会清 `dl_non_contending`（timer 路径 `switched_from_dl()` 已移除 running_bw 但 flag 留着，跳过整个 clear 会让任务回来时 `task_contending()` 看到 flag 不加 running_bw、之后 underflow）；wipe 必须发生在 `pi_blocked_on` 回到 NULL 之后（`remove_waiter()` 在 deboost owner 之前就清掉了它，所以 wipe 得排在 `rt_mutex_adjust_prio()` 之后，否则 hang 复现），倾向把 deadline 代码与 pending flag 放进 rtmutex slow path。
- **09/29 `Reset the deadline and the runtime with the parameters`**：Juri nit（更新函数注释以说明现在也清动态参数）后 Ack；Mathieu 确认 v6 会在注释里写明「也复位 deadline 与 runtime」。

此外 Mathieu 披露：Juri 指出的「0-lag 前带不同参数返回」场景是真实且比本系列更老的问题（v7.4-rc1 上 50ms/100ms 任务经 SCHED_OTHER 以 10ms 回来，接着跑了下一 100ms 的 39ms）；v6 计划在 patch 27 后追加 patch 28（runnable 入类走 wakeup 规则 `update_dl_entity()`，Fixes `a649f237db18`）与 patch 29（`sched_setattr()` 改 runtime/deadline/period 后同处理，`__setparam_dl()` 置 `dl_new_params` 位，Fixes `40767b0dc768`），并补 3 个 `deadline_bw_test` 用例（`return_running_new_params`/`change_running_new_params` 在 v7.4-rc1 上失败、修复后通过；`return_asleep_new_params` 恒过）。

## 版本演进与当前进展

*current_version: v5（2026-11-09 发出，`<20261108185406.1549770-1-mathieu.desnoyers@efficios.com>`）*。今日仍为评审日、无新版本：Juri 对 07/09 给 Ack、对 08 表达机制存疑并给备选；Mathieu 逐条回应并披露 v6 计划（新增 28/29 + 3 自测）。v6 尚未发出。

## Maintainer 意见与讨论焦点

- **Juri Lelli（sched/deadline 维护者）**：07/09 明确 Ack；08 是今日唯一实质分歧——认为「deadline boost 取 waiter rt_mutex 节点参数」这套额外机制不必现在上，可用更简单的 bandaid 顶到 proxy execution 落地。给出了具体代码方案（pi_blocked_on 守卫 / replenish bail）。
- **Mathieu Desnoyers（作者）**：主张 08 的机制虽有代价但把 donor 参数副本做正确，并指出前者在于 `__dl_clear_params()` 清 `dl_non_contending` 的 underflow 风险与 wipe 时序必须在 `rt_mutex_adjust_prio()` 之后。双方对 08 的分歧是「机制复杂度 vs 更简单 bandaid」的取舍，尚未消解。
- 无 NAK；07/09 已收敛，08 待作者改或维护者选择 bandaid 路线。

## 合入评估

*likelihood=high*。Juri 已 Ack 多个补丁、Ingo「修复在前」框架已被遵守，`sched:debug` 部分甚至已进 tip/sched/core HEAD（kernel test robot 当日 BUILD SUCCESS 显示 tip/sched:core HEAD 为 `sched/debug: Protect lockless rq->rd access in print_dl_rq()`）。*blocking_issues*：① patch 08 走「完整机制」还是「bandaid」待定；② 「0-lag 前带新参数返回」已由作者计划在 v6 patch 28/29 修、但需评审。*next_action*：作者出 v6（09 注释 + 07/09 收尾 + 08 路线选择 + 28/29 与 3 自测）。

## 效果评估

今日无新增性能数据。价值在正确性：修 hang、underflow、缺账等（尤其 08 涉及的 PI+DEADLINE hang），cover 未给 benchmark。

## 我可以参与的点

- **review**：就 08 的「完整机制 vs Juri 的两个 bandaid」给出判断（这是当日唯一未消解的设计分歧，Juri 给了具体伪代码，可对照评估）。
- **testing**：复跑 `deadline_bw_test` 现有用例 + 作者预告的 `return_running_new_params`/`change_running_new_params`（v6 发布后），并验证 08 相关 PI+DEADLINE 场景不再 hang。

## 参考链接

- lore thread（v5 cover）: https://lore.kernel.org/all/20261108185406.1549770-1-mathieu.desnoyers@efficios.com/
- Juri 对 07 的 Ack: https://lore.kernel.org/all/avHvPjz4dL0zNyGb@jlelli-thinkpadt14gen4.remote.csb/
- Juri 对 08 的存疑与 bandaid: https://lore.kernel.org/all/avL8oOtjKqVNR7-l@jlelli-thinkpadt14gen4.remote.csb/
- Mathieu 对 08 的回应: https://lore.kernel.org/all/f3fafadf-0829-455d-ad85-ca6c46404f35@efficios.com/

---
id: sched-20261110-009
date: '2026-11-10'
subject: "sched/deadline: bandwidth accounting fixes and selftests"
subsystem: sched
type: fix
status: under_review
severity: critical
thread_root_msgid: "<f3fafadf-0829-455d-ad85-ca6c46404f35@efficios.com>"
lore_url: "https://lore.kernel.org/all/f3fafadf-0829-455d-ad85-ca6c46404f35@efficios.com/"
authors: [Mathieu Desnoyers]
maintainers_involved: [Juri Lelli]
current_version: v5
patch_series:
  - version: v5
    msgid: "<20261108185406.1549770-1-mathieu.desnoyers@efficios.com>"
    date: '2026-11-09'
    summary: "29 补丁：25 修复 + sched_debug + 3 自测，stable 可截取 1-25"
    review_outcome: "Juri Ack 07/09；对 08 给机制存疑与两个 bandaid 备选"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - "patch 08 走完整机制还是 bandaid 待定"
  next_action: "作者出 v6（09 注释 + 07/09 收尾 + 08 路线 + 28/29 与 3 自测）"
contribution_opportunities:
  - kind: review
    description: "就 08 的完整机制 vs Juri 两个 bandaid 给出判断（有具体伪代码可评）"
  - kind: testing
    description: "复跑 deadline_bw_test 及 v6 新增 return/change_running_new_params 用例"
generated_at: "2026-11-11T09:00:00+08:00"
source_email_count: 8
related_articles: [sched-20261105-001, sched-20261106-001, sched-20261107-002, sched-20261108-003, sched-20261109-001]
tags: [deadline, dl_server, cgroup]
---