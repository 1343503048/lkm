---
id: sched-20260803-012
date: 2026-08-03
subsystem: sched
type: bug
status: under_review
severity: critical
thread_root_msgid: "<20260802000000.0000000-1-rseq@kernel.org>"
lore_url: "unknown"
authors: [Peter Zijlstra]
maintainers_involved: [Peter Zijlstra, Mathieu Desnoyers]
current_version: v2
patch_series:
  - version: v1
    msgid: "<20260801000000.0000000-1-rseq@kernel.org>"
    date: 2026-08-02
    summary: "修复 rseq 时间片扩展（TSE）授予路径在开中断下调用要求关中断的 hrtimer_rearm_deferred_tif()，导致 hrtimer 锁反转硬死锁。原为单行 guard(irq)()。属 critical，由真实间歇性 lockup 发现。"
    review_outcome: "08-02 已覆盖（系列 sched-20260802-002）。"
  - version: v2
    msgid: "<unknown>"
    date: 2026-08-03
    summary: "Peter Zijlstra 在 08-03 回帖，建议不要引入新的 guard(irq)() 包装，而是在调用点就明确 reflow（即把 TSE 授予与 hrtimer 重排的上下文重新组织，使重排始终在已知关中断路径下进行）。"
    review_outcome: "方向性 refine：用 reflow 替代新增 guard 包装，更贴合既有锁上下文设计。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["待作者确认采用 reflow 还是保留 guard(irq)()；PeterZ 倾向 reflow"]
  next_action: "等待原作者按 PeterZ 的 reflow 建议调整实现发 v2 定稿，再合入。"
contribution_opportunities:
  - kind: testing
    description: "可在打开 LOCKDEP + 高频 rseq TSE 授予场景下复现原 lockup，验证 reflow 版不再触发 hrtimer 锁反转，回帖 lockdep/lockup 验证数据。"
generated_at: "2026-08-04T00:20:00"
source_email_count: 1
related_articles: ["sched-20260802-002-rseq-fix-hard-lockup-on-granted-time-slice-extension"]
tags: [rseq, hang, preempt]
---
# rseq: 时间片扩展授予路径硬死锁（PeterZ 建议 reflow）


## TL;DR
rseq 时间片扩展授予路径的硬死锁（critical，08-02 系列 002）在 08-03 有新进展：Peter Zijlstra 建议用 reflow 替代新增 `guard(irq)()` 包装，更贴合既有锁上下文。仍 critical，待作者定稿 v2。

## 背景与问题
rseq 的「时间片扩展（TSE）」授予路径需要在中断上下文重排 deferred TIF，调用 `hrtimer_rearm_deferred_tif()`——该调用要求关中断。但授予路径在**开中断**下运行，导致 hrtimer 的 base 锁在 IRQ 重入时被反向获取，构成锁反转，最终表现为硬死锁。该问题最初通过真实间歇性 lockup 发现（非仅 lockdep 理论）。08-02 文章（sched-20260802-002）已覆盖 v1 的单行 `guard(irq)()` 修复。

## 技术方案
08-03 上 Peter Zijlstra 给出 reflow 建议：与其在调用点新增 `guard(irq)()` 包装（引入新的关中断作用域），不如把 TSE 授予与 hrtimer 重排的上下文重新组织（reflow），使 `hrtimer_rearm_deferred_tif()` 始终在已知的关中断路径下执行。这样不新增额外的锁/irq 作用域，更贴合既有锁设计，也避免 `guard(irq)` 可能掩盖更深层上下文问题。

## 版本演进与当前进展
- 08-02：v1 单行 `guard(irq)()`（sched-20260802-002）。
- 08-03：Peter Zijlstra 在 16272 回帖，提出 reflow 改法。当前等待原作者据此调整。

## Maintainer 意见与讨论焦点
Peter Zijlstra（核心 maintainer）：明确倾向 reflow 而非新增 `guard(irq)()`，认为后者「只是把问题藏起来」。这是实现风格/正确性层面的 refine，无方向反对（问题本身必须修）。

## 合入评估
合入可能性 high（critical 必修）。仅剩实现形式（reflow vs guard）的定稿，PeterZ 已给明确方向。

## 效果评估
原问题有真实 lockup 实证（08-02 记录）。reflow 版的效果需 lockdep/lockup 复测确认，作者尚未附 runs。

## 我可以参与的点
- 在 LOCKDEP + 高频 rseq TSE 授予负载下复现原 lockup，对 reflow 版验证 hrtimer 锁反转消失，回帖 lockdep 报告（作者未附 runs）。

## 参考链接
- 08-02 文章：sched-20260802-002-rseq-fix-hard-lockup-on-granted-time-slice-extension
- lore thread: 未获取到
