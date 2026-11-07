---
id: sched-20261107-004
date: '2026-11-07'
subject: Improving latency of short slice tasks
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261106151947.3991524-1-vincent.guittot@linaro.org>
lore_url: https://lore.kernel.org/all/20261106151947.3991524-1-vincent.guittot@linaro.org/
authors:
- Vincent Guittot
maintainers_involved: []
current_version: v3
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 尚无 Peter 等维护者评审
  - 06/20 的 RT 竞争问题需作者回应或改版
  next_action: 作者吸收 Kayra 意见（WRITE_ONCE、min_slice 初值、06/20 RT 排除）出 v4
contribution_opportunities:
- kind: review
  description: 就 06/20 min slice 选 CPU 是否应排除有 RT 任务在跑的 CPU 给出独立判断
- kind: testing
  description: RT 与短 slice 任务混跑场景量化选到有 RT 任务的 CPU 对延迟的影响
generated_at: '2026-11-08T09:00:00+08:00'
source_email_count: 6
related_articles:
- sched-20261106-002
tags:
- cfs
- eevdf
- load_balance
- perf
title: Improving latency of short slice tasks
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-002-improving-latency-of-short-slice-tasks.html">sched-20261106-002</a>：Vincent Guittot（sched/fair 维护者）的 v3 大系列（20 补丁）继续改进短 slice 任务的调度延迟：为正 lag 引入衰减、在选 CPU 时考虑 slice、为 fair 类新增 push 回调机制、用 push 把「入队时没跑上」的短任务迁移到更合适的 CPU、让 feec() 按 cost+slice 选 CPU、并修复多任务同时醒来堆叠同一 idle CPU 的角例。dragonboard rb5 上 4 短任务同时醒来平均延迟约 1051us→61us，hackbench pipe +15-25%；但 cyclictest 99.9 分位略回退。刚发出，尚无评审。
- <a class="article-ref" href="/lkm/2026/11/07/sched-20261107-004-improving-latency-of-short-slice-tasks.html">sched-20261107-004</a>（今天）：Kayra Cizmeci 密集评审 patch 02–06/20：对 03/20、04/20 给 Reviewed-by，对 05/20 给 Reviewed-by 并建议「min_slice 初值在 5/20 就地改为 0 而非 6/20 再改」，对 02/20 指出「需 WRITE_ONCE 与 3/20 的 READ_ONCE 配对」，对 06/20 提出实质担忧——min slice 选 CPU 可能选到有 RT 任务在跑的 CPU 与之竞争，建议在比较时排除「当前有非 fair 任务在跑」的 CPU 并给出 diff。无维护者回帖。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-002-improving-latency-of-short-slice-tasks.html">sched-20261106-002</a>）多个短 slice 任务同时运行时容易堆叠同一 CPU、长期睡眠任务凭陈旧正 lag 抢占短任务。系列分块收敛：正 lag 记账、slice 参与 CPU 选择、短任务 wakeup 未选中后的补救迁移、EAS 对 slice 的考虑。

今日 Kayra 的评审把焦点集中在「min slice 参与选 CPU」的 patch 05/06 以及「重置 lag」的 patch 02/03/04 上，全部是建设性补漏，未否定方向。

## 技术方案

（承接）今日无新补丁，为逐补丁评审意见：

- **02/20（Reset lag at wakeup when prev CPU has been idle）**：Kayra 指出「这里需要 WRITE_ONCE，不是吗？3/20 用了 READ_ONCE()」——lockless 变量读写需显式配对，避免编译器撕裂/重排。
- **03/20（Reset lag at wakeup when migrating and prev has been idle）**：Kayra 先质疑再自证（构造 TA 睡眠攒 lag、TB/TC 离开、TW/TR 入队、TA 醒来走 try_to_wake_up→set_task_cpu→migrate_task_rq_fair→entity_clear_lag 的推演），结论「就这样工作正确」，给 Reviewed-by。
- **04/20（Reset lag when waking up on idle cpu）**：Kayra「LGTM，Reviewed-by」。
- **05/20（Add per cpu cached min_slice）**：Kayra「这个值在 6/20 里本就改成 0 了，与其在那改，不如从这里一开始就改成 0」，其余 Reviewed-by。
- **06/20（Add min slice check when selecting CPU）**：Kayra 的实质担忧——min slice 检查会选到「有 RT 任务在跑」的 CPU（例：CPU1 空、CPU2 有 RT 任务 RA + fair 任务 FC），9ms 醒来任务按 slice 比较会选中 CPU2 从而与 RT 任务竞争，可能比 CPU1 更糟；建议在选择时跳过「当前正跑非 fair 任务」的 CPU（用 `rq->curr` 的调度类或 `is_idle/idle_cpu` 一类判据），并给出 diff 示意。Kayra 注明 Sashiko（AI）已评过此补丁，他只补自己的担忧。

## 版本演进与当前进展

*current_version: v3（2026-11-06 发出，msgid 20261106151947.3991524-1）*。今日仍 v3，无新版本；进展为 Kayra 对 patch 02–06 的第一轮评审。

## Maintainer 意见与讨论焦点

今日为 Kayra Cizmeci（活跃 reviewer）的密集评审，无维护者回帖。Kayra 意见属建设性补漏：02/20 缺 WRITE_ONCE、05/20 初值放置建议、06/20 的 RT 竞争担忧。06/20 的担忧是唯一涉及正确性/权衡的点——「按 slice 选 CPU 时是否应排除有 RT 任务在跑的 CPU」，这直接关系到 「min slice 选 CPU」这一子方向的取舍。无 NAK。

## 合入评估

*likelihood=unknown*。系列规模大（20 补丁）、横跨 EEVDF/EAS/push 机制、触及调度器热路径，刚进入第一轮评审；Kayra 的意见均属可吸收的补漏，尚未有维护者表态。*blocking_issues*：① 尚无 Peter 等维护者评审；② 06/20 的 RT 竞争问题需作者回应或改版。*next_action*：作者吸收 Kayra 意见（WRITE_ONCE、min_slice 初值、06/20 RT 排除）出 v4；等维护者评审。

## 效果评估

今日无新数据。此前窗口内已有：rb5 上 4 短任务平均延迟 1051us→61us、hackbench pipe +15-25%、cyclictest 99.9 分位 -26% 回退等（见 <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-002-improving-latency-of-short-slice-tasks.html">sched-20261106-002</a>）。今日为代码评审，未涉及 benchmark。

## 我可以参与的点

- **review**：跟进 Kayra 在 06/20 提出的「min slice 选 CPU 是否应排除有 RT 任务在跑的 CPU」——这是当前最有价值的独立判断点，可对照 `select_task_rq_fair()`/`find_energy_efficient_cpu()` 的既有判据给出意见或数据。
- **testing**：在含 RT 与短 slice 任务混跑的场景复测，量化「选到有 RT 任务的 CPU」对短任务延迟的实际影响，支撑 06/20 的取舍。

## 参考链接

- lore thread（v3 cover）: https://lore.kernel.org/all/20261106151947.3991524-1-vincent.guittot@linaro.org/
- Kayra 对 06/20 的评审: https://lore.kernel.org/all/au7SabL5pfbsApyB@scheduler.schedules/
- Kayra 对 03/20 的评审: https://lore.kernel.org/all/au3_SlJ-5Hh98m8Q@scheduler.schedules/
