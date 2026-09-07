---
id: sched-20260902-001
date: '2026-09-02'
subject: Sleeping Owner Handling for Proxy Execution (v31)
subsystem: sched
type: feature
status: merged_tip
severity: medium
thread_root_msgid: null
lore_url: null
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: null
authors:
- John Stultz
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: merged
  blocking_issues:
  - 合入后外溢的上下文语义未收口：task_sched_runtime() 与 wq_worker_tick() 修正尚无维护者 ack
  - sched/cache 侧 donor 可能是 deadline 任务，execution context 归属未定
  next_action: 跟进 Hui Su 的 proxy execution 记账后续补丁，并验证 DL/RT 混跑场景
contribution_opportunities:
- 开 PROXY_EXEC 跑 mutex 争用 + RT/DL 混载，验证 donor 抢占保护与 blocked_on 迁移抑制
- '回帖接手 73775（sched/core: fix task_sched_runtime() for proxy execution），该补丁当天无人回应'
- 就 Tim Chen 提出的 deadline donor 场景给出结论与测试
source_email_count: 1
related_articles: []
tags:
- proxy_execution
- sched/core
title: Sleeping Owner Handling for Proxy Execution (v31)
layout: article
---

## TL;DR

PE（proxy execution，解决锁持有者优先级翻转）主线化的增量一批：09-02 有 6 个补丁进入
`tip/sched/core` 并拿到 commit hash，覆盖 sleeping owner 场景下的 donor 迁移与 donor 抢占保护。
合入本身没有争议，值得跟的是它的外溢——这批改动把「调度上下文 `rq->donor` / 执行上下文 `rq->curr`」
的分裂暴露到 runtime 记账、workqueue、sched/cache，9/2~9/3 已连续出现 3 个后续修正补丁。

## 背景与问题

Proxy Execution（PE，解决优先级翻转 / 锁持有者代理运行）在 09-02 有一批改动合入
`tip/sched/core`，是 PE 主线化进程的又一次重要推进。同日另有独立补丁
`sched/core: fix task_sched_runtime() for proxy execution`（UID 73816）也属该方向。

## 技术方案

- `sched: Migrate whole chain in proxy_migrate_task()`
- `sched: Switch rq->next_class in proxy_reset_donor()`
- `sched/core: Don't proxy-exec unmatched cookie lock owners`（UID 73210）
- `sched/core: Don't steal a proxy-exec donor`（UID 73240）
- `sched/core: Avoid migrating blocked_on tasks`（UID 73217）
- `sched: Break out core of attach_tasks() helper into sched.h`（UID 73236）
- `sched/core: fix task_sched_runtime() for proxy execution`（UID 73816，独立补丁）

## 版本演进与当前进展

- 当前状态：**merged_tip**（已进入 `tip/sched/core`，待后续合并窗口进入主线）。
- 合入可能性：**high/已合入**。
- 与 08-26 的「PROXY_EXEC 备选方案 RFC PoC（16 补丁）」是不同路线：本批是主线既有
  PE 实现的增量修复与清理，并非那套备选方案。

## Maintainer 意见与讨论焦点

- 维护者的结论体现在合入上：当天 15:54~15:55 tip-bot2 发了 6 条 `[tip: sched/core]` 通知，4 条署名
  John Stultz（772d9ffb `Migrate whole chain in proxy_migrate_task()`、6b73a09e `Break out core of
  attach_tasks()`、1f880513 `Switch rq->next_class in proxy_reset_donor()`、9be817f9 `Avoid migrating
  blocked_on tasks`），2 条署名 Vasily Gorbik（3dd95f07 `Don't steal a proxy-exec donor`、
  09351db9 `Don't proxy-exec unmatched cookie lock owners`）。v31 封面线程当天没有 reviewer 正文，未见 NAK。
- 真正的问题由第三方提出。Hui Su 连发三封补丁指向同一点："With proxy execution, rq->donor is the
  scheduling context while rq->curr is the execution context."（73775 `fix task_sched_runtime()`、
  74394 `Call wq_worker_tick() for the execution context`、74668 `Use execution context for cache task tick`）。
- sched/cache 侧 Tim Chen 认可方向但留下未决点（75219/75742）："I agree that the execution context
  should be handed to task_tick_cache(). However, the donor may be a deadline…"（缓存中截断）。

## 合入评估

**已合入** `tip/sched/core`（6 个补丁均有 Commit-ID）。卡点不在这批补丁本身，而在它们引发的下游修正：
Hui Su 的 `task_sched_runtime()`（73775）与 `wq_worker_tick()`（74394）当天/次日仍未拿到调度维护者 ack，
`Use execution context for cache task tick`（74668）还悬着 deadline donor 的问题。这批要在下一个合并窗口
才会随 tip 进主线。

## 效果评估

无线程内量化数据，这批是正确性修复而非优化。唯一的「效果」证据是反面：合入不到 4 小时，Hui Su 就报告
runtime 记账与 workqueue worker CPU 时间记账都取错了上下文（73775/74394），说明 PE 的上下文语义尚未在外围路径收敛。
作者对影响面的判断（记账错位）属定性描述，未见测试数据。

## 我可以参与的点

- 开 PROXY_EXEC 跑 mutex 争用 + RT/DL 混载，验证 `Don't steal a proxy-exec donor` 与
  `Avoid migrating blocked_on tasks` 是否影响 DL 任务的 bandwidth/zero-lag timer。
- 接手 73775：该补丁当天零回帖，是唯一一个没人理的 PE 后续修正。
- 回答 Tim Chen 留下的 deadline donor 问题——`account_mm_sched()` 在 donor 是 DL 任务时该记到谁头上。

## 参考链接

- 08-26 007 PROXY_EXEC 备选方案 RFC PoC（不同路线）
