---
id: sched-20260827-018
date: '2026-08-27'
subject: 'sched/fair: which tasks should nr_pref_llc_running be compared against?'
subsystem: sched
type: discussion
status: stalled
severity: medium
thread_root_msgid: <20260827135000.735138-1-zhanxusheng@xiaomi.com>
lore_url: https://lore.kernel.org/all/20260827135000.735138-1-zhanxusheng@xiaomi.com/
authors:
- Zhan Xusheng
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 计数器本意（queued vs runnable）无人确认，当日零回复
  - qemu 环境无法触发 preferred_llc 赋值，缺少可复现失效案例
  next_action: CAS 作者/维护者裁决语义；真实硬件上的复现数据
contribution_opportunities:
- kind: discussion
  description: 回答 nr_pref_llc_running 应比较 h_nr_queued 还是改为 set_delayed/clear_delayed
    维护
- kind: testing
  description: bare-metal 多 LLC 机器上复现 delay-dequeue 导致的 alb_break_llc 误判
generated_at: '2026-09-07T22:05:00'
source_email_count: 1
related_articles:
- sched-20260827-002
tags:
- cfs
- load_balance
title: 'sched/fair: which tasks should nr_pref_llc_running be compared against?'
layout: article
---

## TL;DR
Zhan Xusheng 的源码走读提问：active load balance 里 `alb_break_llc()` 用 `nr_pref_llc_running == cfs.h_nr_runnable` 判断"源 rq 上全部任务都偏好同一 LLC"，但两个计数器追踪的集合不同——`nr_pref_llc_running` 跟的是**已入队**任务（含 delay-dequeued），`h_nr_runnable` 剔除延迟出队任务。DELAY_DEQUEUE 下刚入睡的任务会让等式一侧偏高、检查失效，active balancing 不再尊重 LLC 偏好。错误是单边的（只会漏保护、不会错保护）。当日无人解答；这是理解 CAS 聚合与 active balance 交互的一篇高质量读码记录。

## 背景与问题
`kernel/sched/fair.c`（作者给出行号 10756）：

```
if (env->src_rq->nr_pref_llc_running &&
    env->src_rq->nr_pref_llc_running == env->src_rq->cfs.h_nr_runnable)
```

- `nr_pref_llc_running` 在 `account_entity_enqueue()/dequeue()`（fair.c:4522/4538）维护，随**queued** 计数；
- `h_nr_runnable` 会因 `set_delayed()`（6398）提前扣减、`clear_delayed()`（6418）恢复，而实体实际仍挂在树上、不经过 `account_entity_dequeue()`。

于是任务入睡被 delay-dequeue 后：`nr_pref_llc_running > h_nr_runnable`，等式不成立 → `alb_break_llc()` 返回 false → 本应允许打破 LLC 聚合的 active load balance 被抑制。作者补充：这是读码发现，不是观测到的故障。

## 技术方案
无补丁，给出两个候选方向让该计数器的语义持有者（CAS 作者）裁决：
1. 与 `cfs.h_nr_queued` 比较——两侧集合一致，语义读作"所有已排队的 fair 任务都偏好该 LLC"；
2. 若本意是 runnable 语义，则把 `nr_pref_llc_running` 改由 `set_delayed()/clear_delayed()` 同步维护——作者倾向这条，理由只有 runnable 任务才是 active load balance 的候选，入睡途中的任务不是。

## 版本演进与当前进展
单封提问（`<20260827135000.735138-1-zhanxusheng@xiaomi.com>`，08-27 21:50），当日无人回复。

## Maintainer 意见与讨论焦点
帖子自身附带一条对 CAS 测试方法的观察：作者在双路 qemu guest 上无法触发该路径——cache-aware 开启、6 busy + 10 sleeping 线程的单进程场景下 `p->preferred_llc` 从未被赋值，`nr_pref_llc_running` 恒 0，`alb_break_llc()` 跑了 21 次也测不到；他怀疑 `update_se()` 在模拟环境下因 `delta_exec <= 0` 提前返回、`account_mm_sched()` 在 `mm->sc_stat` 检查前就返回。**"计数器语义无人确认 + 虚拟化环境难以验证"是当前最大的未决点**——而同日 Jianyong Wu 的 cache-aware v2 系列（sched-20260827-002）正建立在这套 LLC 偏好计数机制之上，这类语义含糊是上游化前必须扫清的障碍。

## 合入评估
本身无补丁可评估。问题若被确认，修复方向 2 会牵动 CAS 计数骨架，维护者可能要作者在真实硬件上先演示触发。与 002 一样属于 CAS 上游化的必经清障讨论。

## 效果评估
无性能数据；失效机理为静态推导，逻辑链完整（行号+维护点对照）。

## 我可以参与的点
- **对口且缺人回答**：CAS 的 `nr_pref_llc_*` 系列计数正是大线程组聚合的关键；有 bare-metal 多 LLC 环境者可按帖中条件复现（真实机 delta_exec 正常推进时 preferred_llc 能否赋值、等式何时失效），回帖即是回答。
- OLK 若试水 cache-aware 回合，这个等式值得直接按方向 1/2 之一修正后内部先行验证。

## 参考链接
- lore: https://lore.kernel.org/all/20260827135000.735138-1-zhanxusheng@xiaomi.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到
