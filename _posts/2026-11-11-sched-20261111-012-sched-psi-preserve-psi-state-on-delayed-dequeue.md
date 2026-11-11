---
id: sched-20261111-012
date: '2026-11-11'
subject: 'sched/psi: Preserve PSI state on delayed dequeue'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261110-psi-delayed-deq-v2-1-17ac1688f0e9@gentwo.org>
lore_url: https://lore.kernel.org/all/20261110-psi-delayed-deq-v2-1-17ac1688f0e9@gentwo.org/
authors:
- Shubhang Kaushik
maintainers_involved: []
current_version: v2
patch_series:
- version: v2
  msgid: <20261110-psi-delayed-deq-v2-1-17ac1688f0e9@gentwo.org>
  date: '2026-11-10'
  summary: psi_dequeue 对 DEQUEUE_DELAYED 保持状态不变；修正 Fixes tag
  review_outcome: Kayra Cizmeci Reviewed-by
upstream_commit: null
fixes_commit: c2ae8b0df2d1
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: PSI 维护者收取（适合 fix/stable 队列）
contribution_opportunities: []
generated_at: '2026-11-12T09:00:00+08:00'
source_email_count: 2
related_articles:
- sched-20261103-005
tags:
- psi
- eevdf
title: 'sched/psi: Preserve PSI state on delayed dequeue'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/03/sched-20261103-005-sched-psi-preserve-psi-state-on-delayed-dequeue.html">sched-20261103-005</a>：Shubhang Kaushik（Ampere）修 PSI——EEVDF 的 delayed dequeue（`DEQUEUE_DELAYED`）只「完成」先前已记账的 sleep dequeue，但 `psi_dequeue()` 仍清掉全部 PSI 标志（含 TSK_IOWAIT），导致睡眠压力记账被提前终止、唤醒时触发 `psi: inconsistent task state` 警告；修复让 `DEQUEUE_DELAYED` 与 `DEQUEUE_SAVE` 一样保持 PSI 状态不变。
- <a class="article-ref" href="/lkm/2026/11/11/sched-20261111-012-sched-psi-preserve-psi-state-on-delayed-dequeue.html">sched-20261111-012</a>（今天）：**v2 发出并获 Kayra Cizmeci Reviewed-by**——v2 修正 `Fixes:` tag 为 `c2ae8b0df2d1`（"sched/core: Fix psi_dequeue() for Proxy Execution"），并澄清回归是「post-switch sleeping dequeue 开始清 PSI 状态」时引入的。Kayra 复述故障链后给 Reviewed-by：进 delayed dequeue 后未真正唤醒就离开时不会清标志，真正唤醒时也不会再误清。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/03/sched-20261103-005-sched-psi-preserve-psi-state-on-delayed-dequeue.html">sched-20261103-005</a>）EEVDF 会把阻塞的 fair 任务作为 `sched_delayed` 保留到最终移除前。初次 sleep 时 `psi_dequeue()` 因任务仍 TSK_ONCPU 什么都不做，`psi_sched_switch(sleep=true)` 把任务从 runnable 转 sleeping、保留 TSK_IOWAIT 与持久内存 stall 状态。之后 delayed 任务作为 still-asleep 被物理移除（`wait_task_inactive() → dequeue_task(DEQUEUE_SLEEP|DEQUEUE_DELAYED)`，或 `switching_from_fair() → dequeue_task(...|DEQUEUE_DELAYED|DEQUEUE_NOCLOCK)`），此时 `psi_dequeue()` 清掉了全部 PSI 标志（含 TSK_IOWAIT）——尽管任务仍 asleep；唤醒时 `psi_enqueue()` 期望清理 TSK_IOWAIT 却扑空，`psi: inconsistent task state` 警告即为症状。

## 技术方案

`kernel/sched/stats.h`：把 `psi_dequeue()` 的提前返回条件从 `if (flags & DEQUEUE_SAVE)` 扩展为 `if (flags & (DEQUEUE_SAVE | DEQUEUE_DELAYED))`，并同步注释说明 delayed dequeue 完成的是前一次 sleep dequeue 记账后的 runnable→sleeping 转移。v2 仅修正 `Fixes:` tag（`c2ae8b0df2d1`）并澄清回归引入点，无代码变化。

## 版本演进与当前进展

*current_version: v2（2026-11-10，`<20261110-psi-delayed-deq-v2-1-17ac1688f0e9@gentwo.org>`）*。v1→v2：修正 Fixes tag、澄清回归引入因由。当日 Kayra 给 Reviewed-by。

## Maintainer 意见与讨论焦点

- **Kayra Cizmeci（评审者）**：复述故障链（进 delayed dequeue → 未真唤醒就离开 → `psi_dequeue()` 清标志 → 真唤醒时再次清理落空）后确认修复正确，给 Reviewed-by。
- 无 NAK、无未解决分歧，单补丁低争议。

## 合入评估

*likelihood=high*。单行修复、带准确 Fixes tag、获 Reviewed-by，无明显争议。*blocking_issues*：无。*next_action*：PSI 相关维护者（Johannes Weiner）收取；Fixes 指向 recent commit，适合进 fix 队列或 stable。

## 效果评估

作者给出功能验证：80 核 Ampere Altra 上，v7.4-rc1（`6628e7d4c6b2`）把 delayed direct-I/O 任务从 SCHED_OTHER 切到 SCHED_FIFO 会触发 `psi: inconsistent task state`；打补丁后同一测试无 PSI 警告。无性能数据。

## 我可以参与的点

当前阶段暂无明显参与空间，可持续观察后续是否被收取进 PSI 相关队列。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261110-psi-delayed-deq-v2-1-17ac1688f0e9@gentwo.org/
- Kayra 的 Reviewed-by: https://lore.kernel.org/all/avQfCeibnuffnZUE@scheduler.schedules/
