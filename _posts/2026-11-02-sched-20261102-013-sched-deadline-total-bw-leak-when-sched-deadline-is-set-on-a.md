---
type: bug
status: under_review
severity: high
thread_root_msgid: <3f6e6c87-645b-45fd-8fc6-8da5bc5b82d8@gmail.com>
authors:
- Weiheng Qiu
maintainers_involved:
- Juri Lelli
current_version: v1
patch_series: []
merge_assessment:
  likelihood: high
  blocking_issues:
  - 需确认 exit 后是否只拒 DEADLINE 还是所有策略
  next_action: 作者确认 Juri 修复、Peter 就范围表态后正式提交
contribution_opportunities:
- kind: testing
  description: 用 zombie_admit_leak.c 验证 -ESRCH 生效
- kind: discussion
  description: 讨论 exit 态 setscheduler 的全局策略
upstream_commit: null
fixes_commit: null
merged_branch: null
source_email_count: 1
related_articles:
- sched-20261101-006
tags:
- deadline
id: sched-20261102-013
subject: 'sched/deadline: total_bw leak when SCHED_DEADLINE is set on a dead task'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
title: 'sched/deadline: total_bw leak when SCHED_DEADLINE is set on a dead task'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/11/01/sched-20261101-006-sched-deadline-total-bw-leak-when-sched-deadline-is-set-on-a.html">sched-20261101-006</a>：Weiheng Qiu 报告对 zombie 任务 `sched_setattr(SCHED_DEADLINE)` 会返回 0 并永久占用 root domain `dl_bw->total_bw`、最终打满 admission（`-EBUSY`），附复现程序，尚无 fix。
- sched-20261102（今天）：SCHED_DEADLINE 维护者 Juri Lelli 给出 inline 修复——在 `__sched_setscheduler()` 里拒绝 exit 状态（zombie）任务的 SCHED_DEADLINE（返回 -ESRCH），并请作者确认、同时问 Peter 是否应对其它策略同样处理。

## 背景与问题

（承接）`__sched_setscheduler()` 不检查 `p->exit_state`，zombie 任务设置 SCHED_DEADLINE 时 `sched_dl_overflow()` 照样记账且永不释放。今天 Juri 落点：zombie 不会再被调度，`sched_dl_overflow()` 会 charge 一个永不释放的 total_bw。

## 技术方案

Juri 的修复（`kernel/sched/syscalls.c`，+10）：在策略解析之后、normalize 之前，若 `dl_policy(policy) && p->exit_state` 则 `retval = -ESRCH; goto unlock;`。作者特意做成 **DEADLINE 专属**,因为他不确定 exit 后再 setscheduler 对 SCHED_NORMAL（如 sysrq reset）是否有意义，征询 Peter 意见。

## 版本演进与当前进展

维护者今天首次给出 fix 草案，待报告者与 Peter 确认。

## Maintainer 意见与讨论焦点

Juri 已给出方向明确的修复并主动抛给 Peter：「是否只有 DEADLINE 需要拒、还是 exit 后所有策略都该拒」。这是当前唯一待决分歧。

## 合入评估

likelihood=high。维护者亲自给出 minimal fix，路线清晰；仅需确认是否推广到全部策略。

## 效果评估

（承接）作者此前演示一个 zombie 占 0.25 CPU、再 6 个即 `-EBUSY`、`total_bw` 达 1.850 CPU。

## 我可以参与的点

- testing：用作者 `zombie_admit_leak.c` 验证 `-ESRCH` 生效且不再 leak。
- discussion：就「是否应拒所有 exit 态任务的 setscheduler」给出用例分析。

## 参考链接

- lore thread: https://lore.kernel.org/all/3f6e6c87-645b-45fd-8fc6-8da5bc5b82d8@gmail.com/
