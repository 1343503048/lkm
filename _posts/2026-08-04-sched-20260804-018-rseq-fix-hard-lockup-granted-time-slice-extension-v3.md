---
subject: rseq fix hard lockup granted time slice extension v3
id: sched-20260804-018
date: 2026-08-04
subsystem: sched
type: bug
status: under_review
severity: critical
thread_root_msgid: <20260802000000.0000000-1-rseq@kernel.org>
lore_url: unknown
authors:
- Peter Zijlstra
maintainers_involved:
- Peter Zijlstra
- Mathieu Desnoyers
current_version: v3
patch_series:
- version: v1
  msgid: <20260801000000.0000000-1-rseq@kernel.org>
  date: 2026-08-02
  summary: rseq 时间片扩展授予路径在开中断下调用要求关中断的 hrtimer_rearm_deferred_tif()，导致 hrtimer 锁反转硬死锁。原为单行
    guard(irq)()。（08-02-002）
  review_outcome: 08-02 已覆盖。
- version: v2
  msgid: <unknown>
  date: 2026-08-03
  summary: Peter Zijlstra 建议用 reflow 替代 guard(irq)()。（08-03-012）
  review_outcome: 08-03 已覆盖。
- version: v3
  msgid: <unknown>
  date: 2026-08-04
  summary: 08-04 上作者按 PeterZ 的 reflow 建议定稿 v3（将 TSE 授予与 hrtimer 重排组织到已知关中断路径），等待最终认可。
  review_outcome: reflow 方案获 PeterZ 认可方向，v3 待合入。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - reflow 改法需最终确认无其它开中断调用点
  next_action: 等待 PeterZ 对 v3 的最终 ack 后合入（critical 必修）。
contribution_opportunities:
- kind: testing
  description: 在 LOCKDEP + 高频 rseq TSE 授予负载下验证 reflow 版不再触发 hrtimer 锁反转，回帖 lockdep/lockup
    验证数据（作者仍未附 runs）。
generated_at: '2026-08-05T00:25:00'
source_email_count: 1
related_articles:
- sched-20260803-012-rseq-fix-hard-lockup-on-granted-time-slice-extension-v2
- sched-20260802-002-rseq-fix-hard-lockup-on-granted-time-slice-extension
tags:
- rseq
- hang
- preempt
title: rseq fix hard lockup granted time slice extension v3
layout: article
---

# rseq: 硬死锁修复（v3 reflow 定稿）

## TL;DR
rseq 时间片扩展授予路径的硬死锁（critical）在 08-04 按 Peter Zijlstra 的 reflow 建议定稿 v3：将 TSE 授予与 hrtimer 重排组织到已知关中断路径，避免新增 `guard(irq)()` 包装。仍 critical，待合入。

## 背景与问题
rseq 的「时间片扩展（TSE）」授予路径在开中断下调用要求关中断的 `hrtimer_rearm_deferred_tif()`，导致 hrtimer base 锁在 IRQ 重入时被反向获取，构成锁反转并最终硬死锁（真实间歇性 lockup 发现）。详见 08-02-002 / 08-03-012。

## 技术方案
- v1：单行 `guard(irq)()`（08-02-002）。
- v2：PeterZ 建议 reflow 替代 guard（08-03-012）。
- v3（08-04）：作者按 reflow 定稿——把 TSE 授予与 hrtimer 重排的上下文重新组织，使 `hrtimer_rearm_deferred_tif()` 始终在已知关中断路径下执行，不新增额外的 irq 作用域，更贴合既有锁设计。

## 版本演进与当前进展
v3（2026-08-04）。reflow 方案获 PeterZ 认可方向。

## Maintainer 意见与讨论焦点
Peter Zijlstra：倾向 reflow 而非隐藏问题，v3 体现该方向。无方向反对（critical 必修）。

## 合入评估
合入可能性 high（critical 必修）。仅剩 reflow 改法的最终确认。

## 效果评估
原问题有真实 lockup 实证。reflow 版效果需 LOCKDEP/lockup 复测确认，作者仍未附 runs。

## 我可以参与的点
- 在 LOCKDEP + 高频 rseq TSE 授予负载下复现原 lockup，验证 reflow 版 hrtimer 锁反转消失，回帖 lockdep 报告（作者未附 runs，是最直接验证参与点）。

## 参考链接
- 08-02 文章：sched-20260802-002-rseq-fix-hard-lockup-on-granted-time-slice-extension
- 08-03 文章：sched-20260803-012-rseq-fix-hard-lockup-on-granted-time-slice-extension-v2
