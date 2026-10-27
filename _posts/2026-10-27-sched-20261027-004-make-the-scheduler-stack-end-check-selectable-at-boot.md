---
id: sched-20261027-004
date: 2026-10-27
subject: Make the scheduler stack end check selectable at boot
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <cover.1793082868.git.chris@chrisdown.name>
lore_url: https://lore.kernel.org/all/cover.1793082868.git.chris@chrisdown.name/
authors:
- Chris Down
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <cover.1793082868.git.chris@chrisdown.name>
  date: 2026-10-27
  summary: sched_stack_end_check= boot 参数 + SCS 关闭时跳过 shadow stack 检查 + lkdtm 自测
  review_outcome: Peter 建议 scs_is_enabled 下沉、开关应覆盖全部调用点
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 开关是否覆盖全部 task_stack_end_corrupted() 调用点
  - task_scs_end_corrupted() 是否内联进 task_stack_end_corrupted()
  next_action: 作者按 Peter 意见重构后发 v2
contribution_opportunities:
- kind: review
  description: 核对 task_stack_end_corrupted() 全量调用点中哪些应受开关控制
- kind: testing
  description: 验证开关与 SCS 组合下的 lkdtm CORRUPT_STACK_END 行为
generated_at: '2026-10-28T09:00:00'
source_email_count: 3
related_articles: []
tags: []
title: Make the scheduler stack end check selectable at boot
layout: article
---

## TL;DR
Chris Down（Meta）发 3 补丁系列，把 `CONFIG_SCHED_STACK_END_CHECK` 的栈尾检查从「仅编译期」改为「可用 `sched_stack_end_check=` 在 boot 时开关」，让一组机器共享同一内核镜像；附赠一个 SCS 关闭时跳过 shadow stack 检查的清理补丁，和一个 lkdtm 自测。Peter Zijlstra 当日 review，建议把 `scs_is_enabled()` 下沉、并让其它 `task_stack_end_corrupted()` 调用点也尊重该开关。

## 背景与问题
Meta 的部分 host 类型开启了 `CONFIG_SCHED_STACK_END_CHECK`（每次上下文切换多查一次栈尾），但不想全量开启。目前只能编译期二选一，导致这些 host 需要单独内核镜像。Chris Down 希望做到 boot 时可选，从而共享镜像。

## 技术方案
3 补丁（kernel/sched/core.c、lkdtm、文档 +57/−6）：
1. **sched/core: Skip the shadow stack end check when SCS is disabled**：SCS 未启用时跳过 shadow stack 尾检查（顺手清理）。
2. **sched/core: Add sched_stack_end_check= boot parameter**：新增 boot 参数控制栈尾检查。
3. **lkdtm/bugs: Add CORRUPT_STACK_END**：往 lkdtm 加一个破坏栈尾的自测以验证检查生效。

## 版本演进与当前进展
*current_version: v1*（`<cover.1793082868.git.chris@chrisdown.name>`），当日新发，Peter 已 review。

## Maintainer 意见与讨论焦点
Peter Zijlstra 两点意见：
- 建议把 `scs_is_enabled()` 下沉到 `task_scs_end_corrupted()` 内部，减少噪音、也让下一补丁更干净。
- 注意到还有若干 `task_stack_end_corrupted()` 调用点没有同步做 `task_scs_end_corrupted()`；应考虑把 shadow stack 检查并入 `task_stack_end_corrupted()` 以保证总是成对执行，并让这些调用点也尊重 `sched_stack_end_check=` 开关（「只让这一个点受控看起来怪」）。

## 合入评估
*likelihood=medium*。方向无异议、改动小，但 Peter 要求把开关作用面与 shadow stack 检查的一致性理清。*blocking_issues*：开关是否覆盖全部 `task_stack_end_corrupted()` 调用点、`task_scs_end_corrupted()` 是否应内联进 `task_stack_end_corrupted()`。*next_action*：作者按 Peter 意见重构后发 v2。

## 效果评估
无性能/功能数据。属可调测性与代码清理改进。

## 我可以参与的点
- *kind: review*：核对 `task_stack_end_corrupted()` 全量调用点，评估哪几处应受 `sched_stack_end_check=` 控制。
- *kind: testing*：在开启/关闭 `sched_stack_end_check=` 与 SCS 的组合下验证 lkdtm `CORRUPT_STACK_END` 行为。

## 参考链接
- patch 0/3: https://lore.kernel.org/all/cover.1793082868.git.chris@chrisdown.name/
