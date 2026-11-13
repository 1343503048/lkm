---
id: sched-20261113-006
subject: Make the scheduler stack end check selectable at boot
date: 2026-11-13
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <cover.1794554867.git.chris@chrisdown.name>
lore_url: https://lore.kernel.org/all/cover.1794554867.git.chris@chrisdown.name/
authors:
- Chris Down
maintainers_involved:
- Peter Zijlstra
- Randy Dunlap
current_version: v2
patch_series:
- version: v1
  msgid: <cover.1793082868.git.chris@chrisdown.name>
  date: 2026-10-27
  summary: 初版：sched_stack_end_check= 启动参数 + SCS 检查 + lkdtm 测试
  review_outcome: Peter 建议 scs_is_enabled() 检查位置与 changelog 说明；Randy 建议解析失败返回 1
- version: v2
  msgid: <cover.1794554867.git.chris@chrisdown.name>
  date: 2026-11-13
  summary: 吸收 v1 评审意见并 rebase 到 tip/sched/core
  review_outcome: 刚发出，暂无新回复
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 Peter Zijlstra 对 v2 的最终确认
contribution_opportunities:
- kind: testing
  description: 在 arm64/riscv 上验证与 SCS 的交互及 lkdtm CORRUPT_STACK_END 开/关行为
- kind: review
  description: 核对 patch 1 SCS 检查移动对其它调用者的影响
generated_at: '2026-11-14T01:30:00'
source_email_count: 6
related_articles: []
tags:
- sched_debug
title: Make the scheduler stack end check selectable at boot
layout: article
---

## TL;DR
Chris Down（Meta）发 v2 三补丁系列把 `CONFIG_SCHED_STACK_END_CHECK` 变成可在启动时通过 `sched_stack_end_check=` 切换：Meta 部分机型启用该检查（有用但每次上下文切换有开销），此前只能按 Kconfig 构建不同内核镜像，现在可共享同一镜像。v2 已吸收 Peter 与 Randy 对 v1 的意见（`scs_is_enabled()` 检查位置、参数解析返回 1、changelog 说明为何其它调用点不动），并 rebase 到 tip/sched/core。

## 背景与问题
`CONFIG_SCHED_STACK_END_CHECK` 让 `schedule_debug()` 检查即将切出的任务栈尾的 magic，若被覆写则 panic。该检查有用，但每次上下文切换都有额外开销。Meta 部分机型开、部分机型关，此前只能分别为每类机型构建不同内核镜像，运维成本高。动机是让不同机型共享同一内核镜像、按需在启动时开关。

## 技术方案
新增 `sched_stack_end_check=` 启动参数（`[KNL]`，`<bool>`），Kconfig 选项作为默认值。patch 1 是顺带发现的清理（`scs: Skip the shadow stack end check when SCS is disabled`，可独立收取）；patch 2 实现启动参数并把 `scs_is_enabled()` 检查移进 `task_scs_end_corrupted()`；patch 3 加 lkdtm `CORRUPT_STACK_END` 测试（覆写栈尾 magic 后调 `schedule()`，检查开启时应 panic，关闭时恢复 magic 并 `pr_expected_config_param()` 说明）。

对 `task_stack_end_corrupted()` 的其它调用点保持不动：x86/powerpc 的 oops 路径无 CONFIG_SHADOW_CALL_STACK，`__might_resched()` 与栈 tracer 只在已经出问题时才看 magic，跟随开关反而会让人在关闭时丢掉 oops 里的 "Thread overran stack" 提示。

## 版本演进与当前进展
v1→v2（当日）：
- `scs_is_enabled()` 检查移进 `task_scs_end_corrupted()` 而非 `schedule_debug()`（Peter 意见）
- 参数解析失败时返回 1（Randy 意见）
- changelog 说明为何其它调用点不动（Peter 意见）
- rebase 到 tip/sched/core

## Maintainer 意见与讨论焦点
v1 的评审意见（Peter Zijlstra、Randy Dunlap）已在 v2 逐条落实，无 NAK。今日 v2 发出后尚无新的回帖。基准数据：`sched pipe` 与 `sched messaging` 性能不受影响（作者在 patch 2 changelog 中说明）。

## 合入评估
v2 已吸收全部既有评审意见并 rebase 到维护者分支，合入概率高；等待 Peter 对 v2 的最终确认。

## 效果评估
作者在 patch 2 中注明 benchmark `sched pipe` / `sched messaging` 性能不受影响（未附具体数字）。

## 我可以参与的点
- **testing**：在 arm64 / riscv（有 CONFIG_SHADOW_CALL_STACK 的平台）上验证 `sched_stack_end_check=` 与 SCS 的交互，以及 lkdtm `CORRUPT_STACK_END` 测试的开/关行为。
- **review**：核对 patch 1 的 SCS 检查移动是否影响 `task_scs_end_corrupted()` 其它调用者。

## 参考链接
- lore thread: https://lore.kernel.org/all/cover.1794554867.git.chris@chrisdown.name/
- v1: https://lore.kernel.org/r/cover.1793082868.git.chris@chrisdown.name
