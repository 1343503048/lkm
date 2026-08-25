---
title: "sched_ext：允许 ops.cgroup_set_weight/idle() 可睡眠"
date: 2026-08-25
tags: [sched_ext, cgroup]
series: "sched_ext cgroup_set sleepable"
type: feature
severity: low
status: under_review
lore: ""
---

## 概述

`sched_ext` 的 `ops.cgroup_set_weight()` / `ops.cgroup_set_idle()` 回调当前要求
不可睡眠（原子上下文），限制了 BPF 调度器在回调里执行可能阻塞的操作（如更复杂
的簿记、锁或分配）。本期提出允许这两个回调睡眠，放宽其上下文约束。

## 改动内容 / 核心补丁

- 调整 cgroup knob 更新路径，使 `ops.cgroup_set_weight/idle()` 可在可睡眠上下文
  中被调用（涉及 cgroup knob 更新串行化，见 003）。
- 与 003（Serialize cgroup knob updates）配合：串行化后可在持有适当锁/上下文下
  允许睡眠回调。

## 状态与讨论

- 当前状态：**under_review**（原始补丁 UID 56457，含多条 Re: 讨论 56719/56904）。
- 注意：本系列与 003 的 cgroup knob 串行化高度相关，评审中可能合并考量。

## 关联

- 001 sched_ext：scx_cgroup_init_args 传递 sched_idle（v3）
- 003 sched_ext：Serialize cgroup knob updates（for-7.3-fixes）
- 005 sched：cgroup 更新锁上提到 core
