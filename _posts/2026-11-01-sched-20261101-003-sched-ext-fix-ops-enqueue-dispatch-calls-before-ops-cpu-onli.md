---
id: sched-20261101-003
subject: 'sched_ext: Fix ops.enqueue/dispatch() calls before ops.cpu_online()'
date: 2026-11-01
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261031170541.710939-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20261031170541.710939-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261031170541.710939-1-tj@kernel.org>
  date: 2026-10-31
  summary: 两补丁：0001 抽出 drain_offline_rq()，0002 在 handle_hotplug() 统一管理 SCX_RQ_ONLINE
  review_outcome: v1 刚发出，暂无 review 意见
upstream_commit: null
fixes_commit: 60c27fb59f6c
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: 等待 sched_ext 核心 reviewer（sashiko、Andrea Righi 等）review 后合入 for-7.4-fixes
contribution_opportunities:
- kind: review
  description: 核对 SCX_RQ_ONLINE 移入 handle_hotplug() 后与 cpu_active() 判断的竞态
- kind: testing
  description: 在 CPU hotplug + sched_ext 加载/卸载场景下验证无 ops.enqueue() 早调用
generated_at: '2026-11-02T09:00:00'
source_email_count: 3
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Fix ops.enqueue/dispatch() calls before ops.cpu_online()'
layout: article
---

## TL;DR

修复 runtime CPU up 时，sched 域重建会把 rq 置为 online，导致在 `ops.cpu_online()` 之前就调用 `ops.enqueue()`/`ops.dispatch()` 的问题。方案是移除 rq_online/rq_offline 钩子，改在 `handle_hotplug()` 里统一管理 SCX_RQ_ONLINE。两补丁系列，for-7.4-fixes，Cc stable v6.12+。

## 背景与问题

`ops.cpu_online()` 文档承诺该 op 之前不会调用 `ops.enqueue()`/`ops.dispatch()`，两者都由 SCX_RQ_ONLINE 门控，而该标志经 ext 类的 rq_online/rq_offline 钩子跟随核心 rq online 状态。运行时 CPU up 时 `sched_cpu_activate()` 顺序为：1) `set_cpu_active()` 标记 active；2) `cpuset_cpu_active()` 同步重建 sched 域，`rq_attach_root()` 因 CPU 已 active 而把 rq 置 online，rq_online 钩子设置 SCX_RQ_ONLINE；3) `scx_rq_activate()` 才调用根调度器的 `ops.cpu_online()`。于是 2 和 3 之间，被唤醒/迁移到该 CPU 的任务会触发 `ops.enqueue()`，`ops.dispatch()` 也可能在其上运行。钩子不能直接调用 op（rq lock + IRQ off 下运行，而 op 可能是可睡眠的 BPF 程序），且 `handle_hotplug()` 的 idle 拓扑更新需要已重建的 sched 域。

## 技术方案

在 `handle_hotplug()` 里单独跟踪 SCX_RQ_ONLINE：在根调度器 `ops.cpu_online()` 之后立即置位；CPU 下线时清位并把该 CPU 任务移到本地 DSQ（`drain_offline_rq()`，patch 1 将其从 rq_offline_scx() 中抽出，纯重构无功能变化）。sched 域重建（让活 CPU 的 rq 下/上线）不再触碰该标志，避免远程 dispatch 因重建而被误清标志、错误弹到 global DSQ。2 和 3 之间落到该 CPU 的任务现在进入本地 DSQ 而跳过 `ops.enqueue()`；对 sub-scheduler，若任务所在调度器在该 CPU 缺少 caps，仍会 admit 并计入 SCX_EV_SUB_FORCED_ADMIT（这些在 1 和 2 之间本就发生）。`Fixes: 60c27fb59f6c`（"sched_ext: Implement sched_ext_ops.cpu_online/offline()"），Cc stable v6.12+。

## 版本演进与当前进展

v1（当前）：两补丁首次发出。0001 `sched_ext: Factor out drain_offline_rq()`（纯重构），0002 `sched_ext: Fix ops.enqueue/dispatch() calls before ops.cpu_online()`。基于 sched_ext/for-7.4-fixes（`0aba89317f38`），另提供分支 `git://git.kernel.org/pub/scm/linux/kernel/git/tj/sched_ext.git cpu-online-order`。本窗口内尚无 review 回帖。

## Maintainer 意见与讨论焦点

本窗口内未获取到 reviewer/maintainer 回帖（v1 刚发出）。无已知分歧。

## 合入评估

可能性中高（medium）。修复逻辑清晰、改动集中（4 文件 +68/-53），且属 for-7.4-fixes + stable 目标；但 v1 尚未有人 review，需等待维护者/`sashiko`、Andrea Righi 等 sched_ext 核心 reviewer 表态。阻塞项：暂无 review 结论。

## 效果评估

正确性修复（消除 ops.enqueue/dispatch 早于 ops.cpu_online 的时序窗口），无量化性能数据。

## 我可以参与的点

- review：核对 SCX_RQ_ONLINE 移入 handle_hotplug() 后与 `scx_rq_online()`、`scx_dispatch_sched()` 的 cpu_active() 判断是否仍有竞态。
- testing：在 CPU hotplug + sched_ext 调度器加载/卸载场景下验证无 `ops.enqueue()` 早调用。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261031170541.710939-1-tj@kernel.org/
- 0001: https://lore.kernel.org/all/20261031170541.710939-2-tj@kernel.org/
- 0002: https://lore.kernel.org/all/20261031170541.710939-3-tj@kernel.org/
