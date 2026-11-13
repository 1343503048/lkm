---
id: sched-20261113-005
subject: 'sched/wait: kill leftover bookmark logic in __wake_up_common()'
date: 2026-11-13
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: <avXveWTaLQ4Qlvgr@redhat.com>
lore_url: https://lore.kernel.org/all/avXveWTaLQ4Qlvgr@redhat.com/
authors:
- Oleg Nesterov
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <avXveWTaLQ4Qlvgr@redhat.com>
  date: 2026-11-13
  summary: 清理 __wake_up_common() 遗留的 bookmark 链表 hack
  review_outcome: 刚发出，暂无回复
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待维护者收取（纯清理，无实质阻塞）
contribution_opportunities:
- kind: review
  description: 核对 list_for_each_entry_safe() 对空列表/单元素列表语义是否等价
generated_at: '2026-11-14T01:30:00'
source_email_count: 1
related_articles: []
tags:
- wait
title: 'sched/wait: kill leftover bookmark logic in __wake_up_common()'
layout: article
---

## TL;DR
Oleg Nesterov 提交单补丁清理 `__wake_up_common()` 里的死代码：`list_first_entry` 手动头检查 + `list_for_each_entry_safe_from()` 是 commit `2554db916586`（"sched/wait: Break up long wake list walk"）遗留的 bookmark 逻辑，其主体已被 `37acade0ce89`（"sched: remove wait bookmarks"）移除，但这几个不再必要的链表 hack 留了下来。纯清理，无行为变化。

## 背景与问题
`kernel/sched/wait.c` 的 `__wake_up_common()` 里有一段手动链表头检查与 `list_for_each_entry_safe_from()` 遍历。它们是早期 commit `2554db916586`（"sched/wait: Break up long wake list walk"）引入的 bookmark 机制遗留。后来 commit `37acade0ce89`（"sched: remove wait bookmarks"）把该机制主体删掉了，但这两处依赖 bookmark 的链表技巧没有跟着清掉，变成死代码。

## 技术方案
把 `list_first_entry` + 头检查 + `list_for_each_entry_safe_from()` 替换为直接的 `list_for_each_entry_safe()`，删除一段不必要的提前返回。`kernel/sched/wait.c` 净 -6 行（7 处改动、1 处新增）。

## 版本演进与当前进展
v1 刚发出，尚无 review 意见。作者为 waitqueue 相关代码的资深维护者（Oleg Nesterov），此类清理通常快速被收取。

## Maintainer 意见与讨论焦点
当日无回帖。改动极简、语义等价，无争议点。

## 合入评估
纯死代码清理、作者可信度高，合入概率高；暂无阻塞项。

## 效果评估
无性能数据（纯清理，行为不变）。

## 我可以参与的点
- **review**：核对 `list_for_each_entry_safe()` 覆盖 `list_first_entry` 头检查语义（空列表、单元素列表）是否完全等价。

## 参考链接
- lore thread: https://lore.kernel.org/all/avXveWTaLQ4Qlvgr@redhat.com/
