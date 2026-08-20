---
subject: 'sched_ext: Convert arena-pointer interfaces to __arena arguments'
id: sched-20260814-009
date: 2026-08-14
subsystem: sched
type: cleanup
status: merged_tip
severity: low
thread_root_msgid: <20260814011220.scx_arena_args@tj>
lore_url: 未获取到
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
- David Vernet
current_version: applied
patch_series:
- version: applied
  msgid: <20260814011220.scx_arena_args@tj>
  date: 2026-08-14
  summary: Tejun 将 sched_ext 的 arena-pointer 接口转换为 __arena 参数（PATCHSET 1-3），已 Applied
    到 sched_ext/for-7.3-arena-args。
  review_outcome: Tejun 直接 applied，无额外 review 轮次。
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.3-arena-args
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已进入 scx 分支，随后续进入主线。
contribution_opportunities:
- kind: testing
  description: 在启用 BPF arena 的 scx 调度器上验证接口转换无回归。
generated_at: '2026-08-15T00:15:00'
source_email_count: 1
related_articles:
- sched-20260810-001
tags:
- sched_ext
title: 'sched_ext: Convert arena-pointer interfaces to __arena arguments'
layout: article
---

## TL;DR
Tejun Heo 将 sched_ext 的 arena-pointer 接口转换为 `__arena` 参数（PATCHSET 1-3），已 Applied 到 `sched_ext/for-7.3-arena-args`。merged_tip。

## 背景与问题
sched_ext 此前用 arena-pointer 风格的接口传递 BPF arena 内存，较繁琐。统一改为 `__arena` 参数形式，使接口更简洁、与 BPF arena 使用惯例一致。

## 技术方案
将相关接口从 arena-pointer 形式转换为 `__arena` 参数（PATCHSET 1-3，具体 diff 以分支为准）。属接口现代化清理，无功能性变更（语义等价）。

## 版本演进与当前进展
已由 Tejun 直接 Applied 到 `sched_ext/for-7.3-arena-args`，无后续版本。

## Maintainer 意见与讨论焦点
Tejun 作为维护者直接 applied；无争议。

## 合入评估
已合入 scx 分支（merged_tip），随后续进主线。

## 效果评估
接口现代化，无功能/性能影响。

## 我可以参与的点
- 在启用 arena 的 scx 调度器上验证无回归。

## 参考链接
- 分支: sched_ext/for-7.3-arena-args
