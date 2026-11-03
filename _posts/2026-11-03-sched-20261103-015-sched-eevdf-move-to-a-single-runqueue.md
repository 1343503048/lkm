---
id: sched-20261103-015
date: 2026-11-03
subject: 'sched/eevdf: Move to a single runqueue'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/37fb82ff-ed5d-41d7-91b7-afe4379a636c@linux.alibaba.com/
authors:
- Chengfeng Lin
maintainers_involved: []
current_version: v3
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - DELAY_ZERO 记账语义未收敛
  - 需证明广泛负载下无回退
  next_action: 给出 333238da9a19 回退的修复或 DELAY_ZERO 默认关论证。
contribution_opportunities:
- kind: testing
  description: 交叉验证 context_switch 与 pipe 场景的 DELAY_ZERO on/off。
- kind: review
  description: 评估 333238da9a19 与 DELAY_ZERO 语义是否应解耦。
generated_at: '2026-11-04T09:00:00+08:00'
source_email_count: 3
related_articles:
- sched-20261101-008
- sched-20261102-015
tags:
- eevdf
- cfs
- regression
title: 'sched/eevdf: Move to a single runqueue'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/11/01/sched-20261101-008-sched-eevdf-move-to-a-single-runqueue.html">sched-20261101-008</a>：Chengfeng Lin 的 v3 系列尝试把 EEVDF 收敛到单一 runqueue；窗口内讨论单 runqueue 下 DELAY_DEQUEUE 记账与跳过一次冗余 `update_curr_eevdf()`（15-worker -0.22%、2-worker +1.27%）。
- <a class="article-ref" href="/lkm/2026/11/02/sched-20261102-015-sched-eevdf-move-to-a-single-runqueue.html">sched-20261102-015</a>：作者与 Mike Galbraith 继续 benchmark 对话，澄清 Mike 观测的负面影响来自其 measurement 场景（pinned wakelat + 8 个 pinned CPU-bound worker 挤同一 cgroup），作者愿意全范围重跑。
- <a class="article-ref" href="/lkm/2026/11/03/sched-20261103-015-sched-eevdf-move-to-a-single-runqueue.html">sched-20261103-015</a>（今天）：Tianchen Ding 报告 pipe 上下文切换回退、bisect 到 `333238da9a19`（"sched: Update time before requeueing delayed entities"），机理是「先更新 curr 再算 delayed wakee 的 lag」提前推进 rq 平均 vruntime、配合 DELAY_ZERO 把 wakee 正 lag 截 0 触发 repositioning，使 curr 经 slice 保护持 CPU；建议 DELAY_ZERO 默认关。Chengfeng Lin 实测关闭 DELAY_ZERO 在 15-worker 场景 +13.7% 吞吐。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/01/sched-20261101-008-sched-eevdf-move-to-a-single-runqueue.html">sched-20261101-008</a> / 20261102-015）单一 runqueue 是 EEVDF 方向性重构，目标是消除多核 per-CPU runqueue 的负载分布与迁移开销；评审持续关注对 DELAY_DEQUEUE 记账行为的影响。今日新增一个可复现的 pipe 场景回退定位。

## 技术方案

（承接）今日为回退机理分析，无新补丁：Tianchen 指出 `333238da9a19` 把「更新 curr」提前到「计算 delayed wakee 的 lag」之前，会推进 runqueue 的平均 vruntime；DELAY_ZERO 开启时 wakee 的正 lag 被截为 0、触发 repositioning；当 cfs_rq 里只有 curr 与 wakee 时，两者 vruntime 对齐、双双 eligible，curr 经 slice 保护继续持 CPU（等权等 slice 时 wakee 的新 deadline 还可能晚于 curr 剩余 deadline）。改动前 wakee 通常会在 curr 的 pipe write 后抢占 curr，改动后 curr 常持续到下次 read 发现 reply pipe 空才阻塞自切换。建议尝试默认关 DELAY_ZERO。

## 版本演进与当前进展

*current_version: v3（7 补丁系列，cover msgid 未获取到；今日仍 v3）*。今日 Tianchen、Mike、Chengfeng 继续讨论。

## Maintainer 意见与讨论焦点

Tianchen 提议「是否把 DELAY_ZERO 默认关掉」。Mike 表示「这个回退会随尘埃落定被修好」，并肯定 reporter 的 probe 验证了 DELAY_DEQUEUE 是真实的 QOS 改进。Chengfeng 在 v7.3 内核上三次 fresh boot（DELAY_ZERO on/off/on）实测 15-worker context_switch：off 相对 on 均值 +13.70%（9.172→10.425 百万 handoffs/s），且 15-worker 的非自愿切换占比从 0.36% 变 41.48%（off）——与 Tianchen 的 handoff 解释一致。无 NAK，属技术细节收敛中；Peter/Vincent/Ingo 等核心维护者本窗口未表态。

## 合入评估

*likelihood=low*。单 runqueue 是调度器核心结构重构，DELAY_ZERO 记账语义仍在争论，尚无维护者认可。*next_action*：就 `333238da9a19` 的回退给出修复（或 DELAY_ZERO 默认关的论证），并证明广泛负载下无回退。

## 效果评估

今日 Chengfeng 给出量化数据：15-worker pipe-handoff 关闭 DELAY_ZERO 后 +13.7% 吞吐（9.172→10.425M handoffs/s，boot 内 CV≤0.60%），非自愿切换占比 0.36%→41.48%→0.36%（on/off/on）。Tianchen 报告 pipe 上下文切换回退并 bisect 到 `333238da9a19`。

## 我可以参与的点

- testing：在作者 benchmark（context_switch1_threads -s 15 -t 2/15）与 Tianchen 的 pipe 场景上交叉验证 DELAY_ZERO on/off。
- review：评估 `333238da9a19` 的「先更新 curr」是否应与 DELAY_ZERO 语义解耦、以及 DELAY_ZERO 默认关的可行性与影响面。

## 参考链接

- lore thread（今日 Tianchen 回帖）: https://lore.kernel.org/all/37fb82ff-ed5d-41d7-91b7-afe4379a636c@linux.alibaba.com/
- 相关 commit: 333238da9a19（"sched: Update time before requeueing delayed entities"）
