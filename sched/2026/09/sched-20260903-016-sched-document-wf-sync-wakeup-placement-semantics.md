# sched: Document WF_SYNC wakeup placement semantics

## TL;DR

WF_SYNC 是唤醒标志，用于表达「唤醒者即将睡眠、被唤醒者应立即在就近 CPU 运行」的放置意图。目前RFC 阶段，本日有讨论；与 sched-20260826-004 的 WF_SYNC 相关主题同源。

## 背景与问题

`WF_SYNC` 是唤醒标志，用于表达「唤醒者即将睡眠、被唤醒者应立即在就近 CPU 运行」的放置意图。scx 调度类对该标志的放置语义此前缺乏明确文档。本系列（RFC）补上 `WF_SYNC` 在 scx 下的唤醒放置语义说明，帮助 BPF 调度器作者正确实现 `select_cpu` / `enqueue`。

## 技术方案

- 在 scx 文档中补充 `WF_SYNC` 的唤醒放置语义与推荐实现约定。

## 版本演进与当前进展

- RFC 阶段，本日有讨论；与 `sched-20260826-004` 的 WF_SYNC 相关主题同源。

## Maintainer 意见与讨论焦点

邮件清单中该系列以补丁往返为主，未捕获到维护者明确表态（缓存未含正文，无法给出具体意见）。

## 合入评估

证据不足：邮件缓存未保留正文，无法判断维护者态度与卡点，暂不给合入结论。

## 效果评估

邮件中未提及效果数据（缓存未保留正文，无法确认）。

## 我可以参与的点

证据不足：需结合完整邮件正文再判断参与空间；如该系列进入 review 中后期，可先跑一轮 benchmark 并回帖。

## 参考链接

- 相关文章/系列：
  - [[sched-20260826-004]] WF_SYNC 唤醒放置相关（08-26 讨论）。
- 相关代码/commit：
  - `Documentation/scheduler/sched-ext.rst`
  - `kernel/sched/ext.c` 唤醒/选择路径

---
id: sched-20260903-016
date: '2026-09-03'
subject: 'sched: Document WF_SYNC wakeup placement semantics'
subsystem: sched
type: discussion
status: rfc
severity: low
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched_ext+Document+WF_SYNC+wakeup+placement+semantics
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: null
authors:
- Shubhang Kaushik (Ampere)
- Madadi Vineeth Reddy
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 2
related_articles:
- sched-20260826-004
tags:
- sched_ext
- sched/fair
---
