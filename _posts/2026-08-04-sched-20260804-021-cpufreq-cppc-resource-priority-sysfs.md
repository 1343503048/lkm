---
id: sched-20260804-021
date: 2026-08-04
subsystem: cpufreq
type: feature
status: under_review
severity: none
thread_root_msgid: <unknown>
lore_url: unknown
authors:
- Vanshidhar Konda
maintainers_involved:
- Rafael J. Wysocki
- Sudeep Holla
current_version: v4
patch_series:
- version: v4
  msgid: <unknown>
  date: 2026-08-04
  summary: CPPC v4（自 v3 演进多轮的『Resource Priority』）新增 sysfs 接口，让用户空间设置/amplify 每个 CPU
    的 CPPC 资源优先级（与 sched 的 uclamp/latency 偏好呼应），以在异构/共享电源域下影响硬件调度决策。
  review_outcome: v3 已被讨论多轮，v4 整合反馈；Rafael/Sudeep 尚未在 08-04 给最终 ack。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - sysfs ABI 需 maintainer 确认稳定；与 sched uclamp 的语义衔接需理清
  next_action: 等待 Rafael/Sudeep 对 sysfs ABI 与 sched 语义衔接的认可。
contribution_opportunities:
- kind: review
  description: 可审阅新增 sysfs ABI 的稳定性承诺（Documentation/ABI），以及 CPPC 资源优先级与 sched uclamp
    的语义是否冲突/重复，回帖 ABI review。
generated_at: '2026-08-05T00:25:00'
source_email_count: 1
related_articles: []
tags:
- cpufreq
- cppc
- latency
title: 'cpufreq: intel_pstate: Consolidate HWP P-states initialization'
layout: article
---

# cpufreq: CPPC 资源优先级 sysfs（v4）

## TL;DR
CPPC v4（Resource Priority）新增 sysfs 接口，允许设置每个 CPU 的 CPPC 资源优先级，与 sched 的 uclamp/latency 偏好呼应，在共享电源域下影响硬件调度决策。v4 整合多轮反馈，合入可能性 medium（sysfs ABI 待确认）。

## 背景与问题
CPPC（Collaborative Processor Performance Control）允许平台表达每 CPU 的性能/效率偏好。在共享电源域的异构系统上，缺乏让用户空间按 CPU 表达「资源优先级」的接口，无法与调度器的 uclamp/latency 偏好形成端到端的影响链。

## 技术方案
v4 提供 sysfs 接口（每 CPU）设置/amplify CPPC 资源优先级，硬件据此在电源/性能分配上偏向高优先级 CPU。系列自 v3 多轮演进（v4 整合 review 反馈）。

## 版本演进与当前进展
当前 v4（2026-08-04）。自 v3 起多轮讨论，v4 整合反馈。

## Maintainer 意见与讨论焦点
Rafael J. Wysocki / Sudeep Holla 尚未在 08-04 给最终 ack。焦点在 (1) sysfs ABI 稳定性承诺；(2) 与 sched uclamp 的语义衔接是否冲突/重复。

## 合入评估
合入可能性 medium。sysfs ABI 需 maintainer 确认，且与调度语义衔接需理清。

## 效果评估
无基准；属接口扩展，效果以「用户空间可端到端影响硬件资源分配」衡量，需实测。

## 我可以参与的点
- 审阅新增 sysfs ABI 文档（Documentation/ABI）的稳定性承诺，以及 CPPC 资源优先级与 sched uclamp 语义是否冲突，回帖 ABI review（最直接参与点）。

## 参考链接
- lore thread: 未获取到
