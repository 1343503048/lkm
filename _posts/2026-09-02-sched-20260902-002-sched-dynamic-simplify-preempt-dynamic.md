---
id: sched-20260902-002
date: '2026-09-02'
subject: 'sched: dynamic: Simplify PREEMPT_DYNAMIC'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: null
lore_url: null
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: null
authors:
- Mete Durlu
- Mark Rutland
- Shrikanth Hegde
- Jinjie Ruan
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: merged
  blocking_issues:
  - 'sched: Move some scheduler fields to new static branch API 未随批合入，Peter Zijlstra
    与 Hongyan Xia 仍在讨论'
  - ARCH_HAS_PREEMPT_LAZY 前提是否成立，Jinjie Ruan 的追问无正式结论
  - 当天 tip/sched/core 做过 rebase，3 个补丁 Commit-ID 已变更
  next_action: 实测 preempt_model_str()/sched_dynamic_show() 修复，并跟进未合入的 static branch
    API 补丁
contribution_opportunities:
- 在多架构（arm64/riscv/loongarch）验证 preempt= 切换与 /sys/kernel/debug/sched/preempt 输出
- 就 ARCH_HAS_PREEMPT_LAZY 依赖是否成立提供各架构 Kconfig 现状
- 'review 未合入的 sched: Move some scheduler fields to new static branch API'
source_email_count: 8
related_articles: []
tags:
- sched/core
- preempt
title: 'sched: dynamic: Simplify PREEMPT_DYNAMIC'
layout: article
---

## TL;DR

PREEMPT_DYNAMIC 简化（Mark Rutland）当天以 6 个补丁进 `tip/sched/core`，同批 static key API 迁移的
3 个补丁一并合入。纯清理但当天就暴露一个用户可见的回归并被即时修复合入，另外 static branch API 那一半
其实没进这批，跟进时要注意。

## 背景与问题

09-02 一批 `sched/core` 与 `sched: dynamic` 的清理改动合入 `tip/sched/core`，分成两条
主线：(a) 简化 PREEMPT_DYNAMIC 的各类抢占辅助函数；(b) 把调度子系统内的静态分支
（static key）调用迁移到新版 API。

## 技术方案

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

## 版本演进与当前进展

- 当前状态：**merged_tip**（已进入 `tip/sched/core`）。
- 合入可能性：**high/已合入**。属纯清理，风险低。
- 注意 `[PATCH RESEND] sched: Move some scheduler fields to new static branch API`
  （73285）为重新发送，最终随该批一并合入。

## Maintainer 意见与讨论焦点

- Mark Rutland 当天 00:03/00:04 两封回帖回答 Jinjie Ruan（71699 针对 6/6 的枚举删除、71636 针对 0/6
  封面的前提 "All architectures which currently suppoort PREEMPT_DYNAMIC select ARCH_HAS_PREEMPT_LAZY."），
  Jinjie Ruan 9/3 09:30 又把这条线程顶了一次（75632）——即「依赖 ARCH_HAS_PREEMPT_LAZY 是否成立」这条线
  到最后仍有人在追问，没有正式结论。
- Peter Zijlstra 与 Hongyan Xia 16:18/16:19 仍在 `[PATCH RESEND] sched: Move some scheduler fields to
  new static branch API` 上往返（73274/73283），该补丁**没有**出现在当天的 tip 合入清单中。
- 全程无 NAK。

## 合入评估

**已合入** `tip/sched/core`：6 个 PREEMPT_DYNAMIC 补丁（aa4178f6 / 9650ce11 / 5b9a28ee / 88e0b3bb /
b9d267b9 / d3d16750）+ static key 迁移 3 个（do_balance_callbacks 4248f68f、sched_feat d92d1a18、
paravirt_steal 087b40fe），另有当天新发又当天合入的 `Fix preemption model strings`（ef9293b3）。
两个卡点：(1) `Move some scheduler fields to new static branch API` 未随批合入；(2) 16:32~16:33 有 3 个
同批补丁被以**不同 Commit-ID** 重新通知（do_balance_callbacks → 879eaa76、sched_feat → 2a672daa、
paravirt_steal → a5576ebc），说明 sched/core 当天做过 rebase，引用 hash 要以 16:33 那批为准。

## 效果评估

全线程无性能数字。唯一的事实性效果是 Mark Rutland 自己在 73578 承认的回归："We recently removed the
enum values 'preempt_dynamic_none' and 'preempt_dynamic_voluntary', but forgot to update preempt_modes[]
accordingly. Due to this, preempt_model_str() and sched_dynamic_show() …"（缓存中截断）——抢占模式字符串
会被报错，且该修复从发起到进 tip 只用了 43 分钟。73578 之外，系列其余补丁均无测试数据。

## 我可以参与的点

- 在支持 PREEMPT_DYNAMIC 的平台实测 `cat /sys/kernel/debug/sched/preempt` 与 `preempt=none/voluntary/full`
  切换，确认 preempt_modes[] 修复覆盖到全部组合。
- Jinjie Ruan 的 ARCH_HAS_PREEMPT_LAZY 前提问题仍未闭合，可拿 riscv/loongarch 的 Kconfig 现状回帖。
- review 唯一没合入的那封 static branch API 补丁。

## 参考链接

- 001 Proxy Execution 批合并入（同为 tip/sched/core 当天批量）
