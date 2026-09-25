# sched_ext: Count cap-rejected local DSQ inserts in SCX_EV_SUB_REJECT

## TL;DR

Liang Luo 发的单枚统计修复：`__scx_resolve_local_dsq()` 对「缺 cap 的 local DSQ 入队」有三种结果，其中前两种（强制 admit、rescue）都有计数器，唯独第三种——转入 reject DSQ 等待 BPF 调度器重新决策——没有被计数。补丁新增 `SCX_EV_SUB_REJECT` 把它纳入 sysfs / `scx_dump_state()` / `scx_bpf_events()` 的可观测面，带 `Fixes:` 标签。今日刚发、无回帖。

## 背景与问题

当任务被入队到 local DSQ、但其入队标志要求的 caps 缺失时，`__scx_resolve_local_dsq()` 有三种出路：一是因 rq 正在离线 drain、任务 migration-disabled 或有 pending 迁移而**照样 admit**（计入 `SCX_EV_SUB_FORCED_ADMIT`）；二是入队请求了 rescue、走 **rescue 路径**（计入 `SCX_EV_SUB_RESCUE`）；三是**转入 reject DSQ**、重新入队让 BPF 调度器重新决策。前两种有计数，第三种没有，导致「被转去 reject DSQ 的任务数」在 sysfs、`scx_dump_state()`、`scx_bpf_events()` 里完全缺失，也没有别的计数器能覆盖它（`nr_rejected` 只统计 `ops.init_task()` 拒绝的，`SCX_EV_REENQ_REPEAT` 只在同一任务再次 placement 失败时才看到 reject）。

## 技术方案

在 `struct scx_event_stats` 里新增 `SCX_EV_SUB_REJECT` 字段并纳入 `SCX_EVENTS_LIST`，在 reject 分流点 +1。这样 cap 缺失 local DSQ 入队的三种结果都可观测。规模：kernel/sched/ext/internal.h +10/+1、kernel/sched/ext/sub.c +2。

## 版本演进与当前进展

- v1（2026-09-25，`<20260925070500.565561-1-luoliang@kylinos.cn>`）：首发，`Fixes: 75a8c8202c91 ("sched_ext: Add reject DSQ for cap-rejected dispatches")`。今日无回帖。

## Maintainer 意见与讨论焦点

今日无人回帖；Tejun Heo 尚未表态。作为统计面补全，风险低，但需确认新事件字段是否会影响 ABI/工具解析。

## 合入评估

*likelihood=unknown*。单枚统计补全，带 Fixes 标签，无回帖。*blocking_issues*：无 review。*next_action*：等 Tejun 的 review/ack。

## 效果评估

无运行时数据；效果是让运维/调试观测面完整（三种分流结果都能计数）。

## 我可以参与的点

- `review`：确认 `SCX_EV_SUB_REJECT` 的计数点与 reject DSQ 分流路径一一对应、无误计漏计。
- `testing`：构造缺 cap 的 local DSQ 入队场景，核对三个 SUB 事件计数之和是否等于总入队拒绝数。

## 参考链接

- 补丁: https://lore.kernel.org/all/20260925070500.565561-1-luoliang@kylinos.cn/

---
id: sched-20260925-019
date: 2026-09-25
subject: "sched_ext: Count cap-rejected local DSQ inserts in SCX_EV_SUB_REJECT"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20260925070500.565561-1-luoliang@kylinos.cn>"
lore_url: "https://lore.kernel.org/all/20260925070500.565561-1-luoliang@kylinos.cn/"
upstream_commit: null
fixes_commit: "75a8c8202c91"
merged_branch: null
current_version: v1
generated_at: "2026-09-26T01:15:00"
authors:
  - "Liang Luo"
maintainers_involved: []
patch_series:
  - version: v1
    msgid: "<20260925070500.565561-1-luoliang@kylinos.cn>"
    date: 2026-09-25
    summary: "新增 SCX_EV_SUB_REJECT，补齐 cap 缺失 local DSQ 入队转 reject DSQ 的计数"
    review_outcome: "无回帖"
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - "无 review"
  next_action: "等 Tejun 的 review/ack"
contribution_opportunities:
  - kind: review
    description: "确认 SCX_EV_SUB_REJECT 计数点与 reject DSQ 分流路径一一对应、无误计漏计"
  - kind: testing
    description: "构造缺 cap 的 local DSQ 入队场景，核对三个 SUB 事件计数之和是否等于总入队拒绝数"
source_email_count: 1
related_articles: []
tags:
  - sched_ext
---