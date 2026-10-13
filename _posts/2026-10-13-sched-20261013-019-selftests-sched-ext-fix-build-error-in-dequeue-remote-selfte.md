---
id: sched-20261013-019
subject: 'selftests/sched_ext: Fix build error in dequeue_remote selftest'
date: 2026-10-13
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <20261012115928.1372317-1-smariotti@disroot.org>
lore_url: https://lore.kernel.org/all/20261012115928.1372317-1-smariotti@disroot.org/
authors:
- Samuele Mariotti
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20261012115928.1372317-1-smariotti@disroot.org>
  date: 2026-10-12
  summary: asm volatile 消费 sum 变量，修 gcc 16 构建错误
  review_outcome: Kuba Reviewed-by；Tejun 应用到 for-7.4（去 Fixes 标签）
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.4
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 随 for-7.4 进入下个合并窗口
contribution_opportunities: []
generated_at: '2026-10-14T01:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261012-001
tags:
- sched_ext
title: 'selftests/sched_ext: Fix build error in dequeue_remote selftest'
layout: article
---

> **subject**：selftests/sched_ext: Fix build error in dequeue_remote selftest

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-001-selftests-sched-ext-fix-build-error-in-dequeue-remote-selfte.html">sched-20261012-001</a>：sched_ext 自测 `dequeue_remote` 在较新编译器（gcc 16）下因 `sum`「set but not used」构建报错，作者用一行 `asm volatile("" : : "r"(sum))` 消费该变量，与既有 `dequeue` 自测修法一致；Kuba Piecuch 已 Reviewed-by。
- <a class="article-ref" href="/lkm/2026/10/13/sched-20261013-019-selftests-sched-ext-fix-build-error-in-dequeue-remote-selfte.html">sched-20261013-019</a>（今天）：Tejun Heo 将其 **Applied 到 sched_ext/for-7.4**，去掉原 `Fixes` 标签并追加 `Reviewed-by: Kuba Piecuch`。

## 背景与问题
（承接 20261012-001）gcc 16 等较新编译器构建 `tools/testing/selftests/sched_ext/dequeue_remote.c` 报错 `variable 'sum' set but not used`；`volatile` 只能防写被优化、无法消除「只写不读」告警。

## 技术方案
（承接 20261012-001）与 `dequeue` 自测既有修法（commit 3788e3251653）一致：累加循环后加 `asm volatile("" : : "r"(sum));`，用寄存器输入约束迫使编译器保留累计值，同时消除告警。单文件 +1 行。

## 版本演进与当前进展
v1（`<20261012115928.1372317-1-smariotti@disroot.org>`）。今日 Tejun 应用到 `sched_ext/for-7.4`，移除 `Fixes` 标签、追加 Kuba 的 Reviewed-by。

## Maintainer 意见与讨论焦点
- **Tejun Heo**（sched_ext 维护者）：Applied 到 for-7.4（并决定去掉 Fixes 标签）。
- **Kuba Piecuch**：Reviewed-by。
- 无异议。

## 合入评估
*likelihood=merged*。已合入 `sched_ext/for-7.4`。*blocking_issues*：无。*next_action*：随 for-7.4 进入下个合并窗口。

## 效果评估
构建修复；修复后 gcc 16 下 `dequeue_remote` 自测可正常构建（无性能影响）。

## 我可以参与的点
当前阶段暂无明显参与空间（已合入）。

## 参考链接
- 补丁 lore：https://lore.kernel.org/all/20261012115928.1372317-1-smariotti@disroot.org/
- 合入回帖：https://lore.kernel.org/all/467bae1dc17e2d0a56e226f3c756fc0c@kernel.org/
