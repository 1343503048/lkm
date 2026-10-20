---
id: sched-20261020-005
date: 2026-10-20
subject: 'sched_ext: Reenqueue IMMED tasks when their CPU picks idle'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261017221924.3908922-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20261017221924.3908922-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Tejun Heo
current_version: v2
patch_series:
- version: v1
  msgid: <20261017202025.3834954-1-arighi@nvidia.com>
  date: 2026-10-17
  summary: predict 法：加 higher_class_runnable() 让 rq_is_open() 对 forced-idle 报忙（对应
    Don't report a forced-idle CPU as open）
  review_outcome: Tejun 否决预测方向，建议反应法（见 20261018-005）
- version: v2
  msgid: <20261017221924.3908922-1-arighi@nvidia.com>
  date: 2026-10-18
  summary: react 法：__scx_update_idle() 在 nr_immed 非零时调度本地 DSQ 重入队，新增 SCX_REENQ_IDLE_PICK
    标志
  review_outcome: Tejun 指出 reenq 循环与 SCX_ENQ_LAST 缺陷，建议改从 pick_task_idle() 触发
upstream_commit: null
fixes_commit: 98d709cba319
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - v2 的 forced-idle 上报导致 reenq 循环
  - SCX_ENQ_LAST 下重复 reenq 缺陷
  - SCX_REENQ_TSR_RQ_OPEN 注释需补 SCX_REENQ_IDLE_PICK 说明
  next_action: Andrea 按 Tejun 建议改版（pick_task_idle 触发 + 注释修订）后重发
contribution_opportunities:
- kind: testing
  description: 用 SCX_OPS_ALWAYS_ENQ_IMMED / SCX_ENQ_LAST 调度器复现 reenq 循环与重复 reenq 场景
- kind: review
  description: 核对 pick_task_idle() 触发点在 core-wide 选择与 put_prev_task_scx() 时序下的边界
generated_at: '2026-10-21T01:30:00'
source_email_count: 1
related_articles:
- sched-20261017-003
- sched-20261018-005
tags:
- sched_ext
- core_sched
title: 'sched_ext: Reenqueue IMMED tasks when their CPU picks idle'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/17/sched-20261017-003-sched-ext-don-t-report-a-forced-idle-cpu-as-open-for-immed-t.html">sched-20261017-003</a>：Andrea Righi 发 `Don't report a forced-idle CPU as open for IMMED tasks`——core scheduling 强制某 CPU idle 时 `rq_is_open()` 误报开放，`SCX_ENQ_IMMED` 任务被插进本地 DSQ、parked 在更高类任务之后；方案是加 `higher_class_runnable()` 预测 pick。
- <a class="article-ref" href="/lkm/2026/10/18/sched-20261018-005-sched-ext-reenqueue-immed-tasks-when-their-cpu-picks-idle.html">sched-20261018-005</a>：Tejun 否决「预测」方向，建议「对 pick 做反应」；Andrea 据此重写为 v2 `Reenqueue IMMED tasks when their CPU picks idle`（`__scx_update_idle()` 触发本地 DSQ 重入队，新增 `SCX_REENQ_IDLE_PICK` 标志）。
- <a class="article-ref" href="/lkm/2026/10/20/sched-20261020-005-sched-ext-reenqueue-immed-tasks-when-their-cpu-picks-idle.html">sched-20261020-005</a>（今天）：Tejun 对 v2 给出 Claude 生成的 review——指出 forced-idle CPU 仍被 `update_builtin_idle()` 上报为 idle、trusting idle 的调度器会把任务插回去，形成 reenq 循环直至 `SCX_EXIT_ERROR_REENQ`；且 `SCX_ENQ_LAST` 下「local DSQ head」假设不成立；建议从 `pick_task_idle()` 直接触发。

## 背景与问题

（承接 20261017-003 → 20261018-005）core scheduling 强制 CPU idle 时 IMMED 任务被误插、parked 不回的缺口，v2 改用「反应法」在 `__scx_update_idle()` 里当 `nr_immed` 非零时调度本地 DSQ 重入队。今天 Tejun 的 review 针对 v2 落地形态提出两条具体缺陷：

1. 强制 idle 的 CPU 仍被 `update_builtin_idle()` 上报为 idle，被弹走任务的 `task_cpu()` 仍是那个 CPU——信任 idle 状态的调度器（如 scx_cosmos 对 per-CPU 任务 `test_cpu_idle(prev_cpu)` 后 `SCX_DSQ_LOCAL_ON|cpu + SCX_ENQ_IMMED`）会把任务直接插回去，又触发重入队，形成循环；`p->scx.reenq_cnt` 只在任务运行时才复位，`SCX_REENQ_MAX_REPEAT` 轮后调度器以 `SCX_EXIT_ERROR_REENQ` 退出。
2. 「否则 `pick_task_scx()` 会取走 local DSQ 头」在 `SCX_ENQ_LAST` 下不成立（有无 core scheduling 皆然）：`put_prev_task_scx()` 在 `set_next_task_idle()` 之前跑 `ops.enqueue(SCX_ENQ_LAST)`，若它把任务以 IMMED 插入 local DSQ，此处 `nr_immed==1` 会被误弹，导致 lone 任务每次 slice 到期都多一次 reenq。

## 技术方案

（承接，今日为 review 反馈，无新补丁）Tejun 建议改为**从 `pick_task_idle()` 触发**（无视 `rq->curr`）：它在 `put_prev_task_scx()` 之前运行，且 core-wide 选择会对每个 forced-idle sibling 调用它；并提醒「next_class 走到这里时还不是 idle（插入后的 re-pick 仍是 ext，到 deferred `reenq_local()` 运行时才是 idle）」。另建议给 `%SCX_REENQ_TSR_RQ_OPEN` 描述补上 `SCX_REENQ_IDLE_PICK` 说明。

## 版本演进与当前进展

*current_version: v2*。前身（predict，20261017-003）→ v2（react，20261018-005）→ 今日 Tejun 对 v2 提出 reenq 循环与 `SCX_ENQ_LAST` 缺陷，建议改从 `pick_task_idle()` 触发。尚无 v3。

## Maintainer 意见与讨论焦点

Tejun Heo（sched_ext 维护者）不否认方向，但对 v2 落地位置提出两点具体反对：`update_builtin_idle()` 造成的 reenq 循环风险（可致 `SCX_EXIT_ERROR_REENQ`）、以及 `pick_task_scx()` 取 local DSQ 头的假设在 `SCX_ENQ_LAST` 下失效（lone 任务每次 slice 到期多一次 reenq）。并提出改从 `pick_task_idle()` 触发的具体修法。无形式 NAK，属需要再改版的 review。

## 合入评估

*likelihood=medium*。方案方向（反应法）由维护者首肯，但 v2 落地形态被指出会导致 reenq 循环与重复 reenq 的具体缺陷，需按 Tejun 建议从 `pick_task_idle()` 触发并修订。*blocking_issues*：v2 的 forced-idle 上报导致的 reenq 循环、`SCX_ENQ_LAST` 下重复 reenq 缺陷需改版；`SCX_REENQ_TSR_RQ_OPEN` 的注释需补上 `SCX_REENQ_IDLE_PICK` 说明。*next_action*：Andrea 按 Tejun 建议改版（pick_task_idle 触发 + 注释修订）后重发。

## 效果评估

无量化数据。Tejun 的 review 是逻辑推演——构造了「trusting idle 的调度器把任务插回 → reenq 循环 → `SCX_REENQ_MAX_REPEAT` 后退出」与「`SCX_ENQ_LAST` lone 任务多一次 reenq」两个反例场景，未见实测数字。

## 我可以参与的点

- `testing`：用带 `SCX_OPS_ALWAYS_ENQ_IMMED` / `SCX_ENQ_LAST` 的 BPF 调度器复现 Tejun 描述的两个场景（reenq 循环与 lone 任务重复 reenq），验证改版后不再触发。
- `review`：核对 `pick_task_idle()` 触发点（无视 `rq->curr`）在 core-wide 选择与 `put_prev_task_scx()` 时序下的正确性边界。

## 参考链接

- Tejun 今日 review：https://lore.kernel.org/all/d9ba33d7358769a98a35eea9d603305d@kernel.org/
- v2 patch：https://lore.kernel.org/all/20261017221924.3908922-1-arighi@nvidia.com/
