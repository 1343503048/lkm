# sched/uclamp: Fix race condition leading to imbalanced uclamp_rq

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261025-001：Qais Yousef 修 uclamp static key 非原子翻转导致的 rq 计数失衡竞态。
- sched-20261026-002（v2）：修链接错误、idle 检测改 WARN_ON。
- sched-20261029-001（v4）：拆 1/2（竞态）+2/2（wrapper）；Christian 指出 CFS 带宽节流不调 `uclamp_rq_dec()`。
- sched-20261030-004：上升为 CFS/RT 带宽节流 partial-dequeue 绕过 core {en,de}queue 的「薛定谔任务」；Peter 提议节流路径自补 uclamp_rq_{dec,inc}。
- sched-20261102（今天）：Qais 给出新方案——把 `uclamp_rq_{inc,dec}()` 与 `{add,sub}_nr_running()` 配对，确保增删即 uclamp 增删；RT 侧需部分 revert `f4ebcbc0d7e00`、`{inc,dec}_rt_tasks()` 简化为 `{add,sub}_nr_running()`（`!group_rt_rq()` 时才调，避免 group 计数错乱）；并正视 LTS 修复悬崖（要么保留 `active=1 && bucket=0` 的 WARN、要么 drop Fixes 标签让需要者自行 backport）。

## 背景与问题

（承接）带宽节流绕过 core enqueue/dequeue，使 uclamp 计数与实际 enqueue 状态脱节，触发 `WARN_ON_ONCE(!bucket->tasks)`。

## 技术方案

（承接）今日核心进步：不再「事后纠错」，而是把 uclamp 增减直接绑定到 `nr_running` 增减。Qais 给出 `{inc,dec}_rt_tasks()` 的示意（`if (!group_rt_rq(rt_se)) add/sub_nr_running(...)`），并指出 `sched_rt_rq_dequeue()` 在不编译 RT group 时是死代码。

## 版本演进与当前进展

v4 之后进入新的方案探讨（nr_running 配对），分支已实现并初步验证。

## Maintainer 意见与讨论焦点

方案方向获 Qais 自己推动、Peter 此前提议的「节流路径自补」被扩展为「统一绑定 nr_running」；未决点：LTS 如何处理（保留 WARN vs drop Fixes）。

## 合入评估

likelihood=medium。方案更正确但与 RT 计数重构耦合、LTS 策略未定。

## 效果评估

（承接）`active=1 && bucket->tasks=0` 已被 Christian 复现证实触发 WARN。

## 我可以参与的点

- review：审阅 `{inc,dec}_rt_tasks()` 里 `!group_rt_rq()` 条件对 RT group 计数的影响。
- testing：在启/不启 RT group、含 CFS/RT 节流的场景验证 uclamp 计数不再失衡。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261029131354.11030-1-qyousef@layalina.io/

---
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261029131354.11030-1-qyousef@layalina.io>
authors:
- Qais Yousef
maintainers_involved: []
current_version: v4
patch_series: []
merge_assessment:
  likelihood: medium
  blocking_issues:
  - RT 计数重构耦合、LTS 策略（保留 WARN vs drop Fixes）未定
  next_action: 完善 nr_running 配对方案并决定 LTS 处理
contribution_opportunities:
- kind: review
  description: 审阅 inc/dec_rt_tasks 中 !group_rt_rq 条件的计数影响
- kind: testing
  description: RT group 开/关 + 节流场景验证 uclamp 计数不失衡
upstream_commit: null
fixes_commit: null
merged_branch: null
source_email_count: 2
related_articles:
- sched-20261025-001
- sched-20261026-002
- sched-20261029-001
- sched-20261030-004
tags:
- uclamp
- cfs
- rt
id: sched-20261102-021
subject: 'sched/uclamp: Fix race condition leading to imbalanced uclamp_rq'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
---
