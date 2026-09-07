---
id: sched-20260906-001
date: '2026-09-06'
subject: 'sched_ext: Fix keep-last for sub-scheduler tasks and two scx_qmap placement
  loops'
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: null
lore_url: null
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.3-fixes
current_version: v1
generated_at: '2026-09-07T00:10:00'
authors:
- Tejun Heo
- Andrea Righi
maintainers_involved:
- Tejun Heo
patch_series:
- version: v1
  msgid: null
  date: 2026-09-06
  summary: PATCHSET（4 片）修复 sub-scheduler 任务的 keep-last 决策与 scx_qmap 两处放置循环：1/4 在 dispatch_one()
    中将变量 sch 重命名为 root_sch；2/4 在 dispatch_one() 的 keep 决策里改用 @prev 自己的调度器而非 root 调度器；3/4
    scx_qmap 的 rescue inserts 不再加 SCX_ENQ_IMMED；4/4 scx_qmap 仅把任务放到 caps 实际生效的 cids。
  review_outcome: for-7.3-fixes 分支上收到多轮 Re（82025/82028/82154/82162/82168/82711），围绕放置语义与
    caps 生效判定讨论，尚在 review。
merge_assessment:
  likelihood: high
  blocking_issues:
  - for-7.3-fixes 上的放置语义细节仍在讨论，需确认 sub-scheduler 与 root 调度器的 keep 决策边界
  next_action: 等待 Tejun 在 fixes 分支合入；社区可在 scx_nitosis 下跑 scx_qmap 复现验证
contribution_opportunities:
- kind: testing
  description: 在 scx_nitosis 作为 sub-scheduler 跑 scx_qmap，观察是否仍触发 put_prev_task_scx()
    的 WARN_ON_ONCE 与潜在 stall
- kind: review
  description: review 第 2/4 片：keep 决策从 root 调度器改到 @prev 自身调度器后，对 multi-level sub-scheduler
    的语义是否完整
source_email_count: 8
related_articles:
- sched-20260903-004
- sched-20260904-011
tags:
- sched_ext
title: 'sched_ext: Fix keep-last for sub-scheduler tasks and two scx_qmap placement
  loops'
layout: article
---

## TL;DR

Tejun 在 `sched_ext/for-7.3-fixes` 上贴出 4 片 PATCHSET，修两类 sub-scheduler / scx_qmap 放置 bug（keep-last 决策用错调度器导致 WARN+可能 stall、rescue insert 加 IMMED 导致与 REENQ 互踢）。属于 fixes 分支内容，合入可能性高，值得用 scx_nitosis 跑 scx_qmap 复现验证。

## 背景与问题

把 scx_qmap 作为 sub-scheduler 跑在 scx_nitosis 之下，暴露出一个内核 bug 和两个 scx_qmap bug：
- `dispatch_one()` 当前通过 **root 调度器** 的 `SCX_OPS_ENQ_LAST` 与 bypass 状态来决定是否 keep 运行 `@prev`。但这些属性属于 `@prev` **自己的调度器**，且 `put_prev_task_scx()` 作用在 `@prev` 自己的调度器上。当 root 设置了该 flag 而 `@prev` 所属的 sub-scheduler 没设置时，任务不会被 keep，反而以 `SCX_ENQ_LAST` 入队到一个从未 opt-in 的调度器，触发 `put_prev_task_scx()` 里的 `WARN_ON_ONCE`，且任务入队后没有后续调度事件，可能 stall。第 1-2 片修这个。
- scx_qmap 给 rescue inserts 加了 `SCX_ENQ_IMMED`，会把一次 rescue 请求变成在 time-shared cid 上的常规放置，与内核的 REENQ bounce 互相拉扯，直到 reenqueue 上限把调度器 eject 掉。第 3 片修这个。
- 第 4 片进一步让 scx_qmap 仅把任务放到 caps 实际生效的 cids。

## 技术方案

核心是把「keep 决策」的归属从 root 调度器纠正为 `@prev` 自身所属的调度器（dispatch_one 内 rename `sch`→`root_sch` 以明确作用域），并在 scx_qmap 侧移除 rescue insert 的 IMMED、按 caps 实际生效的 cids 做放置。设计取舍在于：sub-scheduler 任务的 keep 语义应跟随任务自己的调度器，而非被 root 的 flags 误带。

## 版本演进与当前进展

当前为 v1（首次以 PATCHSET 形式发出）。for-7.3-fixes 上已收到 6 封 Re（82025/82028/82154/82162/82168/82711），主要针对放置语义与 caps 生效判定做细节讨论，未见 NAK。

## Maintainer 意见与讨论焦点

讨论集中在第 2 片（keep 决策改用 `@prev` 调度器）与第 4 片（caps 生效判定）的边界。Tejun 本人即作者/维护者，方向已被认可，剩余为 fixes 分支上的实现细节打磨，无明显分歧或反对。

## 合入评估

`merged_branch` 已标 `sched_ext/for-7.3-fixes`，属于稳定修复分支内容；社区讨论为细节完善而非方向性质疑，`likelihood=high`。卡点仅是实现细节收尾。

## 效果评估

暂无量化 benchmark；作者以 scx_qmap 作为 scx_nitosis sub-scheduler 复现触发 WARN/stall 作为验证依据。效果属「消除误触发与潜在 stall」，未见性能数字。

## 我可以参与的点

- 在 scx_nitosis 下跑 scx_qmap，确认 WARN_ON_ONCE 与潜在 stall 是否消失（testing）。
- review 第 2 片对 multi-level sub-scheduler 的 keep 语义是否完整（review）。

## 参考链接

- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到
