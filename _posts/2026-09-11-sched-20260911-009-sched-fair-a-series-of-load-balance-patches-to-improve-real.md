---
id: sched-20260911-009
subject: 'sched/fair: A series of load balance patches to improve real-time performance
  of CFS tasks'
date: '2026-09-11'
subsystem: sched
type: feature
status: rfc
severity: low
thread_root_msgid: <20260910042950.1619727-1-jackzxcui1989@163.com>
lore_url: https://lore.kernel.org/all/20260910042950.1619727-1-jackzxcui1989@163.com/
authors:
- Xin Zhao
maintainers_involved:
- Vincent Guittot
current_version: v1
patch_series:
- version: v1 (RESEND)
  msgid: <20260910042950.1619727-1-jackzxcui1989@163.com>
  date: 2026-09-10
  summary: 10 补丁 RFC RESEND：LB_PROMOTE + select_task_rq_fair_thin() 等，目标是降低交互式 CFS
    负载的调度延迟。
  review_outcome: 09-11：Vincent 质疑 LB_PROMOTE 整体必要性与 real-time 定位（05/10 双重拒绝）；Prateek
    索要 patch 1 数据并给 rq->all_pinned 反方案；作者以作用域论证反驳 Prateek 路线、接受 02/10 commit message
    补写；无新版本。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - Vincent 质疑 LB_PROMOTE 前提本身，要求改为 interactive 定位
  - patch 1 无独立收益数据，且出现 Prateek 竞争方案，取舍未决
  - 效果数据仅作者单一嵌入式平台
  next_action: 作者重新定位问题（interactive）、修正或放弃 thin 选核、补 patch 1 数据后发 v2
contribution_opportunities:
- kind: review
  description: 分析 Prateek 反方案与作者作用域反驳谁成立，产出可进 commit message 的论证
- kind: testing
  description: 小 CPU 数平台上给 patch 1 的独立 A/B 数据，回应 Prateek 索要
- kind: discussion
  description: 就 LB_PROMOTE 改定位 interactive 提供场景输入
generated_at: '2026-09-14T11:35:00'
source_email_count: 6
related_articles:
- sched-20260910-001
- sched-20260815-001
tags:
- cfs
- load_balance
- topology
title: 'sched/fair: A series of load balance patches to improve real-time performance
  of CFS tasks'
layout: article
---

## TL;DR
Xin Zhao 的 10 补丁 RFC（LB_PROMOTE：为交互式 CFS 负载减少调度延迟的负载均衡改造）RESEND 后的讨论在当日继续发酵：Vincent Guittot 进一步加码——不只拒绝 05/10 的新选核函数，还质疑整个 LB_PROMOTE 的存在必要性与「real-time」的提法；K Prateek Nayak 对 01/10 给出反方案（rq->all_pinned）并要求数据；作者逐条回应但未让步。本文为增量更新，系列全貌与 09-10 讨论（Vincent 拒 05/10 等）见 sched-20260910-001。

## 背景与问题
作者观察：小 CPU 数平台上，任务唤醒/负载均衡存在不合理的 CPU 空闲事件与 sys% 代价，提出 LB_PROMOTE feature（patch 4）与 select_task_rq_fair_thin()（patch 5）等 10 补丁改造。Vincent 09-10 已拒绝 05/10（不接受再多一个 select idle cpu 函数），Prateek 质疑 01/10 的 overload 语义，Kayra 质疑 02/10 的冗余检查论证。

## 技术方案
（承 sched-20260910-001：1 通用修复，2/3 前置，4 定义 LB_PROMOTE，5 thin 选核，6/7 抢占式 active balance，8 去 avg_idle 检查，9/10 newly idle 尽力迁移。）当日新增讨论要点：

- patch 5（Vincent，加码）：「如果你有实时需求，为什么不用实时调度器？目前我看不出需要新分支或 LB_PROMOTE 的理由。你没有把问题描述清楚，就给出了一个平台特定的方案而不是修现有代码。藏在 LB_PROMOTE 后面并不能让它变好。」
- patch 4（Vincent，缓和一些）：「4ms tick 下看起来合理；ILB 在下个 tick 会修这个，慢路径唤醒有类似版本。你也该看看 newly idle load balance 路径。实时系统请用实时调度器，但你可以改用 interactive（交互式系统）来表述。」
- patch 1（Prateek）：反问「 overloaded CPU 上任务全部 pin 死时做负载均衡有什么意义？那只是浪费周期」；并贴出 build-tested-only 的反方案：rq 新增 all_pinned 标志，detach_tasks 检出 LBF_ALL_PINNED 时置位、affine_move_task() 与 add_nr_running() 中恢复 set_rd_overloaded()；
- patch 1（作者反驳 Prateek 方案）：LBF_ALL_PINNED 的生效范围是特定 src/dst CPU 对，而 rd->overload 是全局标记，作用域不等价；若因 CPUA→CPUB 的 ALL_PINNED 错误清掉全局 overload，CPUB 可能长时间无 nr_running 变化，「在 add_nr_running 里改可能不合适」；
- patch 2（作者回应 Kayra 09-10 的质疑）：active_load_balance_cpu_stop() 本就运行在 busiest_cpu 上，除非 CPU 正在 offline，busiest_cpu 恒等于 smp_processor_id()；Kayra 接受，只要求把这个论证写进下一版 commit message。

## 版本演进与当前进展
*current_version: v1（RESEND 版，root `<20260910042950.1619727-1-jackzxcui1989@163.com>`，09-10 发出；当日无新版本，作者以回帖响应 review）*。

## Maintainer 意见与讨论焦点
- **Vincent Guittot**：从「拒绝 05/10 的函数」升级为「质疑整个 LB_PROMOTE 前提 + 要求作者改用 interactive 表述」——系列的核心叙事被挑战；
- **K Prateek Nayak**：不给 patch 1 数据就不认可（"Do you have any numbers where Patch 1 specifically improves stuff?"），并给出工程上更贴近现有机制的反方案；
- **作者（Xin Zhao）**：对 patch 1 拒绝 Prateek 的 add_nr_running 路线（作用域论证），对 patch 2 接受 Kayra 的 commit message 要求；对 Vincent 的前提质疑当日缓存内未见回应；
- 分歧焦点：overload 语义的作用域之争（Prateek vs 作者）未闭合；RT vs interactive 的定位之争未闭合。

## 合入评估
*likelihood=low*：核心补丁 05/10 已被 Vincent 两度拒绝且反对面扩大到 LB_PROMOTE 本身；01/10 被要求补数据且出现竞争方案。*blocking_issues*：作者需正面回答「为什么不用 RT 调度器/为何叫 real-time」；patch 1 缺少独立收益数据；Prateek 反方案与作者方案的取舍未决；效果数据全部来自作者单一嵌入式平台。*next_action*：作者明确问题定位（交互式而非实时）、按 Vincent 09-10 建议改做 nr_idle_scan 小 LLC 自适应或放弃 thin 选核、补 patch 1 数据后发正式 v2。

## 效果评估
无新数据：当日讨论为机理与方案之争，作者未提供 patch 1 的独立收益数字（Prateek 明确索要而未获回应）；既有数据承 sched-20260910-001（单一嵌入式 arm64 平台，CONFIG_HZ_250）。

## 我可以参与的点
- kind=review：分析 Prateek 反方案（rq->all_pinned + add_nr_running 恢复 overload）与作者「作用域不等价」反驳谁成立——把结论写成可进 commit message 的论证（02/10 已有先例：Kayra 质疑后由作者补充论证）。
- kind=testing：在小 CPU 数平台上给出 patch 1（overload 清除）的独立 A/B 数据，直接回应 Prateek 的索要。
- kind=discussion：就「LB_PROMOTE 应定位为 interactive 而非 real-time」给出场景输入——Vincent 明确表示若重定位可继续讨论。

## 参考链接
- RESEND cover（09-10）：https://lore.kernel.org/all/20260910042950.1619727-1-jackzxcui1989@163.com/
- Vincent 对 05/10 的回复：https://lore.kernel.org/all/CAKfTPtCQUndM7NfMYpz8S6vXhwbwrOYALr9dNb+971XgZ9GqnA@mail.gmail.com/
- Vincent 对 04/10 的回复：https://lore.kernel.org/all/CAKfTPtBRLNWu6KyLs_=uLh7fwZpc5fEsGCwcSV2dCXuf6UqucQ@mail.gmail.com/
- Prateek 对 01/10 的回复（含反方案）：https://lore.kernel.org/all/b44631c1-4272-4860-88f7-14c62de5e2fd@amd.com/
- 作者对 01/10 的回应：https://lore.kernel.org/all/20260911010623.2425196-1-jackzxcui1989@163.com/
- 作者对 02/10 的回应：https://lore.kernel.org/all/20260911002256.2398467-1-jackzxcui1989@163.com/
