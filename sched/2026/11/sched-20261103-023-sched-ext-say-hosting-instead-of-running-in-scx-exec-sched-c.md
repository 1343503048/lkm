# sched_ext: Say "hosting" instead of "running" in scx_exec_sched() comments

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261102-007：Tejun Heo 的纯注释清理补丁（for-7.5），把 `scx_exec_sched()` 及相关注释里「the sched running @sch's tasks」统一改为「hosting」，消除「running」一词的歧义。
- sched-20261103-023（今天）：Tejun 已把补丁收进 sched_ext/for-7.5。

## 背景与问题

（承接 sched-20261102-007）`scx_exec_sched()` 的注释把「承托某 bypassing 调度器任务的最近非 bypass 祖先」称作「running」，与 `ops.sub_cid_sched_updated()` 用「running on a cid」的含义不同、易混淆。今日无新代码。

## 技术方案

（承接）纯注释/文档改动：`kernel/sched/ext/internal.h`、`sub.c`、`sub.h` 三处注释 `running`→`hosting`/`hosted`，无逻辑变化。今日为收取确认。

## 版本演进与当前进展

*current_version: v1（已合入）*。今日 Tejun 回 Applied：「Applied to sched_ext/for-7.5」。

## Maintainer 意见与讨论焦点

无争议；作者即 sched_ext 维护者，自投自收的文档统一。

## 合入评估

*likelihood=merged*。已进 sched_ext/for-7.5。

## 效果评估

纯注释清理，无效果数据。

## 我可以参与的点

当前阶段暂无明显参与空间。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261102080259.1509843-1-tj@kernel.org/

---
id: sched-20261103-023
date: 2026-11-03
subject: 'sched_ext: Say "hosting" instead of "running" in scx_exec_sched() comments'
subsystem: sched
type: fix
status: merged_tip
severity: none
thread_root_msgid: "<20261102080259.1509843-1-tj@kernel.org>"
lore_url: "https://lore.kernel.org/all/20261102080259.1509843-1-tj@kernel.org/"
authors: [Tejun Heo]
maintainers_involved: [Tejun Heo]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261102080259.1509843-1-tj@kernel.org>"
    date: 2026-11-02
    summary: "纯注释清理：running → hosting。"
    review_outcome: "已收进 sched_ext/for-7.5。"
upstream_commit: null
fixes_commit: null
merged_branch: "sched_ext/for-7.5"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已合入 scx 分支。"
contribution_opportunities: []
generated_at: "2026-11-04T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261102-007]
tags: [sched_ext]
---