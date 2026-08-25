---
title: "sched_ext：串行化 cgroup knob 更新（for-7.3-fixes）"
date: 2026-08-25
tags: [sched_ext, cgroup]
series: "sched_ext serialize cgroup knob updates"
type: fix
severity: medium
status: merged_tip
lore: ""
---

## 概述

sched_ext 的 cgroup knob（weight/idle 等）更新存在并发竞态：并发写 `cpu.shares` 等
控制文件时，CFS 内部锁在调用 SCX 回调前释放，允许多线程穿插，使 CFS 记录值、SCX
簿记、BPF 调度器三者拿到不同参数（此前 08-19/08-20 的「三视图发散」竞态）。

本期以 `[PATCH sched_ext/for-7.3-fixes]` 形式发出（UID 56891），将 cgroup knob 更新
串行化，目标分支为 `sched_ext/for-7.3-fixes`。

## 改动内容 / 核心补丁

- 在 cgroup knob 更新路径上引入串行化（与 005 的「cgroup 更新锁上提到 core」同源
  思路，但本补丁针对 for-7.3-fixes 稳定修复分支）。
- 为后续允许睡眠回调（见 002）提供正确的串行化基础。

## 状态与讨论

- 当前状态：**merged_tip**（以 `for-7.3-fixes` 为目标分支发出，通常为已排队的修复；
  确切合入以 tip 树为准）。
- 与 001/002/005 共同构成 sched_ext cgroup 健壮性的一组修复。

## 关联

- 001 sched_ext：scx_cgroup_init_args 传递 sched_idle（v3）
- 002 sched_ext：cgroup_set_weight/idle 可睡眠
- 005 sched：cgroup 更新锁上提到 core
