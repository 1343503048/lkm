---
id: sched-20260726-005
date: 2026-07-26
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: "<uid-501@qq-imap>"
lore_url: "unknown"
authors: [Liang]
maintainers_involved: [Tejun Heo]
current_version: v1
patch_series:
  - version: v1
    msgid: "<uid-501@qq-imap>"
    date: 2026-07-26
    summary: "修正 kernel-doc 中 SCX_PICK_IDLE_CPU_* 标志前缀书写错误。"
    review_outcome: "维护者直接 apply 到 sched_ext/for-7.3。"
upstream_commit: null
fixes_commit: null
merged_branch: "sched_ext/for-7.3"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已 apply，无需后续动作"
contribution_opportunities: []
generated_at: "2026-07-27T01:10:00"
source_email_count: 1
related_articles: []
tags: [sched_ext, idle]
---

## TL;DR
一处 kernel-doc 文档 bug 修复：更正 `SCX_PICK_IDLE_CPU_*` 标志的前缀书写错误，已被 Tejun 直接应用到 `sched_ext/for-7.3`。琐碎文档修复，无需跟进。

## 背景与问题
sched_ext 的 idle CPU 选择相关标志 `SCX_PICK_IDLE_CPU_*` 在 kernel-doc 注释中前缀写错，导致文档与实际宏名不一致，可能误导阅读者。属纯文档正确性问题。

## 技术方案
将 kernel-doc 中错误的标志前缀更正为正确的 `SCX_PICK_IDLE_CPU_*`，不涉及代码逻辑改动。

## 版本演进与当前进展
单版提交即被接受，Tejun 回复 "Applied to sched_ext/for-7.3"。

## Maintainer 意见与讨论焦点
无争议，维护者直接 apply，无讨论焦点。

## 合入评估
已合入 `sched_ext/for-7.3`，无阻塞项。

## 效果评估
文档修复，无运行时影响，无效果数据。收益为文档与代码一致。

## 我可以参与的点
当前阶段暂无明显参与空间，补丁已合入。

## 参考链接
- lore thread: 未获取到
- tip-bot commit: 未获取到（已 apply 到 sched_ext/for-7.3）
- stable backport: 未获取到
