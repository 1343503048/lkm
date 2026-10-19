---
id: sched-20261019-002
subject: 'sched/fair: avoid redundant updates for unchanged default slices'
date: 2026-10-19
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <CANGjgdmNCfm=SctvKZ44y8b5n8t_JSp4meX=DKGnG74B3g1vVw@mail.gmail.com>
lore_url: https://lore.kernel.org/all/CANGjgdmNCfm=SctvKZ44y8b5n8t_JSp4meX=DKGnG74B3g1vVw@mail.gmail.com/
authors:
- Chengfeng Lin
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <CANGjgdmNCfm=SctvKZ44y8b5n8t_JSp4meX=DKGnG74B3g1vVw@mail.gmail.com>
  date: 2026-10-19
  summary: sched_setparam 热路径先比较 default/custom 模式再比较时长，避免未变的默认 slice 请求误走更新路径
  review_outcome: 暂无回帖
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无 review，slice 边界语义待维护者确认
  next_action: 等 CFS/EEVDF 维护者 review 并确认边界语义
contribution_opportunities:
- kind: review
  description: 复核 default/custom 比较与 custom=默认、RT-PI 后隐式 uclamp 重置两个边界的覆盖
- kind: testing
  description: 非 x86 平台或真实负载下复测 sched_setparam() 微基准确认无回退
generated_at: '2026-10-20T01:30:00'
source_email_count: 1
related_articles: []
tags:
- cfs
- eevdf
- perf
title: 'sched/fair: avoid redundant updates for unchanged default slices'
layout: article
---

## TL;DR

Chengfeng Lin 发往 sched 的单补丁优化：`_sched_setscheduler()` 对使用默认 slice 的 fair 任务，attr.sched_runtime 为零而 se.slice 存实际时长，两者直接比较导致未变的 `sched_setparam()` 请求误走参数更新路径。补丁改为先比较 default/custom 模式再比较时长（按 Peter 建议），实测 syscall 微基准 616.51ns → 162.39ns（省 73.66%）。当日新发，暂无回帖。

## 背景与问题

对于使用默认 slice 的公平任务，`_sched_setscheduler()` 把 `attr.sched_runtime` 留成 0，而 `se.slice` 保存实际时长。直接比较两者会让一个「未改变」的 `sched_setparam()` 请求（priority 未变）误判为有变化，走参数更新路径，产生冗余开销。作者还指出两种「仅比较 runtime 是否相等」覆盖不到的情形：自定义 slice 恰好等于默认值时需切换到 custom 模式；未变的 legacy 请求在 RT-PI 提升结束后仍需重置隐式 uclamp。

## 技术方案

单补丁（`kernel/sched/fair.c` 相关路径）：先比较 default/custom 模式，再比较请求时长（作者注明「如 Peter Zijlstra 所建议」）。default 模式请求还额外检查任务 slice 是否仍等于当前默认值；fair 类之外与需要重置隐式 uclamp 的路径保留更新语义；显式 uclamp 请求继续走既有更新路径。作者标注该补丁「应用于 tip/sched/core b99b7f60c5b4」，且 `Assisted-by: LLM`。

## 版本演进与当前进展

*current_version: v1*。单补丁当日新发（`<CANGjgdmNCfm=SctvKZ44y8b5n8t_JSp4meX=DKGnG74B3g1vVw@mail.gmail.com>`），暂无 review 意见。

## Maintainer 意见与讨论焦点

暂无回帖。作者称方案按 Peter 建议（比较 default/custom 模式）实现，但 Peter 本人今日未在邮件中表态。

## 合入评估

*likelihood=unknown*。属于 `sched_setparam()` 热路径的微优化，改动小、带实测数据，但当日无任何 review，且涉及 slice 语义比较的边界（custom 等于 default、RT-PI 后隐式 uclamp 重置）需调度维护者确认。*blocking_issues*：无 review。*next_action*：等 CFS/EEVDF 维护者 review 并确认边界语义。

## 效果评估

作者给出 syscall 微基准（非应用加速）：i7-12700KF、v7.2，SCHED_OTHER/nice-0 任务反复 `sched_setparam(0, priority=0)`，改前每调用 616.51ns、改后 162.39ns（省 454.12ns，-73.66%）；既有 custom-slice 快速路径 162.57 → 163.22ns（+0.40%）。测试用 GCC 15.2、CPU 2、全抢占、性能模式、关 Turbo，每 boot 15 样本 × 50 万次调用，基线漂移 <0.18%、组内 CV <0.30%。

## 我可以参与的点

- `review`：复核 default/custom 模式比较与「custom 等于默认」/「RT-PI 后隐式 uclamp 重置」两个边界是否被正确覆盖。
- `testing`：在非 x86 平台或不同负载下复测 `sched_setparam()` 微基准，确认真实任务场景无回退。

## 参考链接

- patch：https://lore.kernel.org/all/CANGjgdmNCfm=SctvKZ44y8b5n8t_JSp4meX=DKGnG74B3g1vVw@mail.gmail.com/
