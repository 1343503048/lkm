# sched/psi: clamp negative cpu_clock() skew

> **subject**：`sched/psi: clamp negative cpu_clock() skew`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260929-002：David Stevens 的 PSI 修复——stable clock 系统上 `cpu_clock(cpu)` 忽略 cpu 参数，负 skew 令 u32 活跃态时长计算下溢、产生约 4 秒假 delta 冲进累加器，造成 PSI_POLL 虚假唤醒或 PSI_AVGS nonsense 值；补丁把 elapsed 钳到 >=0。Peter Zijlstra 质疑「sched_clock_stable 下为何还能非单调」并追问机器型号。
- sched-20260930-010（今天）：作者补测另两台设备（Intel i5-1245U、Intel Ultra 5 325），均观测到负 elapsed（均值略低于 100ns、最大 371ns），排除了平台特定性；并提出根因假设——x86 上 `cpu_clock()` 走 `rdtsc()`（跨 CPU 非单调），在 `get_recent_times()` 里 `cpu_clock()` 前加 `rbm()`（对齐 `rdtsc_ordered()`）后过夜测试不再出现负值。Peter 回应「Yeah, although most everybody has a filter on top」并感叹现代芯片 TSC 不达标。

## 背景与问题

（承接 sched-20260929-002）PSI 只比较「同 cpu 参数」的 `cpu_clock(cpu)`，但 stable clock 系统上 cpu 参数被忽略，跨 CPU 比较仍会发生；`get_recent_times()` 恰在另一 CPU 上任务刚进入 active stall 后立即执行时，负 skew 令 u32 时长计算下溢并折进 u64 累加器。今天的增量：作者在另两台 x86 设备（i5-1245U、Ultra 5 325）上用更重的内存压力负载复现——每几分钟就出现一次负 elapsed，说明不是平台特定问题。作者进一步把根因指向 x86 的 `cpu_clock()` → `sched_clock()` → `rdtsc()`：rdtsc 指令可相对其他指令乱序读取 TSC，跨 CPU 比较时非单调，可能令 `get_recent_times()` 先读 TSC、再读 psi 状态而产生负 skew。

## 技术方案

（承接）补丁本身仍是「把 elapsed 钳到 >=0」。今天的增量是作者对根因的排查：在 `get_recent_times()` 里 `cpu_clock()` 调用前加 `rbm()`（memory barrier，对齐 `rdtsc_ordered()` 的行为），过夜测试不再观测到负 elapsed。这暗示「经 `sched_clock()` 转一道」在 x86 上可能无法提供 `cpu_clock()` 契约所需的足够强保证，根因层面或需在 sched_clock/PSI 边界处理跨 CPU 比较的单调性，而非仅钳值。

## 版本演进与当前进展

v1（`<20260928233743.3777102-1-stevensd@google.com>`）仍为最新版本。当日增量：作者补充跨平台复现证据与根因假设；Peter Zijlstra 回复。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**（今日）：「Yeah, although most everybody has a filter on top for some reason or another. Mostly it could happen that when the watchdog would detect the TSC wasn't stable after all, you'd be up a creek if you didn't also have this filter. But I'm very sad to see modern chips have shit TSC, that wasn't supposed to happen.」——既承认「多数平台本就叠加了过滤/校验」的现实（暗指钳值类过滤有其合理性），又对现代芯片 TSC 不稳表示意外，未明确接受或否决钳值修法。
- 分歧仍在根因层面：钳值（psi 侧）vs 修 sched_clock 单调性/跨 CPU 比较语义。

## 合入评估

*likelihood=unknown*。作者给出了更强的跨平台证据与一个可自洽的根因假设（rdtsc 乱序），Peter 的回复偏向理解「叠加过滤」的现状，但未明确表态接受钳值补丁或要求改 sched_clock，方向尚未收敛。*blocking_issues*：根因（stable clock 却非单调）与修法位置（psi 钳值 vs sched_clock 边界）未定。*next_action*：作者回应 Peter，说明 `rbm()` 实验与「sched_clock 在 x86 上是否满足 cpu_clock 契约」的结论，供 Peter 决策。

## 效果评估

作者给出实测现象：两台设备负 elapsed 均值略低于 100ns、最大 371ns；加 `rbm()` 后过夜测试不再出现负值。无量化性能/正确性对比（钳值补丁本身的收益仍未见数字）。

## 我可以参与的点

- `review`：辨析「在 sched_clock/PSI 边界把跨 CPU 比较改为单调」与「钳负值」两种修法的取舍；评估 `rbm()` 实验结论是否支持「cpu_clock() 契约在 x86 上不成立」这一判断。
- `testing`：在更多 stable-clock x86 机型上跑 PSI 内存压力负载，复现负 elapsed 并验证「加 rbm() 或钳值」后的效果。

## 参考链接

- lore（补丁，v1）: https://lore.kernel.org/all/20260928233743.3777102-1-stevensd@google.com/
- David 今日补测: https://lore.kernel.org/all/CAOiLmNF7m96HVP0Wv+6+r5bYdXuyJ=mzOwg8iJd+aMdsdWmVbg@mail.gmail.com/
- Peter 今日回复: https://lore.kernel.org/all/20260930151902.GO88198@noisy.programming.kicks-ass.net/

---
id: sched-20260930-010
date: '2026-09-30'
subject: 'sched/psi: clamp negative cpu_clock() skew'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260928233743.3777102-1-stevensd@google.com>'
lore_url: 'https://lore.kernel.org/all/20260928233743.3777102-1-stevensd@google.com/'
authors:
  - 'David Stevens'
maintainers_involved:
  - 'Peter Zijlstra'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260928233743.3777102-1-stevensd@google.com>'
    date: '2026-09-29'
    summary: '把 PSI elapsed time 钳到 >=0，阻止负 skew 导致的 u32 下溢与 4 秒假 delta'
    review_outcome: '09-30 作者补测两台设备并提 rdtsc 乱序根因假设；Peter 回应并感叹现代芯片 TSC 不稳'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - '根因（stable clock 却非单调）与修法位置（psi 钳值 vs sched_clock 边界）未定'
  next_action: '作者回应 Peter，说明 rbm() 实验结论与 cpu_clock 契约在 x86 上是否成立'
contribution_opportunities:
  - kind: review
    description: '辨析钳负值与修 sched_clock 跨 CPU 单调语义的取舍，评估 cpu_clock 契约结论'
  - kind: testing
    description: '在更多 stable-clock x86 机型复现负 elapsed 并验证 rbm()/钳值效果'
generated_at: '2026-10-01T01:00:00'
source_email_count: 2
related_articles:
  - sched-20260929-002
tags:
  - psi
  - sched_clock
---