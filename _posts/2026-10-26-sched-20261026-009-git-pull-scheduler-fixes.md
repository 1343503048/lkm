---
id: sched-20261026-009
date: 2026-10-26
subject: '[GIT PULL] scheduler fixes'
subsystem: sched
type: fix
status: merged_tip
severity: high
thread_root_msgid: <at3l-1cmp86nIe9M@gmail.com>
lore_url: https://lore.kernel.org/all/at3l-1cmp86nIe9M@gmail.com/
authors:
- Ingo Molnar
maintainers_involved:
- Ingo Molnar
current_version: null
patch_series: []
upstream_commit: 6e723c4f9417663c318d898fa113af211f48a6da
fixes_commit: null
merged_branch: sched-urgent-2026-10-25
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入 torvalds/linux.git；关注三修复的 stable 回合
contribution_opportunities:
- kind: testing
  description: 回归 cache aware + asym packing 混合系统放置与 mmcid affinity 切换
- kind: new_patch
  description: 回合 get_pref_llc() stub 修复时确认 !CONFIG_SCHED_CACHE 路径同构
generated_at: '2026-10-27T01:00:00'
source_email_count: 1
related_articles:
- sched-20261025-004
tags:
- cfs
- load_balance
- regression
title: '[GIT PULL] scheduler fixes'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/25/sched-20261025-004-git-pull-scheduler-fixes.html">sched-20261025-004</a>：Ingo Molnar 向 Linus 发 sched/urgent 修复 pull request（tip 树 `sched-urgent-2026-10-25`，截至 `cac037a85c1971ec75c4d3edf5a28af9ec2a089c`），含三枚修复：mmcid affinity 触发切回 per-task 模式（Hui Su）、cache aware scheduling 在 AMD Ryzen AI HX 370 上错误覆盖 asym packing 放置导致的调度回退（Tim Chen）、`!CONFIG_SCHED_CACHE` 下 stale `get_pref_llc()` 原型（Yafang Shao）。当日缓存未见 Linus 合并回帖。
- <a class="article-ref" href="/lkm/2026/10/26/sched-20261026-009-git-pull-scheduler-fixes.html">sched-20261026-009</a>（今天）：pr-tracker-bot 确认该 pull 已合入 torvalds/linux.git（合并 commit `6e723c4f9417663c318d898fa113af211f48a6da`）。三枚 sched/urgent 修复进入主线。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/10/25/sched-20261025-004-git-pull-scheduler-fixes.html">sched-20261025-004</a>）合入窗口期 Ingo 发 sched/urgent 修复 pull，收集三枚此前已 review 的修复：mmcid（cgroup 调度）affinity 触发不必要切回 per-task 模式；cache aware scheduling 在 hybrid 系统（AMD Ryzen AI HX 370）上错误覆盖 asym packing 放置造成调度回退；`get_pref_llc()` 在 `!CONFIG_SCHED_CACHE` 下的 stale 原型。今日无新背景，为合并确认。

## 技术方案
（承接 <a class="article-ref" href="/lkm/2026/10/25/sched-20261025-004-git-pull-scheduler-fixes.html">sched-20261025-004</a>）三枚 commit（`kernel/sched/core.c` +5/−3、`kernel/sched/fair.c` +22/−4，合计 2 files +20/−7）：

- Hui Su：`sched/mmcid: Fix affinity-triggered switch back to per-task mode`
- Tim Chen：`sched/cache: Honor asym packing over cache aware scheduling on hybrid systems`
- Yafang Shao：`sched: fix stale get_pref_llc() stub for !CONFIG_SCHED_CACHE`

今日无代码变更，为 Linus 合入确认。

## 版本演进与当前进展
*current_version: null*。pull 于 2026-10-25 发出（`<at3l-1cmp86nIe9M@gmail.com>`），2026-10-26 pr-tracker-bot 确认合入 torvalds/linux.git（合并 commit `6e723c4f9417663c318d898fa113af211f48a6da`）。

## Maintainer 意见与讨论焦点
无新增讨论。pr-tracker-bot 确认「pull request 已合入 torvalds/linux.git」。此前三枚修复均已在各自系列通过 review，无争议。

## 合入评估
*likelihood=merged*。pull 已被 Linus 合入主线（合并 commit `6e723c4f9417663c318d898fa113af211f48a6da`），三枚 sched/urgent 修复进入 mainline。*blocking_issues*：无。*next_action*：关注三修复各自的 stable 回合（视各补丁的 `Cc: stable` 而定）。

## 效果评估
无量化数据，属正确性/回退修复集：AMD Ryzen AI HX 370 的 cache aware scheduling 回退修复恢复正确放置；mmcid 修复 affinity 触发的不必要 per-task 切回；stub 修复编译一致性。

## 我可以参与的点
- *kind: testing*：在 v7.4 窗口或 stable 上回归 cache aware + asym packing 混合系统放置、以及 mmcid affinity 切换行为。
- *kind: new_patch*：回合到自家分支时确认 `get_pref_llc()` stub 修复对应 `!CONFIG_SCHED_CACHE` 代码路径是否同构，必要时发回合补丁。

## 参考链接
- GIT PULL: https://lore.kernel.org/all/at3l-1cmp86nIe9M@gmail.com/
- pr-tracker-bot 合并确认: https://lore.kernel.org/all/179298714950.2448250.13466230457999003999.pr-tracker-bot@kernel.org/
- 前文: <a class="article-ref" href="/lkm/2026/10/25/sched-20261025-004-git-pull-scheduler-fixes.html">sched-20261025-004</a>
