---
id: sched-20260919-003
date: '2026-09-19'
subject: 'sched_ext: Add lazy preemption support'
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: <20260918171539.214204-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260918171539.214204-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Tejun Heo
current_version: v7
patch_series:
- version: v7
  msgid: <20260918171539.214204-1-arighi@nvidia.com>
  date: '2026-09-19'
  summary: 收敛命名/语义，补充 NO_HZ_FULL 处理与 selftest，拆 1/2+2/2
  review_outcome: Tejun 应用 1-2 至 sched_ext/for-7.4
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.4
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入 sched_ext/for-7.4，随 7.4 周期进主线
contribution_opportunities: []
generated_at: '2026-09-20T09:00:00'
source_email_count: 4
related_articles:
- sched-20260918-012
tags:
- sched_ext
title: 'sched_ext: Add lazy preemption support'
layout: article
---

## TL;DR
增量更新：Andrea Righi 的 sched_ext 惰性抢占系列推出 v7，本日被 Tejun Heo 应用 1-2 到 `sched_ext/for-7.4`。相比 v6，v7 主要是把即时抢占的 `SCX_ENQ_PREEMPT_LAZY`/`SCX_KICK_PREEMPT_LAZY` 一次性操作与新的持久策略 `scx_bpf_task_set_lazy_resched()`/`SCX_OPS_LAZY_RESCHED` 语义厘清，并补充了无穷大 slice 任务在 NO_HZ_FULL CPU 上恢复 tick、以及 preempt=lazy / nohz_full 分设的 selftest。系列从首个版本起一路获 Tejun 逐版 review，至此收口。

## 背景与问题
背景见 <a class="article-ref" href="/lkm/2026/09/18/sched-20260918-012-sched-ext-add-lazy-preemption-support.html">sched-20260918-012</a>：fair 调度类可以通过 lazy rescheduling 推迟调度边界，但 sched_ext 目前只向 BPF 调度器暴露即时抢占。本系列为 sched_ext 补上惰性抢占能力，让运行中的 sched_ext 任务 slice 到期后，把调度边界推迟到返回用户态或下一个 scheduler tick。

## 技术方案
- 1/2（`sched_ext: Add lazy preemption support`）：新增 enqueue/kick 抢占标志的 lazy 变体；`SCX_OPS_LAZY_RESCHED` 使 slice 到期默认走惰性重调度；调度器可用 `scx_bpf_task_set_lazy_resched()` 为单个任务双向覆盖这一持久策略。与一次性 `SCX_ENQ_PREEMPT_LAZY`/`SCX_KICK_PREEMPT_LAZY` 不同，该 kfunc 本身不请求重调度，只控制后续 tick 发现 slice 耗尽时如何动作；配套兼容包装使调用在缺 kfunc 的旧内核上退化为 no-op。helper 保留子调度器任务归属边界，bypass 仍强制即时重调度。惰性 enqueue/kick 在针对 NO_HZ_FULL 上的无穷 slice 任务时还会恢复 scheduler tick（先置 reschedule 请求让依赖更新的 IPI 在返回用户态时送达，恢复的 tick 兜底后续 promotion）。
- 2/2（`selftests/sched_ext: Add lazy preemption tests`）：覆盖即时/惰性抢占、kick 模式间的合并与优先级、enqueue 抢占、per-task 惰性策略覆盖、非法标志，以及 NO_HZ_FULL CPU 上无穷 slice 任务的惰性抢占（并校验发出惰性请求前 tick 确已停止）。

## 版本演进与当前进展
- v6（此前版本，见 <a class="article-ref" href="/lkm/2026/09/18/sched-20260918-012-sched-ext-add-lazy-preemption-support.html">sched-20260918-012</a>）：已获 Tejun 完整 review，并提出多个命名/实现点。
- v7（`<20260918171539.214204-1-arighi@nvidia.com>`，本日收到）：按前一版 review 收敛命名与语义，补充 NO_HZ_FULL 与测试；Tejun 回帖 "Applied 1-2 to sched_ext/for-7.4. I refilled the code and comments." 表明收口。

## Maintainer 意见与讨论焦点
- **Tejun Heo**：本日直接应用 1-2 至 `sched_ext/for-7.4`，仅在代码/注释上做了润色（refill），未有新异议。此前版本的命名（`scx_bpf_task_set_lazy_resched()`/`SCX_OPS_LAZY_RESCHED`）、`for_each_cpu_or()` 折叠、bit 枚举补全等意见已在 v7 落实。
- 无未决分歧。

## 合入评估
*likelihood=merged*。v7 已由 Tejun 应用到 `sched_ext/for-7.4`。*blocking_issues*：无。*next_action*：随 7.4 开发周期进主线。

## 效果评估
v7 cover 给出测试结果：`vng -a "preempt=lazy"` 下 kick selftest 6/6 通过；`vng --cpus 4 -a "nohz_full=1-3"` 下 nohz_tick 通过（CPU 1 收到 6 次有限 slice tick）。Tejun 另报在 lazy/full 两种模式、nohz_full 于 2-3 与 1-3 的 vng 运行均成功。Tao Cui 在 4-CPU KVM guest 上测 v6：惰性与即时 wakeup 抢占平均 59us、CFS 60us（2000 次迭代）；lazy slice 到期减少了上下文切换（数字后续被截断，未获取到完整值）。

## 我可以参与的点
当前阶段暂无明显参与空间（已合入 `sched_ext/for-7.4`）。如需参与，可持续观察 lazy preemption 在真实 sched_ext 调度器上的行为回归。

## 参考链接
- lore（v7 cover）: https://lore.kernel.org/all/20260918171539.214204-1-arighi@nvidia.com/
- lore（Tejun 应用回帖）: https://lore.kernel.org/all/1c8cd97257ed5794d216432330b5c731@kernel.org/
