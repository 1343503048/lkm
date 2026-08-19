# sched_ext: Drop the dead SCX_DEQ_CORE_SCHED_EXEC test in dequeue_task_scx()

## TL;DR
Tejun Heo 的 4-patch 系列修正在 `sched_ext` core-sched 任务排序的实现：修复 `ops.core_sched_before()` 被倒置调用的 bug（`Fixes: 7b0888b7cc19`，stable v6.12+）、用 `p->scx.runnable_at` 统一等待追踪、让跨两个调度器的任务对按最近公共祖先排序、删除 dequeue 路径里已死的 `SCX_DEQ_CORE_SCHED_EXEC` 测试。已全部 apply 到 `sched_ext/for-7.3`。

## 背景与问题
core-sched 任务排序（用于 SMT 兄弟核上按信任/优先级决定谁先跑）早于 sub-scheduler 出现。原实现有多处缺陷：
1. `scx_prio_less()` 返回 `@a 是否应后跑`，而 `ops.core_sched_before()` 文档约定返回`@a 是否应先跑`——两者语义相反，但 `scx_prio_less()` 把 op 返回值原样返回，**运行时把文档语义反转了**。
2. `core_sched_at` 时间戳兜底在两种不同"stamp 规则"下维护，fallback 不统一。
3. 跨调度器（sub-scheduler）的任务对排序未考虑层级，仅当两任务同属一个调度器才查 `ops.core_sched_before()`。
4. dequeue 路径保留了一个已死的 `SCX_DEQ_CORE_SCHED_EXEC` 测试。

## 技术方案
- patch 1：`scx_prio_less()` 调用 `ops.core_sched_before()` 时交换 a/b 参数，修正倒置语义。`scx_qmap` 此前照"接线"而非文档返回年轻任务为 true，两个反转抵消，现翻转其比较以匹配文档（作者提示 scx_qmap 可能是树内/外唯一用户，按同法翻写的调度器需同步翻转；按文档写的调度器本补丁直接修好）。`Fixes: 7b0888b7cc19`，`Cc: stable@vger.kernel.org # v6.12+`。
- patch 2：用 stall watchdog 已维护的 `p->scx.runnable_at` 替代 `core_sched_at` 作为 fallback 时间戳，统一为单一"等待追踪"规则（运行中的任务排序在所有等待任务之后）。
- patch 3：跨两调度器的任务对，按"最近公共祖先调度器"实现的 `ops.core_sched_before()` 排序，使层级-aware。
- patch 4：删除 dequeue 路径中已死的 `SCX_DEQ_CORE_SCHED_EXEC` 测试。
diffstat：ext.h -3 / ext.c +147/-97 / internal.h +5 / scx_qmap.bpf.c +23/-2。

## 版本演进与当前进展
v1（4 patch，cover 41872）于 2026-08-16 发出，基于 `sched_ext/for-7.3 (3167bd3e0c22)`，git 分支 `core-sched-hier`。Tejun 当日回复 "Applied 1-4 to sched_ext/for-7.3"，并说明这些补丁在"堵 sub-scheduler 支持的明显漏洞"，希望在合并窗口前把支持做得比较完整，且 blast radius 有限，review 意见以 follow-up 处理。

## Maintainer 意见与讨论焦点
- Tejun Heo（作者即维护者）：直接 apply 全部 4 个，强调合并窗口前补齐、影响面小。

## 合入评估
已合入 `sched_ext/for-7.3`。patch 1 带 `Fixes` + stable，属正确性修复，预期随 7.3 进入主线并回合 stable。

## 效果评估
修复 core-sched 排序倒置（正确性 bug，影响 SMT 上按信任度排序的正确性）；统一等待追踪与层级-aware 排序改善 sub-scheduler 场景公平性。无基准数据。

## 我可以参与的点
- 复核第三方 BPF 调度器是否因 `ops.core_sched_before` 语义反转需同步翻转比较（已按"文档"写的不受影响，按"接线"抄 scx_qmap 的需要翻）。

## 参考链接
- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
subject: "sched_ext: Drop the dead SCX_DEQ_CORE_SCHED_EXEC test in dequeue_task_scx()"
id: sched-20260816-002
date: 2026-08-16
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: "<uid-41872@qq-imap>"
lore_url: "未获取到"
authors: [Tejun Heo]
maintainers_involved: [Tejun Heo]
current_version: v1
patch_series:
  - version: v1
    msgid: "<uid-41872@qq-imap>"
    date: 2026-08-16
    summary: "4 patch 修复 sched_ext core-sched 任务排序：倒置的 ops.core_sched_before 调用、用 runnable_at 统一等待追踪、跨调度器层级排序、删除死测试。"
    review_outcome: "Tejun 已 apply 1-4 到 sched_ext/for-7.3（合并窗口前补齐 sub-scheduler 支持）。"
upstream_commit: null
fixes_commit: "7b0888b7cc19 (sched_ext: Implement core-sched support)"
merged_branch: "sched_ext/for-7.3"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已合入；如有 review 点 Tejun 会以 follow-up 处理。"
contribution_opportunities:
  - kind: review
    description: "可复核 scx_qmap 之外的第三方 BPF 调度器是否因 ops.core_sched_before 语义反转需同步翻转比较（作者提示仅 scx_qmap 已知受影响）。"
generated_at: "2026-08-17T00:10:00"
source_email_count: 6
related_articles: [sched-20260816-003]
tags: [sched_ext, core_sched]
---
