---
id: sched-20261020-004
date: 2026-10-20
subject: 'sched_ext: Make ops.cpu_acquire/release() reliable'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <cover.1792248922.git.jpiecuch@google.com>
lore_url: https://lore.kernel.org/all/cover.1792248922.git.jpiecuch@google.com/
authors:
- Kuba Piecuch
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <cover.1792248922.git.jpiecuch@google.com>
  date: 2026-10-18
  summary: RFC 五补丁：将 cpu_acquire/release 可用性归约到 donor 类，反弃用并加 selftests
  review_outcome: 作者自我复盘两处缺陷并提 scx_settle_pick 钩子（20261019）；Tejun 今日否定该回调价值、要求拆分 IMMED
    修复
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - Tejun 认为 ops.cpu_acquire/release 无存在价值、不应保留或更新
  - IMMED 修复需拆分单发
  next_action: 作者把 IMMED 修复单独发；cpu_acquire/release 可靠性方向需重新论证或放弃
contribution_opportunities:
- kind: discussion
  description: 评估 cpu_acquire/release 是否存在 IMMED 无法覆盖的价值，帮作者决定放弃或提反例
- kind: review
  description: 梳理 IMMED 漏洞清单，为拆分单发的 IMMED 修复划定范围
generated_at: '2026-10-21T01:30:00'
source_email_count: 1
related_articles:
- sched-20261018-004
- sched-20261019-015
tags:
- sched_ext
title: 'sched_ext: Make ops.cpu_acquire/release() reliable'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/10/18/sched-20261018-004-sched-ext-make-ops-cpu-acquire-release-reliable.html">sched-20261018-004</a>：Kuba Piecuch 发往 `sched_ext/for-7.4` 的 RFC 五补丁——修复并「反弃用」`ops.cpu_acquire/release()`，把 CPU 可用性判定归约到 `rq->donor` 的类；RFC 首日无回帖。
- <a class="article-ref" href="/lkm/2026/10/19/sched-20261019-015-sched-ext-make-ops-cpu-acquire-release-reliable.html">sched-20261019-015</a>：作者本人主动回帖重新考虑方案——指出 v1 改动了 acquire 语义、且漏掉 RT→RT 切换永不释放 CPU 的情形，提出 `__schedule()` 内的 `scx_settle_pick()` 单钩子，并征询 Tejun/Peter。
- <a class="article-ref" href="/lkm/2026/10/20/sched-20261020-004-sched-ext-make-ops-cpu-acquire-release-reliable.html">sched-20261020-004</a>（今天）：维护者 Tejun Heo 正式表态——「看不到 `ops.cpu_acquire/release()` 的太多价值；它目前没提供 IMMED 覆盖不了的东西，且事件异步、边缘触发的 CPU 可用性视图未必有用。IMMED 之所以成立是因为内核能检查并强制它；如有漏洞就补漏洞，但这些漏洞不足以支撑保留/更新这两个回调」。要求作者把 IMMED 修复单独发。

## 背景与问题

（承接 20261018-004 → 20261019-015）作者 Kuba Piecuch 本想把 `ops.cpu_acquire()/ops.cpu_release()` 修到可靠、并「反弃用」它，为此先自行复盘出 v1 的语义缺陷（acquire 从 `ops.dispatch()` 之前移到 CPU 真正切到 SCX/idle 时、打破调度器作者的既有假设；RT→RT 切换漏 release），并提出 `scx_settle_pick()` 钩子方向。今天维护者 Tejun Heo 给出方向性回应：他质疑这两个回调本身的存在价值，认为其价值可被 `SCX_ENQ_IMMED` 完全覆盖，而 IMMED 的可靠之处在于「内核能检查并强制」；异步、边缘触发的 CPU 可用性视图在他看用途有限。

## 技术方案

（承接，今日为维护者方向性反馈，无新补丁）Tejun 未就 `scx_settle_pick()` 钩子本身表态，而是把问题向上推了一层：与其修/保留 `ops.cpu_acquire/release()`，不如承认它价值有限，把精力放到 IMMED 的漏洞上——「如果 IMMED 有洞，就去补洞」。作者此前（20261019-015）其实也提议「先把 IMMED 修复单独发，v2 系列基于其上 rebase」，与 Tejun 的要求方向一致。

## 版本演进与当前进展

*current_version: v1*（RFC）。v1（20261018-004）→ 作者自我复盘并提出 `scx_settle_pick()`（20261019-015）→ 维护者 Tejun 今日否定 `ops.cpu_acquire/release()` 的价值、要求拆分 IMMED 修复。尚未有新版本补丁。

## Maintainer 意见与讨论焦点

Tejun Heo（sched_ext 维护者）今日明确表态：不认同继续围绕 `ops.cpu_acquire/release()` 做可靠性改造——「看不到太多价值」「不认为这些漏洞足以支撑保留或更新这两个回调」「请把 IMMED 修复单独发」。这是对「反弃用/可靠性化」方向的实质性否定（非形式 NAK，但倾向明确）；对 IMMED 修复部分则持开放态度。

## 合入评估

*likelihood=low*。维护者对系列核心前提（保留并修好 `ops.cpu_acquire/release()`）持否定态度，方向上被要求放弃/大幅收窄。*blocking_issues*：Tejun 认为这两个回调无存在价值、不应保留或更新；IMMED 修复需拆分单发。*next_action*：作者把 IMMED 修复单独发；`ops.cpu_acquire/release()` 可靠性方向需重新论证或放弃。

## 效果评估

无 benchmark，属契约语义/功能方向之争。Tejun 的论据是「IMMED 可被内核检查并强制、而 cpu_acquire/release 的异步边缘触发语义不可靠」，未见量化数据。

## 我可以参与的点

- `discussion`：评估 Tejun「cpu_acquire/release 价值可被 IMMED 覆盖」的判断——枚举 IMMED 目前无法表达、而 cpu_acquire/release 能表达的 CPU 可用性信息，帮助作者决定是放弃还是提出反例。
- `review`：梳理 IMMED 现有的漏洞清单（作者在 20261019-015 中列过 wakeup_preempt 之外的多条路径），为「单独发的 IMMED 修复」划定范围。

## 参考链接

- Tejun 今日回帖：https://lore.kernel.org/all/657547efeaea54276c50a0c106399366@kernel.org/
- 作者前日回帖（重新考虑 + 钩子提议）：https://lore.kernel.org/all/20261019144807.1207781-1-jpiecuch@google.com/
- RFC 封面信（v1）：https://lore.kernel.org/all/cover.1792248922.git.jpiecuch@google.com/
