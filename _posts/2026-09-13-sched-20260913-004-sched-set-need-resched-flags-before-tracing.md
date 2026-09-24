---
id: sched-20260913-004
date: 2026-09-13
subject: 'sched: Set need-resched flags before tracing'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20260911213300.1305763-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260911213300.1305763-1-arighi@nvidia.com/
upstream_commit: null
fixes_commit: adcc3bfa8806
merged_branch: null
current_version: v1
generated_at: '2026-09-14T10:24:00'
authors:
- Andrea Righi
maintainers_involved: []
patch_series:
- version: v1
  msgid: <20260911213300.1305763-1-arighi@nvidia.com>
  date: 2026-09-11
  summary: set_tsk_need_resched() 与 __resched_curr() 两处把 TIF_NEED_RESCHED（含本地分支的标志设置与远程分支的
    set_nr_and_not_polling）提前到 sched_set_need_resched_tp 之前发出，消除 BPF tracepoint 经
    rcu_read_unlock_special() 的递归栈溢出。
  review_outcome: 09-13 kernel-patches CI AI 审查 bot 回帖：远程分支新顺序可能令 RV nrp monitor 在
    any_thread_running 状态收到 schedule_entry_preempt 进入 INVALID_STATE（panic reactor
    下 panic），建议远程分支单独保持先 tp 后标志或文档化乱序可接受；本地分支与 set_tsk_need_resched() 被确认无此问题。作者与人工维护者均未回应。
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - AI 审查提出的 nrp monitor 时序问题无人裁决（远程分支先标志后 tp vs RV 自动机状态转移）
  - 作者未回应审查；无人工维护者表态
  next_action: 作者回应审查（远程分支顺序或文档化乱序可接受），或维护者直接裁决
contribution_opportunities:
- kind: testing
  description: 在 TIF_POLLING_NRFLAG 构型复现审查描述的 nrp monitor INVALID_STATE 场景，验证「tracepoint
    事件乱序」是否实际发生
- kind: review
  description: 核实审查核心命题（fetch_or 先于 probe 遍历提交标志、目标 CPU 凭 need_resched() 抢占不等 IPI）并回帖结论
source_email_count: 2
related_articles: []
tags:
- preempt
- crash
title: 'sched: Set need-resched flags before tracing'
layout: article
---

## TL;DR
Andrea Righi 修复 `sched_set_need_resched_tp` tracepoint 早于 TIF_NEED_RESCHED 标志设置而引发的 BPF tracepoint 递归、直至内核栈溢出的问题（Fixes adcc3bfa8806「sched: Adapt sched tracepoints for RV task model」）。09-13 kernel-patches CI 的 AI 审查 bot 提出：新顺序在远程 CPU 分支可能破坏 runtime verification 的 nrp monitor 状态机，panic reactor 下会直接 panic。作者未回应，无人工维护者表态，合入可能性暂无法判断。

## 背景与问题
`sched_set_need_resched_tp` 在对应线程标志设置之前发出。若 BPF tracepoint 程序在离开自身 RCU 读临界区时递归触发同一 tracepoint，且 `rcu_read_unlock_special()` 在关抢占/关中断下需要推迟静默态而调用 `set_need_resched_current()`——此时 TIF_NEED_RESCHED 仍为清零，再次发出 tracepoint，形成闭环直到栈溢出（补丁 commit message 给出的递归链）：

```
__trace_set_need_resched()
  bpf_trace_run3()
    rcu_read_unlock_migrate()
      rcu_read_unlock_special()
        set_need_resched_current()
          set_tsk_need_resched()
            __trace_set_need_resched()   <- 回到起点
```

触发面：需要 BPF 程序挂在 sched_set_need_resched_tp 上（RV 任务模型监控正是典型用户）。补丁正文没有给出触发该问题的实际报告来源，Fixes 目标 adcc3bfa8806 已在当前主线。

## 技术方案
补丁同时改两处（include/linux/sched.h +5/-1，kernel/sched/core.c +7/-2）：

- `set_tsk_need_resched()`：tracepoint 启用且标志未设时，先 `set_tsk_thread_flag(tsk, TIF_NEED_RESCHED)` 再发 tp；
- `__resched_curr()`：本地 CPU 分支改为 `set_ti_thread_flag()` 之后发 tp；远程分支保留 `set_nr_and_not_polling()` 的返回值用于 IPI 决策，但把 tracepoint 移到标志存储之后——commit message 的理由是「tracing 领先于 IPI 传递，同时仍能观察到已更新的标志」。

## 版本演进与当前进展
*current_version: v1（09-11 21:33 UTC 发出，北京收件 09-12 05:33，属本报 09-12 窗口；该日运行缺失，本次随 09-13 的审查回帖一并覆盖）*。v1 发出后无人工 review；09-13 AI 审查 bot 回帖提出上述 nrp monitor 时序问题，线程停在这里。

## Maintainer 意见与讨论焦点
09-13 唯一回帖来自 kernel-patches CI 的 AI 审查 bot（自动化审查，非维护者；回帖落款「AI reviewed your patch. Please fix the bug or email reply why it's not a bug」，见 vmtest CI 的 claude README）。其反对意见很具体，构成本线程当前唯一未决分歧：

- **远程分支的新顺序可能破坏 RV nrp monitor**：TIF_POLLING_NRFLAG 构型下 `set_nr_and_not_polling()` 是 `fetch_or` 实现——标志存储在 tracepoint probe 遍历开始之前就已提交；目标 CPU 无需等 IPI，任意中断返回遇到可抢占上下文就会凭 `need_resched()` 直接 `preempt_schedule_irq() → __schedule(SM_PREEMPT) → trace_sched_entry_tp(true)`，该事件可能先于 `trace_sched_set_need_resched_tp` 到达。nrp 自动机在 `any_thread_running` 状态收到 `schedule_entry_preempt` 的转移项是 INVALID_STATE——monitor 打印 `rv: monitor nrp does not allow event schedule_entry_preempt on state any_thread_running` 并复位；选 panic reactor 则 panic。
- bot 同时确认本地分支与 `set_tsk_need_resched()` 无此问题：本地路径在 rq raw_spinlock 下关抢占，`rq->curr` 不可能在 probe 返回前调度。
- bot 的两个建议：远程分支单独改回「先 tp 后标志」，或文档化为何乱序的 sched_need_resched 事件对 RV monitor 可接受。
- 无人工维护者表态；作者未回应。

## 合入评估
*likelihood: unknown*——无人工维护者信号；AI 审查的反对意见直指修复方案与 RV monitor 的正确性互斥（要么改顺序要么论证可接受），在作者回应前无法判断走向。*blocking_issues*：AI 审查的 nrp monitor 时序问题无人裁决；作者未回应审查。*next_action*：作者回应审查（远程分支顺序调整或文档化乱序可接受性）；关注 sched 维护者是否直接收取。

## 效果评估
无 benchmark 数据。修复收益是消除一类确定性递归（栈溢出 = 崩溃）；补丁自身引入的回归风险即审查指出的 RV monitor 误报/panic。补丁未提供任何测试结果。

## 我可以参与的点
- 本地验证（testing）：在 TIF_POLLING_NRFLAG 构型上复现审查描述的 nrp monitor INVALID_STATE 场景（挂 sched_set_need_resched_tp 的 BPF 程序 + 中断返回抢占路径），确认或证伪「事件乱序」是否实际发生——bot 的推演基于代码逻辑，未见实测数据。
- 技术判断（review）：审查的核心命题（fetch_or 在 probe 遍历前提交标志、目标 CPU 凭 need_resched() 抢占不等 IPI）可以在自家内核上用几行验证脚本核实，把结论（无论支持哪方）回帖，帮作者和维护者收敛。

## 参考链接
- 补丁（v1）: https://lore.kernel.org/all/20260911213300.1305763-1-arighi@nvidia.com/
- AI 审查回帖（09-13，kernel-patches CI bot）: https://lore.kernel.org/all/9577bd41c257d6510512104a7043602ecacacf60bf50399013240d5abe65539a@mail.kernel.org/
- 审查 bot 说明: https://github.com/kernel-patches/vmtest/blob/master/ci/claude/README.md
- 维护者/作者回应: 未获取到
