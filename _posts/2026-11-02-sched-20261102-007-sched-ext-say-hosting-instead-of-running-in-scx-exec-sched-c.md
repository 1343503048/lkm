---
type: fix
status: under_review
severity: none
thread_root_msgid: <20261102080259.1509843-1-tj@kernel.org>
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20261102080259.1509843-1-tj@kernel.org>
  date: '2026-11-02'
  summary: 把 scx_exec_sched 注释的 running 统一为 hosting/hosted
  review_outcome: 无争议，自投自审
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 维护者直接收取进 sched_ext/for-7.5
contribution_opportunities: []
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.5
source_email_count: 1
related_articles: []
tags:
- sched_ext
id: sched-20261102-007
subject: 'sched_ext: Say "hosting" instead of "running" in scx_exec_sched() comments'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
title: 'sched_ext: Say "hosting" instead of "running" in scx_exec_sched() comments'
layout: article
---

## TL;DR

Tejun Heo 的纯注释清理补丁（for-7.5）：把 `scx_exec_sched()` 及相关注释里「the sched running @sch's tasks」统一改为「the sched hosting @sch's tasks」，与 bypass dispatch 代码里已有的 host 术语对齐，消除读者对「running」一词的歧义（被 bypass 的调度器的任务由最近的非 bypass 祖先"托管"而非"运行"）。

## 背景与问题

`scx_exec_sched()` 的注释把「承托某 bypassing 调度器任务的最近非 bypass 祖先」称作「running」；而 `ops.sub_cid_sched_updated()` 用「running on a cid」描述「拥有在该 cid 上运行任务的 sched」。两种「running」含义不同，易混淆。bypass dispatch 代码已用 host 一词，本补丁统一到 host。

## 技术方案

纯注释/文档改动：`kernel/sched/ext/internal.h`（`scx_exec_sched` doc）、`sub.c`、`sub.h` 三处注释，`running`→`hosting`/`hosted`，无逻辑变化（+7/−7）。

## 版本演进与当前进展

v1（2026-11-02），作者即 sched_ext 维护者，发往 sched_ext/for-7.5。

## Maintainer 意见与讨论焦点

无争议；作者自投自审的文档统一。

## 合入评估

likelihood=high。维护者本人的纯注释清理，无阻塞项，预期直接进 for-7.5。

## 效果评估

无性能/功能影响。

## 我可以参与的点

当前阶段暂无明显参与空间，可持续观察后续版本。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261102080259.1509843-1-tj@kernel.org/
