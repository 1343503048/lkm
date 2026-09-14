---
id: sched-20260911-004
subject: 'sched/fair: Restart hrtick after same-task repicks'
date: '2026-09-11'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260813-sched-fair-hrtick-restart-v1-1-4230d1e18fbb@gentwo.org>
lore_url: https://lore.kernel.org/all/20260813-sched-fair-hrtick-restart-v1-1-4230d1e18fbb@gentwo.org/
authors:
- Shubhang
maintainers_involved:
- Peter Zijlstra
- Vincent Guittot
current_version: v1
patch_series:
- version: v1
  msgid: <20260813-sched-fair-hrtick-restart-v1-1-4230d1e18fbb@gentwo.org>
  date: 2026-08-13
  summary: 在 same-task repick 路径补 hrtick 重启；以 h_nr_runnable == h_nr_queued 抑制 delayed
    实体误触发，新增 rq flag。
  review_outcome: Zhan Xusheng 08-26 指出 delayed dequeue 条件缺陷与设计冗余；作者 09-11 接受并承诺 v2（h_nr_runnable
    > 1、去 rq flag）。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - v2 未发出
  - PeterZ 的 snt_e 跨调度类重构与作者局部 v2 如何合流未定
  next_action: 作者发 v2 后与 PeterZ 商定是否并入 snt_e 重构
contribution_opportunities:
- kind: testing
  description: 混合负载（runnable 竞争者 + 无关 delayed 实体）下用 ftrace 验证 repick 路径 hrtick 重启
- kind: review
  description: 对照 PeterZ 的 snt_e diff 评估 v2 局部修法与全类重构的合并空间
generated_at: '2026-09-14T11:35:00'
source_email_count: 5
related_articles:
- sched-20260826-009
tags:
- cfs
- sched_clock
title: 'sched/fair: Restart hrtick after same-task repicks'
layout: article
---

## TL;DR
Shubhang 修复「同一任务被重新选中时 hrtick 不重新编程」的系列在沉寂两周后当日出现大量进展：作者确认按 Zhan Xusheng 的意见改条件并承诺 v2，Peter Zijlstra 给出把 set_next_task() 的 `bool first` 改成枚举（SNT_PICK/SNT_REPICK）并覆盖全部调度类（含 DL）的重构方向，Vincent Guittot 参与了 protect slice 的折叠讨论。本文为增量更新，v1 背景见 sched-20260826-009。

## 背景与问题
当 pick_next_task 走 same-task repick 路径（任务继续运行而非切换）时，hrtick（hrtimer 驱动的公平 tick）不会重新启动，导致该任务的运行时限控制失效。v1 补丁在 same-task repick 路径上补充 hrtick 重启逻辑，08-26 曾被 Zhan Xusheng 指出 delayed dequeue 条件缺陷与设计冗余。

## 技术方案
- 作者 v1 思路：用 `h_nr_runnable == h_nr_queued` 之类条件避免因 delayed dequeued 实体残留而误触发 rearm，并新增 rq flag 记录状态；
- 作者 09-11 回应：承认该条件过于受限（一个真实竞争者 + 一个无关 delayed 实体的混合负载也会抑制 rearm），将改为 `h_nr_runnable > 1` 并补混合负载测试；rq flag 将重做——same-task 路径可直接检查 fair hrtick 是否使能、非活跃且有其他 runnable 实体后直接 rearm，无需额外状态；
- PeterZ 的重构提案：`set_next_task(rq, p, bool first)` 改为 `enum snt_e`（SNT_PICK / SNT_REPICK），修改面覆盖 core.c、deadline.c、ext.c、fair.c、idle.c、rt.c、stop_task.c、sched.h（+46/-17），并指出 DL 也有同样问题——repick 时 DL 也应重启 hrtick（set_next_task_dl() 里 repick 分支直达 start_hrtick_dl()）；SCX 的 repick 则直接 return（不重做记账）；
- Vincent 提出 hrtick_start_fair() 中 `vdelta = se->deadline - se->vruntime` 改用 vprot——PeterZ 要求拆成独立补丁，并建议在本补丁中把 set_protect_slice() 移到 repick 路径（「既然又被选中，应该重新设置 vprot」）；Vincent 同意折叠 protect slice，但收回了自己 vprot 的提议：超过 vprot 之后仍需要 deadline 才能允许尽快切换到新 eligible 任务，不能一律用 vprot 替代 deadline。

## 版本演进与当前进展
current_version: v1（v1 msgid `<20260813-sched-fair-hrtick-restart-v1-1-4230d1e18fbb@gentwo.org>`，08-13 发出；当日缓存只有回帖，v2 未发出）。

- v1（08-13）：首发，修复 same-task repick 后 hrtick 缺失；
- 08-26：Zhan Xusheng 指出 delayed dequeue 条件缺陷与 rq flag 冗余（见 sched-20260826-009）；
- 09-11：作者回应 review 并承诺 v2（h_nr_runnable > 1、去掉 rq flag）；同日 PeterZ 抛出 snt_e 枚举重构方向，Vincent/PeterZ 就 protect slice 与 vprot 交换意见。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**：肯定问题同时存在于 DL（"you missed this is also true for DL"），给出全调度类 snt_e 重构 diff——意味着修复可能从 fair.c 局部改动升级为跨类接口变更；
- **Vincent Guittot**：参与 hrtick_start_fair() 细节，先提 vprot 替换、随后自我否定（超过 vprot 需要 deadline）；同意把 set_protect_slice() 折入 repick 路径；
- 分歧/未闭合：PeterZ 的 snt_e 重构与作者的 v2（局部改法）如何合流未定——v2 是先发局部版还是直接按 snt_e 重做，当日无结论。

## 合入评估
likelihood=medium：问题诊断一致（作者、PeterZ、Vincent 均认可是缺陷），但最终形态未定——作者 v2 与 PeterZ 的跨类重构需要协调。blocking_issues：v2 未发出；snt_e 重构是跨 fair/dl/scx/rt/idle/stop 的接口变更，评审面大；Vincent 的 vprot 议题被拆为独立补丁后无人认领。next_action：作者发 v2（预期 h_nr_runnable > 1 + 去 rq flag），随后与 PeterZ 商定是否并入 snt_e 重构。

## 效果评估
暂无效果数据：线程内无 benchmark 或 trace 量化结果，作者承诺在 v2 附带混合负载测试（delayed dequeue 场景），测试结果未获取到。

## 我可以参与的点
- kind=testing：作者承诺的混合负载测试（真实 runnable 竞争者 + 无关 delayed 实体）正是此前条件失效的场景，可用 ftrace 验证 repick 路径 hrtick 重启行为并回帖（sched-20260826-009 提出的验证点在 v2 依然适用）。
- kind=review：v2 发出后对照 PeterZ 的 snt_e diff，评估局部修复与全类重构两条路线的差异与合并空间。

## 参考链接
- v1 补丁：https://lore.kernel.org/all/20260813-sched-fair-hrtick-restart-v1-1-4230d1e18fbb@gentwo.org/
- 作者回应（09-11）：https://lore.kernel.org/all/6cc15e71-f6a1-496c-f3d5-3958369a8c00@gentwo.org/
- PeterZ 的 snt_e 重构提案：https://lore.kernel.org/all/20260911112056.GY776954@noisy.programming.kicks-ass.net/
- PeterZ 的 set_protect_slice 折叠提案：https://lore.kernel.org/all/20260911135951.GG1837346@noisy.programming.kicks-ass.net/
