# sched/doc: add a preemption model overview

## TL;DR
本文为增量更新，完整背景见 sched-20260920-003（v1）。Quchaosheng 发出 v2：按 Sebastian Andrzej Siewior 的意见把文档重写为「围绕调度请求」的鸟瞰视角（wakeup → 决定谁让出 CPU → 置 TIF_NEED_RESCHED[LAZY] → 抢占模型决定在哪兑现），删掉错误的测量段与 yield 措辞，并把 debugfs 段并入运行时选择小节。新增 `Documentation/scheduler/sched-preemption.rst`（84 行）。Sebastian 建议合入。

## 背景与问题
背景见 sched-20260920-003：调度文档只有各调度类与调参说明，没有抢占模型（PREEMPT_NONE/VOLUNTARY/FULL/LAZY 等四模型）本身的概述，唯一出处是 `preempt=` 的 kernel-parameters 条目。

## 技术方案
新增 `sched-preemption.rst`，覆盖四种模型、各模型下调度请求如何被兑现、哪些能在运行时选择。v2 改为沿着「调度请求」主线叙述，而非 v1 的「走读 `resched_curr_lazy()`/`scheduler_tick()` 代码」方式。

## 版本演进与当前进展
v2（`<20260922083101.99685-1-quchaosheng000406@163.com>`）当日发出，改动：重写为调度请求视角（Sebastian 要求鸟瞰而非代码走读）；删测量段（v1 误称 lazy 为省跨 CPU IPI，实为 run-to-completion）；删模型表中的 yield 措辞；debugfs 并入运行时选择小节。

## Maintainer 意见与讨论焦点
- **Sebastian Andrzej Siewior**（Suggested-by 本人）：v1 时要求鸟瞰视角，v2 回应后当天回复「looks good... please add it」认可方向。无争议。

## 合入评估
*likelihood=high*。文档补丁、Suggested-by 维护者认可、无争议。blocking_issues 无；next_action 等待文档维护者收取。

## 效果评估
纯文档，无性能数据；澄清了 lazy 抢占的真实动机（run-to-completion，非省 IPI）。

## 我可以参与的点
- **review**：核对四种抢占模型描述与 `preempt=`/debugfs 实际行为的准确性。

## 参考链接
- lore（v2）: https://lore.kernel.org/all/20260922083101.99685-1-quchaosheng000406@163.com/
- Sebastian 回复: https://lore.kernel.org/all/20260922075525.INLFCiYI@linutronix.de/

---
id: sched-20260922-016
date: '2026-09-22'
subject: 'sched/doc: add a preemption model overview'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20260922083101.99685-1-quchaosheng000406@163.com>'
lore_url: 'https://lore.kernel.org/all/20260922083101.99685-1-quchaosheng000406@163.com/'
authors:
  - 'Quchaosheng'
maintainers_involved:
  - 'Sebastian Andrzej Siewior'
current_version: v2
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
    review_outcome: 'Sebastian 认可（looks good, please add it）'
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
generated_at: '2026-09-23T00:00:00'
source_email_count: 4
related_articles:
  - sched-20260920-003
tags:
  - preempt
---