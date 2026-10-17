---
id: sched-20261017-007
subject: 'sched/idle: Make forced polling state race-safe'
date: 2026-10-17
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261015094211.4156055-1-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20261015094211.4156055-1-sh_def@163.com/
authors:
- Hui Su
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <20261015094211.4156055-1-sh_def@163.com>
  date: 2026-10-15
  summary: cpu_idle_force_poll 改 atomic_t，拆分 fallback 永久状态与临时计数
  review_outcome: Peter 质疑并发前提；作者今日以 OMAP4 suspend 的 reader/writer 路径回应，表态可重做
upstream_commit: null
fixes_commit: d16699123434
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Peter 尚未复核作者给出的 reader/writer 路径；补丁是否重做待定
  next_action: 作者按 Peter 反馈决定保持 atomic_t 计数或围绕 reader/writer 并发重做；等 Peter 复核
contribution_opportunities:
- kind: discussion
  description: 核对 cpu_idle_poll_ctrl() 在 OMAP4 之外的调用点是否同样存在 reader/writer 并发
generated_at: '2026-10-18T01:22:00'
source_email_count: 1
related_articles:
- sched-20261015-005
- sched-20261016-012
tags:
- idle
title: 'sched/idle: Make forced polling state race-safe'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/15/sched-20261015-005-sched-idle-make-forced-polling-state-race-safe.html">sched-20261015-005</a>：Hui Su 修复 `cpu_idle_poll_ctrl()` 全局强制 polling 计数用普通自增/自减、各 idle CPU 无同步读它导致的 KCSAN data race，改 `atomic_t` 计数并拆分「fallback 永久状态」与「临时请求计数」。
- <a class="article-ref" href="/lkm/2026/10/16/sched-20261016-012-sched-idle-make-forced-polling-state-race-safe.html">sched-20261016-012</a>：Peter Zijlstra 回帖追问「这是 `cpu_idle_poll_ctr()` 吧？那东西上真有并发吗？我只看到 init 时的 twiddling」——质疑补丁修复的竞态是否真实存在。
- <a class="article-ref" href="/lkm/2026/10/17/sched-20261017-007-sched-idle-make-forced-polling-state-race-safe.html">sched-20261017-007</a>（今天）：Hui Su 回复 Peter——确认存在一条真实 in-tree reader/writer 路径：OMAP4 suspend 期间 `omap_pm_begin()` 调 `cpu_idle_poll_ctrl(true)`，而二级 CPU 仍可能在 `do_idle()` 里读 `cpu_idle_force_poll`；但作者没找到 in-tree 的「并发 writer」对，并表态若 writer 应被串行化，可围绕真实 reader/writer 并发重做补丁。

## 背景与问题
（承接 20261015-005 → 20261016-012）Peter 质疑补丁的前提：`cpu_idle_poll_ctr()` 除 init 阶段外是否真有并发访问。今天作者给出具体回答——存在一条 in-tree reader/writer 并发路径：OMAP4 调 `omap_common_suspend_init(omap4_pm_suspend)` 安装 `omap_pm_ops`，其 `.begin` 回调 `omap_pm_begin()` 调用 `cpu_idle_poll_ctrl(true)`；`platform_suspend_begin()` 从 `suspend_devices_and_enter()` 调用该回调，早于 `suspend_enter()` 里的 `pm_sleep_disable_secondary_cpus()`——因此挂起 CPU 更新 `cpu_idle_force_poll` 时，二级 CPU 仍可能在 `do_idle()` 中读取它。

## 技术方案
（承接 20261015-005）今日无代码变更，作者澄清了两个前提边界：① 真实 in-tree 并发是 **reader/writer**（挂起路径的写 vs 仍在 idle 的二级 CPU 的读），而非其两 worker stress test 模拟的「并发 writer」；② stress test 只验证了计数器在并发 writer 下的行为，并未建立 in-tree 的并发 writer 调用对。作者明确表示：若 `cpu_idle_poll_ctrl()` 的 writer 被预期为串行化，则可围绕真实的 reader/writer 并发来重做补丁。

## 版本演进与当前进展
v1（2026-10-15）→ Peter 质疑前提（2026-10-16）→ 今天作者给出 reader/writer 路径证据并表态可重做。尚无 v2。

## Maintainer 意见与讨论焦点
- Peter Zijlstra（前一日）：「Is there any actual concurrency on that thing? Afaict there is just init time twiddling there.」
- Hui Su（作者，今日）：以 OMAP4 suspend 路径论证存在真实 reader/writer 并发，同时诚实区分「reader/writer 并发」与「并发 writer」，承认 stress test 未建立 in-tree 并发 writer 对，并主动提议围绕真实并发重做。分歧点实质缩小为：atomic_t 计数是否必要，或应针对 reader/writer 路径做更精准修复。

## 合入评估
*likelihood=medium*。作者用真实 in-tree 路径回应了 Peter 的核心质疑，补丁的必要性论证得到补强，但 Peter 尚未回复、是否重做未定。*blocking_issues*：Peter 尚未复核作者给出的 reader/writer 路径；补丁是否围绕该真实并发重做待定。*next_action*：作者按 Peter 反馈决定是保持 atomic_t 计数还是围绕 reader/writer 并发重做；等 Peter 复核。

## 效果评估
无新增数据；今日为对并发前提的论证，无 benchmark。

## 我可以参与的点
- *discussion*：核对 `cpu_idle_poll_ctrl()` 在 OMAP4 之外的调用点是否同样存在 reader/writer 并发，帮助判断应「保持 atomic_t」还是「围绕 reader/writer 做更精准修复」。

## 参考链接
- 作者今日回复：https://lore.kernel.org/all/20261017123500.76882ea23304d57d9a3524ca@163.com/
- Peter 的回复：https://lore.kernel.org/all/20261016090143.GR2009045@noisy.programming.kicks-ass.net/
- 原补丁：https://lore.kernel.org/all/20261015094211.4156055-1-sh_def@163.com/
