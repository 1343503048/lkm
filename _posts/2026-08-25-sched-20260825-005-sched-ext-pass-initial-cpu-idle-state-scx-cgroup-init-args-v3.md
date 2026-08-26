---
id: sched-20260825-005
date: 2026-08-25
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260825023557.27881-1-cui.tao@linux.dev>
lore_url: https://lore.kernel.org/r/20260825023557.27881-1-cui.tao@linux.dev
authors:
- Tao Cui
maintainers_involved:
- Tejun Heo
- Andrea Righi
current_version: v3
patch_series:
- version: v1
  msgid: <20260824133954.561956-1-cui.tao@linux.dev>
  date: 2026-08-24
  summary: 初始版本，在 scx_cgroup_init_args 中添加 idle 字段
  review_outcome: Tejun 建议重命名为 sched_idle，Andrea 建议添加 Fixes 标签
- version: v2
  msgid: <20260824142817.568085-1-cui.tao@linux.dev>
  date: 2026-08-24
  summary: v2 修订
  review_outcome: Tejun 给出字段重命名建议
- version: v3
  msgid: <20260825023557.27881-1-cui.tao@linux.dev>
  date: 2026-08-25
  summary: 字段重命名为 sched_idle，拆分为 2-patch，添加 Fixes 标签
  review_outcome: Andrea Righi Reviewed-by
upstream_commit: null
fixes_commit: 347ed2d566da
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 Tejun Heo 最终 ack 并 apply
contribution_opportunities: []
generated_at: '2026-08-27T10:00:00'
source_email_count: 8
related_articles: []
tags:
- sched_ext
- cgroup
title: 'sched_ext: pass the initial cpu.idle state in scx_cgroup_init_args'
layout: article
---

## TL;DR

Tao Cui 的 v3 修复了 sched_ext cgroup 初始化时不传递 `cpu.idle` 状态的缺陷：已在调度器加载前配置为 idle 的 cgroup，BPF 调度器在 `ops.cgroup_init()` 中看不到其 idle 状态。v3 按 Tejun Heo 建议将新字段命名为 `sched_idle`，并获 Andrea Righi Reviewed-by。2-patch 系列：patch 1 是修复，patch 2 是配套重命名。

## 背景与问题

`scx_cgroup_init_args` 携带 cgroup 的初始 weight 和带宽参数到 `ops.cgroup_init()`，但缺少 `cpu.idle` 状态。这意味着：
- 在调度器加载前已配置 `cpu.idle=1` 的 cgroup，BPF 调度器看到它是 non-idle
- 只有后续再次写入 `cpu.idle` 时，调度器才通过 `ops.cgroup_set_idle()` 得知

这是 cpu controller 中唯一没有传递初始值的 knob。

## 技术方案

- 在 `scx_cgroup_init_args` 中新增 `sched_idle` 字段
- 在四个构造点填充：`scx_tg_online()`、`scx_cgroup_init()`、`scx_cgroup_claim_subtree()`、`scx_cgroup_return_subtree()`
- patch 2 将 `tg->scx.idle` 重命名为 `tg->scx.sched_idle`（纯重命名，无行为变更）

v2→v3 改动：
- 字段从 `idle` 改名为 `sched_idle`（Tejun 建议，避免与 CPU idle 状态混淆）
- 将 `tg->scx.idle` 重命名拆为独立 patch 2（方便 stable 回合）
- 添加 Fixes 标签（Andrea 建议）
- 在 linux-next 上重新生成

## 版本演进与当前进展

v3，已获 Andrea Righi Reviewed-by。Tejun Heo 在 v2 阶段给出了字段重命名建议，v3 已采纳。

## Maintainer 意见与讨论焦点

- **Tejun Heo**（v2 review）：建议将字段命名为 `sched_idle`，因为 "idle" 在 sched_ext 中默认指 CPU idle 状态；同时建议重命名 `tg->scx.idle` 保持一致
- **Andrea Righi**（v3 review）：Reviewed-by，并建议添加 Fixes 标签
- **Tao Cui** 在测试中还发现 `scx_group_set_idle()` 在重复写入相同值时仍触发回调（与 weight/bandwidth 行为不一致），计划在此系列之上单独修复

## 合入评估

- **likelihood: high** — 已获 Andrea Reviewed-by，Tejun 的建议已采纳，Fixes 标签齐全
- **blocking_issues**: 无
- **next_action**: 等待 Tejun 最终 ack 并 apply

## 效果评估

作者在 VM 中用 probe 调度器验证：配置 `cpu.idle=1` 后加载调度器，`ops.cgroup_init()` 正确收到 `sched_idle=1`。无性能数据（正确性修复）。

## 我可以参与的点

- 当前阶段系列已成熟（v3 + Reviewed-by），暂无明显参与空间
- Tao Cui 提到的 `scx_group_set_idle()` 重复写入问题可能是一个独立的小修复机会

## 参考链接

- lore thread (v3): https://lore.kernel.org/r/20260825023557.27881-1-cui.tao@linux.dev
- lore thread (v2): https://lore.kernel.org/r/20260824142817.568085-1-cui.tao@linux.dev
- Fixes: 347ed2d566da ("sched/ext: Implement cgroup_set_idle() callback")
- tip-bot commit: 未获取到
