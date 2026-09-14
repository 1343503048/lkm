---
id: sched-20260913-001
date: 2026-09-13
subject: '[GIT PULL] scheduler fixes'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <aqZcjrj6NEVj6Vgq@gmail.com>
lore_url: https://lore.kernel.org/all/aqZcjrj6NEVj6Vgq@gmail.com/
upstream_commit: null
fixes_commit: null
merged_branch: tip/sched/urgent（sched-urgent-2026-09-13）
current_version: v1
generated_at: '2026-09-14T10:24:00'
authors:
- Ingo Molnar
maintainers_involved:
- Ingo Molnar
patch_series:
- version: v1
  msgid: <aqZcjrj6NEVj6Vgq@gmail.com>
  date: 2026-09-13
  summary: Ingo 向 Linus 拉取 tip/sched/urgent（sched-urgent-2026-09-13，顶端 f5741d2b34519d387edf6e9798fc7030c20a35f3）：4
    条修复、2 位作者、3 files +46/-16。Vincent Guittot 两条 EEVDF augmented rbtree 修复（max_slice
    入队取值、多字段重平衡）与 Hui Su 两条 proxy execution 执行上下文记账修复（cgroup CPU 时间、wq_worker_tick）。逐条细节见
    related_articles。
  review_outcome: 无讨论回帖；四条均为 09-09/09-10 已跟踪系列的合入节点，进 tip 后各自系列状态从 under_review 变为
    merged_tip。
merge_assessment:
  likelihood: merged
  blocking_issues:
  - 无：四条修复已进 tip/sched/urgent
  - 进 Linus 树的合并 commit 与 -rc 归属未获取到（本日无 pr-tracker-bot 回执）
  - 四条修复各自的 stable 回合情况未获取到
  next_action: 跟踪 pr-tracker-bot 合并回执确认进主线时点；按 commit 与内部分支逐条比对回合状态
contribution_opportunities:
- kind: new_patch
  description: 回合自查：四条修复与内部分支逐条比对；EEVDF 两条动了通用 include/linux/rbtree_augmented.h，注意
    rebase 冲突面
- kind: testing
  description: 在 cgroup 压测场景验证 proxy execution 下 cgroup CPU 时间记账口径（cpu.stat 归属）与执行任务的一致性
source_email_count: 1
related_articles:
- sched-20260910-004
- sched-20260910-005
- sched-20260910-016
- sched-20260910-017
tags:
- eevdf
- proxy_execution
- cgroup
title: '[GIT PULL] scheduler fixes'
layout: article
---

## TL;DR
Ingo Molnar 于 09-13 16:19（北京时间）向 Linus 发出 `tip/sched/urgent` 拉取请求（分支 `sched-urgent-2026-09-13`，顶端 f5741d2b34519d387edf6e9798fc7030c20a35f3），共 4 条修复、2 位作者、3 个文件 +46/-16：Vincent Guittot 的两条 EEVDF augmented rbtree 修复与 Hui Su 的两条 proxy execution 执行上下文记账修复。四条全部是本报 09-09/09-10 跟踪过的系列（见 related_articles），本文是它们的合入节点：从「评审中」正式变为「已进 tip」。

## 背景与问题
拉取内容与此前跟踪的对应关系：

- **sched/eevdf: Fix augmented max_slice**（Vincent Guittot）——修正入队时 `se->max_slice` 的取值，对应 sched-20260910-005。
- **sched/eevdf: Fix rb augmented with multi fields**（Vincent Guittot）——修正 EEVDF 多字段 augmented rbtree 的重平衡，对应 sched-20260909-008 与 sched-20260910-004。
- **sched: Account cgroup CPU time to the execution context**（Hui Su）——proxy execution 下 cgroup CPU 时间记到执行上下文而非调度上下文，对应 sched-20260910-016。
- **sched/core: Call wq_worker_tick() for the execution context**（Hui Su）——wq worker tick 同样跟随执行上下文，对应 sched-20260910-017。

本日邮件本身是 pull request 正文，不含新讨论；「背景」在这里是身份变化：这批修复此前只存在于评审线程，现在进入了 `tip/sched/urgent` 的祖先图，成为下游分支（内部分支、stable 回合队列）可以据此对齐的事实。

## 技术方案
无新代码。从 diffstat 可以确认两点事实：`include/linux/rbtree_augmented.h | 35 +++---` 说明 Guittot 的第二条修复动的是通用 augmented rbtree 重平衡基础设施（不只是 sched 私有代码），`kernel/sched/core.c | 9 +-` 是 Hui Su 两条 proxy 记账修复的全部落点，`kernel/sched/fair.c | 18 ++++++--` 承载 EEVDF 两条修复的调度侧改动。合计 3 files changed, 46 insertions(+), 16 deletions(-)。

## 版本演进与当前进展
本 pull 是这四条修复共同的时间节点，时间线：

- 09-09/09-10：Guittot 两条 EEVDF 修复与 Hui Su 两条 proxy 记账修复发出并被本报逐篇跟踪（sched-20260909-008、sched-20260910-004/005/016/017）。
- 09-13 16:19（北京时间）：Ingo 汇总拉取，短句描述四条修复，按「EEVDF 两条在前、Hui Su 两条在后」排列，未附加任何评审说明。
- 进 Linus 树的时点：本日缓存中没有 pr-tracker-bot 回执，未获取到。

## Maintainer 意见与讨论焦点
线程内没有其他回帖，只有 Ingo 的 pull request 本身——这正是 urgent pull 的正常形态。可读出的信号：

- 四条修复被 Ingo 归为同一批「Miscellaneous scheduler fixes」，其中 EEVDF 两条排在前两位，说明在他的排序里 augmented rbtree 的正确性优先级更高；
- Hui Su 两条 proxy execution 记账修复从「作者 09-10 发出」到「09-13 进 tip」只隔了约 3 天，且与 EEVDF 修复同批拉取，proxy execution 的记账口径修正已被维护者当作 -rc 期间的 urgent 修复对待；
- 本日无任何反对或保留意见出现在 pull 正文里。

## 合入评估
likelihood=merged（已成事实）：`status=merged_tip`，合入分支 `tip/sched/urgent`（`sched-urgent-2026-09-13`，顶端 f5741d2b34519d387edf6e9798fc7030c20a35f3）。blocking_issues：落到 Linus 树的合并 commit 与 -rc 归属未获取到（本日无 pr-tracker-bot 回执）；四条修复各自的 stable 回合情况未获取到。next_action：跟踪 pr-tracker-bot 的合并回执确认进主线时点；之后按 commit 与内部分支/OLK 分支逐条比对回合状态。

## 效果评估
pull request 无 benchmark 数据。可量化信息是规模与时延：4 条修复、3 个文件、+46/-16，从最后一批（Hui Su 两条，09-10 发出）到进 tip 约 3 天。收益属正确性一类：EEVDF 的 `max_slice` 与 augmented rbtree 重平衡不再出错；proxy execution 下 cgroup CPU 时间与 wq worker tick 记到真正执行的上下文。

## 我可以参与的点
- 回合自查（new_patch）：四条修复与内部分支逐条比对是否已带。EEVDF 两条动了通用 `include/linux/rbtree_augmented.h`，凡在内部分支改过 rbtree 或 fair.c 的都要留意 rebase 冲突；Hui Su 两条 proxy 记账修复若分支带 proxy execution 实验代码则应同步口径。
- cpuset/cgroup 视角验证（testing）：`sched: Account cgroup CPU time to the execution context` 直接影响 proxy execution 下 cgroup CPU 统计口径，值得在 cgroup 压测场景确认 cpu.stat 与实际执行任务的归属一致性。

## 参考链接
- 本日 pull request: https://lore.kernel.org/all/aqZcjrj6NEVj6Vgq@gmail.com/
- 相关文章/系列：
  - [[sched-20260910-004]] sched/eevdf: Fix rb augmented with multi fields
  - [[sched-20260910-005]] sched/eevdf: Fix augmented max_slice
  - [[sched-20260910-016]] sched: Account cgroup CPU time to the execution context
  - [[sched-20260910-017]] sched/core: Call wq_worker_tick() for the execution context
- 进 Linus 树的合并点: 未获取到（无 pr-tracker-bot 回执）
- stable backport: 未获取到
