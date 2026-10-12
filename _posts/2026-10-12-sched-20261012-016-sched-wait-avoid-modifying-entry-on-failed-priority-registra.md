---
id: sched-20261012-016
date: '2026-10-12'
subject: 'sched/wait: avoid modifying entry on failed priority registration'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261011015019.4056529-1-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20261011015019.4056529-1-sh_def@163.com/
authors:
- Hui Su
maintainers_involved:
- Sean Christopherson
current_version: v1
patch_series:
- version: v1
  msgid: <20261011015019.4056529-1-sh_def@163.com>
  date: '2026-10-11'
  summary: 把 flags 更新移到失败检查之后，避免注册失败时 entry 被改 flags
  review_outcome: Sean Christopherson 给出 Reviewed-by 并澄清当前无害
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 已获 Reviewed-by，等 Peter 收取 wait.c 修复
contribution_opportunities: []
generated_at: '2026-10-13T01:40:00'
source_email_count: 1
related_articles:
- sched-20261011-002
tags:
- wait
title: 'sched/wait: avoid modifying entry on failed priority registration'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/11/sched-20261011-002-sched-wait-avoid-modifying-entry-on-failed-priority-registra.html">sched-20261011-002</a>：Hui Su 修 `add_wait_queue_priority_exclusive()` 的小正确性问题——先设 `WQ_FLAG_EXCLUSIVE|WQ_FLAG_PRIORITY` 再检查失败，导致 `-EBUSY` 失败时 entry 未入队却被改了 flags。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-016-sched-wait-avoid-modifying-entry-on-failed-priority-registra.html">sched-20261012-016</a>（今天）：Sean Christopherson 给出 `Reviewed-by`，并澄清该问题在当前代码基上完全良性（唯一用户 `kvm_irqfd_register()` 失败时 KVM 从不碰 entry；spinlock 外无人窥探 wait 队列条目）。

## 背景与问题

（承接 20261011-002）`add_wait_queue_priority_exclusive()` 在检查是否已有其他 priority waiter 之前就设置了两标志，注册失败（-EBUSY）时 entry 没入队却被修改了 flags——逻辑上不干净，但实际影响有限。

## 技术方案

（承接 20261011-002）把 flags 更新移到失败检查之后，注册失败时 entry 保持原状。Sean 补充：无需依赖 spinlock 获取来为 flags 更新与 `list_add()` 定序（无 RCU 窥探者），当前唯一用户 KVM 失败路径不碰 entry。

## 版本演进与当前进展

v1（10-11）→ 今日（10-12）Sean Christopherson `Reviewed-by`，并说明改动良性。

## Maintainer 意见与讨论焦点

Sean Christopherson 明确 `Reviewed-by` 且无保留；无 NAK。

## 合入评估

*likelihood=high*。小修复 + 资深维护者 R-b + 语义澄清。*blocking_issues*：无。*next_action*：等 Peter 收取 wait.c 修复。

## 效果评估

无性能数字（正确性/健壮性小修复）。

## 我可以参与的点

已获 R-b、无争议，当前阶段暂无明显参与空间。

## 参考链接

- lore（v1）: https://lore.kernel.org/all/20261011015019.4056529-1-sh_def@163.com/
- lore（Sean Reviewed-by）: https://lore.kernel.org/all/aszhbJz0N7cOy5fx@google.com/
