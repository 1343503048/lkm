# cpuidle: speed up do_idle() by caching the governor latency QoS constraint

## TL;DR
Yaxiong Tian 的 cpuidle 系列（v2，6 补丁）试图通过缓存 cpuidle governor 的 latency QoS 约束来加速 `do_idle()`（kernel/sched/idle.c 的 idle 循环）。本日维护者 Rafael Wysocki 明确表示"I'm totally unconvinced"，认为只省下了可省略的防御性检查、且新增两个 per-CPU 变量与大量复杂度；作者在追问下承认 menu_update() 被编译器优化掉、难以给出可见收益，倾向放弃。系列大概率搁置。

## 背景与问题
作者观察到 `do_idle()` 每次进入 idle 都要向 cpuidle governor 查询 latency QoS 约束（`cpu_latency_qos_limit()` 等），希望把该约束缓存起来避免重复计算。v1 发于 2026-07-29，v2（6 补丁）9 月中旬重发。

## 技术方案
在 cpuidle 层缓存 governor 计算出的 latency QoS 约束（新增两个 per-CPU 变量），使 `do_idle()`/cpuidle 入口跳过重复的 governor 计算路径。改动主要落在 `drivers/cpuidle/governors/`，并对 `kernel/sched/idle.c` 的 `do_idle()` 做配合改动。

## 版本演进与当前进展
- v1（2026-07-29，`<20260729061549.13419-1-tianyaxiong@kylinos.cn>`）：首版。
- v2（09-17，cover `<1789693766158145.347.seg@mailgw.kylinos.cn>`）：6 补丁；本日遭 Rafael 否定，作者倾向放弃。

## Maintainer 意见与讨论焦点
- **Rafael J. Wysocki**：核心质疑——被跳过的 governor 函数"除了可省略的防御性检查外并不昂贵"，问作者是否试过直接省掉这些检查；质疑是否有真实可见收益的 workload；指出方案"新增两个 per-CPU 变量 + 大量复杂度"；明确 "I'm totally unconvinced"。后续又追问 "menu_update() 怎么会（被编译器）优化掉"。
- **Yaxiong Tian（作者）**：承认只测了无负载场景、function_graph 会引入测量误差；承认 menu_update() 被编译器内联优化掉导致 ftrace 无法追踪；回应 Rafael 说"确实不值得这个复杂度"。
- 分歧点：优化目标是否真实存在、复杂度是否值得；作者基本放弃，无继续推进迹象。

## 合入评估
*likelihood=low*。维护者对动机与收益均不认可，作者本人已倾向放弃。*blocking_issues*：缺乏可见收益数据；维护者明确 unconvinced。*next_action*：若无作者提供更硬的收益证据，系列将停滞；否则作者需先给出真实 workload 下的 do_idle() 路径开销数据。

## 效果评估
无有效性能数据——作者只测了无负载场景，且 menu_update() 被编译器优化掉、无法用 ftrace 量化，收益不可见（作者自述"主观，未见有效数据"）。

## 我可以参与的点
- kind=testing：在真实 mixed/idle 负载下用 perf 量化 `do_idle()` → cpuidle governor 路径的调用开销，判断是否存在可优化空间（这是当前争议的关键证据缺口）。

## 参考链接
- lore（v2 cover）: https://lore.kernel.org/all/1789693766158145.347.seg@mailgw.kylinos.cn/

---
id: sched-20260918-009
date: '2026-09-18'
subject: 'cpuidle: speed up do_idle() by caching the governor latency QoS constraint'
subsystem: sched
type: feature
status: stalled
severity: none
thread_root_msgid: '<1789693766158145.347.seg@mailgw.kylinos.cn>'
lore_url: 'https://lore.kernel.org/all/1789693766158145.347.seg@mailgw.kylinos.cn/'
authors:
  - 'Yaxiong Tian'
maintainers_involved:
  - 'Rafael J. Wysocki'
current_version: v2
patch_series:
  - version: v1
    msgid: '<20260729061549.13419-1-tianyaxiong@kylinos.cn>'
    date: '2026-07-29'
    summary: '首版：缓存 governor latency QoS 约束'
    review_outcome: '未记录'
  - version: v2
    msgid: '<1789693766158145.347.seg@mailgw.kylinos.cn>'
    date: '2026-09-17'
    summary: '6 补丁，配合 do_idle() 改动'
    review_outcome: 'Rafael 明确 unconvinced，作者倾向放弃'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - '缺少真实 workload 下的可见收益数据'
    - '维护者明确 unconvinced'
  next_action: '作者需提供 do_idle() 路径开销硬数据，否则系列停滞'
contribution_opportunities:
  - kind: testing
    description: '用 perf 量化 do_idle() -> governor 路径在真实负载下的开销'
generated_at: '2026-09-19T09:00:00'
source_email_count: 3
related_articles: []
tags:
  - cpuidle
  - idle
---