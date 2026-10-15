---
id: sched-20261015-007
date: 2026-10-15
subject: 'sched/idle: Destroy on-stack hrtimer in play_idle_precise()'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261015025029.3356060-1-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20261015025029.3356060-1-sh_def@163.com/
authors:
- Hui Su
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <20261015025029.3356060-1-sh_def@163.com>
  date: 2026-10-15
  summary: play_idle_precise() 补 destroy_hrtimer_on_stack() 配对
  review_outcome: K Prateek Nayak R-B/T-B；Peter 倾向 __cleanup() 重构
upstream_commit: null
fixes_commit: c1de45ca831a
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Peter Zijlstra 倾向用 __cleanup() 重构接口而非点修复
  next_action: 探索 __cleanup() 风格的生命周期封装，回应 Peter 的接口意见
contribution_opportunities:
- kind: new_patch
  description: 实现 __cleanup() 风格的 on-stack hrtimer 生命周期封装替换手动配对
- kind: review
  description: 评估 hrtimer_setup_on_stack() 注释缺失是否应一并补文档
generated_at: '2026-10-16T01:05:00'
source_email_count: 3
related_articles: []
tags:
- idle
title: 'sched/idle: Destroy on-stack hrtimer in play_idle_precise()'
layout: article
---

## TL;DR
Hui Su 修 `play_idle_precise()` 的 on-stack hrtimer 生命周期：`it.timer` 用 `hrtimer_setup_on_stack()` 初始化，但函数返回前未调 `destroy_hrtimer_on_stack()`，在 `CONFIG_DEBUG_OBJECTS_TIMERS` 下会残留已注册的 on-stack debug 对象。补丁在 expiry 循环后补一次销毁。K Prateek Nayak 给 `Reviewed-by` + `Tested-by`；但 Peter Zijlstra 不喜欢这个修法，倾向用 `__cleanup()` 做更优雅的接口。带 `Fixes: c1de45ca831a ("sched/idle: Add support for tasks that inject idle")`。

## 背景与问题
`play_idle_precise()` 里 `it.timer` 经 `hrtimer_setup_on_stack()` 初始化。该函数在 `CONFIG_DEBUG_OBJECTS_TIMERS` 下会把 timer 注册为 on-stack debug 对象，而这类对象必须在「分配它的函数」离开前移除。`play_idle_precise()` 只初始化、不销毁，栈对象 out of scope 后残留 debug 对象，触发 debug 检查警告。

## 技术方案
单补丁（kernel/sched/idle.c，+1）：在 `while (!READ_ONCE(it.done)) do_idle();` 之后补 `destroy_hrtimer_on_stack(&it.timer);`，与 `hrtimer_setup_on_stack()` 配对。

## 版本演进与当前进展
v1 刚发出（<20261015025029.3356060-1-sh_def@163.com>）。当日 K Prateek Nayak 给 `Reviewed-by` 与 `Tested-by`（附带一个换行位置的 nit，不需重发）。

## Maintainer 意见与讨论焦点
Peter Zijlstra 明确「hating on this」：
- `hrtimer_setup_on_stack()` 自身注释没提 `destroy_hrtimer_on_stack()`，调用者无从得知该销毁；
- 内核已有 `__cleanup()`，可以做对的事情、把生命周期管理做成更好的接口。

即维护者不反对「要修」，但反对「原来的 API 设计 + 这处打补丁式修复」，倾向重构出更不易误用的接口。K Prateek 则认可当前最小修复。

## 合入评估
*likelihood=medium*。有 reviewer 的 R-B/T-B，但维护者（Peter）明确表达对修法的不满，可能要改方向。*blocking_issues*：Peter 倾向用 `__cleanup()` 重构 on-stack hrtimer 接口，而非点修复。*next_action*：作者或社区探索 `__cleanup()` 风格的生命周期封装，回应 Peter 的接口意见。

## 效果评估
作者在 x86_64 候选树上验证 hrtimer setup/free oracle PASS（127/127、129/129）与 bzImage/modules 构建 PASS。无性能数据，属生命周期/调试正确性修复。

## 我可以参与的点
- *new_patch*：按 Peter 方向实现 `__cleanup()` 风格的 on-stack hrtimer 生命周期封装，替换现有 `hrtimer_setup_on_stack()` 的手动配对。
- *review*：审视 `hrtimer_setup_on_stack()` 注释缺失问题，评估是否应一并补文档。

## 参考链接
- patch：https://lore.kernel.org/all/20261015025029.3356060-1-sh_def@163.com/
- Peter 的意见：https://lore.kernel.org/all/20261015070233.GG4121339@noisy.programming.kicks-ass.net/
- K Prateek Nayak 的 R-B/T-B：https://lore.kernel.org/all/96aa144f-3de7-4326-b574-f7a2cb150424@amd.com/
