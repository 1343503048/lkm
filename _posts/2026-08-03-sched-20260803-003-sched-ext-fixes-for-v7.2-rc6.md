---
subject: 'cgroup: Fixes for v7.2-rc6'
id: sched-20260803-003
date: 2026-08-03
subsystem: sched
type: fix
status: merged_tip
severity: high
thread_root_msgid: <unknown>
lore_url: unknown
authors:
- Tejun Heo
- Kuba Piecuch
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <unknown>
  date: 2026-08-03
  summary: GIT PULL sched_ext-for-7.2-rc6-fixes：子调度器生命周期修复（enable 失败撕裂未链接子调度器导致 UAF；非
    ext class 任务仍收到 enable 回调；policy 拒绝路径静默改写运行中任务的调度策略）、enable/disable 与 cgroup 移除/权重写入经
    kernfs 死锁（重排锁获取顺序）、sync wakeup 把 waker cpu 误标 idle 等。
  review_outcome: 作为 fixes pull 发出，等待 tip 侧接收。
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.2-rc6-fixes
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 等待 Linus 在 7.2-rc6 周期合入；已以 tag sched_ext-for-7.2-rc6-fixes 提交。
contribution_opportunities: []
generated_at: '2026-08-04T00:20:00'
source_email_count: 1
related_articles: []
tags:
- sched_ext
- cgroup
- idle
title: 'sched_ext: Fixes for v7.2-rc6'
layout: article
---

# sched_ext: 7.2-rc6 fixes pull（UAF/死锁/状态错误）


## TL;DR
Tejun 发出 sched_ext 的 7.2-rc6 fixes pull，修复子调度器生命周期中的多处 UAF / 死锁 / 错误状态，其中 sync wakeup 把 waker CPU 误标 idle 与 002 号文章（idle 掩码初始化）属同一正确性主题。已以 tag 提交，合入可能性=merged。

## 背景与问题
7.2-rc6 周期 sched_ext 累积了一批稳定性修复，集中在新的子调度器（sub-scheduler）支持的生命周期边界：

- 子调度器 enable 失败时，可能以「从未链接」的状态被拆除，与根调度器的 disable 竞争导致 **use-after-free**；
- 不在 ext class 的任务仍可能收到 enable 回调；
- policy 拒绝路径静默改写了运行中任务的调度策略，而非中止；
- scheduler enable/disable 与 cgroup 移除、并发 cgroup 权重写入经 kernfs 形成**死锁**，通过重排锁获取顺序修复；
- sync wakeup 会把 waker CPU 在 built-in idle-CPU 跟踪中错误标记为 idle（与 002 同源问题）。

## 技术方案
按子系统分别修复：子调度器生命周期加正确的链接态判断与中止逻辑；cgroup 与 fork/权重写入路径通过「持锁前先 fork worker / 重排锁序」消除锁依赖环；sync wakeup 的 WAKE_SYNC 选择 waker CPU 时显式标记为 busy。

## 版本演进与当前进展
以 fixes pull 形式于 2026-08-03 发出，基于 commit `0e2f4ab68a89`，截至 `d4a00d61a5c2`。包含 Kuba Piecuch 的两笔（WAKE_SYNC 标记 waker busy + 对应 selftest）等。

## Maintainer 意见与讨论焦点
作为 maintainer 自身的 fixes 汇总 pull，无 NAK。修复方向由 Tejun 主导，焦点是子调度器新特性的稳定性收尾。

## 合入评估
已 `merged`（以 fixes tag 提交，等待 7.2-rc6 周期进入主线）。分支 `sched_ext/for-7.2-rc6-fixes`。

## 效果评估
修复集合针对 UAF/死锁/状态错误等稳定性问题，邮件未给基准数字；属稳定性修复，效果以「消除崩溃/死锁」衡量。

## 我可以参与的点
当前阶段暂无明显参与空间，可持续观察 7.2-rc6 后续是否存在回归报告。

## 参考链接
- tag: sched_ext-for-7.2-rc6-fixes (https://git.kernel.org/pub/scm/linux/kernel/git/tj/sched_ext.git)
