---
id: sched-20261121-004
date: '2026-11-21'
subject: 'sched/rt: push a queued task when its priority is boosted'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <179526068763.97100.12205093734161349836@gmail.com>
lore_url: https://lore.kernel.org/all/179526068763.97100.12205093734161349836@gmail.com/
authors:
- Chaosheng Qu
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <179526068763.97100.12205093734161349836@gmail.com>
  date: '2026-11-21'
  summary: 排队非当前 RT 任务优先级提升时入队 push，覆盖 pull 侧够不到的场景
  review_outcome: 暂无 review
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 无维护者 review
  - RT_PUSH_IPI on 路径行为待确认
  next_action: 等 Steven Rostedt 对 v1 的 review，必要时补充真机基准
contribution_opportunities:
- kind: testing
  description: 真机 + RT_PUSH_IPI on/off 复测 PI boost 场景延迟与优先级反转回归
- kind: review
  description: 核对 push 回调触发条件覆盖所有存在迁移目标的提升路径
generated_at: '2026-11-22T01:00:00+08:00'
source_email_count: 91
related_articles: []
tags:
- rt
- preempt
title: 'sched/rt: push a queued task when its priority is boosted'
layout: article
---

## TL;DR

Chaosheng Qu 修 sched/rt 的一个迁移延迟问题：PI boost 把排队 RT 任务提到高于其它 CPU 上所有任务，但它仍不能在自己的 rq 上跑（当前任务优先级相同或更高），`prio_changed_rt()` 只 `resched_curr()`，任务要等当前任务自己让出；pull 侧 `pull_rt_task()` 只挑亲和包含本 CPU 的任务，mask 不含刚 idle CPU 的任务不可达。作者补丁在排队非当前 RT 任务优先级提升时入队一个 push。作者在 4-vCPU QEMU 上给出基准（RT_PUSH_IPI off）：baseline 1/5 获救（约 802/1161/1312/30/1280 ms），打补丁 5/5 获救（约 14/1/0.2/0.2/0.8 ms）。

## 背景与问题

PI boost 可把排队任务提到高于其它 CPU 上所有可运行任务的优先级，而它仍无法在自己 rq 上运行（当前任务优先级相同或更高）。`prio_changed_rt()` 此时只 `resched_curr()`，任务只能等当前任务调度出去。pull 侧也救不了它：`pull_rt_task()` 只挑亲和含 pulling CPU 的任务，因此 mask 不包含刚 idle CPU 的任务在运行任务自己让出前不可达。`RT_PUSH_IPI` off 时，这表现为毫秒级迁移 vs 等 hog 跑完。

## 技术方案

排队非当前 RT 任务优先级提升时入队一个 push。`push_rt_task()` 已会拒绝迁移不可 push 的任务、且在任务优先级高于当前任务时跳过 reschedule 路径，所以新增回调只在存在迁移目标时生效。diff 一行 13 行的 `kernel/sched/rt.c` 改动。作者注明这是与 Steve（Steven Rostedt）在 10 月讨论过的修法，关键场景是「pull 侧因 mask 排除刚 idle CPU 而够不到」的排队任务。

## 版本演进与当前进展

*current_version: v1（2026-11-21，`<179526068763.97100.12205093734161349836@gmail.com>`，单补丁）*。首版，当日无 review；作者附 QEMU 基准并愿提供复现小程序。

## Maintainer 意见与讨论焦点

- **Steven Rostedt**：该修法源于其与作者 10 月的讨论（`<20261015084615.05957ae3@gandalf.local.home>` 为在案线索），但本日缓存未见其对 v1 的正式回复。
- 无 NAK；关键待确认点是 push 回调是否在任何存在迁移目标的提升路径都被正确触发、有无额外开销。

## 合入评估

*likelihood=medium*。方向有据（与 Steve 讨论的既成方案）、附了量化数据，但当日无维护者 review；RT push 路径改动需 Peter/Steve 确认语义。*blocking_issues*：无维护者 review；`RT_PUSH_IPI` on 的路径下行为是否一致待确认。*next_action*：等 Steven Rostedt 对 v1 的 review，必要时补充更大规模/真机 RT 基准。

## 效果评估

作者基准（4-vCPU QEMU guest，TCG 非 KVM，非 RT 内核，RT_PUSH_IPI off；L=FIFO10 mask{cpu1,cpu3}、X=FIFO99 hog cpu1、W=FIFO90 在 cpu2 阻塞于 L 的 PI mutex、R=FIFO60 在 cpu3）：
- baseline：1/5 获救，802.8 / 1161.0 / 1311.8 / 30.2 / 1280.0 ms
- patched：5/5 获救，13.8 / 1.1 / 0.2 / 0.2 / 0.8 ms

为作者自测，未见第三方独立复现。

## 我可以参与的点

- **testing**：在真机（非 TCG）+ `RT_PUSH_IPI` on/off 两种配置下复测该场景，确认延迟改善与无优先级反转回归。
- **review**：核对 push 回调触发条件是否覆盖所有「优先级提升且存在迁移目标」的路径、是否会与既有 push 逻辑重复入队。

## 参考链接

- lore thread: https://lore.kernel.org/all/179526068763.97100.12205093734161349836@gmail.com/
