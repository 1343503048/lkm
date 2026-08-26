---
id: sched-20260826-010
date: 2026-08-26
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: unknown
lore_url: unknown
authors:
- Tim Chen
maintainers_involved:
- Ricardo Neri
- Chen Yu
current_version: v1
patch_series:
- version: v1
  msgid: unknown
  date: 2026-08-26
  summary: 修复 cache-aware 负载均衡在非对称系统上创建 misfit 任务的问题
  review_outcome: Ricardo Neri Reviewed-by + Tested-by, Chen Yu Reviewed-by
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待调度维护者合入
contribution_opportunities:
- kind: testing
  description: 在 ARM big.LITTLE 或 Intel hybrid 平台上 benchmark 验证性能影响
generated_at: '2026-08-27T01:28:00'
source_email_count: 1
related_articles: []
tags:
- cfs
- load_balance
title: 'sched/fair: avoid creating misfits during cache-aware balancing'
layout: article
---

## TL;DR

Tim Chen (Intel) 提交补丁修复 cache-aware 负载均衡在非对称 CPU 容量系统（如 big.LITTLE）上创建 misfit 任务的问题。当 cache-aware 迁移将任务拉向目标 LLC 时，目标 LLC 中的 CPU 可能容量不足，导致任务从 fit 变为 misfit——用缓存局部性收益换取了更大的容量损失。补丁在 `can_migrate_llc_task()` 和 `alb_break_llc()` 中添加容量检查，并已在混合处理器上验证。已获 Ricardo Neri 和 Chen Yu 的 Reviewed-by。

## 背景与问题

Cache-aware 负载均衡将任务偏向其偏好的 LLC（Last Level Cache）。在非对称 CPU 容量系统上（如 big.LITTLE、Intel hybrid），目标 LLC 可能包含容量较小的 CPU。将任务从大核迁移到小核的 LLC 虽然获得了缓存局部性，但容量损失更大，任务变成了 misfit。

## 技术方案

1. **`can_migrate_llc_task()`**：当任务适合源 CPU 但不适合目标 CPU 时，禁止 LLC 迁移
2. **`alb_break_llc()`**：在同一条件下否决 active balance，防止将 runnable 任务推到无法容纳它的 CPU
3. 两项检查都通过混合处理器检查门控，对称系统不受影响
4. 已经不适合源 CPU 的任务留给现有 LLC 策略（移动不会使 fitness 更差，同时保留 misfit up-migration 到大核的路径）
5. 如果在负载均衡分类阶段发现 misfit 任务，在非对称系统上优先处理 misfit 迁移而非 LLC 聚合

## 版本演进与当前进展

v1 刚发出。已获 Ricardo Neri (Intel) 的 `Reviewed-by` + `Tested-by` 和 Chen Yu (Intel) 的 `Reviewed-by`。Tim Chen 在回复中补充了 `Signed-off-by`。

## Maintainer 意见与讨论焦点

Ricardo Neri 和 Chen Yu 都给出了正面 review。无争议点。

## 合入评估

- **likelihood**: high（已有 2 个 Reviewed-by + 1 个 Tested-by，方案合理）
- **blocking_issues**: 无
- **next_action**: 等待调度维护者合入

## 效果评估

作者主观判断：在非对称系统上，避免 misfit 比获得缓存局部性更重要（"A better fitting CPU will boost performance more than better cache locality"）。未见具体 benchmark 数据。

## 我可以参与的点

- 可以在 ARM big.LITTLE 或 Intel hybrid 平台上跑 benchmark 验证性能影响
- 可以测试对称系统上补丁确实无影响（回归测试）

## 参考链接

- lore thread: 未获取到
