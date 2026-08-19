# sched/fair: Prefer fully idle cores for NOHZ balancing

## TL;DR

本文为增量更新，完整背景见 sched-20260730-008。Andrea Righi (NVIDIA) 的 "Prefer fully idle cores for NOHZ balancing" v2 补丁在 20260731 收到 Mete Durlu 的 s390 测试反馈和代码优化建议。Andrea 指出 Mete 建议的 `is_core_idle()` 实现存在不检查目标 CPU 本身的逻辑问题，并提出了修正方案。

## 背景与问题

（完整背景见 sched-20260730-008）NOHZ 负载均衡器可能选择在空闲 SMT 兄弟上运行，这会减少其忙碌兄弟的可用容量。此补丁系列旨在优先选择完全空闲的 SMT 核心。

## 新增讨论（20260731）

**Mete Durlu** 在 s390 上测试并提出代码优化建议：

- 建议在找到 fallback idle CPU 后，始终按 core 粒度遍历而非 per-CPU
- 提供了修改后的遍历逻辑代码

**Andrea Righi** 回应 Mete 的建议：

- 指出 `is_core_idle()` 不检查 supplied CPU 本身，只检查其 siblings
- 这意味着可能返回一个忙碌的 `ilb_cpu`（如果其所有 siblings 都空闲但自身忙碌）
- 提出了修正方案：在 fallback 逻辑中增加 `sched_smt_active()` 检查后跳过整个 core 的 siblings

## 合入评估

- **likelihood: medium** — 方向正确，但逻辑细节需要修正
- **blocking_issues**: is_core_idle() 逻辑问题需解决；s390 测试结果待确认
- **next_action**: Andrea 修正逻辑后发 v3

## 效果评估

前日报告中 NVIDIA Vera GEMM benchmark 6.2 → 9.4 TFLOP/s (+51%) 仍为最新数据。s390 测试结果 Mete 正在测试中。

## 我可以参与的点

- **多平台 SMT 测试**：在 x86、Power、ARM 等不同 SMT 拓扑上测试此补丁，验证性能影响是否一致

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260729163225.1987068-1-arighi@nvidia.com
- 前日分析: sched-20260730-008

---
subject: "sched/fair: Prefer fully idle cores for NOHZ balancing"
id: sched-20260731-007
date: 2026-07-31
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260729163225.1987068-1-arighi@nvidia.com>"
lore_url: "https://lore.kernel.org/lkml/20260729163225.1987068-1-arighi@nvidia.com"
authors: [Andrea Righi]
maintainers_involved: [Mete Durlu, Peter Zijlstra]
current_version: v2
patch_series:
  - version: v2
    msgid: "<20260729163225.1987068-1-arighi@nvidia.com>"
    date: 2026-07-29
    summary: "优先选择完全空闲的 SMT 核心运行 NOHZ 负载均衡器"
    review_outcome: "Mete (s390) 提出 per-core 遍历优化建议；Andrea 指出 is_core_idle() 不检查目标 CPU 本身的问题"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["需要解决 is_core_idle() 不检查目标 CPU 的逻辑问题", "s390 测试结果待反馈"]
  next_action: "等待 Mete 的 s390 测试结果；Andrea 修正 is_core_idle() 逻辑"
contribution_opportunities:
  - kind: testing
    description: "在多平台 SMT 系统上测试（x86、Power、ARM），验证性能影响"
generated_at: "2026-07-31T16:30:00"
source_email_count: 2
related_articles: [sched-20260730-008]
tags: [cfs, nohz, load_balance, hyperthreading]
---
