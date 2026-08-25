# PREEMPT_RT 下 non_block_start()/end() 区间内获取 sleeping spinlock 会触发 might_sleep(...

## TL;DR

PREEMPT_RT 下 non_block_start()/end() 区间内获取 sleeping spinlock 会触发 might_sleep() 告警。Sebastian 的修复为 `__might_resched()` 增加 `sleeping_lock` 参数区分正常调度与 sleeping lock 调度，David Woodhouse 已 ack。

## 背景与问题

Commit `312364f3534cc` 引入 `non_block_start()/end()` 用于检测回调中不应依赖锁或可睡眠条件的场景。spinlock 原本被排除在外，因为"spinlock 不会间接依赖页分配器"。但在 PREEMPT_RT 下，`spinlock_t` 和 `rwlock_t` 被转为 sleeping spinlock，带 `might_sleep()` 检查，锁竞争时会 `schedule()`，从而触发误告警。

主要受影响场景：PWM 子系统中 hrtimer 可能在 RT 上获取 `spinlock_t`。

## 技术方案

为 `__might_resched()` 增加 `sleeping_lock` 布尔参数：
- `true`：来自 sleeping lock 的调度请求（RT 下的 spinlock/rwlock 竞争）
- `false`：常规调度请求

在 `rtlock_might_resched()` 调用时传入 `true`，让检测逻辑区分这两种情况，避免误报。

## 版本演进与当前进展

v1 刚发出，David Woodhouse 已给出 Acked-by。

## Maintainer 意见与讨论焦点

David Woodhouse (Amazon) 已 ack，无争议。

## 合入评估

- **likelihood**: high
- **blocking_issues**: 无
- **next_action**: 等待 syzbot 确认 Tested-by 后合入

Fixes 标签指向 `312364f3534c ("kernel.h: Add non_block_start/end()")`。

## 效果评估

修复 PREEMPT_RT 下的误告警，不影响非 RT 内核。

## 我可以参与的点

当前阶段暂无明显参与空间，补丁已获 ack，等待合入。

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260821095755.am1-Segb@linutronix.de/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260821-002
date: 2026-08-21
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20260821095755.am1-Segb@linutronix.de>"
lore_url: "https://lore.kernel.org/lkml/20260821095755.am1-Segb@linutronix.de/"
authors: ["Sebastian Andrzej Siewior"]
maintainers_involved: ["David Woodhouse"]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260821095755.am1-Segb@linutronix.de>"
    date: 2026-08-21
    summary: "为 __might_resched() 增加 sleeping_lock 参数区分 RT sleeping lock"
    review_outcome: "David Woodhouse acked"
upstream_commit: null
fixes_commit: "312364f3534c"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待 syzbot Tested-by"
contribution_opportunities: []
generated_at: "2026-08-21T10:00:00"
source_email_count: 2
related_articles: []
tags: ["PREEMPT_RT", "sched/core", "locking"]
---
