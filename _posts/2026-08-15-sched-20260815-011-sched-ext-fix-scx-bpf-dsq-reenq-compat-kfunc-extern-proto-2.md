---
subject: 'sched_ext: Fix scx_bpf_dsq_reenq___compat kfunc extern prototype'
id: sched-20260815-011
date: 2026-08-15
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <uid-40870@qq-imap>
lore_url: 未获取到
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <uid-40870@qq-imap>
  date: 2026-08-15
  summary: 修正 scx_bpf_dsq_move_to_local() 的 ___v2 compat 变体的 kfunc 探测/注册逻辑。
  review_outcome: 已 apply 到 sched_ext（follow-up to 10 系列）。
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入，与 010 共同覆盖 kfunc compat 暴露问题。
contribution_opportunities:
- kind: testing
  description: 用依赖 move_to_local ___v2 的旧调度器验证加载成功。
generated_at: '2026-08-16T00:10:00'
source_email_count: 1
related_articles:
- sched-20260815-010
tags:
- sched_ext
title: 'sched_ext: Fix scx_bpf_dsq_reenq___compat kfunc extern prototype'
layout: article
---

## TL;DR
Tejun Heo 修复 `scx_bpf_dsq_move_to_local()` 的 `___v2` compat 变体 kfunc 探测/注册逻辑，使其能被旧 BPF 调度器正确解析。已 apply 到 sched_ext，与 010 同属 kfunc compat 暴露修复系列。

## 背景与问题
`scx_bpf_dsq_move_to_local()` 存在 `___v2` 兼容变体（因签名演进）。其 kfunc 探测在旧内核/旧调度器组合下未正确注册，导致依赖该变体的 BPF 程序加载失败。

## 技术方案
修正 `___v2` 变体的 kfunc 探测/注册分支，确保兼容路径正确暴露。与 010 同源问题（kfunc extern/compat 暴露），属配套修复。

## 版本演进与当前进展
v1（40870）2026-08-15 发出，作为 10 系列的 follow-up。Tejun 直接 apply。

## Maintainer 意见与讨论焦点
Tejun 自审自收，随 010 一起处理 compat kfunc 暴露缺陷。

## 合入评估
已合入 sched_ext。无悬空问题。

## 效果评估
恢复旧 BPF 调度器对 `move_to_local ___v2` 的可用性；无性能影响。

## 我可以参与的点
- 用依赖该变体的旧调度器验证加载成功。

## 参考链接
- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到
