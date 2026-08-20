---
id: sched-20260815-003
date: 2026-08-15
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <uid-41130@qq-imap>
lore_url: 未获取到
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <uid-41130@qq-imap>
  date: 2026-08-15
  summary: 将 balance 时代命名统一改为 dispatch 术语：balance_one()->dispatch_one()，SCX_RQ_IN_BALANCE->SCX_RQ_IN_DISPATCH，并修正
    dispatch 路径相关注释。
  review_outcome: v1 刚发出，暂无 review 意见。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 纯重命名 + 注释修正，无功能改动，通常直接收
  next_action: 等待 Tejun 自行 apply（作者即维护者）。
contribution_opportunities:
- kind: review
  description: 可检查是否有外部 BPF 调度器或文档仍引用旧名 SCX_RQ_IN_BALANCE / balance_one()。
generated_at: '2026-08-16T00:10:00'
source_email_count: 3
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Rename balance-era identifiers to dispatch terms'
layout: article
---

## TL;DR
Tejun Heo 提交 3 个 patch，把 sched_ext 里残留的 "balance" 时代命名统一改为 "dispatch" 术语（`balance_one()`→`dispatch_one()`、`SCX_RQ_IN_BALANCE`→`SCX_RQ_IN_DISPATCH`），并清理相关注释。纯重命名，无功能改动。

## 背景与问题
`sched_class->balance()` 已从 sched_ext 移除，现在 `balance_one()` 实际做的是 dispatch（产出可 pick 的任务）。代码中仍残留 balance 时代命名与注释，易误导读者。

## 技术方案
- `balance_one()` → `dispatch_one()`，全部调用点同步更新。
- `SCX_RQ_IN_BALANCE` 枚举位 → `SCX_RQ_IN_DISPATCH`。autogen 枚举头保留旧名（零填充兼容），新增 `HAVE_SCX_RQ_IN_DISPATCH`。
- 同步修正 `scx_dispatch_sched()`、`sub_ecaps` 等处的注释措辞。
- 无 BPF 调度器读取该标志，故无 ABI 风险。改动涉及 `ext.c`/`inlines.h`/`sub.c`/`sched.h` 及 autogen 头，+37/-32。

## 版本演进与当前进展
v1（3 patch）于 2026-08-15 发出。patch 3 专门做标识符重命名。暂无 review 意见。

## Maintainer 意见与讨论焦点
v1 刚发出，暂无 review 意见（作者本人为 sched_ext 维护者）。

## 合入评估
合入可能性高：纯重命名 + 注释修正，无功能变化，autogen 头保持向后兼容。预期由 Tejun 直接 apply。

## 效果评估
无运行时行为变化，纯可读性/术语一致性改进。

## 我可以参与的点
- 检查外部 BPF 调度器或文档是否仍引用旧名，若有可顺手发补丁或提醒。

## 参考链接
- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到
