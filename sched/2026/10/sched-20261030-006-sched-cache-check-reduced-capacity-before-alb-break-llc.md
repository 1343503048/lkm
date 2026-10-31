# sched/cache: Check reduced capacity before alb_break_llc()

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261029-007：Zhan Xusheng 发单补丁修 cache-aware 调度放置缺陷——源 CPU 容量被压减后仍被 `alb_break_llc()` 以 LLC 优先拦下不迁移，任务滞留低容量 CPU；把 reduced-capacity 检查挪到 `alb_break_llc()` 之前。QEMU 复现：任务 20s 内停在 CPU0 只能跑 1.8e7 iters/s，关 cache-aware 后 4.6e7。Chen Yu 认可方向但要求补 benchmark 并考虑调 `alb_break_llc()` 本身；Kayra 已给 Reviewed-by。
- sched-20261030-006（今天）：Chen Yu 走读 `can_migrate_llc()` 后给出量化澄清——在他的场景里，60% IRQ 压力下 `fits_llc_capacity()` 仍返回 true（1024 剩余 < 1433*0.75），只有 IRQ 压力 >66.7% 才允许迁移；并表态「我会跑 hackbench 与 netperf（更高 IRQ 压力），若无问题，你的原始改动就是 OK 的」。

## 背景与问题
（承接 20261029-007）源 CPU 容量被 hrtimer 抢占/IRQ 记账压减后，LLC 偏好仍把任务钉在低容量 CPU 上。今日 Chen Yu 补上了对该路径更精确的阈值分析：`can_migrate_llc()` 认为 60% 的 IRQ 压力不足以阻止任务迁出 preferred LLC（因为迁走一个 1024 util 任务后剩余 util 仍 fit LLC0）。具体数字推演：p1 util=1024（CPU0）、p2 util=1024（CPU1）；LLC0 cap = 1024 + 1024*0.4 = 1433（含 IRQ 压力）、LLC1 cap=2048。把 p1 从 LLC0 迁到 LLC1 后，LLC0 剩余 1024 < 1433*0.75，故 `can_migrate_llc()` 返回 `mig_forbid`——即仅当 IRQ 压力超过 66.7% 时 `fits_llc_capacity()` 才返回 false、放行迁移。

## 技术方案
（承接 v1，今日为走读结论）补丁方案不变：把 reduced-capacity 检查提前到 `alb_break_llc()` 之前。Chen Yu 在走读中另发现一个潜在不匹配：`fits_llc_capacity()` 直接比较「任务 util」与「CPU capacity」，前者基于 `rq_clock_task`（对 IRQ 压力透明），后者却由 IRQ 压力算出，直接比较不精确；但鉴于它派生自 `group_is_overloaded()`（本就比较 CPU capacity 与 task util），暂维持现状、出现问题时再改。Chen Yu 的初步结论是原始改动方向可行，仅需用更高 IRQ 压力的负载验证。

## 版本演进与当前进展
*current_version: v1*（2026-10-29 发出；今日为 reviewer 走读 + 待测试）。今日无新补丁；Chen Yu 从「要求补 benchmark」进展到「已推演阈值并准备自己跑 hackbench/netperf 验证」。

## Maintainer 意见与讨论焦点
- **Chen Yu（Intel，非 maintainer 但深度 review）**：给出阈值量化（66.7% 临界），并主动承担 hackbench/netperf 验证；对原始改动从「要求数据」软化为「若无问题即 OK」。
- **未解决**：仍需真实负载数据确认「容量优先 vs LLC 优先」的取舍；`fits_llc_capacity()` 的 util/capacity 口径不一致是潜在技术债（暂缓）。

## 合入评估
*likelihood=medium*。已有 Kayra Reviewed-by，Chen Yu 倾向认可且主动测试，若 hackbench/netperf 无回退则合入概率上升；但缺真实 benchmark 数据仍是硬门槛。*blocking_issues*：缺 hackbench/netperf（高 IRQ 压力）数据。*next_action*：等 Chen Yu 的 hackbench/netperf 结果；作者可同步补齐自己的数据。

## 效果评估
无新增性能数据；Chen Yu 给出的是容量阈值推演（66.7%），非实测。此前作者 QEMU 复现的 1.8e7 vs 4.6e7 iters/s 仍为唯一实测。

## 我可以参与的点
- **testing**：跑 hackbench/netperf（配 IRQ_TIME_ACCOUNTING 或高频 hrtimer 扰动制造 IRQ 压力），对比补丁前后迁移行为与吞吐。
- **review**：核对 `fits_llc_capacity()` 的 util/capacity 口径不一致是否会在此改动下被放大。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261029023650.3404429-1-zhanxusheng1024@gmail.com/

---
id: sched-20261030-006
date: 2026-10-30
subject: "sched/cache: Check reduced capacity before alb_break_llc()"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261029023650.3404429-1-zhanxusheng1024@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261029023650.3404429-1-zhanxusheng1024@gmail.com/"
authors: [Zhan Xusheng]
maintainers_involved: []
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "缺真实 workload（hackbench/netperf 高 IRQ 压力）的 benchmark 数据"
  next_action: "等 Chen Yu 的 hackbench/netperf 结果；作者同步补齐自身数据"
contribution_opportunities:
  - kind: testing
    description: "跑 hackbench/netperf（配 IRQ_TIME_ACCOUNTING 或高频 hrtimer 扰动）对比补丁前后迁移行为"
  - kind: review
    description: "核对 fits_llc_capacity() 的 util/capacity 口径不一致在此改动下是否被放大"
generated_at: "2026-10-31T09:00:00"
source_email_count: 1
related_articles: [sched-20261029-007]
tags: [load_balance]
---