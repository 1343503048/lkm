---
id: sched-20261111-020
date: '2026-11-11'
subject: 'cpuidle: cpu_idle_miss accounting fixes'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261111115902.1904523-1-christian.loehle@arm.com>
lore_url: https://lore.kernel.org/all/20261111115902.1904523-1-christian.loehle@arm.com/
authors:
- Christian Loehle
maintainers_involved:
- Rafael J. Wysocki
current_version: v2
patch_series:
- version: v2
  msgid: <20261111115902.1904523-1-christian.loehle@arm.com>
  date: '2026-11-11'
  summary: 排除 broadcast fallback 的 miss 记账；selection 前统一采样 QoS 供记账复用
  review_outcome: 回应 Rafael 两个问题；等 v2 评审
upstream_commit: null
fixes_commit: 04dab58a39d4
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - v2 的较大重构是否影响 stable 可回退性待确认
  next_action: Rafael 评审 v2 后收取
contribution_opportunities:
- kind: testing
  description: 在其它带 timer broadcast 平台上复测 patch 1 的 miss 统计改善
- kind: review
  description: 评估统一采样 QoS 是否漏掉 governor 内部另行取约束的路径
generated_at: '2026-11-12T09:00:00+08:00'
source_email_count: 7
related_articles:
- sched-20261030-016
- sched-20261105-023
tags:
- idle
title: 'cpuidle: cpu_idle_miss accounting fixes'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/10/30/sched-20261030-016-cpuidle-idle-miss-accounting-fixes.html">sched-20261030-016</a> / <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-023-cpuidle-idle-miss-accounting-fixes.html">sched-20261105-023</a>：Christian Loehle 的两补丁系列修复 cpuidle 的 idle_miss 记账，方向获 Rafael J. Wysocki 初步认可。
- <a class="article-ref" href="/lkm/2026/11/11/sched-20261111-020-cpuidle-cpu-idle-miss-accounting-fixes.html">sched-20261111-020</a>（今天）：**作者回应 Rafael 对 v1 的两个问题并发出 v2**——Rafael 问「broadcast fallback 跳过记账是理论问题还是实际可观测」，作者答「真实问题，约占 arm64 上 5% 的 idle_miss」；Rafael 问「below miss 用的延迟约束与 governor 实际用的不同怎么办」，作者承认「selection 后只几个 cycle，你是对的」，v2 改为在 `cpuidle_select()` 里采样一次 QoS 并保存到 `dev->latency_req` 供 governor 与记账共用。v2 新增 broadcast fallback 观测统计（Orion O6 上 90.4% 的 below miss 来自 fallback，排除后 miss ratio 9.06%→7.83%）。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/10/30/sched-20261030-016-cpuidle-idle-miss-accounting-fixes.html">sched-20261030-016</a> / 20261105-023）cpuidle 的 `idle_miss`（above/below）记账有两点缺陷：① 当 `tick_broadcast_enter()` 失败、core 强制选更浅状态时，这些被迫的 fallback 被当作 governor 的「below miss」记入——但这不是 governor 预测错误；② 一个被判为 above/below miss 的更深状态可能违反复用延迟 QoS 约束，造成假 below miss。二者都让 `cpu_idle_miss` 这个 trace 事件失真，影响基于它的 idle 分析。

## 技术方案

v2 两补丁：

1. `Skip miss accounting for timer broadcast fallbacks`——`tick_broadcast_enter()` 失败导致的 fallback（`broadcast_failed`）直接 `goto out`，跳过 above/below miss 记账，但保留 residency/usage/governor 反馈。`Fixes: 04dab58a39d4`。
2. `Respect latency constraints when accounting below misses`——在 `cpuidle_select()` 里用 `cpuidle_governor_latency_req()` 采样一次 QoS 并存入 `dev->latency_req`，governor 与 miss 记账共用同一约束；`cpuidle_enter_state()` 里排除 `exit_latency_ns > dev->latency_req` 的更深状态，不做额外的 state 表遍历。`Fixes: 04dab58a39d4`。

## 版本演进与当前进展

*current_version: v2（2026-11-11，`<20261111115902.1904523-1-christian.loehle@arm.com>`）*。v1→v2：patch 1 加 broadcast fallback 观测统计（Rafael 要求）；patch 2 改为 selection 前采样一次 QoS 并复用（Rafael 建议）。作者注明 v2 的更大重构让 backport 吸引力下降，但极大提升 `cpu_idle_miss` trace 在「运行期动态改延迟约束的旧 stable Android」场景下的价值。

## Maintainer 意见与讨论焦点

- **Rafael J. Wysocki（cpuidle 维护者）**：v1 阶段两个问题——①「这是理论问题还是实际可观测？」②「below miss 用的约束与 governor 实际用的不同怎么办？」。作者已在 v2 回应：①实测可观测（arm64 约 5% 的 idle_miss）；②采样一次并共享，消除不一致。
- 无 NAK。方向获维护者认可，处于低争议的待收取状态。

## 合入评估

*likelihood=high*。两补丁带明确 `Fixes:`、Rafael 的问题均已回应并有实测数据支撑，方向无异议；但 v2 比 v1 重构更广，会在 stable backport 上引入取舍。*blocking_issues*：无硬阻塞；v2 的较大重构是否影响 stable 可回退性待确认。*next_action*：Rafael 评审 v2 后收取。

## 效果评估

作者给出 Orion O6（menu+TEO，schbench/tbench/hackbench）实测：6930 个 cpu_idle_miss 打在 8172 个 broadcast fallback 上，打 patch 1 后 7763 个 fallback 上 0 个；9782/33136 个 fallback 触发 below miss（占总 below miss 的 90.4%），排除后 miss ratio 从 9.06% 降到 7.83%。

## 我可以参与的点

- **testing**：在其它带 timer broadcast 的平台上复测 patch 1，确认 broadcast fallback 排除对 miss 统计的改善幅度是否一致。
- **review**：评估 v2 在 `cpuidle_select()` 里统一采样 QoS 是否会漏掉 governor 内部另行取约束的路径。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261111115902.1904523-1-christian.loehle@arm.com/
- 作者对 Rafael 的回应（1/2）: https://lore.kernel.org/all/77dc00cf-49ce-4f3e-a2fd-32c80f9b8b5a@arm.com/
- 作者对 Rafael 的回应（2/2）: https://lore.kernel.org/all/f50285a8-61b6-4173-8f91-6259d3e595e8@arm.com/
