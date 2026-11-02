---
type: feature
status: under_review
severity: none
thread_root_msgid: <CANGjgd=DvO72NiB8SC3hNEadmxgzy1niN-mnWyY-LGMJ4H=J0g@mail.gmail.com>
authors:
- Chengfeng Lin
maintainers_involved: []
current_version: v3
patch_series: []
merge_assessment:
  likelihood: low
  blocking_issues:
  - 实验性重构，accounting 语义与 benchmark 影响未收敛
  next_action: 按 Mike 场景重测并收敛 accounting 行为
contribution_opportunities:
- kind: testing
  description: pinned wakelat+8 hog 同 cgroup 竞争场景复测
- kind: review
  description: 评估 __dequeue_task 更新对 DELAY_DEQUEUE 记账影响
upstream_commit: null
fixes_commit: null
merged_branch: null
source_email_count: 2
related_articles:
- sched-20261101-008
tags:
- eevdf
- cfs
id: sched-20261102-015
subject: 'sched/eevdf: Move to a single runqueue'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
title: 'sched/eevdf: Move to a single runqueue'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/11/01/sched-20261101-008-sched-eevdf-move-to-a-single-runqueue.html">sched-20261101-008</a>：Chengfeng Lin 的 v3 系列尝试把 EEVDF 收敛到单一 runqueue；本窗口内讨论单 runqueue 下 DELAY_DEQUEUE 记账与一次冗余 `update_curr_eevdf()` 的跳过（15-worker 场景 -0.22%、2-worker +1.27%）。
- sched-20261102（今天）：作者与 Mike Galbraith 继续benchmark对话——Mike 说明他观测到的负面影响来自「pinned wakelat + 8 个 pinned CPU-bound worker 挤在同一 cgroup 相互竞争」的 measurement 场景，作者表示愿意在他改动后全 worker 数量范围重跑 context-switch benchmark。

## 背景与问题

（承接）单 runqueue 是 EEVDF 方向性重构；今日聚焦 Mike 的实测场景定义与其 `__dequeue_task()` 更新处的问题定位。

## 技术方案

（承接）无新代码；今日为测试场景澄清与后续验证承诺。

## 版本演进与当前进展

v3；今日为 niceties 之外的实际测试安排。

## Maintainer 意见与讨论焦点

Mike 指出只要 `update_curr()` 远离 `cfs_rq_of(se)`、probe 就会安静（对纯 flat 单跑场景，这是 probe 产生的唯一信号）；作者愿意在其后续改动上全范围重跑。方向一致，无 NAK。

## 合入评估

likelihood=low。方向性、实验性重构，远未到合入阶段。

## 效果评估

（承接）跳过一次冗余 update：15-worker -0.22%、2-worker +1.27%；今日 no新数字。

## 我可以参与的点

- testing：在「pinned wakelat+8 pinned hog 竞争同一 cgroup」场景复测 context-switch。
- review：评估 `__dequeue_task()` 更新对 accounting 的语义影响。

## 参考链接

- lore thread: https://lore.kernel.org/all/CANGjgd=DvO72NiB8SC3hNEadmxgzy1niN-mnWyY-LGMJ4H=J0g@mail.gmail.com/
