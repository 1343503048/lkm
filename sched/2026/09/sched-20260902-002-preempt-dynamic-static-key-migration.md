---
title: "sched/core 清理：PREEMPT_DYNAMIC 简化 + 新 static key API 迁移（合入 tip）"
date: 2026-09-02
tags: [sched/core, preempt]
series: "preempt dynamic simplify static key api migration"
type: fix
severity: low
status: merged_tip
lore: ""
---

## 概述

09-02 一批 `sched/core` 与 `sched: dynamic` 的清理改动合入 `tip/sched/core`，分成两条
主线：(a) 简化 PREEMPT_DYNAMIC 的各类抢占辅助函数；(b) 把调度子系统内的静态分支
（static key）调用迁移到新版 API。

## 改动内容 / 核心补丁（合入 tip 的提交）

PREEMPT_DYNAMIC 简化：
- `sched: dynamic: Simplify irqentry_exit_cond_resched()`（73207）
- `sched: dynamic: Simplify preempt model accessors`（73209）
- `sched: dynamic: Remove HAVE_PREEMPT_DYNAMIC_{CALL,KEY}`（73216）
- `sched: dynamic: Simplify {cond,might}_resched()`（73229）
- `sched: dynamic: Simplify preempt_schedule{,_notrace}()`（73230）
- `sched: dynamic: Make PREEMPT_DYNAMIC depend on ARCH_HAS_PREEMPT_LAZY`（73231）
- `sched: dynamic: Fix preemption model strings`（73627/73726）

static key API 迁移：
- `sched/feat: Use the new static key API for sched_feat`（73228/73300）
- `sched: Convert paravirt_steal to new static key APIs`（73208/73312）
- `sched: Move some scheduler fields to new static branch API`（73285 RESEND / 73298）
- `sched: Remove unneeded function type cast in do_balance_callbacks()`（73215/73311）

## 状态与讨论

- 当前状态：**merged_tip**（已进入 `tip/sched/core`）。
- 合入可能性：**high/已合入**。属纯清理，风险低。
- 注意 `[PATCH RESEND] sched: Move some scheduler fields to new static branch API`
  （73285）为重新发送，最终随该批一并合入。

## 关联

- 001 Proxy Execution 批合并入（同为 tip/sched/core 当天批量）
