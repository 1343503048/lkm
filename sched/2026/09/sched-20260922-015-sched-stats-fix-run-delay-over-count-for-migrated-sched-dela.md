# sched/stats: Fix run_delay over-count for migrated sched_delayed tasks

## TL;DR
本文为增量更新，完整背景见 sched-20260921-006（v2）。Wei Yang 发出 v3：新增收集 Kayra Cizmeci、K Prateek Nayak 的 Reviewed-by 与 K Prateek 的 Tested-by。Peter Zijlstra 回帖提出新问题——proxy execution 是否存在同类 over-count（是否该用 `t->is_blocked` 判断更合适）。补丁本身已集齐多组 review/test，合入概率高，但 Peter 的问题待回应。

## 背景与问题
背景见 sched-20260921-006：DELAY_DEQUEUE 下被迁移的 sched_delayed 任务，`sched_info_enqueue()` 在迁移时错误重挂 `last_queued`，导致真实唤醒时被抑制，整段「迁移→唤醒」睡眠时长被计入 run_delay。

## 技术方案
方案见 sched-20260921-006：`sched_info_enqueue()` 对 sched_delayed 任务不重挂 `last_queued`（唤醒路径清掉 sched_delayed 后才到该函数，故真实唤醒仍正确重挂，普通 runnable 任务不受影响）。

## 版本演进与当前进展
- v3（`<20260922082432.2987855-1-albin_yang@163.com>`）：新增 Kayra Cizmeci 与 K Prateek Nayak 的 Reviewed-by、K Prateek 的 Tested-by。
- v2：修正负载均衡描述（sched_delayed 任务其实不排斥主动负载均衡），收 Chen Yu Reviewed-by。
- v1：初版。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**：新问题——「Will we not have a similar problem with proxy exec? That is, would `t->is_blocked` be more appropriate?」，暗示 proxy execution 场景下可能有同类 run_delay 记账偏差，需澄清判定条件。
- 无反对意见；已有多位 reviewer/tested（Chen Yu、Kayra、K Prateek）。

## 合入评估
likelihood=high。补丁修正路径清晰、多组 review/test 已到位；唯一待办是回应 Peter 关于 proxy exec 场景的疑问。blocking_issues：Peter 的 proxy exec 同类问题未回应。next_action：作者澄清 proxy exec 场景（是否 `is_blocked` 更合适），随后可合。

## 效果评估
无本日新增 benchmark；为统计记账正确性修复（详见 sched-20260921-006）。

## 我可以参与的点
- **review**：分析 Peter 提出的 proxy exec 场景——`t->is_blocked` 与 `sched_delayed` 在 run_delay 记账上的差异，帮助作者判断判定条件。
- **testing**：验证 DELAY_DEQUEUE + proxy execution 组合下的 run_delay 数值。

## 参考链接
- lore（v3）: https://lore.kernel.org/all/20260922082432.2987855-1-albin_yang@163.com/
- Peter 回复: https://lore.kernel.org/all/20260922105522.GO1837346@noisy.programming.kicks-ass.net/

---
id: sched-20260922-015
date: '2026-09-22'
subject: 'sched/stats: Fix run_delay over-count for migrated sched_delayed tasks'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260922082432.2987855-1-albin_yang@163.com>'
lore_url: 'https://lore.kernel.org/all/20260922082432.2987855-1-albin_yang@163.com/'
authors:
  - 'Wei Yang'
maintainers_involved:
  - 'Peter Zijlstra'
current_version: v3
patch_series:
  - version: v1
    msgid: null
    date: '2026-09-09'
    summary: '初版'
    review_outcome: '未获取到 v1 原帖细节'
  - version: v2
    msgid: '<20260920043116.1298017-1-albin_yang@163.com>'
    date: '2026-09-20'
    summary: '修正负载均衡描述，收 Chen Yu Reviewed-by'
    review_outcome: '见 sched-20260921-006'
  - version: v3
    msgid: '<20260922082432.2987855-1-albin_yang@163.com>'
    date: '2026-09-22'
    summary: '收集 Kayra、K Prateek Reviewed-by 与 K Prateek Tested-by'
    review_outcome: 'Peter 提出 proxy exec 同类问题待回应'
upstream_commit: null
fixes_commit: '152e11f6df29'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - 'Peter 的 proxy exec 同类问题未回应'
  next_action: '作者澄清 proxy exec 场景（is_blocked vs sched_delayed）后合入'
contribution_opportunities:
  - kind: review
    description: '分析 t->is_blocked 与 sched_delayed 在 run_delay 记账上的差异'
  - kind: testing
    description: '验证 DELAY_DEQUEUE + proxy execution 组合下的 run_delay 数值'
generated_at: '2026-09-23T00:00:00'
source_email_count: 2
related_articles:
  - sched-20260921-006
tags:
  - cfs
  - sched_debug
---