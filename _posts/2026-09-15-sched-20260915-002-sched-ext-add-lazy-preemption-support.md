---
id: sched-20260915-002
date: '2026-09-15'
subject: 'sched_ext: Add lazy preemption support'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260915090127.2321020-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260915090127.2321020-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Tejun Heo
current_version: v4
patch_series:
- version: v3
  msgid: <20260914144620.2032614-1-arighi@nvidia.com>
  date: '2026-09-14'
  summary: 见 sched-20260914-006
  review_outcome: 见 sched-20260914-006
- version: v4
  msgid: <20260915090127.2321020-1-arighi@nvidia.com>
  date: '2026-09-15'
  summary: 保留 KICK_WAIT 同步、恢复无限 slice 的 tick 依赖、kselftest 拓扑健壮性修正（Sashiko 意见）
  review_outcome: selftest 全绿；作者确认将修一处 autoconf.h 依赖后出 v5
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - selftest 的 autoconf.h 依赖修正尚未落地
  next_action: 作者发 v5 修 selftest 后，待 Tejun 收入 sched_ext/for-7.4
contribution_opportunities:
- kind: testing
  description: 在不同 preempt 模型与 NOHZ_FULL 拓扑上跑 kick/nohz_tick selftest 并回帖结果
- kind: review
  description: v5 发布后核对 autoconf.h 依赖修复与既有意见落实
generated_at: '2026-09-16T01:05:00'
source_email_count: 4
related_articles:
- sched-20260914-006
- sched-20260912-005
tags:
- sched_ext
- preempt
title: 'sched_ext: Add lazy preemption support'
layout: article
---

## TL;DR
本文为增量更新，完整背景见 related_articles。Andrea Righi 09-15 发出 v4：给 sched_ext 增加 lazy 抢占——`SCX_ENQ_PREEMPT_LAZY`/`SCX_KICK_PREEMPT_LAZY` 让 BPF 调度器像 fair 类一样把调度边界推迟到返回用户态或下一个 tick，并新增 `SCX_OPS_LAZY_SLICE_EXPIRY` 默认策略与 `scx_bpf_task_set_slice_expiry()` 每任务覆盖。v4 修完 Sashiko 反馈的 SCX_KICK_WAIT 同步与无限 slice NOHZ_FULL 下的 tick 恢复问题，selftest 全绿（kick 6 项、nohz_tick 1 项）。合入概率高。

## 背景与问题
fair 调度类可通过 lazy rescheduling 推迟调度边界（推迟到返回用户态或下一次 scheduler tick），而 sched_ext 此前只暴露立即抢占，BPF 调度器无法做同样的权衡。目标是让 BPF 调度器在吞吐与时延之间也能选择 lazy 抢占，并能在无限 slice 任务停掉 NOHZ_FULL CPU 的 tick 时仍保证前向进展。

## 技术方案
- 新增 `SCX_ENQ_PREEMPT_LAZY` 与 `SCX_KICK_PREEMPT_LAZY`：两者都会结清当前 sched_ext 任务的 slice，但请求 lazy 重调度；立即抢占、WAIT 与普通 kick 在组合请求中优先。
- 新增 `SCX_OPS_LAZY_SLICE_EXPIRY` 作为新启用任务的默认过期策略（在 `ops.enable()` 前初始化）；新增 `scx_bpf_task_set_slice_expiry()` 让调度器从任意回调按任务覆盖默认值，同时保留 sub-scheduler 的任务所有权边界；bypass 继续强制立即过期。
- 对因无限 slice 停掉 tick 的 NOHZ_FULL CPU 上的任务，lazy 请求会恢复 tick 依赖，保证前向进展；kick 请求独立累加、在持目标 rq 锁时解算优先级；拒绝未知 kick flag 与非法 SCX_KICK_IDLE 组合。

## 版本演进与当前进展
- **v1**（09-11）、**v2**（09-14 08:49，见 <a class="article-ref" href="/lkm/2026/09/12/sched-20260912-005-sched-ext-add-lazy-preemption-support.html">sched-20260912-005</a>）、**v3**（09-14 14:46，见 <a class="article-ref" href="/lkm/2026/09/14/sched-20260914-006-sched-ext-add-lazy-preemption-support.html">sched-20260914-006</a>）。
- **v4**（本日 17:00，`<20260915090127.2321020-1-arighi@nvidia.com>`）：保留 SCX_KICK_WAIT 与 SCX_KICK_PREEMPT_LAZY 组合时的同步（Sashiko）；lazy 过期无限 slice 时恢复 tick 依赖（Sashiko）；kselftest 验证延迟 SCX_KICK_WAIT 回调确实执行、kick 测试控制器脱离 victim CPU、nohz_tick 控制器选 housekeeping CPU 并优雅跳过（Sashiko）。
- 本日回帖：作者 104545 就 selftest 一条反馈（`autoconf.h` 可包含并据此判断）确认「I'll include this fix in the next version」。

## Maintainer 意见与讨论焦点
- **Tejun Heo**（v2 意见，见 changelog）：lazy slice 过期改为 per-task 属性、增加 `scx_bpf_task_set_slice_expiry()`、恢复 NOHZ_FULL tick 依赖、kick 请求独立累加并解算优先级、PREEMPT|PREEMPT_LAZY 与 WAIT|PREEMPT_LAZY 组合规则、preemption 掩码一起清理。
- **Sashiko**（审查反馈）：多轮 kselftest 项修正（WAIT 同步、tick 恢复、测试拓扑健壮性）。
- 作者解释 selftest 一处 `autoconf.h` 依赖问题，将在下一版修复。

## 合入评估
*likelihood=high*。已迭代四版、selftest 全绿（`preempt=lazy` 下 kick 6 PASSED、`nohz_full=8-15` 下 nohz_tick 1 PASSED），v4 基本消化完 Tejun 与 Sashiko 的全部意见，仅剩 selftest 一处小修待 v5。*blocking_issues*：selftest 的 `autoconf.h` 依赖修正未落地。*next_action*：作者发 v5 修 selftest 后，待 Tejun 收入 sched_ext/for-7.4。

## 效果评估
作者 virtme-ng 实测（cover 原文）：`preempt=lazy` 下 `runner -t kick` → PASSED 6 / FAILED 0；`preempt=lazy nohz_full=8-15` 下 `runner -t nohz_tick` → CPU 8 收到 7 个 finite-slice tick，PASSED 1 / FAILED 0。无性能回退/提升的量化数据，本轮以正确性验证为主。

## 我可以参与的点
- kind=testing：在更多组合（`preempt=voluntary/full`、不同 NOHZ_FULL 拓扑、自家 scx 调度器）下跑 kick/nohz_tick selftest 并回帖结果，验证 lazy 抢占与 WAIT/立即抢占的优先级规则。
- kind=review：v5 发布后核对 `autoconf.h` 依赖修复与 Sashiko 意见的落实是否完整。

## 参考链接
- v4 cover：https://lore.kernel.org/all/20260915090127.2321020-1-arighi@nvidia.com/
- v3：https://lore.kernel.org/r/20260914144620.2032614-1-arighi@nvidia.com/
- 本日 selftest 回帖：https://lore.kernel.org/all/aqlJnaPRbhncTbcQ@gpd4/
