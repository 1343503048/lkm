---
id: sched-20261010-004
date: '2026-10-10'
subject: 'sched/cache: Avoid publishing partial LLC utilization'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261010113425.34829-1-jemmywong512@gmail.com>
lore_url: https://lore.kernel.org/all/20261010113425.34829-1-jemmywong512@gmail.com/
authors:
- Jemmy Wong
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261010113425.34829-1-jemmywong512@gmail.com>
  date: '2026-10-10'
  summary: env->cpus 未覆盖整组时跳过发布部分 LLC 利用率，保留上一份完整快照
  review_outcome: 当日无回帖
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无 review
  - 部分快照保留语义需 reviewer 确认
  next_action: 等 cache-aware 方向维护者 review
contribution_opportunities:
- kind: review
  description: 复核热插拔窗口保留旧快照是否引入新的误判
- kind: testing
  description: 构造 affinity-pinned 双 LLC 场景验证 can_migrate_llc() 误判是否消失
generated_at: '2026-10-11T09:00:00'
source_email_count: 1
related_articles: []
tags:
- cfs
- load_balance
title: 'sched/cache: Avoid publishing partial LLC utilization'
layout: article
---

## TL;DR
Jemmy Wong 修 cache-aware 调度的一个新问题（`[PATCH]`，当日新发）：`update_sg_lb_stats()` 对 `sched_group_span(group)` 与 `env->cpus` 两个可能不一致的 CPU 集合求和利用率、却用整组 `sgc->capacity` 求容量，`record_sg_llc_stats()` 把两者都发出去——亲和性重试或 CPU 热插拔会在两者不一致的窗口里发布「部分利用率 + 完整容量」，让 `can_migrate_llc()` 把忙碌的 preferred LLC 误判为有富余容量。补丁在 `env->cpus` 未覆盖整组时跳过发布、保留上一份完整快照。当日无回帖，`likelihood=unknown`。

## 背景与问题
`update_sg_lb_stats()` 把利用率按 `sched_group_span(group)` 和 `env->cpus` 两个集合求和，容量却取自整组的 `group->sgc->capacity`；`record_sg_llc_stats()` 把这两个量一并发布。当「拒绝掉一个 all-affinity-pinned 的源 runqueue」时，该 CPU 会从 `env->cpus` 移除并重试组选择——重试可能发布「部分利用率 + 完整容量」（作者举例：双 CPU LLC 上把 1800/2048 替换成 900/2048）。`can_migrate_llc()` 随之把忙碌的 preferred LLC 当成有富余容量：更多任务聚合进来、迁出受阻，两个忙碌 LLC 可能无法回退到通用均衡，加剧 CPU 争用与任务时延。作者注明此问题「Found by inspection」。

## 技术方案
单补丁（`kernel/sched/fair.c` +7）：在 `record_sg_llc_stats()` 里，当 `env->cpus` 未完整覆盖 `sched_group_span(group)` 时直接返回，不发布部分利用率——部分扫描保留上一份完整快照，其它组照常刷新，负载均衡仍使用亲和性过滤后的统计。作者同时指出 CPU 热插拔存在同样的不一致窗口（`set_cpu_active(false)` 移走 CPU，但组 span 与 `sgc->capacity` 仍含该 CPU，直到 `cpuset_cpu_inactive()` 重建域），保留旧快照同样避免错误发布；重建后下一个周期均衡会重新记录。

## 版本演进与当前进展
*current_version: v1*（单枚，`<20261010113425.34829-1-jemmywong512@gmail.com>`）。当日新发，无回帖、无维护者 review。

## Maintainer 意见与讨论焦点
当日无回帖。与作者同日另发的 exec footprint 修复（见 <a class="article-ref" href="/lkm/2026/10/10/sched-20261010-003-sched-cache-remove-the-old-cache-group-footprint-on-exec.html">sched-20261010-003</a>）同属 cache-aware 记账方向，但本枚针对「LLC 统计发布」路径、独立成篇。潜在评审点（无人提出）：「跳过发布、保留上一份快照」在热插拔期间的陈旧窗口是否可接受。

## 合入评估
*likelihood=unknown*。当日新发、无回帖，无 cache-aware 方向维护者表态。*blocking_issues*：无 review；部分快照保留的语义需要 reviewer 确认。*next_action*：等 cache-aware 系列维护者 review。

## 效果评估
暂无效果数据。作者给出的 900/2048 vs 1800/2048 属构造出的示意（两 CPU LLC），非实测；影响（争用与时延上升）为作者基于代码逻辑的推断，未见复现数据。

## 我可以参与的点
- 复核「跳过发布、保留旧快照」在热插拔窗口的陈旧窗口是否引入新的误判；
- 构造 affinity-pinned 的双 LLC 场景，验证修复前后 `can_migrate_llc()` 的误判是否消失。

## 参考链接
- patch: https://lore.kernel.org/all/20261010113425.34829-1-jemmywong512@gmail.com/
