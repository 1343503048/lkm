---
id: sched-20261016-002
date: 2026-10-16
subject: 'sched/eevdf: Move to a single runqueue'
subsystem: sched
type: regression
status: under_review
severity: medium
thread_root_msgid: <20260605105513.354837583@infradead.org>
lore_url: https://lore.kernel.org/all/20260605105513.354837583@infradead.org/
authors:
- Jakub Okoński
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - cpu.idle cgroup 的 wakeup preemption 语义变化是否属预期取舍，Peter 未定论
  next_action: 等 Peter 回应 cpu.idle 语义变化是否为单运行队列的已知/预期取舍
contribution_opportunities:
- kind: testing
  description: 用 wakelat.c + systemd-run CPUWeight=idle 复现 p99 恶化并回帖数据
- kind: discussion
  description: 核对 se_is_idle() 退化对 cpu.idle 语义的影响是否为设计预期
generated_at: '2026-10-17T01:30:00'
source_email_count: 1
related_articles:
- sched-20260923-001
- sched-20261007-009
- sched-20261012-022
tags:
- eevdf
- cfs
- regression
title: 'sched/eevdf: Move to a single runqueue'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-001-sched-eevdf-move-to-a-single-runqueue.html">sched-20260923-001</a> / 20261007-009：Aishwarya Rambhadran（ARM）报告 v7.2→v7.3 在 AWS Graviton3 上个别 schbench 线程配置 p99 回退 ~30%，bisect 指向「sched/eevdf: Move to a single runqueue」commit；后续怀疑点收敛到 WA_WEIGHT/task_h_load。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-022-sched-eevdf-move-to-a-single-runqueue.html">sched-20261012-022</a>：Mike Galbraith 以 7.2+flat 对照观察到 cgroup vs cgroup 的 CPU 分配抖动被放大，但未给数字。
- <a class="article-ref" href="/lkm/2026/10/16/sched-20261016-002-sched-eevdf-move-to-a-single-runqueue.html">sched-20261016-002</a>（今天）：Jakub Okoński 给出**可复现的量化回归**——单运行队列改动疑似破坏 `cpu.idle` cgroup 的 wakeup preemption 语义，`SCHED_NORMAL` 任务在 `cpu.idle` cgroup 下不再被当 idle 对待，wakelat 测试 p99 从 12µs 恶化到 2029µs。

## 背景与问题
（承接 20260923-001/20261007-009/20261012-022）单运行队列改动落地 v7.3 后，cgroup 竞争场景的 CPU 分配稳定性一直存疑。今天 Jakub Okoński 提出一个新的具体机制：单运行队列移除了 `find_matching_se()`，`se_is_idle()` 退化为 `task_has_idle_policy()`，导致 `SCHED_NORMAL` 任务放在 `cpu.idle` cgroup 时不再被 `wakeup_preempt_fair()` 当作 idle，从而不再被低延迟任务抢占。

## 技术方案
无新方案；今天为 Jakub 的独立复测，首次把回归钉到一个具体机制（`cpu.idle` + wakeup preemption 语义变化），并给出可运行的复现脚本（wakelat：固定 1ms 周期 wakeup、记录迟到时长、再忙等 200µs）。

## 版本演进与当前进展
回归报告持续跟踪中（20260923-001 → 20261007-009 → 20261012-022 → 今天）；Jakub 的复现把问题从「schbench 特定配置」扩展到「cpu.idle cgroup 语义」，仍未见 Peter 定论。

## Maintainer 意见与讨论焦点
Jakub（非 maintainer）以 7.2.9 vs 7.3.0-rc6 对比数据断言这是单运行队列对 `cpu.idle` 影响的改变；他自疑 cyclictest 复现不出来是因为其 EEVDF 累积 lag 把延迟压住了。Peter Zijlstra 尚未回复。

## 合入评估
*likelihood=unknown*。属已合入改动的性能回归跟踪，是否预期取舍待 Peter 定夺。*blocking_issues*：无定论。*next_action*：等 Peter 回应 `cpu.idle` 语义变化是否为单运行队列的已知/预期取舍。

## 效果评估
Jakub 的 wakelat 数据（15000 周期内，7.2.9 vs 7.3.0-rc6，Icelake 桌面 + `systemd-run -p CPUWeight=idle` 竞争者）：
- 7.2.9：p50 11µs、p90 11µs、p99 12µs、max 1869µs；
- 7.3.0-rc6：p50 11µs、p90 12µs、p99 2029µs、max 2116µs；rc6 有 1147 次 wakeup 延迟超过 1ms。
p99 延迟从 12µs 恶化到 2029µs（约 170 倍），是该系列迄今最硬的数据点。

## 我可以参与的点
- *testing*：按 Jakub 附带的 wakelat.c 与 systemd-run 命令复现（AllowedCPUs=7 + CPUWeight=idle 竞争者 + 固定 1ms wakeup），确认 p99 恶化是否稳定、并回帖确认/补充数据。
- *discussion*：核对单运行队列下 `se_is_idle()` 退化为 `task_has_idle_policy()` 对 `cpu.idle` 语义的影响是否为设计预期。

## 参考链接
- Jakub 的回归报告：https://lore.kernel.org/all/58dc8e8a-7260-43ce-aebb-8d9c29a6afc9@okonski.org/
- 系列 thread：https://lore.kernel.org/all/20260605105513.354837583@infradead.org/
