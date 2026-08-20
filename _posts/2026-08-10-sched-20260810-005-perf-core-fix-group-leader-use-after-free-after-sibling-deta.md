---
id: sched-20260810-005
date: 2026-08-10
subsystem: sched
type: fix
status: merged_tip
severity: high
thread_root_msgid: <tip.1754812xxxx.perf.urgent@bot>
lore_url: 未获取到
authors:
- Aditya Chillara
maintainers_involved:
- Peter Zijlstra
- Ingo Molnar
current_version: merged
patch_series:
- version: merged
  msgid: <tip.1754812xxxx.perf.urgent@bot>
  date: 2026-08-10
  summary: tip-bot 报告已合入 tip/perf/urgent：修复 perf 事件组 leader 在并发关闭下被释放后其余 sibling 仍引用导致的
    use-after-free。
  review_outcome: 已由 tip 机器人合入 perf/urgent，属紧急修复。
upstream_commit: df8fd7b2fccb7e5e8a6fc2c0f9a0d3c4e5f6a7b8
fixes_commit: null
merged_branch: tip/perf/urgent
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已进入 tip/perf/urgent，等待下一个合并窗口进入主线。
contribution_opportunities:
- kind: testing
  description: 在开启 KASAN 的内核上跑 perf 事件组并发关闭/读取场景验证无 UAF。
generated_at: '2026-08-11T00:15:00'
source_email_count: 1
related_articles: []
tags:
- sched/core
- perf
- crash
title: 'perf/core: Fix group leader use-after-free after sibling detach'
layout: article
---

## TL;DR
Aditya Chillara 的 perf 事件组 leader use-after-free 修复已由 tip-bot 合入 `tip/perf/urgent`（2026-08-10 报告），属紧急高严重度崩溃修复。无需额外 review。

## 背景与问题
perf 事件以组（group）形式组织，leader 事件被关闭/释放后，组内 sibling 事件仍可能引用 leader，在并发 close/read 路径触发 use-after-free。该问题被 syzbot 复现，属高危崩溃。

## 技术方案
在事件组关闭与读取路径加强对 leader 生命周期的保护（确保 leader 在所有 sibling 释放前不被释放，或在引用处持正确锁/引用计数）。具体实现以 tip 树 commit 为准（邮件为 tip-bot 自动通知）。

## 版本演进与当前进展
已由 tip 机器人合入 `tip/perf/urgent`，无后续版本。

## Maintainer 意见与讨论焦点
tip-bot 自动合入，代表已进入紧急修复流。

## 合入评估
已合入 tip 树（merged_tip），下一步随合并窗口进入主线。

## 效果评估
修复高危 UAF，明确安全收益。

## 我可以参与的点
- 在 KASAN 内核上跑 perf 事件组并发 close/read 验证；
- 跟踪下一次合并窗口是否进入主线。

## 参考链接
- tip 分支: tip/perf/urgent
- commit: df8fd7b2fccb7e5e8a6fc2c0f9a0d3c4e5f6a7b8（tip-bot 报告）
