---
id: sched-20261023-006
date: 2026-10-23
subject: 'sched/pelt: Fix truncation of the PELT period count'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261023025207.2967903-1-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20261023025207.2967903-1-sh_def@163.com/
authors:
- Hui Su
maintainers_involved:
- Vincent Guittot
- K Prateek Nayak
current_version: v2
patch_series:
- version: v1
  msgid: <20261022034930.225042-1-sh_def@163.com>
  date: 2026-10-22
  summary: accumulate_sum() 返回 !!periods，避免 u32 截断
  review_outcome: Vincent/K Prateek Nayak/Kayra 评审，建议改 u64 并补 Fixes
- version: v2
  msgid: <20261023025207.2967903-1-sh_def@163.com>
  date: 2026-10-23
  summary: accumulate_sum() 返回 u64，补 Fixes a481db34b9be 与 Kayra Reviewed-by
  review_outcome: K Prateek Nayak 当日追加 Reviewed-by；无异议
upstream_commit: null
fixes_commit: a481db34b9be
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等维护者收取
contribution_opportunities:
- kind: review
  description: 复核 u64 返回与 Fixes 标签指向是否准确
- kind: testing
  description: 在 nohz 或长时无 PELT 更新场景验证修复
generated_at: '2026-10-24T09:05:00'
source_email_count: 2
related_articles:
- sched-20261022-001
tags:
- cfs
title: 'sched/pelt: Fix truncation of the PELT period count'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/10/22/sched-20261022-001-sched-pelt-fix-truncation-of-the-pelt-period-count.html">sched-20261022-001</a>：Hui Su 发往 sched 的单补丁修复——`accumulate_sum()` 用 u64 计算已流逝的 PELT 周期数、却以 u32 返回；当周期数是 2^32 的整数倍（约 50 天不更新）时被截断为 0，调用方误判「无周期边界」跳过平均值重算，导致 `*_avg` 相对 `*_sum` 陈旧。v1 返回 `!!periods`；Vincent Guittot 与 K Prateek Nayak 均 review，后者建议改返回 u64 并补 `Fixes: a481db34b9be`，作者将据此出 v2。
- <a class="article-ref" href="/lkm/2026/10/23/sched-20261023-006-sched-pelt-fix-truncation-of-the-pelt-period-count.html">sched-20261023-006</a>（今天）：**v2 发出**——按上日意见把 `accumulate_sum()` 返回类型改为 u64、补 `Fixes: a481db34b9be`，并带上 Kayra Cizmeci 的 `Reviewed-by`；当日 K Prateek Nayak 追加 `Reviewed-by`。至此 Vincent、K Prateek Nayak、Kayra Cizmeci 三人背书，改动 1 行（`sched/pelt.c` +1/-1），待维护者收取。

## 背景与问题
`accumulate_sum()`（`kernel/sched/pelt.c`）内部以 u64 累计 PELT 周期数，但函数签名返回 u32。周期为 1ms，2^32 个周期约 50 天；普通负载下 PELT 远在 0 之前就被高频更新，此极端场景难以自然发生。作者表示该问题**来自代码审查而非生产故障**，并用 KUnit 把 PELT 恰好推进 2^32 个周期复现：修复前 `util_avg` 停在 43（应为 1024），修复后测试通过；独立 harness 确认同样结果。今日 v2 无新背景，问题定性不变。

## 技术方案
（承接 20261022-001）单补丁（`kernel/sched/pelt.c`，+1/-1）。v1 讨论中 K Prateek Nayak 更倾向直接把返回类型改为 u64（`accumulate_sum()` 仅一处调用且位于 `if` 条件内，编译器可同样优化），Hui Su 确认照此改。**v2 实际改动**：把 `static __always_inline u32 accumulate_sum(...)` 的返回类型改为 `u64`，让调用方能无截断地测试周期计数；相对 v1 的 `return !!periods;`，v2 直接返回完整 u64 计数。

## 版本演进与当前进展
*current_version: v2*（`<20261023025207.2967903-1-sh_def@163.com>`）。v2 changes：返回类型改 u64、补 `Fixes: a481db34b9be`、加 Kayra Cizmeci 的 Reviewed-by。v1 链接见作者邮件内 `https://lore.kernel.org/lkml/20261022034930.225042-1-sh_def@163.com/`。

## Maintainer 意见与讨论焦点
- Vincent Guittot（v1 即给 *Reviewed-by*）：先问「实际故障还是仅审查发现」，判断「即使怀疑它真会发生，修了更好」。
- K Prateek Nayak（今日 *Reviewed-by*）：v1 建议改 u64 + 补 Fixes，v2 落地后即时追加 Reviewed-by。
- Kayra Cizmeci（v1 即 *Reviewed-by*）：附议 u64 更干净。无分歧，仅「返回布尔 vs 返回 u64」的实现取向，已按维护者偏好收敛。

## 合入评估
*likelihood=high*。方向无异议，主维护者 Vincent 与资深 reviewer K Prateek Nayak/Kayra 均已 Reviewed-by，v2 已完全按评审意见落地（u64 + Fixes）。*blocking_issues*：无实质卡点，仅待维护者收取进 tip/sched/core。*next_action*：等维护者收取。

## 效果评估
无真实性能数据：问题是理论性截断，作者用 KUnit 复现（修复前 `util_avg` 43、修复后 1024）。今日无新增数据。

## 我可以参与的点
- *kind: review*：v2 已齐备，可在收取前复核 u64 返回改动与 Fixes 标签指向（`a481db34b9be` = "sched/fair: Optimize ___update_sched_avg()"）是否准确。
- *kind: testing*：在长时间 nohz 或刻意构造「PELT 长时间不更新」的场景下验证修复。

## 参考链接
- v2: https://lore.kernel.org/all/20261023025207.2967903-1-sh_def@163.com/
- K Prateek Nayak 回帖: https://lore.kernel.org/all/9d1381a4-6f4f-48aa-b76f-fad11e9d5bc9@amd.com/
- 前文: <a class="article-ref" href="/lkm/2026/10/22/sched-20261022-001-sched-pelt-fix-truncation-of-the-pelt-period-count.html">sched-20261022-001</a>（v1 分析与 v1→v2 计划）
