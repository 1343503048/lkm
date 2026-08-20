---
id: sched-20260814-005
date: 2026-08-14
subsystem: sched
type: docs
status: under_review
severity: low
thread_root_msgid: <20260814070121.scx_docs_v2@tao>
lore_url: 未获取到
authors:
- Tao Cui
maintainers_involved:
- Tejun Heo
- David Vernet
current_version: v2
patch_series:
- version: v1
  msgid: <20260813xxxxxx.scx_docs@tao>
  date: 2026-08-13
  summary: sched_ext 文档与注释的小修复（events sysfs 路径、show_state 示例、stale 引用）。
  review_outcome: Tejun review 后 v2 调整。
- version: v2
  msgid: <20260814070121.scx_docs_v2@tao>
  date: 2026-08-14
  summary: v2（2 patches）：修正 events sysfs 路径与 show_state 示例（drgn bool 打印为 False）；inlines.h
    用 scx_bpf_sub_dispatch()；internal.h 命名 %SCX_DEQ_SCHED_CHANGE 而非删除未定义的 %SCX_DEQ_SAVE；internal.h
    重述 @name 覆盖子调度器；rebase 到 sched_ext/for-7.3。
  review_outcome: v2 发出，无功能改动。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 Tejun 接受（文档/注释，低风险）。
contribution_opportunities:
- kind: review
  description: 评审文档示例与注释修正的准确性。
generated_at: '2026-08-15T00:15:00'
source_email_count: 4
related_articles: []
tags:
- sched_ext
- docs
title: 'Documentation: sched_ext: fix events sysfs path and show_state example'
layout: article
---

## TL;DR
Tao Cui 提交 v2（2 patches）「sched_ext: minor doc and comment fixes」。纯文档/注释修正（events sysfs 路径、show_state 示例、stale 引用、%SCX_DEQ 命名），无功能改动。合入可能性 high。

## 背景与问题
阅读 sched_ext 代码时发现的若干文档与注释不一致：events sysfs 路径过时、show_state drgn 示例中布尔打印语义、inlines.h 用了错误的 BPF 辅助函数名、internal.h 引用了从未定义的 `%SCX_DEQ_SAVE` 等。

## 技术方案
- Documentation/scheduler/sched-ext.rst：修正 events sysfs 路径与 show_state 示例（drgn bool 打印为 `False`）。
- kernel/sched/ext/inlines.h：改用 `scx_bpf_sub_dispatch()` 而非 `scx_bpf_dsq_insert()`。
- kernel/sched/ext/internal.h：将 `%SCX_DEQ_SAVE` 改为命名 `%SCX_DEQ_SCHED_CHANGE`（而非删除未定义项），并重述 `@name` 覆盖子调度器。
- rebase 到 `sched_ext/for-7.3`。无功能改动。

## 版本演进与当前进展
当前 v2（按 Tejun review 调整）。8/14 发出。

## Maintainer 意见与讨论焦点
Tejun 的 review 意见已在 v2 吸收；纯文档类，无实质争议。

## 合入评估
合入可能性 high。低风险文档/注释修复。

## 效果评估
无功能/性能影响。

## 我可以参与的点
- 评审文档示例准确性（如 show_state drgn 片段）。

## 参考链接
- lore: 未获取到
