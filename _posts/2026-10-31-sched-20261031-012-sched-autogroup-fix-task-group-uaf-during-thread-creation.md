---
id: sched-20261031-012
date: 2026-10-31
subject: 'sched/autogroup: Fix task_group UAF during thread creation'
subsystem: sched
type: fix
status: under_review
severity: critical
thread_root_msgid: <20261023013631.881730-1-4ncienth@gmail.com>
lore_url: https://lore.kernel.org/all/20261023013631.881730-1-4ncienth@gmail.com/
authors:
- Daehyeon Ko
maintainers_involved:
- Peter Zijlstra
- Tejun Heo
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: b1e8206582f9
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 三条路线（再校验 / cgroup_threadgroup_rwsem / 后移 autogroup 赋值）未收敛
  - 需作者就最终方案发 v2
  next_action: 作者选 Tejun 的后移赋值（成本最低）方向发 v2
contribution_opportunities:
- kind: review
  description: 评估后移 autogroup 赋值是否确实消除与 setsid() 的竞态窗口及其它调用点影响
- kind: discussion
  description: 对三条路线的锁竞争与复杂度做权衡
generated_at: '2026-11-01T09:00:00'
source_email_count: 1
related_articles:
- sched-20261030-008
tags:
- autogroup
- cgroup
title: 'sched/autogroup: Fix task_group UAF during thread creation'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/23/sched-20261023-004-sched-autogroup-fix-task-group-uaf-during-thread-creation.html">sched-20261023-004</a>：Daehyeon Ko 单补丁修 autogroup use-after-free（`sched_cgroup_fork()` 在 CLONE_THREAD 子进程发布前指向旧 `autogroup->tg`，与 `ksys_setsid()` 竞态，`Fixes: b1e8206582f9`、`Cc: stable`）。
- <a class="article-ref" href="/lkm/2026/10/26/sched-20261026-003-sched-autogroup-fix-task-group-uaf-during-thread-creation.html">sched-20261026-003</a>：Peter Zijlstra 质疑会 NULL deref，建议把复杂度移到 `ksys_setsid()`。
- <a class="article-ref" href="/lkm/2026/10/30/sched-20261030-008-sched-autogroup-fix-task-group-uaf-during-thread-creation.html">sched-20261030-008</a>：Daehyeon 论证无 NULL deref、且「仅挪 tasklist_lock 不关窗」；Peter 收回否定、提议 `autogroup_move_group()` 也持 `cgroup_threadgroup_rwsem`。
- <a class="article-ref" href="/lkm/2026/10/31/sched-20261031-012-sched-autogroup-fix-task-group-uaf-during-thread-creation.html">sched-20261031-012</a>（今天）：Tejun Heo 介入——指出 `cgroup_threadgroup_rwsem` 是全局 percpu rwsem，经常写持会非常贵；既然 autogroup 侧不必像 cgroup 侧那样在 fork 早期就定案，不如**把 autogroup 赋值挪到 fork 更晚、不会与 setsid() 竞态的位置**。

## 背景与问题
（承接）竞态时序不变：`clone(CLONE_THREAD)` 侧在发布前把子进程指向旧 autogroup，`setsid()` 侧在窗口内换掉 `signal->autogroup`。今日分歧从「用不用校验」转向「autogroup 是否真要跟 cgroup 串行化」——Tejun 的切入点是成本：`cgroup_threadgroup_rwsem` 是 per-CPU 全局读写信号量，让 `autogroup_move_group()` 常态写持会显著放大锁竞争。

## 技术方案
（今日为方向讨论，无新补丁）Tejun 的提议：autogroup 侧不需要 cgroup 侧的早 fork 定案，把 `sched_autogroup`/task_group 的赋值从 `copy_process()` 早期挪到 fork 流程更晚的点，使其在时序上不可能与 `setsid()` 竞态，「从而完全不需要 `cgroup_threadgroup_rwsem`」。相比 Peter 前一日「让 autogroup 也用 cgroup_threadgroup_rwsem」的方案，这是降低锁成本的新方向。

## 版本演进与当前进展
*current_version: v1*（2026-10-23 首发；今日无新版本，方向进一步分叉）。从「作者再校验 vs cgroup_threadgroup_rwsem」扩展为「移动 autogroup 赋值点」第三条路线。

## Maintainer 意见与讨论焦点
- **Tejun Heo（cgroup/sched_ext 维护者）**：不赞成常态写持 `cgroup_threadgroup_rwsem`（成本高），提出「把 autogroup 赋值后移到 fork 更晚、不与 setsid() 竞态」。
- **Peter Zijlstra（maintainer，前一日）**：倾向复用 `cgroup_threadgroup_rwsem`。
- **Daehyeon Ko（作者）**：坚持既有再校验方案的正确性。
- 未解决：三条路线（再校验 / cgroup_threadgroup_rwsem / 后移 autogroup 赋值）尚未收敛；`Cc: stable` 诉求仍在。

## 合入评估
*likelihood=medium*。维护者已不否定 bug 与修复必要性，但设计仍在三方讨论中，未收敛到具体补丁。*blocking_issues*：三条路线未定案；需要作者（或 Tejun/Peter）就最终方案发 v2。*next_action*：作者在三条路线中选择实现（Tejun 的「后移赋值」成本最低），发 v2。

## 效果评估
无性能数据；修复为正确性（KASAN slab UAF）。今日新增的是**锁成本**考量（`cgroup_threadgroup_rwsem` 常态写持昂贵），属定性判断、无 benchmark。

## 我可以参与的点
- **review**：评估「把 autogroup 赋值后移到 fork 晚阶段」是否真的消除与 setsid() 的竞态窗口，并核对对 `sched_cgroup_fork()` 之外的调用点影响。
- **discussion**：对三条路线（再校验 / cgroup_threadgroup_rwsem / 后移赋值）的锁竞争与复杂度做权衡。

## 参考链接
- Tejun 今日回帖: https://lore.kernel.org/all/36ce43428e53d1d6e47dddb43697ccf2@kernel.org/
- 系列起点: https://lore.kernel.org/all/20261023013631.881730-1-4ncienth@gmail.com/
