# sched_ext: Fix stale pick when a wakeup resets the donor during dispatch

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261030-009：Tejun Heo 修 sched_ext 在 proxy execution 下的 stale pick 缺陷——`do_pick_task_scx()` 把 `rq->donor` 作为 `@prev` 传给 `dispatch_one()`，但 dispatch 释放 rq lock 期间 donor 可能被唤醒并迁移走，导致 verdict 描述的是旧 donor。v1 修法是 `@prev` 不再是 donor 时 `SCX_DSP_RETRY` 重试 pick（`+10/-0`，`Fixes: c6fe97c34a1a`）。
- sched-20261031-003（今天）：v2/v3 连发——v2 按 Sashiko 意见把重试逻辑扩展到 dispatch 内部每次 rq lock drop 之后，v3 再按 Sashiko 意见「`ops.dispatch()` 之后不得保留陈旧 `@prev`」。Andrea Righi 审 v3 后给 **Reviewed-by**，同时把 Sashiko 提出的 `dl_server` 问题定性为「独立的 core 调度器 bug，应另行处理」。

## 背景与问题
（承接 sched-20261030-009）proxy execution 下 `rq->donor` 与 `rq->curr` 分离，`dispatch_one()` 为跨 CPU 移任务会多次释放 rq lock，期间 donor 可被唤醒迁移（`proxy_needs_return()` 将其 dequeue 并重置 donor 为 `rq->curr`）。v1 只在 `dispatch_one()` **返回后**重试，但 Sashiko 指出这个检查来得太晚——`dispatch_one()` 内部第一次 drop 后到返回之间，`update_curr_scx(rq)` 已可能作用在**新** donor 而非 ext 任务上。今日 v2/v3 把重试判断内推到每个 lock drop 之后。

## 技术方案
（承接 v1，今日为 v2/v3）核心仍是在 `@prev` 不再是 donor 时 `SCX_DSP_RETRY` 重试 pick，但覆盖范围逐步扩大：

- v2：`dispatch_one()` 在每个可能 drop 锁的步骤之后都校验 `@prev` 是否仍是 donor（回应 Sashiko「检查来的太晚」）。
- v3：`scx_dispatch_sched()` 按 `ops.dispatch()` 的每次调用来决定是否交还 `@prev`，覆盖「跨 drop 的调度类或调度器变更」，并确保 `ops.dispatch()` 之后不保留陈旧 `@prev`。

donor 在 pick 期间只会变到 `rq->curr`，因此重试后的 pick 不会再陈旧。

## 版本演进与当前进展
*current_version: v3*。

- v1（2026-10-30，`<20261030142338.3453484-1-tj@kernel.org>`）：仅在 `dispatch_one()` 返回后重试。
- v2（2026-10-31，`<20261030235728.4098872-1-tj@kernel.org>`）：回应 Sashiko「检查太晚」——覆盖 dispatch 内 lock drop。
- v3（2026-10-31，`<20261031015414.219280-1-tj@kernel.org>`）：回应 Sashiko「`ops.dispatch()` 之后不得保留陈旧 @prev」。获 Andrea Righi Reviewed-by。

## Maintainer 意见与讨论焦点
- **Andrea Righi（sched_ext co-maintainer）**：审 v3 给 Reviewed-by；确认 Sashiko 的 dl_server 发现有效，但为「独立 core 调度器 bug，应另行处理」（即今日 002 篇所记 dl_server 报告）。
- 无 NAK；v1 阶段 Sashiko 的两点意见（检查太晚、保留陈旧 @prev）已被 v2/v3 逐条消化。

## 合入评估
*likelihood=high*。co-maintainer 已在 v3 上 Reviewed-by、`Fixes:` 明确、改动聚焦 `sched_ext/for-7.4-fixes` 分支，属 v7.4 修复窗口常规收取。*blocking_issues*：暂无实质阻塞。*next_action*：合入 `sched_ext/for-7.4-fixes`。

## 效果评估
作者标注「Verified with a synthetic reproducer」，未给出具体性能数字或复现脚本全文；dl_server 侧问题（独立 bug）当前无运行时副作用数据。

## 我可以参与的点
- **testing**：在 proxy execution + sched_ext 下复跑「dispatch 期间 donor 被唤醒迁移」场景，验证 v3 后不再跨 rq 误跑、无 `SCX_OPS_ENQ_LAST` 警告。
- **review**：核对 dispatch 内每处 lock drop 后的重试是否覆盖完整、有无遗漏路径引入活锁。

## 参考链接
- lore thread（v1）: https://lore.kernel.org/all/20261030142338.3453484-1-tj@kernel.org/
- v3: https://lore.kernel.org/all/20261031015414.219280-1-tj@kernel.org/

---
id: sched-20261031-003
date: 2026-10-31
subject: "sched_ext: Fix stale pick when a wakeup resets the donor during dispatch"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261030142338.3453484-1-tj@kernel.org>"
lore_url: "https://lore.kernel.org/all/20261030142338.3453484-1-tj@kernel.org/"
authors: [Tejun Heo]
maintainers_involved: [Andrea Righi]
current_version: v3
patch_series:
  - version: v1
    msgid: "<20261030142338.3453484-1-tj@kernel.org>"
    date: 2026-10-30
    summary: "dispatch_one() 返回后发现 @prev 非 donor 则 SCX_DSP_RETRY 重试"
    review_outcome: "Sashiko 提出检查太晚、ops.dispatch() 后保留陈旧 @prev"
  - version: v2
    msgid: "<20261030235728.4098872-1-tj@kernel.org>"
    date: 2026-10-31
    summary: "把重试判断扩展到 dispatch 内每次 rq lock drop 之后"
    review_outcome: "回应 Sashiko「检查太晚」"
  - version: v3
    msgid: "<20261031015414.219280-1-tj@kernel.org>"
    date: 2026-10-31
    summary: "scx_dispatch_sched() 按 ops.dispatch() 每次调用决定是否交还 @prev，不保留陈旧 @prev"
    review_outcome: "Andrea Righi Reviewed-by"
upstream_commit: null
fixes_commit: c6fe97c34a1a
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "合入 sched_ext/for-7.4-fixes"
contribution_opportunities:
  - kind: testing
    description: "proxy execution + sched_ext 下复跑 dispatch 期间 donor 被唤醒迁移，验证 v3 后无跨 rq 误跑"
  - kind: review
    description: "核对 dispatch 内每处 lock drop 后的重试覆盖是否完整、有无活锁风险"
generated_at: "2026-11-01T09:00:00"
source_email_count: 4
related_articles: [sched-20261030-009]
tags: [sched_ext, proxy_execution]
---