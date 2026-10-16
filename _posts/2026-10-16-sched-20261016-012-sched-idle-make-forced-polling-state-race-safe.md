---
id: sched-20261016-012
date: 2026-10-16
subject: 'sched/idle: Make forced polling state race-safe'
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
  review_outcome: Peter 质疑计数是否有真实并发访问
upstream_commit: null
fixes_commit: d16699123434
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - Peter 质疑 cpu_idle_poll_ctr 是否有真实并发访问，作者未回应
  next_action: 作者回应 cpu_idle_poll_ctr() 是否仅在 init 路径访问
contribution_opportunities:
- kind: discussion
  description: 核对 cpu_idle_poll_ctr() 所有调用点，判断除 init 外是否真的存在并发访问
generated_at: '2026-10-17T01:30:00'
source_email_count: 1
related_articles:
- sched-20261015-005
tags:
- idle
title: 'sched/idle: Make forced polling state race-safe'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/15/sched-20261015-005-sched-idle-make-forced-polling-state-race-safe.html">sched-20261015-005</a>：Hui Su 修复 `cpu_idle_poll_ctrl()` 全局强制 polling 计数用普通自增/自减维护、而各 idle CPU 无同步读它导致的 KCSAN data race，改 `atomic_t` 计数并拆分「fallback 永久状态」与「临时请求计数」。
- <a class="article-ref" href="/lkm/2026/10/16/sched-20261016-012-sched-idle-make-forced-polling-state-race-safe.html">sched-20261016-012</a>（今天）：Peter Zijlstra 回帖追问「这是 `cpu_idle_poll_ctr()` 吧？那个东西上真有并发吗？我看到只有 init 时的 twiddling」——质疑补丁修复的竞态是否真实存在。

## 背景与问题
（承接 20261015-005）原补丁的动机是 KCSAN 报告 `cpu_idle_force_poll` 计数缺同步的 data race。今天 Peter 的质疑直接针对这一点：`cpu_idle_poll_ctr()` 除了 init 阶段外是否有真实并发读写，需要作者论证。

## 技术方案
（承接 20261015-005）无代码变更；作者需回应计数到底有没有 non-init 的并发访问，从而判断用 `atomic_t` 是否有必要。

## 版本演进与当前进展
v1（2026-10-15）→ 今天 Peter 质疑竞态的前提。作者尚未回复。

## Maintainer 意见与讨论焦点
Peter Zijlstra：「Is there any actual concurrency on that thing? Afaict there is just init time twiddling there.」——这是对补丁存在意义的直接质疑，若作者无法证明运行时并发，补丁可能被判定为过度修改。

## 合入评估
*likelihood=unknown*。维护者质疑问题前提，作者未回应。*blocking_issues*：Peter 质疑计数是否有真实并发访问，需作者证明或修正范围。*next_action*：作者回应 `cpu_idle_poll_ctr()` 是否仅在 init 路径访问。

## 效果评估
无新增数据。

## 我可以参与的点
- *discussion*：核对 `cpu_idle_poll_ctr()` 的全部调用点，判断除 init 外是否真的存在并发访问，帮助澄清补丁的必要性。

## 参考链接
- Peter 的回复：https://lore.kernel.org/all/20261016090143.GR2009045@noisy.programming.kicks-ass.net/
- 原补丁：https://lore.kernel.org/all/20261015094211.4156055-1-sh_def@163.com/
