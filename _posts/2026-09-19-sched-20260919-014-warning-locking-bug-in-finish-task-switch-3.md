---
id: sched-20260919-014
date: '2026-09-19'
subject: 'WARNING: locking bug in finish_task_switch (3)'
subsystem: sched
type: bug
status: under_review
severity: low
thread_root_msgid: <6aae3202.514bccd6.255447.0001.GAE@google.com>
lore_url: https://lore.kernel.org/all/6aae3202.514bccd6.255447.0001.GAE@google.com/
authors: []
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 提议补丁复测仍未解决告警
  - 根因（真实 wait-context bug vs lockdep 误报）与归属待 triage
  next_action: sched/lockdep 维护者 triage 告警根因与归属
contribution_opportunities:
- kind: review
  description: 分析 finish_lock_switch 获取 rq 锁的 wait-context 语义，判断真实问题还是误报
generated_at: '2026-09-20T09:00:00'
source_email_count: 1
related_articles: []
tags:
- syzbot
title: 'WARNING: locking bug in finish_task_switch (3)'
layout: article
---

## TL;DR
syzbot 针对 `kernel/sched/core.c` 的 `finish_task_switch()` 锁上下文告警（lockdep `DEBUG_LOCKS_WARN_ON`）报告：有人提出的补丁经 syzbot 复测后告警仍触发。告警出现在 `finish_lock_switch` 获取 rq 锁时，触发路径经 net socket（tcp diag dump 持 socket 锁后 schedule）。标签为 `[net?]`（syzbot 不确定归属），告警点确在调度器上下文切换路径。

## 背景与问题
syzbot 报告 lockdep 告警 `WARNING: locking bug in finish_task_switch`（本封为第 3 次发生）。触发栈：`tcp_get_info`→`inet_sk_diag_fill`（netlink diag dump）→`__lock_sock`→`schedule()`→`__schedule()`→`finish_task_switch()`→`finish_lock_switch`（kernel/sched/core.c:5248）→`lock_acquire`，在 `check_wait_context`（lockdep.c:238）处 `DEBUG_LOCKS_WARN_ON(1)`。即任务在持 socket 锁等待时 schedule，上下文切换阶段获取 rq 锁触发了 lockdep 的 wait-context 检查告警。测试配置为 `PREEMPT(full)`、GCE、i386 用户态、clang 22 构建；commit `18fbf515`（mm-stable merge）。本日邮件为 syzbot 对某人提议补丁的复测结论：reproducer 仍触发。

## 技术方案
本日无合入方案；此前有人（`hdanton@sina.com`）提议了补丁，syzbot 复测显示未解决。告警性质为 lockdep 的 wait-context 校验告警（`DEBUG_LOCKS_WARN_ON`，非 panic）。

## 版本演进与当前进展
- syzbot 原始报告（第 1、2 次）不在本窗口。
- 本日（`<6aae3202.514bccd6.255447.0001.GAE@google.com>`）：syzbot 复测提议补丁后仍触发，附带完整栈与复现信息（dashboard `extid=b5ddc2aecb8d1b29c871`）。

## Maintainer 意见与讨论焦点
本日无调度维护者表态。关键未决点：该告警是 rq 锁在"持 socket 锁后 schedule"场景下的真实 wait-context 问题，还是 lockdep 对该路径的误报/已知噪音；以及 `[net?]` 标签下归属 net 还是 sched 尚未定论。

## 合入评估
*likelihood=unknown*。已有提议补丁但复测未通过，根因未明、无维护者介入，证据不足。*blocking_issues*：提议补丁未解决告警；根因（真实 wait-context bug vs lockdep 误报）待 triage。*next_action*：sched/lockdep 维护者 triage 该 wait-context 告警的根因与归属。

## 效果评估
syzbot 复测：提议补丁下 reproducer 仍触发 `WARNING: locking bug in finish_task_switch`。无其他数据。

## 我可以参与的点
- kind=review：分析 `finish_lock_switch` 获取 rq 锁在持 socket 锁 schedule 场景下的 wait-context 语义，判断是真实问题还是 lockdep 误报。

## 参考链接
- lore（syzbot 复测）: https://lore.kernel.org/all/6aae3202.514bccd6.255447.0001.GAE@google.com/
- syzbot dashboard: https://syzkaller.appspot.com/bug?extid=b5ddc2aecb8d1b29c871
