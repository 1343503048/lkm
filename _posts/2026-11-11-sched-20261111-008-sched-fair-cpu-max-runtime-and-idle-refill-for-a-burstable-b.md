---
id: sched-20261111-008
date: '2026-11-11'
subject: 'sched/fair: cpu.max.runtime and idle refill for a burstable budget'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <cover.1794398404.git.sieberf@amazon.com>
lore_url: https://lore.kernel.org/all/cover.1794398404.git.sieberf@amazon.com/
authors:
- Fernand Sieber
maintainers_involved:
- Tejun Heo
current_version: v3
patch_series:
- version: v3
  msgid: <cover.1794398404.git.sieberf@amazon.com>
  date: '2026-11-11'
  summary: 砍掉 sched_ext 侧，只留 cpu.max.runtime 与 idle refill 两补丁，修正 max 语义
  review_outcome: Tejun 要求 fair-only 已落实；待 CFS 维护者评审
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: 等 CFS 维护者评审 v3 并评估 patch 2 的行为变化
contribution_opportunities:
- kind: testing
  description: 在真实 burstable VM 场景验证 kexec/reboot 前后额度读写与 idle refill 行为
- kind: review
  description: 评估 patch 2 对现有 cpu.max.burst 用户的行为变化可接受性
generated_at: '2026-11-12T09:00:00+08:00'
source_email_count: 8
related_articles:
- sched-20261110-003
tags:
- cfs
- cgroup
title: 'sched/fair: cpu.max.runtime and idle refill for a burstable budget'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/10/sched-20261110-003-sched-fair-cpu-max-runtime-and-idle-refill-for-cpu-credits.html">sched-20261110-003</a>：Fernand Sieber（Amazon）发 v2 四补丁系列，为 CFS 带宽控制器补上「CPU credits」场景的三个能力：新增 `cpu.max.runtime` 读写文件、解除 `cpu.max.burst` 不能超过一个 quota 的限制、让空闲组在 idle 期间持续挣取额度；补丁 3/4 把额度透传给 BPF 调度器并把 SCX 任务计入同一 runtime。
- <a class="article-ref" href="/lkm/2026/11/11/sched-20261111-008-sched-fair-cpu-max-runtime-and-idle-refill-for-a-burstable-b.html">sched-20261111-008</a>（今天）：**Tejun Heo 明确否定 v2 的 maximalist 方案，作者改发 v3（只保留 fair 侧两补丁）**——Tejun 认为用例（卖 burstable CPU 额度）太 niche、且同时侵入 fair 与 sched_ext 并让二者无缝交接的成本过高，要求「先单独做 fair 侧、sched_ext 部分用你自己的 BPF 调度器实现」。作者接受，v3 砍掉 patch 3/4，只保留 `cpu.max.runtime` 与 idle refill 两补丁；并针对 bpf-ci 的三条 AI 评审修正了 `cpu.max.runtime` 在 `cpu.max="max"` 时的读值语义与「去掉 quota 即丢 runtime」的行为。v3 自测 18/18 通过（含 9 个新增）。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/10/sched-20261110-003-sched-fair-cpu-max-runtime-and-idle-refill-for-cpu-credits.html">sched-20261110-003</a>）作者运行以 CPU credits 计费的 VM：每个实例有 baseline（挣额度速率）、运行时低于 baseline 挣额度、高于 baseline 花额度、额度有上限，花完被压回 baseline。CFS bandwidth 控制器几乎就是那个信用桶，缺三件事：上限无法超过一个 quota、额度无法读/写、空闲组不挣额度。v2 额外加了「额度在 fair 与 sched_ext 之间无缝交接」两个补丁，Tejun 认为这部分跨类集成「没有强用例、成本远超收益」，要求砍掉。

## 技术方案

v3 只保留两补丁：

1. `sched/fair: expose cpu.max.runtime to set bandwidth runtime directly`——新增 cgroup v2 `cpu.max.runtime`（读写 `cfs_b->runtime`，微秒）；写被拒绝（无 quota 时）或限制在 quota+burst 内；解除 burst≤quota 限制，改为只要求 quota+burst ≤ max_bw_runtime_us（约 203 天）；写把新 runtime 立即分发给 throttled cfs_rq 并平移 `runtime_snap` 以保持 burst 记账一致。v3 修正：`cpu.max="max"` 时读返回 0、写返回 EINVAL；去掉 quota 会丢弃已有 runtime 而非保留。
2. `sched/fair: refill bandwidth for the periods the timer slept through`——period 定时器在组无运行的一个 period 后停止，重启时 `hrtimer_forward_now()` 丢弃睡过的 period；改为计数错过的 period 并在重启时按 quota 逐个补 refill（上限 quota+burst）。改变现有 `cpu.max.burst` 用户行为：idle 后变 runnable 的组拥有最多 quota+burst。

## 版本演进与当前进展

*current_version: v3（2026-11-11，`<cover.1794398404.git.sieberf@amazon.com>`）*。v3 相对 v2：砍掉 sched_ext 侧（patch 3/4，Tejun 要求）；`cpu.max.runtime` 在 `cpu.max="max"` 时读 0、去掉 quota 丢 runtime（bpf-ci 反馈）；删除 `distribute_cfs_runtime()` 的 `lockdep_assert_irqs_disabled()`（PREEMPT_RT 下两个 bandwidth timer 都以 hardirq 使能运行）；burst_kept 自测更新。作者注明 Claude Code 协助写 selftests/changelog 并跑构建测试矩阵，本人复核。

## Maintainer 意见与讨论焦点

- **Tejun Heo（sched_ext 维护者）**：明确否定 v2 的跨类集成——「too maximalist」「用例 niche」「在 fair 和 sched_ext 里同时改并让二者无缝交接对没有强用例的东西太多余」；认可「若 burstable budget 对 fair 有价值，先单独做」，并给出降级方案（sched_ext 部分用作者自己的 BPF 调度器实现，credit 是 BPF map 里的状态，交接可走用户态）。
- **bpf-ci（AI 评审 bot）**：三条——`cgroup_set_runtime` 的「不超过最近给定 quota」保证在缺 `cgroup_set_bandwidth` 的调度器上不成立；`cpu.max="max"` 时 `cpu.max.runtime` 读回陈旧值；selftest 的 `join_path()`/`cgroup_id()`/`controller_enabled()` 与 `cgroup_nr_cpus.c` 重复。作者在 v3 修了前两条语义，第三条属 nit。
- **Fernand Sieber（作者）**：接受砍 sched_ext 侧，但指出用户态交接唯一覆盖不到的 case 是「BPF 调度器出错/被 watchdog 杀掉、非计划回退到 fair」——此时没有用户态交接窗口，额度会丢。

## 合入评估

*likelihood=medium*。v3 已按 Tejun 的要求收敛为纯 fair 侧、方向获认可，但「卖 burstable CPU 额度」这一用例本身被 Tejun 定性为 niche，且 patch 2 会改变现有 `cpu.max.burst` 用户的行为，仍需 CFS 侧维护者（Peter/Ingo）确认接受。*blocking_issues*：无硬阻塞；风险在于 niche 用例的正当性尚未获广泛认同。*next_action*：等 CFS 维护者评审 v3（fair-only）并评估 patch 2 的行为变化可接受性。

## 效果评估

作者给出功能自测：tip/sched/core + qemu + lockdep 下 cgroup test_cpu 18/18 通过（含 9 个新增），无 lockdep 报告；两补丁在 W=1、含/不含 CONFIG_CFS_BANDWIDTH、32 位下均无告警。无端到端性能/额度收益数据。

## 我可以参与的点

- **testing**：在真实 burstable VM/容器场景验证「kexec/reboot 前后读写 `cpu.max.runtime`」能否保住额度、以及 idle 后变 runnable 的组是否按预期攒满 quota+burst。
- **review**：评估 patch 2 对现有 `cpu.max.burst` 用户的行为变化（idle 组醒来后额度从「停定时器时的值」变为「最多 quota+burst」）是否可接受，这是 Tejun 之后 CFS 维护者最可能质疑的点。

## 参考链接

- lore thread: https://lore.kernel.org/all/cover.1794398404.git.sieberf@amazon.com/
- v2 cover: https://lore.kernel.org/all/cover.1794303670.git.sieberf@amazon.com/
- Tejun 对 v2 的否定: https://lore.kernel.org/all/3bdd435fd868ed7ca7ea9061e5966b7b@kernel.org/
