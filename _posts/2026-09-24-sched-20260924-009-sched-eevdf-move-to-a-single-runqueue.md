---
id: sched-20260924-009
date: '2026-09-24'
subject: 'sched/eevdf: Move to a single runqueue'
subsystem: sched
type: regression
status: under_review
severity: medium
thread_root_msgid: <bd81bbec-ee59-401a-bec6-116196ad3a34@arm.com>
lore_url: https://lore.kernel.org/all/bd81bbec-ee59-401a-bec6-116196ad3a34@arm.com/
authors:
- Aishwarya Rambhadran
maintainers_involved:
- Chen Yu
- K Prateek Nayak
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - WA_WEIGHT/task_h_load 与 p99 回退因果链未坐实
  - 需报告者在 NO_WA_WEIGHT/cgroup_mode 下复测
  next_action: 报告者复测并回帖，Peter 对是否预期取舍定性
contribution_opportunities:
- kind: testing
  description: 复测 NO_WA_WEIGHT 与 cgroup_mode 对 schbench p99/netperf 的影响并回帖
- kind: discussion
  description: 判断 weightless burst stacking 与尾部延迟回退的关联
generated_at: '2026-09-25T09:00:00'
source_email_count: 3
related_articles:
- sched-20260923-001
tags:
- eevdf
- cfs
- regression
title: 'sched/eevdf: Move to a single runqueue'
layout: article
---

## TL;DR
- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-001-sched-eevdf-move-to-a-single-runqueue.html">sched-20260923-001</a>：ARM 的 Aishwarya Rambhadran 报告 v7.2 → v7.3 周期在 AWS Graviton3 上的 schbench p99 请求延迟回归，Fastpath 自动 bisect 定位到「sched/eevdf: Move to a single runqueue」这个 commit；整体 schbench 中性、但个别线程配置出现 ~30% 的 p99 回退，正待 Peter Zijlstra 定性是否为预期取舍。
- <a class="article-ref" href="/lkm/2026/09/24/sched-20260924-009-sched-eevdf-move-to-a-single-runqueue.html">sched-20260924-009</a>（今天，增量更新）：社区把怀疑点收敛到 **WA_WEIGHT / task_h_load()** 上——Chen Yu 提议试 `NO_WA_WEIGHT`（他实测能恢复 netperf 吞吐，task_h_load() 会变大）；K Prateek Nayak 补充可再试 `cgroup_mode`（smp vs concur），并指 Peter 有 `sched/task_h_load` 修复分支可试；Mike Galbraith 回忆早年 WA_WEIGHT 曾让 firefox 事件线程池叠在单 CPU，并给 `task_h_load()` 加了 GP 下限。尚未有 Peter 的正式定性回复。

## 背景与问题
- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-001-sched-eevdf-move-to-a-single-runqueue.html">sched-20260923-001</a>：Fastpath 对比 v7.2 与 v7.3 周期，在 AWS Graviton3（m7g.metal）跑 schbench；整体无显著回退，但少数线程配置 p99 请求延迟明显回退（m16/t16 -31.63%、m64/t4 -22.48%），m32/t4 反而 +30.90% 改善。Fastpath bisect 判定「sched/eevdf: Move to a single runqueue」为 first bad commit（原始回退约 30.9%，复现校验约 27.8%）。该 commit 改变了 EEVDF 运行队列组织，其上有后续修复（如 `68e37487810a` "sched/fair: Fix flat hierarchy"，`Fixes: 85570f10a4c6`）。
- <a class="article-ref" href="/lkm/2026/09/24/sched-20260924-009-sched-eevdf-move-to-a-single-runqueue.html">sched-20260924-009</a>（今天）：背景延续——新焦点是「单运行队列 + 层级公平」下 `task_h_load()`（层级负载 / WA_WEIGHT 加权）是否在特定 cgroup/层级配置里造成尾部延迟回退。

## 技术方案
- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-001-sched-eevdf-move-to-a-single-runqueue.html">sched-20260923-001</a>：本文为回归报告，不含补丁方案；核心疑点是单运行队列拍平 EEVDF 层级后，公平/cgroup 调度配置下 p99 尾部延迟是否与收益不对称。
- <a class="article-ref" href="/lkm/2026/09/24/sched-20260924-009-sched-eevdf-move-to-a-single-runqueue.html">sched-20260924-009</a>（今天）：社区提出的是**定位/规避**手段而非补丁：
  - Chen Yu：`echo NO_WA_WEIGHT > /sys/kernel/debug/sched/features` 关掉 WA_WEIGHT（他实测该 workaround 能恢复 netperf 吞吐——注意是吞吐而非延迟，且他观察到 `task_h_load()` 会变大，同样见于 `sched/task_h_load` 分支）。
  - K Prateek Nayak：若 NO_WA_WEIGHT 不解决问题，再试 `/sys/kernel/debug/sched/cgroup_mode` 的不同模式（smp 用旧权重公式、concur 用新公式）；他实测 schbench 在默认 concur 模式 RPS 指标有回归、smp 模式则与 hierarchical pick 打平；并指 Peter 的 `sched/task_h_load` 修复分支（`git.kernel.org/.../peterz/queue.git?sched/task_h_load`）可试自定义内核。
  - Mike Galbraith：早年发现 WA_WEIGHT 导致 firefox 事件线程池 32 个线程叠在单 CPU（8 rq 机器），虽大多回去睡觉无害，但实测有真实 stacking 影响，于是给 `task_h_load()` 加了 GP 下限；猜测「weightless burst stacking」对某些场景影响更大。

## 版本演进与当前进展
- 回归报告（09-23，`<bd81bbec-ee59-401a-bec6-116196ad3a34@arm.com>`）发出后，本日（09-24）进入 WA_WEIGHT/task_h_load 的定位讨论，仍无正式补丁或 Peter 定性。

## Maintainer 意见与讨论焦点
- **Chen Yu（Intel）**：提出 NO_WA_WEIGHT 的 workaround 与 netperf 吞吐侧证据。
- **K Prateek Nayak（AMD）**：补充 cgroup_mode 试法与 Peter 的 task_h_load 修复分支，并给出自己在 concur/smp 模式下的 schbench 观察。
- **Mike Galbraith**：历史经验支持「WA_WEIGHT / task_h_load 与 stacking 相关」。
- 无 NAK；尚未见 Peter Zijlstra 对「是否预期取舍」的正式回复（这是回归定性的关键）。

## 合入评估
*likelihood=unknown*。回归仍在定位阶段：尚未确认是单运行队列改动的预期取舍还是需修复的 bug，也未定修复方案（NO_WA_WEIGHT 只是规避）。*blocking_issues*：WA_WEIGHT/task_h_load 与 p99 回退的因果链未坐实；需报告者在 NO_WA_WEIGHT/cgroup_mode 下复测并回帖。*next_action*：报告者试 NO_WA_WEIGHT 与 cgroup_mode 并回帖数据，Peter 对是否预期取舍给出定性。

## 效果评估
- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-001-sched-eevdf-move-to-a-single-runqueue.html">sched-20260923-001</a> 的 schbench p99 实测（上文已列）：m16/t16 -31.63%、m64/t4 -22.48%、m32/t4 +30.90%。整体为混合、无全局回退。
- 本日新增：Chen Yu 的 netperf 吞吐侧（NO_WA_WEIGHT 恢复，属吞吐非延迟）；K Prateek 的 schbench concur vs smp 模式观察（concur 有 RPS 回归、smp 打平）。均指向 WA_WEIGHT 相关，但报告者尚未给出 NO_WA_WEIGHT 下的 p99 复测。

## 我可以参与的点
- kind=testing：在报告者同类环境（或任何多核 x86/arm64）复测 NO_WA_WEIGHT、`cgroup_mode=smp/concur` 对 schbench p99 与 netperf 的影响，把数据回帖到该线程——这是当前最缺的收敛依据。
- kind=discussion：判断「weightless burst stacking」在层级公平下的影响面，是否与报告者观察到的尾部延迟回退一致。

## 参考链接
- lore (回归报告): https://lore.kernel.org/all/bd81bbec-ee59-401a-bec6-116196ad3a34@arm.com/
- Chen Yu NO_WA_WEIGHT: https://lore.kernel.org/all/arQCykkkCnADu5ek@chenyu-dev/
- K Prateek cgroup_mode: https://lore.kernel.org/all/587a9b32-bc54-46b9-b81e-c46a19f47e17@amd.com/
- Mike Galbraith WA_WEIGHT: https://lore.kernel.org/all/128e93ca1424630546e39f9e9c1377f8185f7644.camel@gmx.de/
