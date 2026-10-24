---
id: sched-20261024-014
date: 2026-10-24
subject: '[linus:master] [sched/core] 118a2cf4ce: stress-ng.schedpolicy.ops_per_sec
  14.1% regression'
subsystem: sched
type: regression
status: under_review
severity: high
thread_root_msgid: <202610231954.51716452-lkp@intel.com>
lore_url: https://lore.kernel.org/all/202610231954.51716452-lkp@intel.com/
authors:
- kernel test robot
maintainers_involved:
- Peter Zijlstra
- Paul E. McKenney
current_version: null
patch_series: []
upstream_commit: 118a2cf4ced60777a2408001e2b4838fed1cea55
fixes_commit: null
merged_branch: linus/master
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无复现/归因
  - Peter 所指补丁是否确能缓解未定
  next_action: 等待 -rc1 补丁收取并观察影响；作者复现并定位类切换路径额外切换
contribution_opportunities:
- kind: discussion
  description: 复现 schedpolicy 负载，用 perf sched/tracepoint 定位额外 wakeup 抢占来源
generated_at: '2026-10-25T01:00:00'
source_email_count: 3
related_articles:
- sched-20261023-009
tags:
- cfs
- preempt
- regression
- x86
title: '[linus:master] [sched/core] 118a2cf4ce: stress-ng.schedpolicy.ops_per_sec
  14.1% regression'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/23/sched-20261023-009-linus-master-sched-core-118a2cf4ce-stress-ng-schedpolicy-ops.html">sched-20261023-009</a>：kernel test robot 报告 commit `118a2cf4ce`（"sched/core: Call wakeup_preempt() for queued tasks during class change"）在 linus master 上使 `stress-ng.schedpolicy` 的 `ops_per_sec` 回退 **14.1%**（275785 → 236940），且 voluntary/involuntary 上下文切换分别暴涨 +634.5% / +734.4%。尚无修复或作者回应。
- <a class="article-ref" href="/lkm/2026/10/24/sched-20261024-014-linus-master-sched-core-118a2cf4ce-stress-ng-schedpolicy-ops.html">sched-20261024-014</a>（今天）：Peter Zijlstra 回应——「I think I have a patch somewhere stuck in my review queue for -rc1 that might help」（附 patch.msgid.link 链接），并留有余地「If not, too bad, correctness first」。Paul McKenney 两次附和表示期待。回归归因仍待落地。

## 背景与问题
（承接 20261023-009）0day 对 linus:master 的 `118a2cf4ce` 做回归对比：224 线程 2 socket Sapphire Rapids、performance governor 下，`stress-ng.schedpolicy` 各指标一致 -14.1%。该提交在类切换（task 在 fair/rt 等类间迁移）时对 queued 任务调用 `wakeup_preempt()`，疑似改变大量 `sched_setscheduler()` 负载的抢占行为。今日无新背景，为维护者初步回应。

## 技术方案
非补丁，为回归报告的维护者回应。Peter 指出其 review queue 里可能有相关补丁（`https://patch.msgid.link/CANGjgdmNCfm=SctvKZ44y8b5n8t_JSp4meX=DKGnG74B3g1vVw@mail.gmail.com`）能帮助改善，但强调「correctness first」——若该补丁未能缓解，则接受回退以保正确性。

## 版本演进与当前进展
非补丁系列。今日进展：Peter Zijlstra 回应（`<20261023170023.GY2823843@noisy.programming.kicks-ass.net>`）、Paul McKenney 附和（`<bc1c06ff-...@paulmck-laptop>` 与 `<b39cd288-...@paulmck-laptop>`）。

## Maintainer 意见与讨论焦点
Peter Zijlstra 今日表态：有补丁在 review queue 待 -rc1 收取，可能缓解该回归；并暗示若无效则「correctness first」接受回退。Paul McKenney 两次表示「Here is hoping / Hear, hear!」表达期待。尚未有 `118a2cf4ce` 作者的直接回应或具体归因分析。

## 合入评估
*likelihood=unknown*。仍是针对已合入 mainline 提交的性能回退报告；今日仅获维护者「可能有缓解补丁」的模糊预告，尚无复现、归因或修复落地。*blocking_issues*：无复现/归因；Peter 所指补丁是否确能缓解未定。*next_action*：等待 Peter 的 -rc1 补丁收取并观察其对该回归的影响；作者复现 schedpolicy 负载并定位类切换路径上的额外切换/抢占。

## 效果评估
无新数据。既有 0day 数据延续：`ops_per_sec` 275785 → 236940（-14.1%）、voluntary_context_switches +634.5%、involuntary_context_switches +734.4%（见 20261023-009）。

## 我可以参与的点
- *kind: discussion*：复现 schedpolicy 负载，用 `perf sched`/tracepoint 对比类切换路径的抢占来源，为 Peter 的补丁与回归归因提供实测依据。

## 参考链接
- 报告: https://lore.kernel.org/all/202610231954.51716452-lkp@intel.com/
- Peter 今日回帖: https://lore.kernel.org/all/20261023170023.GY2823843@noisy.programming.kicks-ass.net/
- 前文: <a class="article-ref" href="/lkm/2026/10/23/sched-20261023-009-linus-master-sched-core-118a2cf4ce-stress-ng-schedpolicy-ops.html">sched-20261023-009</a>
