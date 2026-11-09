# sched: core-sched fixes and balancing

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261107-001：Peter Zijlstra 的 v2 系列（12 补丁）发出，核心是 rq_clock/rq_lock 语义整体重做——cover 明说「主差异是 rq_clock 的重做，因为 TJ（Tejun Heo）指出上一版把它彻底搞错了」。新增 `rq_drop_lock()`、分解 `update_rq_clock()`、引入 `RQCF_NOP_MASK` 让已 UPDATED 的 rq 跳过重复更新，取代 v1 靠 `core_clock_updated` 布尔量猜时钟的绕路逻辑。
- sched-20261108-005：Kayra Cizmeci 评审 patch 02/12（`Introduce rq_drop_lock()`）并给 Reviewed-by（仅一处拼写 nit）。
- sched-20261109-007（今天）：**Kayra 评审 patch 05/12（`Abstract/fix rq_clock_start_loop_update()`）并发现类型 bug**——`rq_clock_freeze()` 返回 `unsigned int` 而 `rq_clock_thaw()` 形参是 `bool`，导致 `flags & RQCF_FREEZE` 恒为 false；且 `double_rq_clock_clear_update()` 会误清 RQCF_FREEZE。

## 背景与问题

（承接 sched-20261107-001 / 20261108-005）Peter 处理 core scheduling 三类问题的 v2 系列（12 补丁）：`pick_next_task()` 自重入、core-sched 下 newidle balance 被整条关掉、`sched_class::balance()` 与 `pick_task()` 职责重叠。v2 的核心变化是 rq_clock/rq_lock 语义整体重做（Tejun 指出 v1 的 rq_clock 方向错了）。今日进入 patch 05 的评审。

## 技术方案

今日评审 patch 05（`Abstract/fix rq_clock_start_loop_update()`）——抽离 rq_clock 循环更新的入口并修正语义。Kayra 在评审中发现两处类型/位操作缺陷：

- `rq_clock_freeze()` 返回 `unsigned int`，但 `rq_clock_thaw(struct rq *rq, bool flags)` 的 `flags` 是 `bool`：`rq->clock_update_flags |= RQCF_UPDATED | (flags & RQCF_FREEZE)` 里 `flags & RQCF_FREEZE` 恒为 false（bool 只有 0/1，与 RQCF_FREEZE 位 4 相与永远为 0），thaw 时无法保留 FREEZE 位。
- `double_rq_clock_clear_update()` 用 `&= (RQCF_REQ_SKIP|RQCF_ACT_SKIP)` 清位，会顺带清掉 `RQCF_FREEZE`（若 freeze 位是 freezable 状态，这会误清）。

## 版本演进与当前进展

*current_version: v2（2026-11-07 发出，12 补丁）*。今日：Kayra 评审 patch 05 并提交两处类型 bug（`bool` vs `unsigned int`、`double_rq_clock_clear_update()` 误清 FREEZE 位）。尚未见 Peter 回应。

## Maintainer 意见与讨论焦点

- **Kayra Cizmeci**：评审趣味性高（自嘲「这补丁真的很好玩」），但明确点了两处实质缺陷——① `rq_clock_thaw()` 的 `flags` 应为 `unsigned int` 而非 `bool`；② `double_rq_clock_clear_update()` 会误清 RQCF_FREEZE。均属需要作者修正的问题。
- 无 NAK。整体方向（rq_clock 重做）仍待 Tejun Heo 这一关，尚未表态。

## 合入评估

*likelihood=medium*。系列评审已启动（Kayra 逐 patch 推进），但 rq_clock 重做（patch 02-07）尚在收 bug，且需 Tejun 认可 v2 的方向修正。*blocking_issues*：① patch 05 的类型/位操作缺陷待修；② rq_clock 重做整体待 Tejun 确认。*next_action*：Peter 修 patch 05 的 `bool`/位清问题后出 v3，或先由 Tejun 审 rq_clock 重做部分。

## 效果评估

无量化性能数据，属正确性/并发语义重构（core-sched 与 rq_clock 记账）。Kayra 的发现是静态审码得出，无运行时影响数据。

## 我可以参与的点

- **review**：审查 patch 06-12（`New rq_{pin,drop,repin,unpin}_lock()` 语义、`Simplify/fix time updates`、`Allow newidle for core-sched` 等）——这些尚未有人逐条评审。
- **testing**：在 core-sched（超线程隔离）环境跑 v2 系列，验证 rq_clock 重做后无 WARN_DOUBLE_CLOCK、newidle balance 恢复。

## 参考链接

- Kayra 对 patch 05 的评审: https://lore.kernel.org/all/avBDWS-AY6QQtCuH@scheduler.schedules/

---
id: sched-20261109-007
date: '2026-11-09'
subject: "sched: core-sched fixes and balancing"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<avBDWS-AY6QQtCuH@scheduler.schedules>"
lore_url: "https://lore.kernel.org/all/avBDWS-AY6QQtCuH@scheduler.schedules/"
authors: [Peter Zijlstra]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v2
    msgid: "<20261107120207.242460109@infradead.org>"
    date: '2026-11-07'
    summary: "12 补丁：rq_clock/rq_lock 语义重做 + core-sched newidle balance 修复"
    review_outcome: "Kayra 对 02 给 Reviewed-by，对 05 提类型/位操作缺陷"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "patch 05 的 bool/位清缺陷待修"
    - "rq_clock 重做整体待 Tejun 确认"
  next_action: "Peter 修 patch 05 后出 v3 或先由 Tejun 审 rq_clock 部分"
contribution_opportunities:
  - kind: review
    description: "审查 patch 06-12（rq_lock 语义、time updates、newidle for core-sched）"
  - kind: testing
    description: "在 core-sched 环境验证 rq_clock 重做后无 WARN_DOUBLE_CLOCK"
generated_at: "2026-11-10T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261107-001, sched-20261108-005]
tags: [core_sched, sched_clock, preempt]
---
