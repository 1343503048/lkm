---
id: sched-20260819-002
date: 2026-08-19
subsystem: sched
type: discussion
status: under_review
severity: high
thread_root_msgid: "<unknown>"
lore_url: "未获取到"
authors: [Aaron Lu, Peter Zijlstra, K Prateek Nayak]
maintainers_involved: [Peter Zijlstra]
current_version: v1
patch_series:
  - version: v1
    msgid: "<unknown>"
    date: 2026-08-19
    summary: "Peter 在 8/19 回复 Aaron Lu 7/2 报告的 core_sched pick_task() 竞态：pick_task() 释放 core-wide 锁后未触发 RETRY_TASK 而继续，导致 rqX->core_pick 被对端置 NULL 后 NULL 解引用。Peter 倾向在 pick 时取本地 core_task_seq 副本、末尾校验，但仍担心活锁；并点出 sched_ext 让问题更复杂（引用 8/19 另一封 sched_ext 邮件 [1]）。"
    review_outcome: "讨论中，尚无合入补丁；Peter 自述 'Only bad ideas so far'，需先理清 core-sched 与 sched_ext 的交互。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["缺乏带前进进度保证的修复（RETRY_TASK 重做有活锁风险）", "sched_ext 参与 pick 使 core-sched 的锁中断语义更复杂"]
  next_action: "Peter 表示需进一步研究，可能等其休假回来后再推进；需限定 lock-break/newidle 调用次数以提供前进保证。"
contribution_opportunities:
  - kind: discussion
    description: "可帮忙构造一个最小化复现/syzkaller 用例，或分析如何用 core_task_seq 本地副本 + 有限次重试消除活锁担忧。"
generated_at: "2026-08-20T00:30:00"
source_email_count: 3
related_articles: ["sched-20260817-001", "sched-20260818-001", "sched-20260818-002"]
tags: [core_sched, sched/core, crash, proxy_execution]
---

## TL;DR
core_sched 在 `pick_task()` 释放 core-wide 锁后未触发 `RETRY_TASK` 而继续，造成 `rqX->core_pick` 被对端置 NULL 后空指针解引用。Peter 8/19 回复承认这是个漂亮竞态，但尚无好修复，且 sched_ext 参与让问题更复杂。属于 08-17→08-18 core_sched/proxy_exec 讨论线的延续。

## 背景与问题
Aaron Lu 7/2 报告：假设 cpuX/cpuY 是兄弟核，core-sched 下 `pick_next_task()` → `pick_task(rqY)` → `sched_balance_newidle(rqY)` 释放 core 锁后，对端 cpuY 也进入 `pick_next_task()` 并把 `rqX->core_pick` 因 `rqX->curr == rqX->core_pick` 置 NULL；锁收回后 cpuX 拿到 `p = rqX->core_pick == NULL`，`cookie_equals(p, cookie)` 空解引用。

## 技术方案
Peter 的初步想法：在 pick 时取 `core_task_seq` 的本地副本，末尾双重校验仍有效则继续，否则 restart。但此方案对活锁敏感、无前进进度保证；需要限制 lock-break / newidle 调用次数才能有保证。Prateek 也指出：在 core cookie 最终确定前做 balance 可能把任务错移到别的 core 上白等；一切释放 core-wide 锁的操作都应在单条 core-wide 锁临界区内 RETRY_TASK 重做。

## 版本演进与当前进展
- 7/2 Aaron Lu 报告竞态，附完整两核交错时序。
- 7/3 Prateek 质疑在 pick 内做 balance 的正确性，并对 core-sched 用 RETRY_TASK 存疑。
- 8/19 Peter 回复：承认竞态真实（lock-break 未触发 RETRY_TASK 而继续），初步修复有活锁风险；并点出 "the whole sched_ext thing [1] makes it more complicated than I'd like"。

## Maintainer 意见与讨论焦点
分歧/未决点：
- 修复必须提供前进进度保证（活锁风险未解）。
- sched_ext 现在也参与 pick，使 core-sched 锁中断语义更复杂，Peter 明确把 [1]（8/19 的 sched_ext 邮件）列为额外复杂度来源。
- 尚无 NAK，但 Peter 自述 "Only bad ideas so far"，说明方案尚未成形。

## 合入评估
合入可能性 medium：问题明确、严重（NULL 解引用），但修复设计悬而未决，且被 sched_ext 耦合放大。短到中期难有补丁落地，需 Peter 进一步研究（可能等休假后）。

## 效果评估
暂无效果数据（属正确性问题讨论，非性能优化）。

## 我可以参与的点
- 构造最小复现或 syzkaller 用例，帮助稳定触发竞态以验证未来补丁。
- 分析 `core_task_seq` 本地副本 + 有限重试能否消除活锁担忧，回帖补充。

## 参考链接
- lore thread: 未获取到
- Peter 引用的 [1] sched_ext 邮件（2026-08-19）: 未获取到具体 URL
