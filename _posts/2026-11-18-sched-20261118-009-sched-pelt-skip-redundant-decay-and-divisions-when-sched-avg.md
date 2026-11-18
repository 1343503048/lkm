---
id: sched-20261118-009
date: '2026-11-18'
subject: 'sched/pelt: Skip redundant decay and divisions when sched_avg is zero'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <18e8d60c92652608.3137322e32332e3235332e313736.371783.0000sendgmr@google.com>
lore_url: https://lore.kernel.org/all/18e8d60c92652608.3137322e32332e3235332e313736.371783.0000sendgmr@google.com/
authors:
- Chris Wiseman
maintainers_involved:
- Vincent Guittot
- Peter Zijlstra
current_version: v2
patch_series:
- version: v1
  msgid: <18e837a02ddbadb6.3137322e32332e3235332e313736.1b3220.0000sendgmr@google.com>
  date: '2026-11-15'
  summary: 零负载提前返回 + !running 跳过 capacity scaling
  review_outcome: 无 review
- version: v2
  msgid: <18e8d60c92652608.3137322e32332e3235332e313736.371783.0000sendgmr@google.com>
  date: '2026-11-17'
  summary: v2（细节承接 v1）
  review_outcome: 共识：v3 去 ___update_load_avg hunk，保留 accumulate_sum/update_irq_load_avg
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 需作者出裁剪后的 v3
  next_action: Chris 出 v3（仅 accumulate_sum + update_irq_load_avg）
contribution_opportunities:
- kind: testing
  description: arm64 复测 0 除法 early-exit 下收益
- kind: review
  description: 核对 v3 裁剪后 update_irq_load_avg 跳过的正确性
generated_at: '2026-11-19T09:00:00+08:00'
source_email_count: 3
related_articles:
- sched-20261115-003
tags:
- cfs
- perf
title: 'sched/pelt: Skip redundant decay and divisions when sched_avg is zero'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/15/sched-20261115-003-sched-pelt-skip-redundant-decay-and-divisions-when-sched-avg.html">sched-20261115-003</a>：Chris Wiseman（Google）发 PELT 微优化——`sched_avg` 各字段归零后 `accumulate_sum()` 仍跑三次 `decay_load(0, periods)` 并触发三次零除法；补丁在零负载+已归零时提前返回 0、`!running` 时跳过 capacity scaling，100 万步随机化验证 bit-for-bit 一致，x86_64 idle 场景 -74.7%。
- <a class="article-ref" href="/lkm/2026/11/18/sched-20261118-009-sched-pelt-skip-redundant-decay-and-divisions-when-sched-avg.html">sched-20261118-009</a>（今天）：**v2 评审收口**——Peter 从「大多数现代 uarch 0 除法有 early out」角度提示收益可能有限，Vincent 指出「arm64 的 0 除法有优化、或许该始终做除法」，作者 Chris 表示共识是「v3 丢掉 ___update_load_avg 那一段（及 Suggested-by），只保留 accumulate_sum 与 update_irq_load_avg 的跳过」。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/15/sched-20261115-003-sched-pelt-skip-redundant-decay-and-divisions-when-sched-avg.html">sched-20261115-003</a>）承接 commit d040e0734fb3 的「跳过零负载」优化，本系列继续填补「已归零但仍做冗余衰减/除法」的空档。今日收口在：哪些提前返回真正值得保留（不同 uarch 上 0 除法的成本差异会改变收益判断）。

## 技术方案

今日为评审讨论、无新代码：

- **Peter Zijlstra**：提示多数现代 uarch 对「除以 0」都有 early out（更便宜）；但若分支预测率接近 100%，条件跳转可能在减少端口竞争上胜出；「若你的 uarch 除法很差，那几乎总是赚」。
- **Vincent Guittot**：arm64 已对 0 被除数做了优化（early exit），因此「或许始终做除法更好」——即部分平台上补丁的除法跳过未必是净收益。
- **Chris Wiseman（作者）**：综合共识，v3 将**丢掉 `___update_load_avg()` 那一 hunk（连同 Suggested-by）**，只保留 `accumulate_sum()` 与 `update_irq_load_avg()` 的跳过逻辑。

## 版本演进与当前进展

*current_version: v2（2026-11-17 发出，`<18e8d60c92652608.3137322e32332e3235332e313736.371783.0000sendgmr@google.com>`）*。今日为评审收口：作者宣布 v3 将裁剪 `___update_load_avg` hunk，只保留两处跳过。

## Maintainer 意见与讨论焦点

- **Vincent Guittot（sched/fair 维护者）**：arm64 0 除法 early-exit 使「始终除法」更优，暗示部分跳过无收益。
- **Peter Zijlstra**：0 除法 early out 普遍存在，收益取决于预测率与端口竞争。
- 无 NAK；共识已形成——缩小补丁范围（去 `___update_load_avg`），保留 `accumulate_sum`/`update_irq_load_avg`。

## 合入评估

*likelihood=medium*。方向被维护者认可、且有 bit-for-bit 正确性验证，但收益在部分 uarch 存疑，需作者按共识裁剪出 v3。*blocking_issues*：需作者出裁剪后的 v3（去 `___update_load_avg` hunk）。*next_action*：Chris 出 v3（仅 accumulate_sum + update_irq_load_avg）。

## 效果评估

既有（20261115-003）：1,000,000 步随机化 bit-for-bit 一致；10,000,000 次 x86_64 微基准 idle 场景 72.53→18.33 cyc（-74.7%）、最坏 +0.5%。今日 Peter/Vincent 提示：0 除法在 arm64/多数现代 uarch 有 early exit，补丁在那些平台收益打折。

## 我可以参与的点

- **testing**：在 arm64 上复测「始终保持除法 vs accumulate_sum 提前返回」的周期级差异，验证 Peter/Vincent 对 0 除法 early-exit 的判断。
- **review**：核对 v3 裁剪后 `update_irq_load_avg()` 跳过在 `!running` 下的正确性（是否遗漏 `cap_scale` 依赖）。

## 参考链接

- lore thread（v2）: https://lore.kernel.org/all/18e8d60c92652608.3137322e32332e3235332e313736.371783.0000sendgmr@google.com/
- Peter 对 0 除法 early out 的评论: https://lore.kernel.org/all/20261117160522.GH1922751@noisy.programming.kicks-ass.net/
- Vincent 对 arm64 的评论: https://lore.kernel.org/all/CAKfTPtB4dKRmK5hnv_Me7CJVECKmoNw7_VywgLyuFjKDi-Pa6w@mail.gmail.com/
