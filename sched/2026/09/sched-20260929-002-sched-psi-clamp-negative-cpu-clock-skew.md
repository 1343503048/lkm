# sched/psi: clamp negative cpu_clock() skew

> **subject**：`sched/psi: clamp negative cpu_clock() skew`

## TL;DR

David Stevens 的 PSI 修复：在 stable clock 系统上 `cpu_clock(cpu)` 会忽略 cpu 参数，导致 PSI 内部出现跨 CPU 的时间戳比较，负 skew 会让 u32 的活跃态时长计算下溢，产生约 4 秒的假 delta 冲进累加器，造成 PSI_POLL 的虚假唤醒或 PSI_AVGS 的 nonsense 值（如 full>some、psi>100%），可能诱发用户态 OOM 守护进程误杀进程。补丁把 elapsed 钳到 >=0。Peter Zijlstra 连回两条：质疑为何在 `sched_clock_stable()` 下还能观测到非单调（暗示硬件有问题），并追问是什么机器。

## 背景与问题

PSI 在用时间戳时很小心地只比较「同 cpu 参数」的 `cpu_clock(cpu)`；但在 stable clock 系统上 cpu 参数被忽略，跨 CPU 的 `cpu_clock()` 比较仍会发生。通常跨 CPU skew 比测量间隔小好几个数量级、被 cyclic times 计数器自然吸收，但若 `get_recent_times()` 恰在另一 CPU 上任务刚进入 active stall 态后立即执行，负 skew 会让 u32 的 active 态时长计算下溢；若该态自上次 `get_recent_times()` 以来未 active，`times` 与 `times_prev` 相等，巨大的下溢值会被零扩展并折进 u64 总累加器，形成约 4 秒再按该 CPU 非 idle 占比缩放的大 delta。

后果是 PSI_POLL 聚合器虚假唤醒、或 PSI_AVGS 得出 nonsense 值；用户态可能据此误判内存压力、OOM 守护进程误杀进程。作者在 Intel N100 上跑浏览器负载（持续 psi.mem.some 2-3%）时，每几小时观测到一次该下溢。

## 技术方案

把 elapsed time 钳到 `>= 0`，阻止假 jump。作者同时分析了备选方案：

- **把 times 扩成 u64 来防止 u32→u64 转换出错**——被否决，因为这会让面向用户态的总计数器不再单调，破坏靠连续 total 值算速率的消费者。
- **钳到 0 的代价**：总累加器会比真实值略微偏高，但误差受 skew 限定、实际上总比当前（折进 4 秒假 delta）小。

作者还指出 clock skew 另两处隐患：`record_times()` 里的负 skew 会经 times 累加器传导到下溢；连续两次 `get_recent_times()` 的 elapsed 若第一次正 skew、第二次负 skew 会「倒退」导致 delta 下溢。

## 版本演进与当前进展

v1 刚发出（`<20260928233743.3777102-1-stevensd@google.com>`）。当日 Peter Zijlstra 回两条，尚未得到作者最终回复。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**（09-29，两条）：其一质疑前提——`sched_clock_stable()` 意味着 1) 跑在 x86 且 2) CPU A/B 的 RDTSC 不该出现非单调运动：「若你真能看到非单调运动，那 1) 你硬件坏了，2) 你也不该有 `sched_clock_stable()`」，并问「你是在什么机器上看到的？」。其二自嘲式补充「Reading is hard. This is sad, that's a relatively modern chip :-(」（针对作者问题机器型号的感叹，原文较简略）。
- 核心分歧尚未展开：Peter 认为根本症结是「stable clock 却在观测到非单调」，可能想先搞清楚作者的硬件/场景，再决定是钳值、还是别处（sched_clock）该修。

## 合入评估

*likelihood=unknown*。修复方向（钳负值）合理、副作用已作者分析，但 Peter 的质疑直指「为何会有非单调」的根因，尚未澄清便难以判断 maintainer 是接受钳值修补、还是要求去修 sched_clock 本身。*blocking_issues*：Peter 对根因的质疑待作者回应。*next_action*：作者说明复现机器与触发场景，回应 Peter「是不是硬件/sched_clock_stable 判定犯了」的质疑。

## 效果评估

无 benchmark 数字；作者给出的是现象频率（N100 浏览器负载、psi.mem.some 2-3% 下每几小时一次下溢）与机制推演，钳值后的量化收益未见数据。

## 我可以参与的点

- `review`：辨析「负 elapsed 钳到 0」与「在 sched_clock/PSI 边界把跨 CPU 比较改为单调」两种修法的取舍；确认 author 列出的另两处 skew 隐患是否也应一并修。
- `testing`：在 stable-clock x86 机器上跑 PSI 压力负载，观测是否能复现 psi>100% 或该下溢并验证钳值补丁。

## 参考链接

- lore（补丁）: https://lore.kernel.org/all/20260928233743.3777102-1-stevensd@google.com/
- Peter 第一问: https://lore.kernel.org/all/20260929081004.GS4120091@noisy.programming.kicks-ass.net/
- Peter 第二问: https://lore.kernel.org/all/20260929081740.GH4121620@noisy.programming.kicks-ass.net/

---
id: sched-20260929-002
date: '2026-09-29'
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
    summary: '把 PSI elapsed time 钳到 >=0，阻止负时钟 skew 导致的 u32 下溢与 4 秒假 delta'
    review_outcome: 'Peter Zijlstra 追问为何 sched_clock_stable 下仍非单调、以及复现机器'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - 'Peter 对根因（stable clock 却观测到非单调）的质疑待作者回应'
  next_action: '作者说明复现机器与场景，回应 Peter 的根因质疑'
contribution_opportunities:
  - kind: review
    description: '辨析钳负值与修 sched_clock 边界的取舍，确认另两处 skew 隐患是否一并修'
  - kind: testing
    description: '在 stable-clock x86 机器复现 psi>100% 或下溢并验证钳值补丁'
generated_at: '2026-09-30T01:15:00'
source_email_count: 3
related_articles: []
tags:
  - psi
  - sched_clock
---