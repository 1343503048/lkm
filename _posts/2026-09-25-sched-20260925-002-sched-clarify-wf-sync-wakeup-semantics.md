---
id: sched-20260925-002
date: 2026-09-25
subject: 'sched: Clarify WF_SYNC wakeup semantics'
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: <179033364193.2819794.10008973300214008226.tip-bot2@tip-bot2>
lore_url: https://lore.kernel.org/all/179033364193.2819794.10008973300214008226.tip-bot2@tip-bot2/
upstream_commit: e4c353c3933968fe8efecb269fdbe3baa1d1ddd0
fixes_commit: null
merged_branch: tip/sched/core
current_version: v3
generated_at: '2026-09-26T01:15:00'
authors:
- Shubhang Kaushik (Ampere)
maintainers_involved:
- Peter Zijlstra
patch_series:
- version: v1
  msgid: <20260825-sched-wf-sync-doc-v1-0-f899edb44ff5@gentwo.org>
  date: 2026-08-25
  summary: 按实现调用流描述 WF_SYNC，新增 sched-wake-affinity.rst
  review_outcome: Vineeth Reddy 指出太实现相关
- version: v2
  msgid: <20260917-sched-wf-sync-doc-v2-0-6d1f107c0596@gentwo.org>
  date: 2026-09-17
  summary: 两枚：sched 文档 + sched/wait 注释修正
  review_outcome: Peter 质疑独立文档、倾向内联注释
- version: v3
  msgid: <20260922-sched-wf-sync-doc-v3-1-23ebe9e27bef@gentwo.org>
  date: 2026-09-22
  summary: 单枚：收敛为 WF_SYNC 定义旁内联注释 + 删除过时 waitqueue 措辞
  review_outcome: 09-25 Peter 合入 tip/sched/core
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入 tip/sched/core，等待进入合并窗口
contribution_opportunities: []
source_email_count: 1
related_articles:
- sched-20260923-005
- sched-20260918-001
tags:
- cfs
title: 'sched: Clarify WF_SYNC wakeup semantics'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles 中的 <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-005-sched-clarify-wf-sync-wakeup-semantics.html">sched-20260923-005</a> / <a class="article-ref" href="/lkm/2026/09/18/sched-20260918-001-sched-document-wf-sync-wakeup-placement-semantics.html">sched-20260918-001</a>。Shubhang Kaushik 的 WF_SYNC 唤醒语义文档修复（v3，单枚）已被 Peter Zijlstra 合入 tip/sched/core（commit e4c353c3933968fe8efecb269fdbe3baa1d1ddd0，09-25 12:45:59 +0200）。

## 背景与问题

同步 waitqueue 唤醒的注释长期声称「同步 wakee 不会被迁移到其他 CPU」。但调度器唤醒路径并不保证这一点。`WF_SYNC` 只是一个建议性提示：调用者预期 waker 很快会调度离开；调度类可以用它做放置或抢占，但调用者**不能**依赖它来阻止迁移、保持 CPU 局部性或让 wakee 下一个运行。错误的文档会误导使用方做出不成立的假设。

## 技术方案

把这一契约（contract）放到 `WF_SYNC` 标志定义旁边（`kernel/sched/sched.h`），删除 `kernel/sched/wait.c` 中过时的 waitqueue 措辞，并让带锁的 helper 引用不带锁的变体。合入版本 diffstat：kernel/sched/sched.h 与 kernel/sched/wait.c 共 12 insertions(+), 19 deletions(-)。

## 版本演进与当前进展

- v1（2026-08-25，`<20260825-sched-wf-sync-doc-v1-0-f899edb44ff5@gentwo.org>`）：按实现调用流描述 WF_SYNC，新增 sched-wake-affinity.rst；Vineeth Reddy 指出太实现相关。
- v2（2026-09-17，`<20260917-sched-wf-sync-doc-v2-0-6d1f107c0596@gentwo.org>`）：拆两枚（sched 文档 + sched/wait 注释修正）；Peter 质疑独立文档、倾向内联注释。
- v3（2026-09-22，`<20260922-sched-wf-sync-doc-v3-1-23ebe9e27bef@gentwo.org>`）：单枚，收敛为 WF_SYNC 定义旁内联注释 + 删除过时措辞；作者本为 Peter（Intel）签名。
- 09-25：合入 tip/sched/core（Commit-ID e4c353c3933968fe8efecb269fdbe3baa1d1ddd0）。

## Maintainer 意见与讨论焦点

Peter Zijlstra 更倾向把语义契约内联到标志定义旁、而不是独立文档（v2 拆分方案被否），v3 采纳了这条路线；本日 Peter 作为作者+committer 直接合入。无 NAK、无遗留分歧。

## 合入评估

已合入 tip/sched/core（*likelihood=merged*），commit e4c353c3933968fe8efecb269fdbe3baa1d1ddd0。纯文档/注释修复向的内联收敛，无阻塞项。

## 效果评估

文档/注释修复，无 benchmark 或运行时数据；效果体现在 API 契约表述的准确性上，属静态可证。暂无效果数据。

## 我可以参与的点

修复已合入，当前阶段暂无明显参与空间。

## 参考链接

- lore thread（tip-bot 合入通知）: https://lore.kernel.org/all/179033364193.2819794.10008973300214008226.tip-bot2@tip-bot2/
- gitweb: https://git.kernel.org/tip/e4c353c3933968fe8efecb269fdbe3baa1d1ddd0
- v3 补丁: https://lore.kernel.org/all/20260922-sched-wf-sync-doc-v3-1-23ebe9e27bef@gentwo.org/
