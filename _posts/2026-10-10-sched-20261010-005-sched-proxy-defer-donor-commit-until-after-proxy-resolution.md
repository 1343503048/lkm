---
id: sched-20261010-005
date: '2026-10-10'
subject: 'sched/proxy: Defer donor commit until after proxy resolution'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20260827-sched-proxy-v3-1-1af63ac5ae56@zohomail.com>
lore_url: https://lore.kernel.org/all/20260827-sched-proxy-v3-1-1af63ac5ae56@zohomail.com/
authors:
- Xukai Wang
maintainers_involved: []
current_version: v3
patch_series:
- version: v3
  msgid: <20260827-sched-proxy-v3-1-1af63ac5ae56@zohomail.com>
  date: '2026-08-27'
  summary: pick_next_task() 选择与提交解耦，提交推迟到 proxy 解析之后
  review_outcome: 作者今日交出回调开销实测（-81.7% 调用、11.29→2.52ms），端到端时延无稳定变化
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - CONFIG_SCHED_PROXY_EXEC 主线未定稿
  - 端到端时延收益不显著
  next_action: 等 Prateek/John 及 proxy-exec 维护者对数据与 v4 表态
contribution_opportunities:
- kind: review
  description: 复跑 priority-inversion-demo 验证回调计数/耗时数据
- kind: discussion
  description: 分析回调节省未转化为端到端收益的原因与还需的证据
generated_at: '2026-10-11T09:00:00'
source_email_count: 1
related_articles:
- sched-20260810-007
- sched-20260827-004
tags:
- proxy_execution
title: 'sched/proxy: Defer donor commit until after proxy resolution'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/08/10/sched-20260810-007-sched-proxy-defer-donor-commit-until-after-proxy-resolution.html">sched-20260810-007</a>：Xukai Wang 提交 RFC v2「sched/proxy: Defer donor commit until after proxy resolution」，把 donor 的 commit（成为 rq->curr）推迟到 proxy 解析完成后，避免中途状态被负载均衡/统计看到。RFC 阶段，合入可能性低（依赖 proxy 主线）。
- <a class="article-ref" href="/lkm/2026/08/27/sched-20260827-004-sched-proxy-defer-donor-commit-until-after-proxy-resolution.html">sched-20260827-004</a>：发出 v3——把 `pick_next_task()` 的「选择」与「提交」（`put_prev_set_next_task()`）解耦，v3 把 v1 讨论里的量化数据写进 commit message（60 秒压测中被放弃的 blocked donor 提交 3224 次、重试从不选同一 donor）；当日无人回复，未决点延续成「只量化了频率、没量化开销」。
- <a class="article-ref" href="/lkm/2026/10/10/sched-20261010-005-sched-proxy-defer-donor-commit-until-after-proxy-resolution.html">sched-20261010-005</a>（今天）：**作者对 v2 review 里 John Stultz 的「真实影响/是否可测」之问交出定向测量**——`put_prev_task()`/`set_next_task()` 回调调用次数从 49037 降到 8968（-81.7%）、每次 workload run 的调度类回调耗时 11.29ms → 2.52ms；但端到端 p99/p999 时延基线约 5.00ms/9.00ms、与 v3 无稳定差异。作者请 Prateek/John 判断这些数据是否回应了 v2 关切、是否需要 v4。

## 背景与问题
（承接）proxy execution 下 `pick_next_task()` 可能选中一个 blocked donor，它还要过 `find_proxy_task()`；若解析失败，`__schedule()` 走 pick_again 重选，但上一轮已为被放弃的候选做过 `put_prev_task()`/`set_next_task()`，紧接着又为新候选再做一遍。v3 的方案是把提交推迟到 proxy 解析成功之后。今天回应的是 v2 review 遗留的一个关键问题——John Stultz 问该改动的**真实影响是什么、是否可测量**：作者此前只量化到「被放弃的次数」，一直没量化「被放弃的提交实际浪费了多少回调开销」。

## 技术方案
（承接 v3 的「选择与提交解耦」）今天不改进方案本身，而是补上之前缺失的开销测量：

1. 在 `put_prev_set_next_task()` 的 donor commit 路径上插桩 `put_prev_task` / `set_next_task` 两个调度类回调，用 `local_clock()` 对计时，并校准空 `local_clock()` 对的 15ns 开销、逐调用扣减。
2. 用 John 的 priority-inversion-demo 压测，每个内核跑 3 次裸金属 x86。

结果：回调调用次数 49037 → 8968（-81.7%）；回调执行时间（扣减校准后）平均 11.29ms → 2.52ms。单次 idle→fair 转移约 0.69µs（put_prev_task(idle) 142-154ns + set_next_task(fair) 503-557ns）。此外作者强调语义收益：把调度类状态提交放到 donor 在 proxy 解析中存活之后，避免为可能被放弃的候选提交状态。

## 版本演进与当前进展
*current_version: v3*（RFC）。今天的增量（`<0fe8a0fe-68f5-467b-be82-cf631e00fd87@zohomail.com>`）是作者对 v2 review 问题的数据回应：

- 回调调用次数 -81.7%（49037 → 8968，三次运行合并）。
- 回调耗时 11.29ms → 2.52ms（三次分别 2.361/2.548/2.642ms，基线 11.131/11.157/11.578ms）。
- 端到端：未观察到稳定时延位移——p99 基线约 5.00ms 与 v3 一致，p999 约 9.00ms 一致。

作者请 Prateek/John 判断数据是否回应关切、是否需 v4。当日尚无回复。

## Maintainer 意见与讨论焦点
- **John Stultz / Prateek**（被作者点名，非常驻维护者）：v2 review 里提出「真实影响/是否可测」之问，正是今天数据的动机。
- 未决点仍是此前的方向性依赖：本补丁挂在 `CONFIG_SCHED_PROXY_EXEC` 整体之下（多轮 RFC 未定稿），且作者承认端到端时延未见稳定变化——「约 8.8ms 的回调节省未转化为稳定的端到端时延收益」可能成为维护者后续质疑点。当天无 NAK、也无新增维护者表态。

## 合入评估
*likelihood=low*（不变）。作者的测量闭合了「是否可测」一问，证明方案确能显著减少被放弃提交的回调开销；但端到端时延无稳定收益，且 proxy-exec 主线本体仍未定稿，此类重构通常要随主系列一起收。*blocking_issues*：`CONFIG_SCHED_PROXY_EXEC` 主线未定稿；端到端收益不显著。*next_action*：等 Prateek/John 与 proxy-exec 维护者对数据与 v4 的表态。

## 效果评估
作者今天首次给出量化：调度类回调调用 -81.7%（49037 → 8968 次/三次合并）；每次 workload run 回调耗时 11.29ms → 2.52ms（约省 8.8ms）；单次 idle→fair 转移约 0.69µs。但**未观察到稳定的端到端时延位移**（p99 约 5.00ms、p999 约 9.00ms，基线与 v3 一致）——作者如实说明「local reduction 未转化为稳定端到端 shift」。

## 我可以参与的点
- 复跑 John 的 priority-inversion-demo（`github.com/johnstultz-work/priority-inversion-demo`）验证回调计数与耗时，给作者第二份数据背书；
- 评估「回调节省未见端到端收益」是否意味着该改动价值有限，帮助作者定位还需要补什么证据。

## 参考链接
- v3: https://lore.kernel.org/all/20260827-sched-proxy-v3-1-1af63ac5ae56@zohomail.com/
- 今日数据回帖: https://lore.kernel.org/all/0fe8a0fe-68f5-467b-be82-cf631e00fd87@zohomail.com/
- 压测 workload: https://github.com/johnstultz-work/priority-inversion-demo
