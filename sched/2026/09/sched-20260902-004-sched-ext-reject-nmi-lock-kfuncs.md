---
title: "sched_ext：拒绝在 NMI 上下文调用会拿锁的 kfuncs（v3）"
date: 2026-09-02
tags: [sched_ext]
series: "sched ext reject nmi lock kfuncs"
type: fix
severity: medium
status: under_review
lore: ""
---

## 概述

sched_ext 的若干 BPF kfunc 内部会获取锁（如 rq 锁、dsq 锁）。在 NMI 上下文调用这些
kfunc 会破坏锁协议、导致死锁或状态不一致。本期把「NMI 上下文调用会拿锁的 kfunc」显式
拒绝，提升 sched_ext 的健壮性。

## 改动内容 / 核心补丁

- 主补丁 `sched_ext: Reject NMI calls to lock-taking kfuncs`：在 kfunc 入口检测
  `in_nmi()` 并对会拿锁的 kfunc 返回错误 / 拒绝调用。
- 演进：v2（UID 72739）→ v3（UID 72748）；同日多条 Re:（72334/72340/72408/73046/
  74212）为评审交流。
- 关联小补丁 `sched_ext: Use atomic cpumask_clear_cpu in scx_idle_test_and_clear_cpu()`
  （71683 Re:），把空闲测试/清除改成原子操作，与 NMI 安全主题呼应。

## 状态与讨论

- 当前状态：**under_review**（v3）。
- 合入可能性 medium/high；属明确的健壮性修复，争议点少。
- 与 005（vtime 排序约束）、006（NULL deref）同为当日 sched_ext 修复集群。

## 关联

- 005 sched_ext：文档化并强制 vtime 排序约束（v3）
- 006 sched_ext：修复 select_cpu_and 子调度空指针解引用
