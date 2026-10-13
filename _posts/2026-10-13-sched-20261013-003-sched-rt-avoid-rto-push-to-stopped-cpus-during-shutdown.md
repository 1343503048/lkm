---
id: sched-20261013-003
subject: 'sched/rt: Avoid RTO push to stopped CPUs during shutdown'
date: 2026-10-13
subsystem: sched
type: bug
status: rfc
severity: medium
thread_root_msgid: <20261013030140.682182-1-wangqk1@xiaopeng.com>
lore_url: https://lore.kernel.org/all/20261013030140.682182-1-wangqk1@xiaopeng.com/
authors:
- wangqk1
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <20261013030140.682182-1-wangqk1@xiaopeng.com>
  date: 2026-10-13
  summary: 终端 system_state 后停止 RTO 转发并跳过 offline 候选，workaround 式修复
  review_outcome: Peter Zijlstra 否定方案，要求改在停机协议处修复
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - Peter Zijlstra 否定了消费侧加固路线，认为应修在无预警停机 CPU 的源头
  next_action: 与停机协议相关方讨论，把 RTO quiesce 放在停机正确位置
contribution_opportunities:
- kind: discussion
  description: 分析 smp_send_stop() 与 hotplug teardown 差异，参与停机前状态 quiesce 方案讨论
- kind: testing
  description: 在 PREEMPT_RT arm64/x86 上尝试复现关机时 rto push 到停机 CPU 的路径
generated_at: '2026-10-14T01:00:00+08:00'
source_email_count: 2
related_articles: []
tags:
- rt
title: 'sched/rt: Avoid RTO push to stopped CPUs during shutdown'
layout: article
---

> **subject**：sched/rt: Avoid RTO push to stopped CPUs during shutdown

## TL;DR
wangqk1（小鹏）发 RFC：SMP PREEMPT_RT arm64 系统关机时 `machine_power_off()` 触发 `smp_send_stop()`，被 stop 的 CPU 不跑正常 hotplug teardown，其 RT overload 状态残留 stale 的 `rto_mask` 位；仍在跑的 CPU 的 `rto_push_irq_work_func()` 会选中该 stale 位并把 irq_work 排到已停机的 CPU。补丁在终端 system_state 后停止 RTO 转发、跳过已 offline 的候选。Peter Zijlstra 直接否定该方案（「This is horrific; lets not do this」），要求把 bug 修在「无预警停机 CPU」的地方。

## 背景与问题
SMP PREEMPT_RT arm64 上，`machine_power_off()` 最终调 `smp_send_stop()`；`IPI_CPU_STOP` 处理器直接 park 目标 CPU，不跑正常 CPU hotplug teardown——尤其 `rq_offline_rt()` 不会被走到，导致 overloaded 的 RT runqueue 在其 CPU 不再 online 后仍保留 stale 的 `rto_mask` 位。另一 CPU 仍可继续跑 `rto_push_irq_work_func()` 并选中该 entry。观测到的调用栈：

```
irq_work_queue_on()
rto_push_irq_work_func()
irq_work_single()
__flush_smp_call_function_queue()
generic_smp_call_function_single_interrupt()
ipi_handler()
```

正常 hotplug 会在 CPU park 前清理 RT overload 状态并 flush 待处理的 call-function 与 irq_work 回调；`smp_send_stop()` 有意绕过该协议（因为它也服务 panic/crash 路径）。

## 技术方案
单补丁 `kernel/sched/rt.c`（+19/−1）：
- 新增 `rto_push_allowed()`，读 `system_state`，在 `SYSTEM_HALT/SYSTEM_POWER_OFF/SYSTEM_RESTART` 时返回 false。
- `rto_next_cpu()` 开头 `if (unlikely(!rto_push_allowed())) { rd->rto_cpu = -1; return -1; }`
- 遍历 `rto_mask` 时，`if (cpu < nr_cpu_ids)` 分支内加 `if (!cpu_online(cpu)) continue;`（`smp_send_stop()` 不会清 stale 位）。

作者自述这是 workaround、非完整同步协议：`cpu_online()` 与 `irq_work_queue_on()` 非原子，panic / crash-kexec 路径不先设置终结 system_state 就停机。

## 版本演进与当前进展
RFC v1 今日首发（cover `<20261013030140.682182-1-wangqk1@xiaopeng.com>` + 1/1）。Peter 当日即回帖否定。作者测试仅「x86_64 defconfig 编译通过 + checkpatch 无告警」，**尚未在主线上做运行期复现**。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**（sched 维护者）：明确反对——「This is horrific; lets not do this. The bug really is at the place where you randomly and without warning take CPUs down. We're not adding random hacks for things like that.」即：真正该修的是「无预警停机 CPU」的源头（停机协议），而不是在 RTO 消费侧加防御。

## 合入评估
*likelihood=low*。维护者已 NAK 当前实现路线。*blocking_issues*：Peter 拒绝消费侧加固，要求改在停机协议处修复；作者未做运行期复现。*next_action*：作者与停机路径（如 arch 的 stop/smp_send_stop 协议）相关方讨论，把 RTO 状态的 quiesce 放在停机的正确位置，或论证为何必须消费侧防御。

## 效果评估
无运行期复现数据；作者仅编译验证 + checkpatch 通过。未获取到任何运行时效果数字。

## 我可以参与的点
- discussion：停机协议下 RTO/irq_work quiesce 的正确位置是一个开放问题——可分析 `smp_send_stop()` 与 CPU hotplug teardown 的差异，评估哪些调度/irq 状态需要在停机前显式 quiesce，参与讨论。
- testing：作者尚未在主线上复现，可在 PREEMPT_RT arm64 或 x86 上尝试复现关机时的 rto push 到停机 CPU 路径。

## 参考链接
- 补丁 lore：https://lore.kernel.org/all/20261013030140.682182-1-wangqk1@xiaopeng.com/
