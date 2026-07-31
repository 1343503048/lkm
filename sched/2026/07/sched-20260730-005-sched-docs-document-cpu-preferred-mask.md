---
id: sched-20260730-005
date: 2026-07-30
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<sched-docs-v9-01-11...>"
lore_url: "https://lore.kernel.org/lkml/sched-docs-v9"
authors: [Yury Norov]
maintainers_involved: [Yury Norov]
current_version: v9
patch_series:
  - version: v9
    msgid: "<sched-docs-v9-01-11...>"
    date: 2026-07-30
    summary: "11-patch series documenting cpu_preferred_mask and Preferred CPU concept"
    review_outcome: "Yury Norov suggests possibly moving to sched-paravirt.rst"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["Documentation location discussion ongoing"]
  next_action: "Decide on documentation file placement"
contribution_opportunities: []
generated_at: "2026-07-31T00:10:00"
source_email_count: 1
related_articles: []
tags: [sched_debug, topology]
---

## TL;DR

Yury Norov 的 v9 文档系列（11 patches）为 `cpu_preferred_mask` 和 Preferred CPU 概念添加文档。社区讨论文档放置位置，可能移至 `sched-paravirt.rst`。

## 背景与问题

`cpu_preferred_mask` 是一个调度相关概念，用于描述 CPU 偏好性（例如在虚拟化环境中，某些 vCPU 可能被优先调度）。目前缺乏正式文档说明。

## 技术方案

11-patch 系列，系统性文档化 Preferred CPU 概念和 `cpu_preferred_mask` 的使用。

## 版本演进与当前进展

- v9 已迭代到第 9 版，说明系列经过多轮 review
- 2026-07-30: Yury Norov 建议可能移至 `sched-paravirt.rst`

## Maintainer 意见与讨论焦点

- Yury Norov: 建议考虑将内容放在 `sched-paravirt.rst` 而非当前 proposed location

## 合入评估

- **likelihood**: medium
- 文档内容已成熟（v9），但放置位置仍在讨论

## 效果评估

暂无效果数据（纯文档改进）。

## 我可以参与的点

当前阶段暂无明显参与空间。

## 参考链接

- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到
