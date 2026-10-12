---
id: sched-20261012-007
date: '2026-10-12'
subject: 'sched/cache: Avoid publishing partial LLC utilization'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261010113425.34829-1-jemmywong512@gmail.com>
lore_url: https://lore.kernel.org/all/20261010113425.34829-1-jemmywong512@gmail.com/
authors:
- Jemmy Wong
maintainers_involved:
- K Prateek Nayak
current_version: v1
patch_series:
- version: v1
  msgid: <20261010113425.34829-1-jemmywong512@gmail.com>
  date: '2026-10-10'
  summary: 发布 LLC 利用率前用 cpumask_subset() 校验 env->cpus 完整覆盖该组，避免发布「部分利用率+完整容量」
  review_outcome: Prateek 建议改用更便宜的 LBF_ALL_PINNED 标志检查，Jemmy 反驳并保留 cpumask_subset()
merge_assessment:
  likelihood: medium
  blocking_issues:
  - cpumask_subset() 与 LBF_ALL_PINNED 标志两种实现未收敛
  - hotplug 窗口覆盖性需 Prateek 确认
  next_action: 等 Prateek 认可 cpumask_subset() 的必要性，或补测热插拔窗口
contribution_opportunities:
- kind: testing
  description: 在 CPU hotplug + 亲和性重试并发下验证「部分利用率」是否仍会漏发
- kind: discussion
  description: 就 LBF_ALL_PINNED 语义（反映上一最忙 rq 而非当前组覆盖）与 cpumask_subset 的开销权衡发表意见
generated_at: '2026-10-13T01:40:00'
source_email_count: 2
related_articles:
- sched-20261010-004
tags:
- load_balance
title: 'sched/cache: Avoid publishing partial LLC utilization'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/10/sched-20261010-004-sched-cache-avoid-publishing-partial-llc-utilization.html">sched-20261010-004</a>：Jemmy Wong 修 cache-aware 调度的「部分 LLC 利用率」问题——`update_sg_lb_stats()` 对 `sched_group_span(group)` 与 `env->cpus` 两个可能不一致的集合求和利用率，`record_sg_llc_stats()` 会把「部分利用率 + 完整容量」一起发布，让 `can_migrate_llc()` 误判忙碌的 preferred LLC 为空。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-007-sched-cache-avoid-publishing-partial-llc-utilization.html">sched-20261012-007</a>（今天）：Prateek 建议用更便宜的 `LBF_ALL_PINNED` 标志检查替代 `cpumask_subset()`；Jemmy 反驳——该标志反映的是「上一个最忙 rq」，而非「当前被记录组是否被完整覆盖」，且漏掉 hotplug 窗口，坚持保留 `cpumask_subset()`。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/10/10/sched-20261010-004-sched-cache-avoid-publishing-partial-llc-utilization.html">sched-20261010-004</a>）当负载均衡因为 all-pinned 而 redo、或 CPU hotplug 使 `env->cpus` 与 `sched_group_span(group)` 不一致时，若仍把只覆盖部分 CPU 的利用率当作整组利用率发布，`can_migrate_llc()` 会做出错误判断。作者用 `cpumask_subset()` 保证「只有 env->cpus 完整覆盖该组才更新」。

## 技术方案

（承接 <a class="article-ref" href="/lkm/2026/10/10/sched-20261010-004-sched-cache-avoid-publishing-partial-llc-utilization.html">sched-20261010-004</a>）保持作者 v1 的 `cpumask_subset()` 方案。今日新增讨论：Prateek 提出 redo 到达该处时 `env->flags` 恒有 `LBF_ALL_PINNED`，可用该标志做更便宜的「env->cpus 覆盖全部 CPU」校验；Jemmy 逐条反驳——(1) `LBF_ALL_PINNED` 反映上一个最忙 rq 是否 all-pinned，不反映当前记录的组是否被完整覆盖（例：LLC0 的 cpu1 因 all-pinned 被拒后 redo，下次扫描带 `LBF_ALL_PINNED` 记录 LLC1 时该标志仍置位，但 LLC1 完整覆盖，标志检查会错误跳过更新，`cpumask_subset()` 不会）；(2) 标志检查漏掉 hotplug 窗口（cpu1 下线、domains 重建前新一次 balance 把 cpu1 排除出 env->cpus，组 span/capacity 仍含两 CPU，标志未置位会放行部分发布，`cpumask_subset()` 会拦截）。

## 版本演进与当前进展

v1（10-10）发出；今日（10-12）Prateek 提 nit、Jemmy 反驳后方案维持 v1 不变。

## Maintainer 意见与讨论焦点

K Prateek Nayak 提实现优化建议（LBF_ALL_PINNED 更便宜），Jemmy Wong 以两个具体反例（redo 语义 + hotplug 窗口）论证 `cpumask_subset()` 必要；分歧点已摆明，未见第三方裁决。

## 合入评估

*likelihood=medium*。修复动机清晰，但校验手段的取舍仍在讨论。*blocking_issues*：两种实现未收敛、hotplug 覆盖性待确认。*next_action*：Prateek 确认是否接受 `cpumask_subset()`，或作者补 hotplug 场景测试数据。

## 效果评估

无性能数字；Jemmy 的论证是正确性层面（避免误判 busy LLC），未附 benchmark。

## 我可以参与的点

- `testing`：构造 CPU hotplug 与 all-pinned redo 并发场景，验证「部分利用率」是否仍会被发布。
- `discussion`：对 `LBF_ALL_PINNED` 语义与 `cpumask_subset()` 的运行时开销权衡发表意见（后者对每组多一次 cpumask 遍历）。

## 参考链接

- lore（v1）: https://lore.kernel.org/all/20261010113425.34829-1-jemmywong512@gmail.com/
- lore（Prateek nit）: https://lore.kernel.org/all/7c4dbf1d-ba28-484d-b7e1-a713414c284d@amd.com/
- lore（Jemmy 反驳）: https://lore.kernel.org/all/A360FD1F-A067-4466-824F-5702E96F3E05@gmail.com/
