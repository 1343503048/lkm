# sched/doc: add a preemption model overview

## TL;DR
本文为增量更新，完整背景见 sched-20260922-016（v2）。Quchaosheng 快速迭代：v3 按 Sebastian Andrzej Siewior 的要求把「such a call」明确写为 `cond_resched()`（保留其 Reviewed-by），随后仅因第二枚 patch 变化而重发 v4（diff 无变化）。文档已获 Suggested-by/Reviewed-by 维护者认可，等待收取。

## 背景与问题
背景见 sched-20260922-016：调度文档只有各调度类与调参说明，没有抢占模型本身的概述，唯一出处是 `preempt=` 的 kernel-parameters 条目。

## 技术方案
新增 `Documentation/scheduler/sched-preemption.rst`（85 行）并挂进 `Documentation/scheduler/index.rst`，覆盖四种抢占模型、各模型下调度请求如何被兑现、哪些能在运行时选择。v3 唯一实质变化：把指代不清的「such a call」明确写为 `cond_resched()`。

## 版本演进与当前进展
- v1（09-20）：代码走读式概述（见 sched-20260920-003）。
- v2（09-22）：重写为「调度请求」视角（见 sched-20260922-016）。
- **v3**（09-22 22:53 UTC，`<20260923075304.584348-1-quchaosheng000406@163.com>`）：把「such a call」改写为 `cond_resched()`，Sebastian 要求，Reviewed-by 保留（仅该段变化）。
- **v4**（09-22 23:39 UTC，`<20260923083903.616271-1-quchaosheng000406@163.com>`）：diff 无变化，仅因第二枚 patch 变化而重发。

## Maintainer 意见与讨论焦点
维护者 Sebastian Andrzej Siewior（Suggested-by、Reviewed-by 本人）此前已认可（「looks good... please add it」），v3 的措辞修正即回应其要求。无争议、无 NAK。

## 合入评估
likelihood=high。纯文档补丁、Suggested-by/Reviewed-by 维护者已给、无争议。blocking_issues：无。next_action：等待文档维护者（或 sched 侧）收取合入。

## 效果评估
纯文档，无性能数据；澄清了 lazy 抢占真实动机（run-to-completion，非省 IPI，见 v2 分析）。

## 我可以参与的点
- kind=review：核对四种抢占模型描述与 `preempt=`/debugfs 实际行为的一致性（承前作验证点）。

## 参考链接
- lore（v4 补丁）: https://lore.kernel.org/all/20260923083903.616271-1-quchaosheng000406@163.com/
- lore（v3 补丁）: https://lore.kernel.org/all/20260923075304.584348-1-quchaosheng000406@163.com/
- lore（v2，见前作）: https://lore.kernel.org/all/20260922083101.99685-1-quchaosheng000406@163.com/

---
id: sched-20260923-010
subject: 'sched/doc: add a preemption model overview'
date: '2026-09-23'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20260923083903.616271-1-quchaosheng000406@163.com>'
lore_url: 'https://lore.kernel.org/all/20260923083903.616271-1-quchaosheng000406@163.com/'
authors:
  - 'Quchaosheng'
maintainers_involved:
  - 'Sebastian Andrzej Siewior'
current_version: v4
patch_series:
  - version: v1
    msgid: null
    date: '2026-09-20'
    summary: '代码走读式概述（见 sched-20260920-003）'
    review_outcome: 'Sebastian 要求鸟瞰视角'
  - version: v2
    msgid: '<20260922083101.99685-1-quchaosheng000406@163.com>'
    date: '2026-09-22'
    summary: '重写为调度请求视角，删测量段与 yield 措辞'
    review_outcome: 'Sebastian 认可'
  - version: v3
    msgid: '<20260923075304.584348-1-quchaosheng000406@163.com>'
    date: '2026-09-22'
    summary: '把 such a call 明确写为 cond_resched()'
    review_outcome: '回应 Sebastian 要求，Reviewed-by 保留'
  - version: v4
    msgid: '<20260923083903.616271-1-quchaosheng000406@163.com>'
    date: '2026-09-22'
    summary: 'diff 无变化，仅因第二枚 patch 更新而重发'
    review_outcome: '等待收取'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: '等待文档维护者收取'
contribution_opportunities:
  - kind: review
    description: '核对四种抢占模型描述与 preempt=/debugfs 实际行为的一致性'
generated_at: '2026-09-24T09:00:00'
source_email_count: 2
related_articles:
  - sched-20260922-016
  - sched-20260920-003
tags:
  - preempt
---