---
id: sched-20261113-010
subject: 'sched: RT throttling cleanup and a bit of documentation'
date: 2026-11-13
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261113-sched_dl-v3-0-a76ffa1cdeee@linutronix.de>
lore_url: https://lore.kernel.org/all/20261113-sched_dl-v3-0-a76ffa1cdeee@linutronix.de/
authors:
- Sebastian Andrzej Siewior
maintainers_involved:
- Juri Lelli
current_version: v3
patch_series:
- version: v1
  msgid: null
  date: 2026-11-05
  summary: 标记 RT_GROUP_SCHED broken 之后的七补丁清理
  review_outcome: Peter/Tejun 要求先标记 RT_GROUP_SCHED broken
- version: v2
  msgid: <20261110-sched_dl-v2-0-cc9399f7aeb1@linutronix.de>
  date: 2026-11-10
  summary: 七补丁：DL 准入迁 sysfs、per-CPU fair_server sysfs、rcutorture 迁移、文档
  review_outcome: Paul 认可但报 divide-by-zero；Randy 文档 nit；Juri 追问与 Mathieu 系列重叠
- version: v3
  msgid: <20261113-sched_dl-v3-0-a76ffa1cdeee@linutronix.de>
  date: 2026-11-13
  summary: 八补丁，新增 rcutorture 关闭 fair_server 与 fairserver 文档；吸收 v2 评审
  review_outcome: Juri 评审 1/8 认为 Mathieu 途径更安全，作者决定 drop 该 bit
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 1/8 的替代方向需对齐 Mathieu 的 dl_server 修复途径
  - Paul 报告的 divide-by-zero 是否已在 v3 解决未确认
  next_action: drop 1/8 后发 v4，并确认 divide-by-zero 修复情况
contribution_opportunities:
- kind: testing
  description: 复现 Paul 报告的 divide-by-zero，确认 v3 是否修复
- kind: discussion
  description: 厘清本系列 rcutorture 处理与 Mathieu dl_server 修复是否同一根因
generated_at: '2026-11-14T01:30:00'
source_email_count: 9
related_articles:
- sched-20261111-001
- sched-20261112-010
tags:
- rt
- dl_server
- rt_bandwidth
- cgroup
title: 'sched: RT throttling cleanup and a bit of documentation'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/11/sched-20261111-001-sched-rt-throttling-cleanup-and-a-bit-of-documentation.html">sched-20261111-001</a>：Sebastian Andrzej Siewior 发 v2 七补丁梳理 RT throttling 历史包袱（标记 RT_GROUP_SCHED broken、DL 准入控制迁 sysfs、新增 per-CPU fair_server sysfs、rcutorture 迁移、文档更新）。Paul E. McKenney 认可但指出系列仍带一个 divide-by-zero 问题，Randy Dunlap 提文档 nit。
- <a class="article-ref" href="/lkm/2026/11/12/sched-20261112-010-sched-rt-throttling-cleanup-and-a-bit-of-documentation.html">sched-20261112-010</a>：Juri Lelli 追问该系列是否与 Mathieu Desnoyers 的 dl_server 修复重叠；Sebastian 解释 rcutorture dl_server 处理；Randy 对 1/7 给 LGTM。
- <a class="article-ref" href="/lkm/2026/11/13/sched-20261113-010-sched-rt-throttling-cleanup-and-a-bit-of-documentation.html">sched-20261113-010</a>（今天）：**v3 发出，扩到八补丁**（新增 `sched: rcutorture: Allow to disable DL fair_server` 与 `Documentation/sched: Add fairserver to sched-deadline`）；**Juri Lelli 评审 1/8，认为 Mathieu 的途径更安全并解释理由，Sebastian 决定 drop 该 bit**。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/11/11/sched-20261111-001-sched-rt-throttling-cleanup-and-a-bit-of-documentation.html">sched-20261111-001</a> / 20261112-010）人们过去通过向 `/proc/sys/kernel/sched_rt_runtime_us` 写 -1 来关闭 RT throttling；自 v6.12 起该行为已被 fair_server 接管，但文档滞后、全局 DL 资源控制又与 RT_GROUP_SCHED 共享同一 proc 文件（启用 RT_GROUP_SCHED 时还会卡住）。系列清理这堆历史包袱并补文档。今日进入 v3 收口。

## 技术方案
v3 八补丁（相对 v2 新增两补丁、调整 rcutorture 处理）：
1. `sched/deadline: Reject debugfs dl_server writes for not-active CPUs.`（今日被 Juri 挑战、作者决定 drop 该 bit）
2. `sched: Mark RT_GROUP_SCHED broken`
3. `rcutorture: Don't try to disable to RT throttling.`
4. `sched: rcutorture: Allow to disable DL fair_server`
5. `sched: Move DL's admission control to sysfs`（`/sys/kernel/sched/dl_period_us`、`dl_runtime_us`）
6. `sched: Limit sysctl sched_rt_{period|runtime}_us to RT_GROUP_SCHED`
7. `sched: Add sysfs files for the per-CPU fair_server knobs`（`/sys/kernel/sched/cpuX`）
8. `Documentation/sched: Add fairserver to sched-deadline`

v2→v3 changelog：措辞修正 sched-rt-group.rst（Randy）；rcutorture 改为从 boost-thread 关闭 fair_server；`sched_dl_try_boundary()` 用私有 mutex 做更新（回应 sashiko 的 stale 写回担忧）；`NSEC_PER_USEC` 乘法的 u64 强转；`sysfs_dl_runtime` 非 static 供 `dl_bandwidth_enabled()` 访问；剩余 `sysctl_sched_rt_{runtime|period}` 也隐藏到 RT_GROUP_SCHED 之后。

## 版本演进与当前进展
- RFC（2026-10-23）→ v1（2026-11-05，Peter/Tejun 要求先标记 RT_GROUP_SCHED broken）→ v2（2026-11-10）→ **v3（今日）**。
- 今日 Juri 评审 1/8，Sebastian 决定 drop 该 bit。

## Maintainer 意见与讨论焦点
- **Juri Lelli（deadline 维护者）**：对 1/8（Reject debugfs dl_server writes for not-active CPUs）表示「Mathieu 的途径看起来更安全」——`sched_cpu_deactivate()` 在不持 rq->lock 时调 `set_cpu_active(false)`，通过 `cpu_active()` 检查的写仍可能在飞行直到 `sched_set_rq_offline()`（需 !cpus 检查覆盖）；online 侧 `set_cpu_active(true)` 先于 domains rebuild，检查会让写通过 def rd 的记账；而 `rq->online` 只在写方已持有的 rq->lock 下改变。
- **Sebastian Andrzej Siewior（作者）**：接受并决定 drop 该 bit。
- 无 NAK；Paul 报告的 divide-by-zero 是否已在 v3 解决，当日讨论未明确确认。

## 合入评估
系列持续推进、维护者积极参与，合入概率中等偏高。当前待决：1/8 的替代方向（跟随 Mathieu 的 dl_server 修复途径）与 divide-by-zero 的最终确认。

## 效果评估
无性能数据（清理/文档系列）。

## 我可以参与的点
- **testing**：复现 Paul 报告的 divide-by-zero（rcutorture 场景禁用/重建 fair_server 或写 DL 准入控制），确认 v3 是否修复。
- **discussion**：厘清 Sebastian 的 rcutorture dl_server 处理与 Mathieu 的 dl_server 修复（patch 06/29）是否针对同一根因，避免两系列重复。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261113-sched_dl-v3-0-a76ffa1cdeee@linutronix.de/
- Juri 对 1/8 的评审: https://lore.kernel.org/all/avcjQMlVELcauQld@jlelli-thinkpadt14gen4.remote.csb/
