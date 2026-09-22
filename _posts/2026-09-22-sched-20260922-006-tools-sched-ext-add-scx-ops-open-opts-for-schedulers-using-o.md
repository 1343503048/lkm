---
id: sched-20260922-006
date: '2026-09-22'
subject: 'tools/sched_ext: Add SCX_OPS_OPEN_OPTS for schedulers using open opts'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260922031618.2858-1-zhaofuyu@vivo.com>
lore_url: https://lore.kernel.org/all/20260922031618.2858-1-zhaofuyu@vivo.com/
authors:
- Fuyu Zhao
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20260922031618.2858-1-zhaofuyu@vivo.com>
  date: '2026-09-22'
  summary: 新增 SCX_OPS_OPEN_OPTS 宏，保留兼容检查同时允许传 open opts
  review_outcome: Tejun 建议 SCX_OPS_OPEN 以 0 opts 调 SCX_OPS_OPEN_OPTS 收敛实现
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 宏实现有两份展开，待按 Tejun 建议收敛
  next_action: 作者按 SCX_OPS_OPEN 调 SCX_OPS_OPEN_OPTS(0) 方向改版重投
contribution_opportunities:
- kind: testing
  description: 在用到 open opts 的调度器上验证兼容检查与打开行为
- kind: review
  description: 确认收敛后各调度器（含旧宏用户）无回归
generated_at: '2026-09-23T00:00:00'
source_email_count: 2
related_articles: []
tags:
- sched_ext
title: 'tools/sched_ext: Add SCX_OPS_OPEN_OPTS for schedulers using open opts'
layout: article
---

## TL;DR
Fuyu Zhao 为 sched_ext 工具链新增 `SCX_OPS_OPEN_OPTS()` 宏，让调度器在打开 BPF skeleton 时能传入自定义 `bpf_object_open_opts`，同时保留 `SCX_OPS_OPEN()` 的兼容性检查。此前直接用 bpftool 生成的 `*_open_opts()` 会绕过 `SCX_OPS_OPEN()` 的兼容校验。Tejun Heo 回帖建议 `SCX_OPS_OPEN()` 直接以 0 为 opts 调用 `SCX_OPS_OPEN_OPTS()` 来减少重复。

## 背景与问题
`sched_ext` 调度器用 `SCX_OPS_OPEN()` 宏打开 BPF skeleton，内部做 kernel 版本兼容性检查（`hotplug_seq` 注入、`dump()` 字段存在性、`cgroup_set_bandwidth` 等）。有些调度器需要向 `bpf_object__open` 传额外 open opts，但 bpftool 生成的 `*_open_opts()` 接口会完全绕过 `SCX_OPS_OPEN()` 的兼容处理。

## 技术方案
把 `__SCX_OPS_OPEN` 重构为接受一个 open 表达式（`__open_expr`），新增 `SCX_OPS_OPEN_OPTS(__ops_name, __scx_name, __opts)` 宏：内部仍走同一套兼容性检查（`dump()` 检查、`hotplug_seq`、`SCX_ENUM_INIT`、`cgroup_set_bandwidth` 告警），只是把 skeleton 打开动作换成 `__scx_name##__open_opts(__opts)`。`SCX_OPS_OPEN()` 保留为旧宏，展开为以 `__scx_name##__open()` 为 open 表达式。`tools/sched_ext/include/scx/compat.h` 改动约 +15/-5 行。

## 版本演进与当前进展
v1 当日发出。Tejun Heo 回帖提问：「Can SCX_OPS_OPEN() just call SCX_OPS_OPEN_OPTS() with 0 as opts?」——建议收敛为一个实现，尚无作者回复与新版。

## Maintainer 意见与讨论焦点
- **Tejun Heo**：方向认可（保留兼容处理是对的），但希望实现上避免两份 `SCX_OPS_OPEN`/`SCX_OPS_OPEN_OPTS` 的重复展开，建议 `SCX_OPS_OPEN` 内部以 0 opts 调 `SCX_OPS_OPEN_OPTS`。无争议性反对。

## 合入评估
likelihood=medium。方向无异议，但需按 Tejun 建议收敛实现后再审。blocking_issues：宏实现有重复、待作者按「SCX_OPS_OPEN 调 SCX_OPS_OPEN_OPTS(0)」方向改版。next_action：作者改版后重新提交。

## 效果评估
无性能数据，纯工具链易用性增强（允许传入 open opts 而不丢兼容检查）。

## 我可以参与的点
- **testing**：在用到 open opts 的 sched_ext 调度器上验证新宏的兼容检查与 skeleton 打开行为。
- **review**：确认 `SCX_OPS_OPEN_OPTS` 与 `SCX_OPS_OPEN` 收敛后各调度器（尤其已用旧宏的）无回归。

## 参考链接
- lore thread: https://lore.kernel.org/all/20260922031618.2858-1-zhaofuyu@vivo.com/
