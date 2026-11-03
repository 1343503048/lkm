---
id: sched-20261103-016
date: 2026-11-03
subject: 'sched/uclamp: Fix race condition leading to imbalanced uclamp_rq'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261103005953.56271-1-qyousef@layalina.io>
lore_url: https://lore.kernel.org/all/20261103005953.56271-1-qyousef@layalina.io/
authors:
- Qais Yousef
maintainers_involved: []
current_version: v5
patch_series:
- version: v5
  msgid: <20261103005953.56271-1-qyousef@layalina.io>
  date: 2026-11-03
  summary: 4 补丁：竞态 idle 校正、wrapper、RFC revert RT nr_running、uclamp 与 nr_running 配对。
  review_outcome: 刚发出，暂无外部 review。
upstream_commit: null
fixes_commit: 46609ce227039
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: 等维护者对 v5（尤其 3/4 revert 与 4/4 配对）review。
contribution_opportunities:
- kind: review
  description: 审阅 RT revert 的 nr_running 语义与 psi 交互。
- kind: testing
  description: uclamp + RT/CFS 带宽节流负载上验证计数平衡。
generated_at: '2026-11-04T09:00:00+08:00'
source_email_count: 5
related_articles:
- sched-20261102-021
tags:
- uclamp
- rt
title: 'sched/uclamp: Fix race condition leading to imbalanced uclamp_rq'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/25/sched-20261025-001-sched-uclamp-fix-race-condition-leading-to-imbalanced-uclamp.html">sched-20261025-001</a>：Qais Yousef 修 uclamp static key 非原子翻转导致的 rq 计数失衡竞态。
- <a class="article-ref" href="/lkm/2026/10/26/sched-20261026-002-sched-uclamp-fix-race-condition-leading-to-imbalanced-uclamp.html">sched-20261026-002</a>（v2）：修链接错误、idle 检测改 WARN_ON。
- <a class="article-ref" href="/lkm/2026/10/29/sched-20261029-001-sched-uclamp-fix-race-condition-leading-to-imbalanced-uclamp.html">sched-20261029-001</a>（v4）：拆 1/2（竞态）+2/2（wrapper）；Christian 指出 CFS 带宽节流不调 `uclamp_rq_dec()`。
- <a class="article-ref" href="/lkm/2026/10/30/sched-20261030-004-sched-uclamp-fix-race-condition-leading-to-imbalanced-uclamp.html">sched-20261030-004</a>：上升为 CFS/RT 带宽节流 partial-dequeue 绕过 core {en,de}queue 的问题；Peter 提议节流路径自补 uclamp_rq_{dec,inc}。
- <a class="article-ref" href="/lkm/2026/11/02/sched-20261102-021-sched-uclamp-fix-race-condition-leading-to-imbalanced-uclamp.html">sched-20261102-021</a>：Qais 给出新方案——把 `uclamp_rq_{inc,dec}()` 与 `{add,sub}_nr_running()` 配对，RT 侧部分 revert `f4ebcbc0d7e00`。
- <a class="article-ref" href="/lkm/2026/11/03/sched-20261103-016-sched-uclamp-fix-race-condition-leading-to-imbalanced-uclamp.html">sched-20261103-016</a>（今天）：v5 正式发出，扩展为 4 补丁：1/4 竞态修复（idle 进入时校正）、2/4 UCLAMP_FLAG_IDLE wrapper、3/4（RFC）revert RT 的 `rq->nr_running` 越界管理、4/4 把 `uclamp_rq_{inc,dec}()` 从 core.c 移出并与 `{add,sub}_nr_running()` 配对；Qais 自评 4/4 对 psi 的影响。暂无外部 review。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/02/sched-20261102-021-sched-uclamp-fix-race-condition-leading-to-imbalanced-uclamp.html">sched-20261102-021</a>）带宽节流绕过 core enqueue/dequeue，使 uclamp 计数与实际 enqueue 状态脱节；static key 非原子翻转又使 `uclamp_rq_inc` 与 `dec` 不对称。v5 把方案从「事后纠错」升级为「结构性配对」。

## 技术方案

（承接）v5 的核心是把 `uclamp_rq_{inc,dec}()` 与 `{add,sub}_nr_running()` 绑定：每个关心 uclamp 的调度类在更新 nr_running 的同时更新 rq uclamp 状态，消除 partial-dequeue 的计数错乱。3/4 部分 revert `f4ebcbc0d7e0`（RT 的 out-of-line `rq->nr_running` 管理），改在 `{inc,dec}_rt_tasks()` 里做 `{add,sub}_nr_running()`，并删除 `rt_queued`、让 `sched_rt_is_runnable()` 成为 `rt_rq_is_runnable()` 的别名。4/4 顺带删掉 `uclamp_rq_{inc,dec}()` 里的 `sched_delayed` 守卫与 `flags` 参数（现在在恰当时机做操作，无需再关心 delayed 细节）。

## 版本演进与当前进展

*current_version: v5（2026-11-03 发出，cover msgid 20261103005953.56271-1-qyousef@layalina.io）*。较 v4（2 补丁）扩展为 4 补丁，新增 RFC 的 RT revert 与「移出 core.c」两块。

## Maintainer 意见与讨论焦点

今日无外部 review；Qais 自评 4/4 时指出 `psi_enqueue/dequeue()` 在 core 做、不确定节流绕过 core 对其影响多大。此前 Peter 的方向性建议（节流路径自补 uclamp 计数）已在 v5 的结构性配对中体现。无 NAK。

## 合入评估

*likelihood=unknown*。方案从 v4 到 v5 仍在结构性重构（含 RFC revert RT 计数），尚无维护者对新版表态。*next_action*：等 Peter 及 uclamp 相关维护者对 v5（尤其 3/4 revert 与 4/4 配对）的 review。

## 效果评估

无性能数据；属正确性修复（uclamp 计数失衡/节流 bypass）。作者在 1/4 注释中说明竞态「unlikely but ensure uclamp_rq state 在每次进 idle 时被校正」。

## 我可以参与的点

- review：审阅 3/4 的 RT revert 是否改变 RT throttle 的 `nr_running` 语义、4/4 与 psi 的交互。
- testing：在开启 uclamp + RT/CFS 带宽节流的负载上验证计数不再失衡。

## 参考链接

- lore thread（v5 cover）: https://lore.kernel.org/all/20261103005953.56271-1-qyousef@layalina.io/
