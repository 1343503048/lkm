---
id: sched-20261012-021
date: '2026-10-12'
subject: 'sched/fair: Preserve wake-affine CPU for non-SMT reciprocal sync wakeups'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261008-b4-sched-sync-wakeup-v5-1-1af9fab48965@gentwo.org>
lore_url: https://lore.kernel.org/all/20261008-b4-sched-sync-wakeup-v5-1-1af9fab48965@gentwo.org/
authors:
- Shubhang Kaushik
maintainers_involved:
- Peter Zijlstra
current_version: v5
patch_series:
- version: v5
  msgid: <20261008-b4-sched-sync-wakeup-v5-1-1af9fab48965@gentwo.org>
  date: '2026-10-08'
  summary: 非 SMT 系统上 reciprocal WF_SYNC 唤醒保住 wake-affine CPU
  review_outcome: Peter 强烈质疑可读性与 !SMT 必要性，last_wakee 无 in_task 守卫
merge_assessment:
  likelihood: low
  blocking_issues:
  - Peter 认为代码难懂、!SMT 动机不清晰、last_wakee/record_wakee 存在隐患
  - 需用可读代码重新说服
  next_action: 作者重写/精简补丁并说明 !SMT 与 sync-pair 语义
contribution_opportunities:
- kind: review
  description: 核对 Peter 提出的 record_wakee() 无 in_task() 守卫是否属实，及 last_wakee 语义边界
- kind: discussion
  description: 厘清 sync-pair 判断为何要限定 !SMT
generated_at: '2026-10-13T01:40:00'
source_email_count: 1
related_articles:
- sched-20261009-005
tags:
- cfs
title: 'sched/fair: Preserve wake-affine CPU for non-SMT reciprocal sync wakeups'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/09/sched-20261009-005-sched-fair-preserve-wake-affine-cpu-for-non-smt-reciprocal-s.html">sched-20261009-005</a>：Shubhang Kaushik（Ampere）发 v5——narrow reciprocal 的 `WF_SYNC` 唤醒在非 SMT 系统上保住在 wake-affine 选中的 waker CPU，不被 `select_idle_sibling()` 搬走；附 `perf bench sched pipe` 数据（80 核非 SMT Ampere Altra，mean 3.651→2.20）。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-021-sched-fair-preserve-wake-affine-cpu-for-non-smt-reciprocal-s.html">sched-20261012-021</a>（今天）：Peter Zijlstra 强烈吐槽——「一看这补丁就 WTF」、代码难懂、!SMT 动机不清晰、`last_wakee` 不干净（`record_wakee()` 无 `in_task()` 守卫），要求「用可读代码说服我」。

## 背景与问题

（承接 20261009-005）pipe 式 ping-pong（A 唤醒 B、B 唤醒 A 循环）在非 SMT 系统上，wake-affine 选中的 waker CPU 会被后续空闲搜索搬走，破坏局部性。

## 技术方案

（承接 20261009-005）补丁试图在 `new_cpu == current` 且 `p` 上次被我们唤醒（+随机）时留在原地。Peter 按此读法指出：函数大谈 sync-pair 却未真正操作「一对」或确保成对存在，逻辑隐晦；并指出 `last_wakee` 依赖的 `record_wakee()` 缺 `in_task()` 守卫，本身就不稳。

## 版本演进与当前进展

v5（10-08）→ 今日（10-12）Peter 强烈负评，未给方向性认可；无 v6。

## Maintainer 意见与讨论焦点

Peter Zijlstra：核心关切是可读性（「Hurmph.. just looking at this patch makes me go WTF」）+ !SMT 动机不明 + `last_wakee`/`record_wakee` 缺乏 `in_task()` 守卫的既有缺陷；要求作者用可读代码重新论证。

## 合入评估

*likelihood=low*。维护者强烈负评，需实质性重写。*blocking_issues*：可读性、!SMT 论证、last_wakee 语义。*next_action*：作者精简代码、说明 !SMT 与 sync-pair 语义。

## 效果评估

今日无新数据；v5 附带的 `perf bench sched pipe` 数据（mean 3.651→2.20，80 核非 SMT）仍在，但 Peter 的质疑未指向数据本身。

## 我可以参与的点

- `review`：核对 `record_wakee()` 是否确无 `in_task()` 守卫、`last_wakee` 在多生产者下的语义边界。
- `discussion`：帮作者厘清「为何限定 !SMT」并给出更简洁的条件表达。

## 参考链接

- lore（v5）: https://lore.kernel.org/all/20261008-b4-sched-sync-wakeup-v5-1-1af9fab48965@gentwo.org/
- lore（Peter 负评）: https://lore.kernel.org/all/20261012113340.GS4121339@noisy.programming.kicks-ass.net/
