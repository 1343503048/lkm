---
title: "docs/sched_ext：文档化 cgroup CPU 可调参数（scheduler-dependent）"
date: 2026-08-24
tags: [sched_ext, documentation, cgroup]
series: "document sched_ext cgroup cpu knobs"
type: fix
severity: low
status: under_review
lore: ""
---

## 概述

sched_ext 允许每个 cgroup 设置调度器相关的 CPU 参数（scheduler-dependent knobs），
但文档缺失，用户难以知晓可用参数与含义。v3（UID 54704）与 v4（UID 55221）持续
完善这部分文档，补充参数说明与示例。

## 改动内容 / 核心补丁

- 在 Documentation/sched-ext 中新增/扩充 cgroup CPU 可调参数的说明。
- 阐明哪些参数依赖具体调度器实现、如何读取与设置、以及缺省行为。

## 状态与讨论

- 当前状态：**under_review**（v4 已发）。
- 与 001（传递 cpu.idle 到 scx_cgroup_init_args）配套，共同完善 sched_ext 的
  cgroup 能力面。

## 关联

- 001 sched_ext：传递初始 cpu.idle 状态
- 005 sched：cgroup 更新锁上提到 core
