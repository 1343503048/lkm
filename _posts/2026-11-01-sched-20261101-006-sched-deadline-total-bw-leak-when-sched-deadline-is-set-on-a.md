---
id: sched-20261101-006
subject: 'sched/deadline: total_bw leak when SCHED_DEADLINE is set on a dead task'
date: 2026-11-01
subsystem: sched
type: bug
status: rfc
severity: medium
thread_root_msgid: <3f6e6c87-645b-45fd-8fc6-8da5bc5b82d8@gmail.com>
lore_url: https://lore.kernel.org/all/3f6e6c87-645b-45fd-8fc6-8da5bc5b82d8@gmail.com/
authors:
- Weiheng Qiu
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <3f6e6c87-645b-45fd-8fc6-8da5bc5b82d8@gmail.com>
  date: 2026-11-01
  summary: bug 报告 + x86-64 复现程序（zombie_admit_leak.c）
  review_outcome: 无人回复
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无维护者/社区成员确认与诊断
  next_action: 需要 sched/deadline 维护者或社区成员确认根因并确定修复方向
contribution_opportunities:
- kind: new_patch
  description: 基于根因（__sched_setscheduler() 未检查 p->exit_state）提交修复补丁
- kind: testing
  description: 在其它架构/发行版复现确认泄漏与恢复行为
generated_at: '2026-11-02T09:00:00'
source_email_count: 1
related_articles: []
tags:
- deadline
title: 'sched/deadline: total_bw leak when SCHED_DEADLINE is set on a dead task'
layout: article
---

## TL;DR

Weiheng Qiu 报告：对已退出但未 reaped（zombie）的任务调用 `sched_setattr(SCHED_DEADLINE)` 会返回 0 并占用 root domain 的 `dl_bw->total_bw`，且永不释放，最终把 admission 打满、后续 DL 请求与 CPU offline 报 -EBUSY。附带完整复现程序，尚无 fix 补丁。

## 背景与问题

`__sched_setscheduler()` 不检查 `p->exit_state`，因此对 zombie 任务设置 SCHED_DEADLINE 时 `sched_dl_overflow()` 照样记账。DL 任务的带宽本应在最后一次 dequeue 时释放，而已经完成最终 `__schedule()` 的 zombie 永远不会再走到那一步。反复操作会把 `total_bw` 填到 admission 上限（作者在 mainline `c339f4010dea` 上演示：一个 zombie 占用 0.25 CPU 后，再 6 个 zombie 即触发 -EBUSY，`total_bw` 达 1.850 CPU）；此后新 DL 请求与 CPU offline 都因「Device or resource busy」失败，只有完整重建 root domain 才能重算。需要 CAP_SYS_NICE（任何 DL admission 都需要）。

## 技术方案

未给出补丁。根因定位清晰：`__sched_setscheduler()` 缺少对 `p->exit_state`（zombie/dead）的检查。作者提供 x86-64 复现程序（`zombie_admit_leak.c`，读 `/sys/kernel/debug/sched/debug` 的 `dl_bw->total_bw`）。

## 版本演进与当前进展

v1：单一 bug 报告 + 复现程序，本窗口内无回复。

## Maintainer 意见与讨论焦点

未获取到（无人回复）。

## 合入评估

未知（unknown）。刚发出的 bug 报告，无人认领或表态。阻塞项：无维护者/社区成员确认与诊断。根因明确但修复方案（在 `__sched_setscheduler()` 拒绝 zombie 还是释放其带宽）尚未讨论。

## 效果评估

作者复现数据（mainline `c339f4010dea`，0.25 CPU == 262144）：zombie 设 DL 后 `total_bw` 由 0.100 增至 0.350 CPU；reap 后仍为 0.350（+0.250 泄漏）；再 6 个 zombie 后 -EBUSY，`total_bw` 1.850 CPU；root-domain 重建后回到 0.100 CPU。

## 我可以参与的点

- new_patch：基于根因（`__sched_setscheduler()` 未检查 `p->exit_state`）提交修复补丁，例如在 DL admission 前拒绝已退出任务或在退出路径正确释放带宽。
- testing：在其它架构/发行版复现确认泄漏与恢复行为。

## 参考链接

- lore thread: https://lore.kernel.org/all/3f6e6c87-645b-45fd-8fc6-8da5bc5b82d8@gmail.com/
