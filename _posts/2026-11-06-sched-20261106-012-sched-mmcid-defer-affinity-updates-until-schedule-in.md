---
id: sched-20261106-012
date: 2026-11-06
subject: 'sched/mmcid: Defer affinity updates until schedule-in'
subsystem: sched
type: bug
status: under_review
severity: critical
thread_root_msgid: <20261106120846.2405936-1-bestswngs@gmail.com>
lore_url: https://lore.kernel.org/all/20261106120846.2405936-1-bestswngs@gmail.com/
authors:
- Weiming Shi
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261106120846.2405936-1-bestswngs@gmail.com>
  date: 2026-11-06
  summary: MM-CID 允许掩码更新推迟到 schedule-in，修复 mm/exec 竞速 UAF。
  review_outcome: 暂无评审。
upstream_commit: null
fixes_commit: 7e019dcc470f
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 无评审
  - 需确认推迟传播不改变既有语义
  next_action: 等待 MM-CID/sched 侧审阅与 CONFIG_FUTEX=n 场景验证
contribution_opportunities:
- kind: testing
  description: CONFIG_FUTEX=n + CONFIG_SCHED_MM_CID=y 下复跑 setaffinity/exec 竞速验证 UAF
    消除
- kind: review
  description: 审阅 schedule-in 推迟是否覆盖所有 p->mm 释放路径
generated_at: '2026-11-07T09:00:00+08:00'
source_email_count: 1
related_articles: []
tags:
- affinity
title: 'sched/mmcid: Defer affinity updates until schedule-in'
layout: article
---

## TL;DR

Weiming Shi 修复 MM-CID 亲和性更新路径的 use-after-free（KASAN 已抓到、`panic_on_warn` 直接 panic）：`set_cpus_allowed_common()` 把远端任务的 `p->mm` 传给 `mm_update_cpus_allowed()`，但调度锁并不稳定这个指针——同一 owner 的 `sched_setaffinity()` 会与目标任务的 exec（替换并释放旧 mm）竞速，当前内核只是「碰巧」被 `futex_exec_done()` 取 `p->pi_lock`（且需 CONFIG_FUTEX=y）串行化，`CONFIG_FUTEX=n` 的合法配置仍然脆弱。修复把 MM-CID 允许掩码更新推迟到任务的 schedule-in（mm 稳定时），并在 first run 前同步 fork 任务的共享 mm。带 `Fixes: 7e019dcc470f`、`Cc: stable`。

## 背景与问题

MM-CID（rseq 并发 ID）依赖任务 affinity 变化时同步更新每 mm 的允许掩码。`set_cpus_allowed_common()` 调用 `mm_update_cpus_allowed()` 时直接取远端任务的 `p->mm`，而这条路径在调度锁下并不保证 `p->mm` 指针仍然有效——若任务正在 exec，`setup_new_exec()` 里的 `mmput()` 会释放旧 mm，`set_cpus_allowed_common()` 再去读就命中 KASAN slab-use-after-free（kasan 报告 `Read of size 4`，位于释放对象 588 字节处，`panic_on_warn` 直接内核 panic）。报告者为 `co+cab19e2ebe4d535a@bugs.sh`。

## 技术方案

- 把「MM-CID 允许掩码更新」从 `set_cpus_allowed_common()`（affinity 变更的当下）推迟到任务的下一次 schedule-in——那时其当前 mm 是稳定的（`sched_mm_cid.cpus_allowed_changed` 布尔标记 + 在调度点完成传播）。
- fork 后的任务在首次运行前同步其共享 mm，避免从父进程继承的待传播 affinity 扩展丢失；fork 时的 mask 快照用任务的 runqueue 锁保护（任务在 `sched_post_fork()` 前就已发布）。
- `include/linux/rseq_types.h` 新增 `cpus_allowed_changed` 字段（rq 锁保护）。

改动 4 文件 +20/-5 行。作者注明「LLM 协助开发」。

## 版本演进与当前进展

*current_version: v1（2026-11-06 发出）*。当日无评审。

## Maintainer 意见与讨论焦点

当日无维护者回复。补丁为修复 KASAN 抓到的真实 UAF，带 `Fixes`/`Reported-by`/`Cc: stable`，且明确点出「当前仅靠 CONFIG_FUTEX=y 的 `futex_exec_done()` 碰巧串行化」这个隐蔽前提。无 NAK。

## 合入评估

*likelihood=medium*。真实 UAF、有清晰根因与复现、Fixes 标签齐全，但刚发出、无人评审，且方案（推迟到 schedule-in + fork 同步 + rq 锁快照）触及 mm/exec 竞速的边角，需要 Mathieu Desnoyers（MM-CID 作者）等确认。*blocking_issues*：① 无评审；② 需确认推迟传播不改变既有语义。*next_action*：等待 MM-CID/sched 侧审阅与 CONFIG_FUTEX=n 场景验证。

## 效果评估

KASAN 报告（co+cab19e2ebe4d535a@bugs.sh）已抓到 UAF 且 `panic_on_warn` 触发内核 panic，复现可靠。作者未附修后回归数据（补丁说明偏机理，未给出「修复后 N 轮无 UAF」的数据）。

## 我可以参与的点

- **testing**：在 CONFIG_FUTEX=n、CONFIG_SCHED_MM_CID=y 的内核上复跑 sched_setaffinity 与 exec 竞速，验证 UAF 消除。
- **review**：审阅「推迟到 schedule-in」是否覆盖所有 `p->mm` 会被释放的路径（exec、setns、unshare 等）。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261106120846.2405936-1-bestswngs@gmail.com/
