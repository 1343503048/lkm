# sched/core: Skip rq->avg_idle update without a valid idle_stamp

## TL;DR

`rq->avg_idle` 在没有有效 `idle_stamp` 时应跳过更新，作者 Shubhang Kaushik（Ampere）。补丁从 v1
迭代到 v3 后才被接收，9/2 已进 `tip/sched/urgent`（Commit-ID c6dcd97c8be7）。是 urgent 修复，不是新行为。

## 背景与问题

09-02 `tip/sched/urgent` 合入两笔修复，分别来自调度核心与 x86 调度相关代码：

1. `sched/core: Skip rq->avg_idle update without a valid idle_stamp`（UID 73124）：
   在没有有效 `idle_stamp` 时跳过 `rq->avg_idle` 更新，避免用陈旧/无效时间戳计算
   idle 均值。
2. `x86/itmt: Don't make ITMT enablement depend on debugfs`（UID 73115）：
   x86 ITMT（Intel Turbo Boost Max Technology）的启用此前依赖 debugfs 是否挂载，
   改为不依赖，确保在无 debugfs 的生产环境也能正确启用 ITMT 调度偏好。

## 技术方案

- 见概述两条 `[tip: sched/urgent]` 提交。

## 版本演进与当前进展

- 当前状态：**merged_tip**（已进入 `tip/sched/urgent`）。
- 合入可能性：**high/已合入**。两笔均为小型正确性/健壮性修复。

## Maintainer 意见与讨论焦点

- 当天邮件只有合入通知（73115，9/2 15:22）；同一分钟还有 `[tip: sched/urgent] x86/itmt: Don't make
  ITMT enablement depend on debugfs`（73120，Commit-ID eaece4849991，作者 Mario Limonciello）。
- v1→v2→v3 的版本推进说明被要求改过东西：K Prateek Nayak、Zhan Xusheng、John Stultz 都出现在该线程的
  参与者列表里（清单来自 8 月缓存的 msgid），但当日缓存未保留这些回帖正文，**具体谁要求了什么改动无法核实**。
- 无 NAK（否则不会进 urgent）。

## 合入评估

**已合入** `tip/sched/urgent`。无卡点。需要注意的是 v3 才是被接收的版本，任何引用都应指向 v3 之后的
Commit-ID，而不是早期版本。

## 效果评估

无效果数据。`avg_idle` 影响 `select_task_rq_fair()` 的唤醒侧决策（是否唤醒到空闲 CPU），但线程内
无人给出唤醒延迟或迁移次数的对比数字。

## 我可以参与的点

- 已合入后仍可做的：在 idle 密集与隔离核（nohz_full）场景验证 urgent 落地后无唤醒延迟回归。
- 若结果异常再回帖；无异常不需要占邮件列表。
- 更有意义的是顺带看 v1→v3 的改动为什么没留下评审记录——如果 8 月缓存能补齐，这条线程值得复盘一次。

## 参考链接

- 002 PREEMPT_DYNAMIC 简化（同属 tip 当天批量）

---
id: sched-20260902-011
date: '2026-09-02'
subject: 'sched/core: Skip rq->avg_idle update without a valid idle_stamp'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: null
lore_url: null
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v3
generated_at: null
authors:
- K Prateek Nayak
- Shubhang Kaushik (Ampere)
- Zhan Xusheng
- John Stultz
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "验证 urgent 合入后 idle 密集/隔离核场景无唤醒延迟回归"
contribution_opportunities:
- "在 nohz_full 或大量 idle 的平台上验证 avg_idle 修复后的唤醒延迟无回归"
- "补一次 v1→v3 的改动复盘（当日缓存缺评审正文，无法确认要求过什么）"
source_email_count: 9
related_articles: []
tags:
- sched/core
- compatibility
---
