---
id: sched-20261031-008
date: 2026-10-31
subject: '[GIT PULL] Scheduler updates for v7.4'
subsystem: sched
type: discussion
status: merged_tip
severity: none
thread_root_msgid: <atSiuBt4n03_iQNW@gmail.com>
lore_url: https://lore.kernel.org/all/atSiuBt4n03_iQNW@gmail.com/
authors: []
maintainers_involved:
- Linus Torvalds
- Frederic Weisbecker
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 推动 cputime 误报警告修复（001 篇）合入，避免 v7.4 -rc 携带该 boot WARN
contribution_opportunities:
- kind: testing
  description: x86 平台验证 001 篇修复合并后 boot 不再出现 kcpustat_dyntick_stop WARN
- kind: discussion
  description: 评估该 WARN 是否构成 v7.4 -rc 发布门槛（是否需 urgent 修复）
generated_at: '2026-11-01T09:00:00'
source_email_count: 4
related_articles: []
tags: []
title: '[GIT PULL] Scheduler updates for v7.4'
layout: article
---

## TL;DR
v7.4 的调度子系统主 GIT PULL 已进 Linus 树，但 Linus 在自家笔记本（Dell XPS 13 9380）上合并后**两次**命中 boot 时的 `kcpustat_dyntick_stop()` WARN splat 并向列表报告。社区很快定位到这正是当日 001 篇的误报警告（sched/cputime），Thorsten Leemhuis、Stian Halseth、Frederic Weisbecker 纷纷指向 Stian 的修复补丁。本条本质是「合并确认 + 一处回归曝光」的讨论串。

## 背景与问题
调度子系统在 v7.4 合并窗口通过 GIT PULL 进 mainline。Linus 合并后在其 XPS 13 9380（`7.3.0-19045-gb92f6e90cf05`）上不止一次触发 boot WARN：`now < tick_start` → `WARNING: kernel/sched/cputime.c:481 at kcpustat_dyntick_stop`，call trace 为 `tick_nohz_idle_exit → do_idle → cpu_startup_entry → start_secondary`。Linus 未定位原因，直接「notifying the guilty parties」。

## 技术方案
无补丁方案（合并确认 + 回归报告）。讨论焦点转向现有修复：Thorsten Leemhuis 指路 Stian 的 `sched/cputime: Don't warn when the tick period starts after idle exit`；Stian 确认 Paul Menzel、Breno Leitao 同命中、并称会发 v2；Frederic Weisbecker 表示正在吃透 Stian 的修复、准备给最终 ACK。

## 版本演进与当前进展
*current_version: null*。pull 已合并进 mainline；当日进展为「回归被 Linus 曝光 → 社区快速关联到已存在的修复」。pull 原文邮件不在当日缓存中，仅 4 封回复入缓存。

## Maintainer 意见与讨论焦点
- **Linus Torvalds**：报告 boot WARN（「I haven't tried to figure out why, I'm just notifying the guilty parties...」）。
- **Frederic Weisbecker（nohz maintainer）**：认领并正在核对 Stian 的修复（「Sorry about that, Stian has a fix, I'm just trying to wrap my head around it」）。
- **Thorsten Leemhuis（回归跟踪）**：把 Linus 的 splat 与 Stian 的补丁关联。
- **Stian Halseth**：确认同类报告（Paul/Breno）并承诺发 v2。
- 无分歧；本质是既有修复（001 篇）的加速推进信号。

## 合入评估
*likelihood=merged*（就 pull 本身而言，已进 mainline）。随 pull 带入的 cputime WARN 回归则依赖 001 篇的修复尽快进 sched/urgent。*blocking_issues*：无（pull 已合并）；回归修复（001）待 Frederic 最终 ACK。*next_action*：推动 cputime 修复合入，避免 v7.4 -rc 携带该 boot WARN。

## 效果评估
无性能数据；为合并确认 + 回归报告类条目。Linus 的 splat 为「不止一次」触发的真实 boot 警告（未计次数）。

## 我可以参与的点
- **testing**：在 x86 平台验证 001 篇修复合并后 boot 不再出现 `kcpustat_dyntick_stop` WARN。
- **discussion**：确认该 WARN 是否影响 v7.4 -rc 的发布门槛（是否需 urgent 修复）。

## 参考链接
- Linus 的报告: https://lore.kernel.org/all/CAHk-=winC2u2D1FAX5grfq9F=bxmARxhuiQ4MvHAiJFu3iF6gw@mail.gmail.com/
- 关联修复（001 篇）: https://lore.kernel.org/all/20261031081408.3378884-1-stian@itx.no/
- pull 原始 Message-ID 取自回复的 references 头，原文邮件未在缓存中：<atSiuBt4n03_iQNW@gmail.com>
