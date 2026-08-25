---
title: sched-20260824-001-sched_ext-cgroup-init-cpu-idle
date: 2026-08-24
tags:
- sched_ext
- cgroup
series: scx_cgroup_init_args cpu.idle
type: fix
severity: low
status: under_review
lore: ''
layout: article
---

## 概述

sched_ext 的 cgroup 支持在向调度器传递 cgroup 初始化参数（scx_cgroup_init_args）时，
缺少对 CPU 初始 idle 状态的传递，导致调度器在初始化阶段无法感知 cpu 的 idle 标记。
v1（UID 55269）首发后被反馈需要补充说明，v2（UID 55403）跟进修正。

## 改动内容 / 核心补丁

- 在 scx_cgroup_init_args 结构体中新增并传递初始 `cpu.idle` 状态字段。
- 使 BPF 调度器在 cgroup 初始化回调中即可读到正确的 cpu idle 标记，便于做
  与 idle 相关的调度决策（如 idle 后端调度、idle 重新平衡）。

## 状态与讨论

- 当前状态：**under_review**（v2 已发，等待维护者评审）。
- 与 sched_ext cgroup knobs 文档系列（见 003）配套，属于同一轮 sched_ext/cgroup
  能力完善的一部分。

## 关联

- 003 docs/sched_ext：cgroup CPU 可调参数文档化
- 005 sched：cgroup 更新锁上提到 core
