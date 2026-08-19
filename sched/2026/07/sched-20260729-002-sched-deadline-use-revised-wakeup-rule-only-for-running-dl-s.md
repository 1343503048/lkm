# sched/deadline: Use revised wakeup rule only for running dl_server

## TL;DR

Gabriele Monaco（Red Hat）5 月发的 dl_server wakeup rule 修复被搁置两个多月，7-29 ping 之后 Peter Zijlstra（度假归来）直接回复 "sched/urgent this?"，作者确认——该修复大概率很快进入 tip/sched/urgent。跟踪合入即可，无参与空间。

## 背景与问题

补丁正文发布于 2026-05-22（不在当日邮件缓存内，按数据源边界不展开细节），主题为：SCHED_DEADLINE 的 revised wakeup rule（CBS 唤醒时的 deadline/runtime 重算规则）应当只应用于处于 running 状态的 dl_server，其他情况沿用原规则。当日邮件是作者的 ping 和后续短交流。

## 技术方案

从标题与线程判断：将 revised wakeup rule 的适用范围收窄到 running dl_server。补丁 diff 细节未在当日邮件中出现，标注 unknown，不做推测。

## 版本演进与当前进展

v1（5 月）无人响应两个月；7-29 作者两次 ping（第二封补上 lore 链接 [1]）。PeterZ 回复：

> "Yes, just back from holidays, so immense backlog. sched/urgent this?"

作者确认 "I'd say so, thanks!"。

## Maintainer 意见与讨论焦点

PeterZ 未对内容提出异议，直接询问是否按紧急修复处理——表明他认可这是需要尽快合入的修复。无争议点。

## 合入评估

likelihood: high。维护者已明确表态走 sched/urgent 通道，剩余动作只是排队。若下周未见 tip-bot 通知，可关注是否需要 rebase。

## 效果评估

暂无效果数据（修复类补丁，当日邮件未包含测试数字）。

## 我可以参与的点

当前阶段暂无明显参与空间：修复已被维护者接手，可持续观察 tip-bot 合并通知（预期出现 `[tip: sched/urgent]` 回帖）。

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260522125833.264145-1-gmonaco@redhat.com/
- tip-bot commit: 未获取到（尚未合入）

---
subject: "sched/deadline: Use revised wakeup rule only for running dl_server"
id: sched-20260729-002
date: 2026-07-29
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20260522125833.264145-1-gmonaco@redhat.com>"
lore_url: "https://lore.kernel.org/r/20260522125833.264145-1-gmonaco@redhat.com"
authors: [Gabriele Monaco]
maintainers_involved: [Peter Zijlstra]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260522125833.264145-1-gmonaco@redhat.com>"
    date: 2026-05-22
    summary: "限制 SCHED_DEADLINE 的 revised wakeup rule 只应用于 running 状态的 dl_server（补丁正文发布于 5 月，未在当日邮件缓存内）。"
    review_outcome: "长期无人处理；7-29 作者 ping 后 PeterZ 度假归来响应，确认走 sched/urgent。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待 PeterZ 将补丁排入 tip/sched/urgent"
contribution_opportunities: []
generated_at: "2026-07-30T09:30:00"
source_email_count: 4
related_articles: []
tags: [deadline, dl_server]
---
