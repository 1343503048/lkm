---
subject: 'sched_ext: Move the config-off sub-cap kfunc stubs into sub.c'
id: sched-20260816-003
date: 2026-08-16
subsystem: sched
type: cleanup
status: merged_tip
severity: low
thread_root_msgid: <uid-41856@qq-imap>
lore_url: 未获取到
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <uid-41856@qq-imap>
  date: 2026-08-16
  summary: 把 CONFIG_EXT_SUB_SCHED 关闭时的 sub-cap kfunc EOPNOTSUPP 桩从 ext.c 移到 sub.c，使所有
    sub kfunc 定义集中一处。
  review_outcome: Tejun 已 apply 到 sched_ext/for-7.3。
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.3
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入。
contribution_opportunities:
- kind: review
  description: 纯代码移动，可顺带确认 BTF_KFUNCS 注册在两个文件中无重复/遗漏。
generated_at: '2026-08-17T00:10:00'
source_email_count: 2
related_articles:
- sched-20260816-002
tags:
- sched_ext
- cleanup
title: 'sched_ext: Move the config-off sub-cap kfunc stubs into sub.c'
layout: article
---

## TL;DR
Tejun Heo 把 `CONFIG_EXT_SUB_SCHED` 关闭时 sub-cap kfunc 的 `EOPNOTSUPP` 桩函数从 `ext.c` 移到 `sub.c`，让所有 sub-scheduler kfunc 定义集中在同一文件（`sub.c`）。纯代码移动，无功能变化，已 apply 到 `sched_ext/for-7.3`。

## 背景与问题
sub-cap kfunc（`scx_bpf_sub_grant`/`sub_revoke`/`sub_caps`/`sub_kill_bstr`）的真实定义位于 `sub.c`，但它们的"config-off 桩"却散落在 `ext.c`（`#ifndef CONFIG_EXT_SUB_SCHED` 段）。代码组织分散，不利于维护与后续重构（接续 002 系列的 sub-scheduler 支持完善）。

## 技术方案
将 4 个 `EOPNOTSUPP` 桩从 `ext.c` 删除，移入 `sub.c` 的 `#else /* !CONFIG_EXT_SUB_SCHED */` 分支，并补上 `__bpf_kfunc_start_defs()/end_defs()` 包裹，使桩与真实定义同文件。改动 `ext.c -29 / sub.c +33`，仅移动。

## 版本演进与当前进展
v1（41856）于 2026-08-16 发出。Tejun 当日回复 "Applied to sched_ext/for-7.3"。

## Maintainer 意见与讨论焦点
- Tejun Heo：直接 apply，作为 sub-scheduler 代码归并的一部分。

## 合入评估
已合入 `sched_ext/for-7.3`。无悬空问题。

## 效果评估
代码组织改善，无运行时行为变化。与 002 系列共同推进 sub-scheduler 支持在合并窗口前归整。

## 我可以参与的点
- 顺带确认 BTF_KFUNCS 在两个文件中无重复/遗漏注册（纯移动风险低）。

## 参考链接
- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到
