# Documentation: sched-preemption: Add a SPDX license identifier

## TL;DR

Quchaosheng 给 `Documentation/scheduler/sched-preemption.rst` 补上缺失的 SPDX 许可证标识（`GPL-2.0`），与 `Documentation/scheduler/` 下其它文件保持一致。这是 Jonathan Corbet（文档维护者）建议的 2 行 trivial 补丁，v1 刚发出。

## 背景与问题

`Documentation/scheduler/sched-preemption.rst` 之前以无许可证标识的方式合入，与同目录其它文件不一致。这是文档合规性修补，无功能影响。

## 技术方案

在文件头加一行 `.. SPDX-License-Identifier: GPL-2.0`（并空行分隔），仅 `2 insertions(+0)`。

## 版本演进与当前进展

*current_version: v1*，28 日发出，暂无回复。

## Maintainer 意见与讨论焦点

- **Jonathan Corbet**（文档维护者）：`Suggested-by: Jonathan Corbet <corbet@lwn.net>`——该补丁即由其建议触发。
- 无 NAK，无争议。

## 合入评估

*likelihood=unknown*。trivial 文档合规补丁、低风险，但 v1 刚发出、无人正式表态，合入通常很快（可能直接进 docs 树）。*blocking_issues*：无实质项，仅待收取。*next_action*：等待 Jonathan Corbet 或文档维护者收取。

## 效果评估

无功能/性能影响；属许可证合规修补。

## 我可以参与的点

- 当前阶段暂无明显参与空间（trivial 2 行文档补丁），可持续观察是否被 docs 树直接收取。

## 参考链接

- 补丁: https://lore.kernel.org/all/20260928023638.1397038-1-quchaosheng000406@163.com/

---
id: sched-20260928-012
date: '2026-09-28'
subject: 'Documentation: sched-preemption: Add a SPDX license identifier'
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: '<20260928023638.1397038-1-quchaosheng000406@163.com>'
lore_url: 'https://lore.kernel.org/all/20260928023638.1397038-1-quchaosheng000406@163.com/'
authors:
  - 'Quchaosheng'
maintainers_involved:
  - 'Jonathan Corbet'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260928023638.1397038-1-quchaosheng000406@163.com>'
    date: '2026-09-28'
    summary: '为 sched-preemption.rst 补 SPDX GPL-2.0 标识'
    review_outcome: '暂无回复'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: '等待文档维护者收取'
contribution_opportunities: []
generated_at: '2026-09-29T01:00:00'
source_email_count: 1
related_articles: []
tags:
  - preempt
---