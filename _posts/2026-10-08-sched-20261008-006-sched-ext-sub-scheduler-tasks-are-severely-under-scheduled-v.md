---
id: sched-20261008-006
subject: 'sched_ext: sub-scheduler tasks are severely under-scheduled vs root-owned
  tasks'
date: '2026-10-08'
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: <163e2397-0e3e-4cc0-842b-0d36598d13d7@linux.dev>
lore_url: https://lore.kernel.org/all/163e2397-0e3e-4cc0-842b-0d36598d13d7@linux.dev/
authors:
- Tao Cui
maintainers_involved:
- Tejun Heo
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 缺调度器源码与完整复现步骤（Tejun 明确要求）
  next_action: 作者补全复现材料后再判定 handover 路径是否饥饿
contribution_opportunities:
- kind: testing
  description: 复现 attach 顺序 (a)/(b) 并给出最小调度器源码
- kind: discussion
  description: 分析 handover 与 migration 两条 claim 路径差异
generated_at: '2026-10-09T01:00:00'
source_email_count: 2
related_articles: []
tags:
- sched_ext
title: 'sched_ext: sub-scheduler tasks are severely under-scheduled vs root-owned
  tasks'
layout: article
---

## TL;DR

Tao Cui 报告一个疑似 dispatch 饥饿：在 `sched_ext/for-7.4` + caps-clear 补丁上，父子 cid 调度的最小复现里，若 busy-loop 任务在子调度器 attach **之前**就进了 cgroup，子调度器每轮都能 claim 到该任务（handover 触发、`p->scx.sched == child`），但其运行 duty cycle 只有 ~0.3%（10s 窗口 0 或 ~20-27 tick），而同属 root 的等价任务跑到 ~100%；attach **之后**再移入则走迁移路径、完全正常，饥饿比约 300x。Tejun 回复要求补全调度器源码与完整复现步骤，否则「不是一个有用的 bug report」。当前处于待作者补材料的定位阶段。

## 背景与问题

报告针对 sub-scheduler attach 流程的 dispatch 饥饿。复现环境：KVM guest（4 vCPU，HZ=1000），`sched_ext/for-7.4` + caps-clear 补丁；一对最小 cid-form 测试调度器——父级向子级 grant `SCX_CAP_PERF | SCX_CAP_ENQ_IMMED`（by cgroup），子级在 `ops.tick()` 里写 cpuperf target 1；busy-loop 任务（`taskset 1 sh -c 'while :; do :; done'`）放进子级 cgroup 并 pin 到 cpu0，每秒采样 `rq->scx.cpuperf_target` 与 per-task CPU 时间。两种 attach 顺序：(a) 任务先移入 cgroup、子级后 attach；(b) 子级 attach 后任务再移入。

## 技术方案

本日是问题报告而非补丁，无技术方案。关键观察集中在两条 attach 顺序的差异：(a) 走 enable walk 的 handover 路径，child 每轮都 claim 成功但任务近乎饿死（10s 窗口内累计 0 或 ~20-27 tick，约一个 `SCX_SLICE_DFL`）；(b) 走迁移路径，任务正常跑满（两档父级负载下 16 轮均无饥饿）。作者据此怀疑 handover 路径存在已知 starve 或调度模型本身的限制，希望先确认是否为已知问题再深挖。

## 版本演进与当前进展

单条 `[REPORT]`（`<163e2397-0e3e-4cc0-842b-0d36598d13d7@linux.dev>`），非补丁系列。Tejun 当日回复要求补全：调度器源码 + 完整复现步骤。

## Maintainer 意见与讨论焦点

- **Tejun Heo**（sched_ext 维护者）：不采信当前形态——「Can you explain exactly what you tested and how, including the scheduler source and complete reproduction steps? This isn't a useful bug report without that information.」要求提供可复现材料才算有效 bug 报告。
- 分歧/未决：作者给出的两条 attach 顺序的差异（handover vs migration）是否指向 bug，取决于缺的复现细节。

## 合入评估

*likelihood=unknown*。尚无补丁，也暂无结论：Tejun 明确要求补复现材料，在作者补齐前无法判断是真实内核缺陷、子调度器使用方式问题，还是已知限制。*blocking_issues*：缺调度器源码与完整复现步骤。*next_action*：作者补全 Tejun 要求的材料（源码 + 复现步骤），再判定 handover 路径是否存在饥饿。

## 效果评估

作者给出定量观察：order (a) 下 child-owned 繁忙任务 ~0.3% duty（0 或 ~20-27 tick/10s） vs root-owned 等价任务 ~100%（1000 ticks/s），饥饿比约 300x；order (b) 无饥饿。属现象级数据，未附可复现脚本/调度器源码，故难以独立验证。

## 我可以参与的点

- `testing`：若熟悉 sched_ext sub-scheduler，可复现 (a)/(b) 两条 attach 顺序并给出最小调度器源码，直接回应 Tejun 的复现要求。
- `discussion`：分析 handover（enable walk）与 migration 两条 claim 路径在 slice 消耗/再入队上的差异，帮助定位 ~0.3% duty 的来源。

## 参考链接

- 报告: https://lore.kernel.org/all/163e2397-0e3e-4cc0-842b-0d36598d13d7@linux.dev/
- Tejun 回复: https://lore.kernel.org/all/68208eef89abff9423de730ef585327f@kernel.org/
