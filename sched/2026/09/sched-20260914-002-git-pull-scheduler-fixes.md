# [GIT PULL] scheduler fixes

## TL;DR
增量更新：pr-tracker-bot 回执确认 09-13 Ingo Molnar 发出的 `tip/sched/urgent` 拉取请求已被合入 torvalds/linux.git，合并 commit 为 `b2a8a7669e9befcec50fec990e1e1ee96f040cdf`。这是 sched-20260913-001 一直缺失的「进主线时点」，四条修复（两条 EEVDF augmented rbtree、两条 proxy execution 记账）正式从 tip 进入主线。

## 背景与问题
承 sched-20260913-001：Ingo 于 09-13 16:19（北京时间）向 Linus 发出 urgent pull（分支 `sched-urgent-2026-09-13`），内容为 4 条修复、2 位作者、3 files +46/-16。前文已判定 likelihood=merged、status=merged_tip，但当时缓存中**无 pr-tracker-bot 回执**，「进 Linus 树的合并 commit 与 -rc 归属未获取到」。今日回执补上了这一环节。

## 技术方案
无新代码。今日唯一内容是 pr-tracker-bot 的合并确认：回执引用 Linus 侧 pull 邮件（`aqZcjrj6NEVj6Vgq@gmail.com`，09-13 10:19:26 +0200），给出合并 commit 链接 `https://git.kernel.org/torvalds/c/b2a8a7669e9befcec50fec990e1e1ee96f040cdf`。

## 版本演进与当前进展
- 09-09/09-10：四条修复各自发出并被逐篇跟踪（sched-20260909-008、sched-20260910-004/005/016/017）。
- 09-13：Ingo 汇总拉取（sched-20260913-001）。
- 09-14（本文窗口）：pr-tracker-bot 确认合入 torvalds/linux.git，commit `b2a8a7669e9befcec50fec990e1e1ee96f040cdf`。

## Maintainer 意见与讨论焦点
本日无维护者技术意见，只有 bot 的合并通知。「被合入 torvalds/linux.git」即 Linus 接受该 pull 的事实信号。四条修复未再出现反对或保留意见。

## 合入评估
likelihood=merged（已成事实）：四条修复已进入主线。blocking_issues：无合入层面的卡点；四条修复各自的 stable 回合情况仍未获取到（邮件中未讨论）。next_action：按 commit 与内部分支/OLK 分支逐条比对回合状态；关注是否进入 stable 队列。

## 效果评估
无 benchmark 数据。可量化的是时间线：从最后一批修复（Hui Su 两条，09-10 发出）到进 tip 约 3 天，再到进主线约 5 天。收益属正确性一类（EEVDF 的 max_slice 与 augmented rbtree 重平衡不再出错；proxy execution 下 cgroup CPU 时间与 wq_worker_tick 记到执行上下文）。

## 我可以参与的点
- kind=new_patch：回合自查——四条修复与内部分支逐条比对。EEVDF 两条动了通用 `include/linux/rbtree_augmented.h`，凡内部分支改过 rbtree 或 fair.c 的都需留意 rebase 冲突；Hui Su 两条 proxy 记账修复若分支带 proxy execution 实验代码应同步口径。
- kind=testing：在 cgroup 压测场景验证 proxy execution 下 cpu.stat 归属是否与执行任务一致。

## 参考链接
- 合并回执（pr-tracker-bot）：https://lore.kernel.org/all/178932106844.3902938.1977938545599194021.pr-tracker-bot@kernel.org/
- 合并 commit：https://git.kernel.org/torvalds/c/b2a8a7669e9befcec50fec990e1e1ee96f040cdf

---
id: sched-20260914-002
date: '2026-09-14'
subject: '[GIT PULL] scheduler fixes'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: '<178932106844.3902938.1977938545599194021.pr-tracker-bot@kernel.org>'
lore_url: 'https://lore.kernel.org/all/178932106844.3902938.1977938545599194021.pr-tracker-bot@kernel.org/'
authors:
  - 'Ingo Molnar'
maintainers_involved:
  - 'Linus Torvalds'
current_version: null
patch_series: []
upstream_commit: 'b2a8a7669e9befcec50fec990e1e1ee96f040cdf'
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: merged
  blocking_issues:
    - '四条修复各自的 stable 回合情况未获取到'
  next_action: '按 commit 与内部分支逐条比对回合状态；跟踪是否进入 stable 队列'
contribution_opportunities:
  - kind: new_patch
    description: '回合自查：四条修复与内部分支逐条比对，EEVDF 两条动了通用 rbtree_augmented.h 注意 rebase 冲突'
  - kind: testing
    description: 'cgroup 压测验证 proxy execution 下 cpu.stat 归属与执行任务一致'
generated_at: '2026-09-15T09:30:00'
source_email_count: 1
related_articles:
  - 'sched-20260913-001'
  - 'sched-20260910-004'
  - 'sched-20260910-005'
  - 'sched-20260910-016'
  - 'sched-20260910-017'
tags:
  - eevdf
  - proxy_execution
  - cgroup
---