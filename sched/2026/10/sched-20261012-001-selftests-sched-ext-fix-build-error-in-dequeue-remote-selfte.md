# selftests/sched_ext: Fix build error in dequeue_remote selftest

## TL;DR

sched_ext 自测用例 `dequeue_remote` 在较新编译器（如 gcc 16）下因 `sum` 变量「set but not used」触发构建错误，作者用一个空 `asm()` 消费该变量，与既有 `dequeue` 自测的修法一致；当日 Kuba Piecuch 已 `Reviewed-by`，改动很小、合入阻力低。

## 背景与问题

用 gcc 16 等较新编译器构建 `tools/testing/selftests/sched_ext/dequeue_remote.c` 报错 `dequeue_remote.c:39:32: error: variable ‘sum’ set but not used`。`volatile` 限定只能防写操作被优化掉，无法消除「只写不读」的告警——`sum` 的写操作确实从未被读取。

## 技术方案

与 commit 3788e3251653（"selftests/sched_ext: Fix build error in dequeue selftest"）对 `dequeue` 自测的修法一致：在累加循环后加一行 `asm volatile("" : : "r"(sum));`，用寄存器输入约束迫使编译器保留累计值（保住 CPU 压测循环），同时消除构建告警。单文件 +1 行。

## 版本演进与当前进展

v1 当日新发（2026-10-12）。Kuba Piecuch（sched_ext selftest 评审者）同日回帖 `Reviewed-by: Kuba Piecuch`（"LGTM, thank you Samuele!"），无异议。

## Maintainer 意见与讨论焦点

Kuba Piecuch 直接 `Reviewed-by`，无争议点。selftest 类修复通常由 sched_ext 维护者径收集取。

## 合入评估

*likelihood=high*。改动 +1 行、有 `Reviewed-by`、`Fixes:` 指向引入该自测的 commit cc07fae1de5d。*blocking_issues*：无。*next_action*：等维护者收取合入 sched_ext 分支。

## 效果评估

暂无性能数据（纯构建修复）。作者未给量化说明，仅说明可消除 gcc16 下的构建错误。

## 我可以参与的点

改动过小且已 R-b，当前阶段暂无明显参与空间，持续观察即可。

## 参考链接

- lore（本补丁）: https://lore.kernel.org/all/20261012115928.1372317-1-smariotti@disroot.org/
- lore（Kuba Reviewed-by）: https://lore.kernel.org/all/DM2W05XKJT97.2ATHPA28J84ZH@google.com/

---
id: sched-20261012-001
date: '2026-10-12'
subject: 'selftests/sched_ext: Fix build error in dequeue_remote selftest'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261012115928.1372317-1-smariotti@disroot.org>
lore_url: https://lore.kernel.org/all/20261012115928.1372317-1-smariotti@disroot.org/
authors:
- Samuele Mariotti
maintainers_involved:
- Kuba Piecuch
current_version: v1
patch_series:
- version: v1
  msgid: <20261012115928.1372317-1-smariotti@disroot.org>
  date: '2026-10-12'
  summary: 用空 asm() 消费 sum 变量，消除 gcc16 的 set-but-not-used 构建错误
  review_outcome: Kuba Piecuch 给出 Reviewed-by（LGTM）
fixes_commit: cc07fae1de5d
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等 sched_ext 维护者（Tejun/David）收取合入 sched_ext 分支，基本无阻
contribution_opportunities: []
generated_at: '2026-10-13T01:40:00'
source_email_count: 2
related_articles: []
tags:
- sched_ext
---
