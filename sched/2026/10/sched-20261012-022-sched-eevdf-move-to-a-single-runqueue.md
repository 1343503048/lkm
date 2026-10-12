# sched/eevdf: Move to a single runqueue

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260923-001 / 20261007-009：Aishwarya Rambhadran（ARM）报告 v7.2→v7.3 在 AWS Graviton3 上个别 schbench 线程配置 p99 回退 ~30%，bisect 指向「sched/eevdf: Move to a single runqueue」commit；后续怀疑点收敛到 WA_WEIGHT/task_h_load，社区提议试 NO_WA_WEIGHT 与 cgroup_mode 规避。
- sched-20261012-022（今天）：Mike Galbraith 把 flat（单运行队列）搬回 7.2 做混合负载对比（7.2-virgin vs 7.2+flat，默认配置），观察到竞争者负载从「1 组 8」切到「4 组 2」时 CPU 分布出现 delta，结论是「cgroup vs cgroup 的数值抖动一定会比平常更大」。

## 背景与问题

（承接 20260923-001/20261007-009）单运行队列改动在 cgroup 竞争场景下的 CPU 分配稳定性存疑，此前的 p99 回退报告聚焦特定 schbench 线程配置。

## 技术方案

无新方案；今日为 Mike 的独立复测观察，进一步把现象框定为「cgroup vs cgroup 分配的抖动放大」。

## 版本演进与当前进展

回归报告持续跟踪中（20260923-001 → 20261007-009 → 今日）；Mike 补充 7.2+flat 对照观察，仍未得到 Peter 的定论。

## Maintainer 意见与讨论焦点

Mike Galbraith（资深调度专家，非 maintainer）以 7.2+flat 对照实验提示 cgroup vs cgroup 数值会「wiggle more than usual」；未见 Peter 就此表态。

## 合入评估

*likelihood=unknown*。属已合入改动的性能回归跟踪，是否预期取舍待 Peter 定夺。*blocking_issues*：无定论。*next_action*：等 Peter 回应抖动是否在预期内。

## 效果评估

Mike 未给具体数字（仅定性描述「CPU distribution delta…wiggle more than usual」），此前的 ~30% p99 回退与 NO_WA_WEIGHT/cgroup_mode 规避仍在 related 中。

## 我可以参与的点

- `testing`：复现 Mike 的混合负载（1×8 vs 4×2 竞争者 + 固定 4 client netperf），量化 cgroup vs cgroup 的抖动幅度并回帖数据。

## 参考链接

- lore（Mike 的 7.2+flat 对照）: https://lore.kernel.org/all/eac663e09be5dbadaded334f2f80d2c21f3b14cb.camel@gmx.de/

---
id: sched-20261012-022
date: '2026-10-12'
subject: 'sched/eevdf: Move to a single runqueue'
subsystem: sched
type: regression
status: under_review
severity: medium
thread_root_msgid: <20260605105513.354837583@infradead.org>
lore_url: https://lore.kernel.org/all/20260605105513.354837583@infradead.org/
authors:
- Aishwarya Rambhadran
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 单运行队列改动的 p99 回退是否属预期取舍，Peter 未定论
  next_action: 等 Peter 回应「cgroup vs cgroup 数值抖动」是否在预期内
contribution_opportunities:
- kind: testing
  description: 复现 Mike 的混合负载（1×8 vs 4×2 竞争者 + 4 client netperf），量化 cgroup vs cgroup 抖动幅度
generated_at: '2026-10-13T01:40:00'
source_email_count: 1
related_articles:
- sched-20260923-001
- sched-20261007-009
tags:
- eevdf
- cfs
- regression
---
