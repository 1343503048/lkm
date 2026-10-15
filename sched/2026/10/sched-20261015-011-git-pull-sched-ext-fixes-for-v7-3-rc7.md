# [GIT PULL] sched_ext: Fixes for v7.3-rc7

## TL;DR
Tejun Heo 向 Linus 发 sched_ext v7.3-rc7 修复的 GIT PULL（tag `sched_ext-for-7.3-rc7-fixes`），包含 7 个 commit、覆盖 5 类问题（任务回本 CPU 本地队列后 stall、destroyed user DSQ 的 use-after-free、dispatch 中移动任务、bypass 重叠、idle CPU 选择越界）。pr-tracker-bot 确认已合并进 torvalds/linux.git（merge commit `db7afcbf9eef65aa8bfe6edb5ff4b4a92d1a4792`）。

## 背景与问题
本拉取汇总 sched_ext 在 v7.3 后期发现的 5 个修复：
- 任务回本 CPU 本地队列时跳过 BPF 调度器，CPU 已决定转 idle，任务可一直 stall 到 watchdog；
- destroyed user dispatch queue 被 deferred re-enqueue 请求 use-after-free；
- 任务可在「调度它的 CPU 仍在跑 `ops.dequeue()`」时就被移出 DSQ；
- bypass 模式误处理子调度器与祖先 bypass 重叠（如系统 suspend），后代可能在 teardown 中离开 bypass、任务滞留在 bypass 队列；
- idle CPU 选择 helper 可能返回 pinned / migration-disabled 任务允许 CPU 之外的 CPU。

## 技术方案
拉取内容（`kernel/sched/ext/` 相关，7 commit）：
- Hui Su：`sched_ext: idle: Respect task affinity in restricted CPU selection`
- Kuba Piecuch（2）：`Rename scx_reenq_wait_dispatching()` → `scx_wait_dispatching()`；`Wait for SCX_OPSS_DISPATCHING before moving tasks off DSQs`
- Tejun Heo（4）：`Fix stall when a task enqueued with SCX_ENQ_LAST lands back on its CPU's local DSQ`、`Fix use-after-free of a destroyed user DSQ by a deferred reenqueue`、`Fix bypass propagation and the bypass dispatch claim for overlapping bypasses`（另 1 项见列表）

## 版本演进与当前进展
拉取请求（<3d82bc8d063a217f2d6583d285feca4b@kernel.org>）→ pr-tracker-bot 确认已合并进 torvalds/linux.git（<179207740215.3496071.9985947087057023494.pr-tracker-bot@kernel.org>）。

## Maintainer 意见与讨论焦点
Tejun Heo（sched_ext 维护者）作为发起人汇总；Linus 已合并，无争议。

## 合入评估
*likelihood=merged*。已合并进 torvalds/linux.git，将随 v7.3 发布。*blocking_issues*：无。*next_action*：无（已合入）。

## 效果评估
无量化数据，属缺陷修复集。

## 我可以参与的点
当前阶段暂无明显参与空间，修复已合入主线。

## 参考链接
- GIT PULL：https://lore.kernel.org/all/3d82bc8d063a217f2d6583d285feca4b@kernel.org/
- pr-tracker-bot 合并确认：https://lore.kernel.org/all/179207740215.3496071.9985947087057023494.pr-tracker-bot@kernel.org/
- merge commit：https://git.kernel.org/torvalds/c/db7afcbf9eef65aa8bfe6edb5ff4b4a92d1a4792

---
id: sched-20261015-011
date: 2026-10-15
subject: "[GIT PULL] sched_ext: Fixes for v7.3-rc7"
subsystem: sched
type: fix
status: merged_tip
severity: none
thread_root_msgid: "<3d82bc8d063a217f2d6583d285feca4b@kernel.org>"
lore_url: "https://lore.kernel.org/all/3d82bc8d063a217f2d6583d285feca4b@kernel.org/"
authors: ["Tejun Heo"]
maintainers_involved: ["Tejun Heo"]
current_version: null
patch_series: []
upstream_commit: "db7afcbf9eef65aa8bfe6edb5ff4b4a92d1a4792"
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已合入主线，随 v7.3 发布"
contribution_opportunities: []
generated_at: "2026-10-16T01:05:00"
source_email_count: 2
related_articles: []
tags: [sched_ext]
---