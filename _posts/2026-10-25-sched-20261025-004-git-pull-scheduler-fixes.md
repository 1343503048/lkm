---
id: sched-20261025-004
date: 2026-10-25
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
upstream_commit: cac037a85c1971ec75c4d3edf5a28af9ec2a089c
fixes_commit: null
merged_branch: sched-urgent-2026-10-25
merge_assessment:
  likelihood: high
  blocking_issues:
  - 当日缓存未见 pr-tracker-bot 合并确认
  next_action: 等待 Linus 合入，关注三修复的 stable 回合
contribution_opportunities:
- kind: testing
  description: 回归 cache aware + asym packing 混合系统放置与 mmcid affinity 切换
generated_at: '2026-10-26T09:00:00'
source_email_count: 1
related_articles: []
tags:
- cfs
- load_balance
- regression
title: '[GIT PULL] scheduler fixes'
layout: article
---

## TL;DR
Ingo Molnar 向 Linus 发 sched/urgent 修复 pull request（tip 树 `sched-urgent-2026-10-25`，截至 `cac037a85c1971ec75c4d3edf5a28af9ec2a089c`），含三枚修复：mmcid affinity 触发切回 per-task 模式（Hui Su）、cache aware scheduling 在 AMD Ryzen AI HX 370 上错误覆盖 asym packing 放置导致的调度回退（Tim Chen）、`!CONFIG_SCHED_CACHE` 下 stale `get_pref_llc()` 原型（Yafang Shao）。当日缓存未见 Linus 合并回帖。

## 背景与问题
合入窗口期 Ingo 发 sched/urgent 修复 pull，收集三枚此前已 review 的修复：mmcid（cgroup 调度）affinity 触发不必要切回 per-task 模式；cache aware scheduling 在 hybrid 系统（AMD Ryzen AI HX 370）上错误覆盖 asym packing 放置造成调度回退；`get_pref_llc()` 在 `!CONFIG_SCHED_CACHE` 下的 stale 原型。

## 技术方案
三枚 commit（`kernel/sched/core.c` +5/−3、`kernel/sched/fair.c` +22/−4，合计 2 files +20/−7）：

- Hui Su：`sched/mmcid: Fix affinity-triggered switch back to per-task mode`
- Tim Chen：`sched/cache: Honor asym packing over cache aware scheduling on hybrid systems`
- Yafang Shao：`sched: fix stale get_pref_llc() stub for !CONFIG_SCHED_CACHE`

## 版本演进与当前进展
*current_version: null*。pull 当日发出（2026-10-25，`<at3l-1cmp86nIe9M@gmail.com>`）。缓存内未见 Linus 合并回帖。

## Maintainer 意见与讨论焦点
Ingo Molnar（调度 maintainer）作为发起人汇总；三枚修复均在各自补丁系列中已通过 review（asym packing 见 <a class="article-ref" href="/lkm/2026/10/24/sched-20261024-012-sched-cache-honor-asym-packing-over-cache-aware-scheduling-o.html">sched-20261024-012</a>、get_pref_llc 见 <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-017-sched-fix-stale-get-pref-llc-stub-for-config-sched-cache.html">sched-20261021-017</a>/20261024-013、mmcid 见相关文章）。无争议。

## 合入评估
*likelihood=high*。三枚修复均已过 review 并进 tip/sched/urgent；窗口期的 urgent 修复 pull 通常很快被 Linus 收取。*blocking_issues*：当日缓存未见 pr-tracker-bot 合并确认。*next_action*：等待 Linus 合入；三枚修复的 stable 回合与否视各自补丁的 Cc 而定。

## 效果评估
无量化数据，属正确性/回退修复集：AMD Ryzen AI HX 370 的 cache aware scheduling 回退修复直接恢复正确放置；mmcid 修复 affinity 触发的不必要 per-task 切回；stub 修复编译一致性。

## 我可以参与的点
- *kind: testing*：在 v7.4 窗口或 stable 上回归 cache aware + asym packing 混合系统放置，以及 mmcid affinity 切换行为。
- 回合视角：OLK-6.6 回合 `get_pref_llc()` stub 修复时应确认对应 `!CONFIG_SCHED_CACHE` 代码路径是否同构。

## 参考链接
- GIT PULL: https://lore.kernel.org/all/at3l-1cmp86nIe9M@gmail.com/
