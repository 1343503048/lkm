---
id: sched-20261105-008
date: 2026-11-05
subject: 'sched/cache: Fix group_llc_balance being unreachable above the first NUMA
  level'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261104141313.185433-1-wujianyong@hygon.cn>
lore_url: https://lore.kernel.org/all/20261104141313.185433-1-wujianyong@hygon.cn/
authors:
- Jianyong Wu
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261104141313.185433-1-wujianyong@hygon.cn>
  date: 2026-11-04
  summary: 让 group_llc_balance 在第一层 NUMA 之上可达，恢复任务被拉回首选 LLC。
  review_outcome: Tim Chen 提供重构、Chen Yu 要求 benchmark；作者将并入 v2 并 drop Fixes。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 缺少 v2 与 benchmark 数据（NUMA balancing 开/关）
  next_action: 发 v2 并入 Tim 的重构并附 benchmark 数字
contribution_opportunities:
- kind: testing
  description: 在 SNC/NPS 多层域系统测 NUMA balancing 开关下的任务回拉与回归
- kind: review
  description: 核对 busiest_llc_balance 重构在各配置下的编译与 static branch 行为
generated_at: '2026-11-06T09:00:00+08:00'
source_email_count: 4
related_articles: []
tags:
- load_balance
- numa_balancing
- topology
title: 'sched/cache: Fix group_llc_balance being unreachable above the first NUMA
  level'
layout: article
---

## TL;DR

Jianyong Wu（Hygon）的补丁修复 cache-aware 调度里 `group_llc_balance` 这一 LLC 级任务聚合在「第一层 NUMA 之上」不可达的问题：此前任务一旦落到第一层 NUMA 之外，mainline 不会再把任务拉回其首选 LLC。Intel 的 Tim Chen / Chen Yu 给出积极反馈与更清晰的重构版本，作者将把 Tim 的版本并入 v2 并补充 NUMA balancing 开关下的 benchmark 数据。

## 背景与问题

该补丁从作者早前「把 cache-aware 调度扩展到 LLC 粒度」的大系列中拆出。作者同事 Yibin 发现：缺少本补丁时，任务位于第一层 NUMA 之外后，mainline 不会再把任务拉回其首选 LLC——即 `group_llc_balance` 的 LLC 任务聚合只在第一层 NUMA 内生效，跨层后失效。Chen Yu 指出这实际是「增强」而非「修复」：补丁前 NUMA 层任务聚合被禁用、仅 SNC/第一层 Nodes 级聚合开启，补丁后 NUMA 层与 SNC 层都开启聚合。

## 技术方案

补丁让 `group_llc_balance` 在更高层的调度域也可达。Tim Chen 建议重构：新增 `busiest_llc_balance()` 内联 helper（`sched_cache_enabled() && busiest->group_type == group_llc_balance`），并吸收 Peter Zijlstra 在作者更早提案（lore 20260827122816）中的意见——在非 cache-aware 调度下不做 llc_balance 检查。作者认可该版本「更清晰也更便宜：非 cache-aware 时该 group type 检查被编译出或经 static branch 跳过」，将并入 v2。

## 版本演进与当前进展

*current_version: v1*。今日无新版本；作者确认会在 v2 中采纳 Tim Chen 的重构版本，并（回应 Chen Yu）放弃 `Fixes:` 标签、补充 NUMA balancing 开/关两组 benchmark 数据。

## Maintainer 意见与讨论焦点

无调度维护者直接表态；两位 Intel 调度工程师（Tim Chen、Chen Yu）给出实质评审：Tim Chen 提供更清晰且更便宜的重构（非 cache-aware 下跳过检查，并入 Peter 在早期提案中的意见）；Chen Yu 质疑其「fix vs 增强」的定位并明确要求 v2 附上 benchmark（NUMA balancing 开关、SNC 等多层域系统上「有收益且无回归」的证据）。作者全盘接受。

## 合入评估

*likelihood=medium*。方向得到 Intel 侧积极评审与具体重构代码，但尚需 v2 + benchmark 数据证明「多层域系统上有收益且无回归」。*blocking_issues*：① 缺少 v2 与 benchmark 数据；② fix/enhancement 定位需作者在 changelog 中重新表述（已决定 drop Fixes tag）。*next_action*：作者发 v2（并入 Tim 的重构），附 NUMA balancing 开/关的 benchmark 数字。

## 效果评估

暂无量化数据。Chen Yu 明确要求「多层域系统（NUMA balancing 开关等）上无回归且有收益」的 benchmark 支撑，作者承诺在 v2 中提供。

## 我可以参与的点

- testing：在 Intel SNC 或 AMD/Hygon NPS 多层域系统上测 v2，重点验证 NUMA balancing 开/关两种配置下任务是否被正确拉回首选 LLC、且无跨 NUMA 迁移回归。
- review：核对 `busiest_llc_balance()` 重构在 `!CONFIG_SCHED_DEBUG` 等配置下的编译与 static branch 行为。

## 参考链接

- lore thread（补丁）: https://lore.kernel.org/all/20261104141313.185433-1-wujianyong@hygon.cn/
- Tim Chen 重构建议: https://lore.kernel.org/all/5b9e949a64935bc280ae72b3acea80745a5600f3.camel@linux.intel.com/
