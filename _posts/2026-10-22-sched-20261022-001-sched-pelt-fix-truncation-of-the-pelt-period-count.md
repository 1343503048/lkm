---
id: sched-20261022-001
date: 2026-10-22
subject: 'sched/pelt: Fix truncation of the PELT period count'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261022034930.225042-1-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20261022034930.225042-1-sh_def@163.com/
authors:
- Hui Su
maintainers_involved:
- Vincent Guittot
current_version: v1
patch_series:
- version: v1
  msgid: <20261022034930.225042-1-sh_def@163.com>
  date: 2026-10-22
  summary: accumulate_sum() 返回 !!periods，避免 u32 截断
  review_outcome: Vincent Guittot / K Prateek Nayak / Kayra Cizmeci 评审，建议改 u64 并补
    Fixes
upstream_commit: null
fixes_commit: a481db34b9be
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 作者按意见（u64 返回 + Fixes 标签）发 v2
contribution_opportunities:
- kind: review
  description: v2 发出后复核 u64 返回与 Fixes 标签
- kind: testing
  description: 在 nohz 或长时无 PELT 更新场景验证修复
generated_at: '2026-10-23T01:20:00'
source_email_count: 7
related_articles: []
tags:
- cfs
title: 'sched/pelt: Fix truncation of the PELT period count'
layout: article
---

## TL;DR
Hui Su 发往 sched 的单补丁修复：`accumulate_sum()` 用 u64 计算已流逝的 PELT 周期数、却以 u32 返回；当周期数是 2^32 的整数倍（约 50 天不更新）时被截断为 0，调用方误判「无周期边界」跳过平均值重算，导致 `*_avg` 相对 `*_sum` 陈旧。v1 返回 `!!periods` 只告诉调用方「是否有周期流逝」。Vincent Guittot 与 K Prateek Nayak 均已 review：后者建议改返回 u64 并补 `Fixes: a481db34b9be`，作者将据此出 v2。

## 背景与问题
`accumulate_sum()`（`kernel/sched/pelt.c`）内部以 u64 累计 PELT 周期数，但函数签名返回 u32。周期为 1ms，2^32 个周期约 50 天；普通负载下 PELT 远在 0 之前就被高频更新，此极端场景难以自然发生。作者表示该问题**来自代码审查而非生产故障**，并用 KUnit 把 PELT 恰好推进 2^32 个周期复现：修复前 `util_avg` 停在 43（应为 1024），修复后测试通过；独立 harness 确认同样结果。

## 技术方案
单补丁（`kernel/sched/pelt.c`，+1/-1）：把返回语句从 `return periods;` 改为 `return !!periods;`——调用方只需要「是否有周期流逝」这一布尔信息，不需具体计数。讨论中 K Prateek Nayak 更倾向直接把返回类型改为 u64（`accumulate_sum()` 仅一处调用且位于 `if` 条件内，编译器可同样优化）；Hui Su 已确认 v2 将改用 u64 返回。

## 版本演进与当前进展
*current_version: v1*（`<20261022034930.225042-1-sh_def@163.com>`）。当日多轮讨论，作者确认 v2 将：改 `accumulate_sum()` 返回 u64、补 `Fixes: a481db34b9be`（"sched/fair: Optimize ___update_sched_avg()"）。

## Maintainer 意见与讨论焦点
Vincent Guittot 先问「是遇到实际故障还是仅审查发现」，随后给出 *Reviewed-by*，并判断「即使怀疑它真会发生，修了更好」。K Prateek Nayak 指出 nohz 下「至少一小时不更新 PELT」是可能的，建议返回 u64 并补 Fixes 标签。Kayra Cizmeci 附议 u64 更干净，给出 *Reviewed-by*。无明显分歧，仅「返回布尔 vs 返回 u64」的实现取向差异。

## 合入评估
*likelihood=high*。方向无异议，主维护者 Vincent 已 Reviewed-by；*blocking_issues*：无实质卡点，仅需作者按意见改 u64 与补 Fixes 后重发 v2；*next_action*：作者发 v2。

## 效果评估
无真实性能数据：问题是理论性截断，作者用 KUnit 复现（修复前 `util_avg` 43、修复后 1024）。Vincent 明确「怀疑它真会发生」，故作为正确性/健壮性修复对待，而非回退修复。

## 我可以参与的点
- *kind: review*：v2 发出后复核 u64 返回改动与 Fixes 标签是否准确。
- *kind: testing*：在长时间 nohz 或刻意构造「PELT 长时间不更新」的场景下验证修复，回帖确认。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261022034930.225042-1-sh_def@163.com/
- v2 计划由作者后续发出（未获取到 msgid）
