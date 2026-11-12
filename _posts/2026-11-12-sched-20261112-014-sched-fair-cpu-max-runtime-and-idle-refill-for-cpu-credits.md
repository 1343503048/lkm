---
id: sched-20261112-014
date: '2026-11-12'
subject: 'sched/fair: cpu.max.runtime and idle refill for CPU credits'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <cover.1794303670.git.sieberf@amazon.com>
lore_url: https://lore.kernel.org/all/cover.1794303670.git.sieberf@amazon.com/
authors:
- Fernand Sieber
maintainers_involved:
- Tejun Heo
current_version: v3
patch_series:
- version: v3
  msgid: <cover.1794398404.git.sieberf@amazon.com>
  date: '2026-11-11'
  summary: 只留 fair 侧 cpu.max.runtime 与 idle refill 两补丁，修正 max 语义
  review_outcome: Tejun 论证 sched_ext 侧出局；Fernand 确认 fair-only；待 CFS 维护者评审
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: 等 CFS 维护者评审 v3 并评估 patch 2 行为变化
contribution_opportunities:
- kind: testing
  description: 真实 burstable 场景验证 kexec/reboot 前后额度读写与 idle refill 行为
- kind: review
  description: 评估 patch 2 对现有 cpu.max.burst 用户的行为变化可接受性
generated_at: '2026-11-13T09:00:00+08:00'
source_email_count: 2
related_articles:
- sched-20261110-003
- sched-20261111-008
tags:
- cfs
- cgroup
title: 'sched/fair: cpu.max.runtime and idle refill for CPU credits'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/10/sched-20261110-003-sched-fair-cpu-max-runtime-and-idle-refill-for-cpu-credits.html">sched-20261110-003</a>：Fernand Sieber（Amazon）发 v2 四补丁，为 CFS 带宽控制器补「CPU credits」能力（`cpu.max.runtime` 读写、burst 上限放宽、空闲组 idle 期间挣额度），并加两个「额度在 fair 与 sched_ext 间无缝交接」的补丁。
- <a class="article-ref" href="/lkm/2026/11/11/sched-20261111-008-sched-fair-cpu-max-runtime-and-idle-refill-for-a-burstable-b.html">sched-20261111-008</a>：Tejun 否定 v2 的跨类集成，作者改发 v3（只留 fair 侧两补丁）。
- <a class="article-ref" href="/lkm/2026/11/12/sched-20261112-014-sched-fair-cpu-max-runtime-and-idle-refill-for-cpu-credits.html">sched-20261112-014</a>（今天）：**Tejun 进一步论证为何 sched_ext 侧的 credit 交接不值得**——「在调度器崩溃（kernel 全 CPU/task 扫描、临时退化到 FIFO）的过渡里，credits 是否精确毫无意义」；**Fernand 接受，明确只专注 fair 侧补丁**，并指 v3（两 fair 补丁、已修 bot 意见）已在列表上。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/10/sched-20261110-003-sched-fair-cpu-max-runtime-and-idle-refill-for-cpu-credits.html">sched-20261110-003</a> / 20261111-008）作者运行以 CPU credits 计费的 VM：baseline 挣额度、超出花额度、额度有上限、花完压回 baseline。CFS bandwidth 控制器几乎就是这个信用桶，缺三件事：上限无法超过一个 quota、额度无法读/写、空闲组不挣额度。v2 额外加的 sched_ext 跨类集成被 Tejun 否掉，今日 Tejun 补齐了「为何不该做」的设计论证。

## 技术方案

（承接）今日为设计收口，无新代码：Tejun 论证 sched_ext 侧的 credit 交接在「调度器崩溃回退」这一过渡中失去意义——内核要扫描所有 CPU/task 中止在飞调度器、把所有任务推到临时 dumb FIFO 才能前进，此时 credits 是否精确已不是这台机器的主要问题；「以『最低可接受线』作为设计论据」不成立，设计必须有通用性理由。Fernand 接受，专注 fair 侧两补丁（v3 已发，`cover.1794398404.git.sieberf@amazon.com`）。

## 版本演进与当前进展

*current_version: v3（2026-11-11，`<cover.1794398404.git.sieberf@amazon.com>`）*。v3 只含 fair 侧两补丁（`cpu.max.runtime` + idle refill），已按 bpf-ci 意见修正 `cpu.max="max"` 语义与「去 quota 丢 runtime」行为。今日确认 sched_ext 侧彻底出局，系列最终形态 = fair-only。

## Maintainer 意见与讨论焦点

- **Tejun Heo（sched_ext 维护者）**：否定 v2 跨类集成的核心论据——「崩溃调度器」过渡中 credit 记账精度无意义；「最低可接受线」不是通用设计论据。
- **Fernand Sieber（作者）**：接受，明确「专注于 fair 补丁」，v3（fair-only、bot 意见已修）已在列表。
- 无 NAK（对 fair 侧）；sched_ext 侧被作者主动放弃。剩余问题是 fair 侧 v3 是否获 CFS 维护者（Peter/Ingo）评审通过。

## 合入评估

*likelihood=medium*。系列已收敛为 fair-only（v3），方向获 Tejun 认可；但「卖 burstable CPU 额度」用例本身被定性为 niche，且 patch 2 改变现有 `cpu.max.burst` 用户行为，仍需 CFS 侧维护者确认。*blocking_issues*：无硬阻塞；待 CFS 维护者评审 v3 并接受 patch 2 的行为变化。*next_action*：等 CFS 维护者评审 v3，评估 patch 2 行为变化的可接受性。

## 效果评估

无当日新增数据。此前（承接 20261111-008）：v3 自测 18/18 通过（含 9 个新增），无 lockdep 报告，两补丁在 W=1、含/不含 CONFIG_CFS_BANDWIDTH、32 位下无告警。

## 我可以参与的点

- **testing**：在真实 burstable VM/容器场景验证 kexec/reboot 前后读写 `cpu.max.runtime` 能否保住额度、idle 后变 runnable 的组是否按预期攒满 quota+burst。
- **review**：评估 patch 2 对现有 `cpu.max.burst` 用户的行为变化（idle 组醒来后额度从「停定时器时的值」变为「最多 quota+burst」）是否可接受——这是 CFS 维护者最可能质疑的点。

## 参考链接

- lore thread（v2）: https://lore.kernel.org/all/cover.1794303670.git.sieberf@amazon.com/
- Tejun 的设计论证: https://lore.kernel.org/all/e795d4feb4a4e7ca4cf24f3cde9e301b@kernel.org/
- Fernand 的 v3 告知: https://lore.kernel.org/all/20261112081144.38224-1-sieberf@amazon.com/
