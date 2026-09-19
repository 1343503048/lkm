---
id: sched-20260919-012
date: '2026-09-19'
subject: 'sched/proxy_exec: detect cycles without persistent walk state'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20260914165455.2126134-1-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20260914165455.2126134-1-sh_def@163.com/
authors:
- Hui Su
maintainers_involved: []
current_version: v1
patch_series:
- version: RFC 0/1
  msgid: <20260914165455.2126134-1-sh_def@163.com>
  date: '2026-09-14'
  summary: Brent 环检测，无持久 walk 状态
  review_outcome: 见 sched-20260915-009；本日作者补 tip/sched/core 追加验证
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - RFC 阶段，无维护者对环检测方案的反馈
  next_action: 等待 proxy execution 维护者评估方案与追加验证
contribution_opportunities:
- kind: review
  description: 评估 backlink 环不逃逸的控制流论断在复杂交织下的成立性
- kind: testing
  description: 在 PE 深度 owner 变更负载下复现并验证环检测
generated_at: '2026-09-20T09:00:00'
source_email_count: 1
related_articles:
- sched-20260915-009
tags:
- proxy_execution
title: 'sched/proxy_exec: detect cycles without persistent walk state'
layout: article
---

## TL;DR
增量更新：Hui Su 的 proxy execution 环检测 RFC（Online Brent，无持久 walk 状态）本日由作者贴出对 tip/sched/core（`e81ee0630837`）的追加验证——针对 `772d9ffbfd26`（"sched: Migrate whole chain in proxy_migrate_task()"）引入的 `p->blocked_donor` 直接遍历，作者用只读插桩在深链/跨 CPU 环/对象复用/KCSAN 等用例下未观测到逃逸进迁移路径的临时 backlink 环。仍为 RFC，无维护者表态。

## 背景与问题
背景见 sched-20260915-009：proxy execution 的 proxy walk 检测 donor 环通常需要持久化 walk 状态；RFC 用 Brent 环检测在无持久状态的情况下探测环。近期 `772d9ffbfd26` 让 `proxy_migrate_task()` 直接遍历 `p->blocked_donor`，成为 RFC 提到的"临时 backlink 环"最重要的当前消费者，作者因此做了追加验证。

## 技术方案
见 sched-20260915-009：Brent 环检测（checkpoint/power/span 三段状态完全属单次 `find_proxy_task()` 调用）。本日验证方式为 validation-only 的只读插桩——在 `proxy_migrate_task()` 入口检查已建 backlink 前缀，但不修复/截断/改动生产迁移路径。

## 版本演进与当前进展
- RFC 0/1（2026-09-14，`<20260914165455.2126134-1-sh_def@163.com>`）：环检测方案（见 sched-20260915-009）。
- 本日作者回帖（`<77591907f579598e5cf293e2ac03682a.sh_def@163.com>`）追加 tip/sched/core 上与 `proxy_migrate_task()` 相关的验证数据。

## Maintainer 意见与讨论焦点
本日无维护者表态，为作者的追加验证。作者的控制流论断：remote-owner 迁移前 `find_proxy_task()` 尚未为该 owner 边安装 backlink，故 `proxy_migrate_task()` 看到的是由当前 donor 构建的有限前缀；一旦本地 backlink 环可闭合，这些 owner 已在持 rq 锁时通过 same-rq 校验。作者也自我限定"这不能证明所有可能的 owner 变更交织"。

## 合入评估
likelihood=unknown。仍为 RFC，本日仅有作者追加验证，无维护者评论，证据不足以判断合入可能性。blocking_issues：RFC 阶段、无维护者对环检测方案的反馈。next_action：等待 proxy execution 相关维护者/社区对 RFC 方案与追加验证的评估。

## 效果评估
作者在 tip/sched/core `e81ee0630837` 上的插桩结果：非环 depth-1024 用例 2921/2921 次全链迁移完成、最大 backlink 前缀 1016 个任务；`curr_in_chain`/current-task 保护被触发 959 次且无 current task 进入迁移前缀；同对象复用 100 轮 + 亲和性变化强制 remote-owner 放置下 226/226 次迁移完成；观测中未见 backlink 环/重复任务/错 rq 任务/离 rq 任务；干净内核 + 干净 KCSAN 构建的环用例也无报告。

## 我可以参与的点
- kind=review：评估"临时 backlink 环不会逃逸进 `proxy_migrate_task()` 全链 blocked_donor 消费"这一控制流论断在更复杂 owner 变更交织下是否成立。
- kind=testing：在 PE 启用下的深度 owner 变更负载（交叉互斥、多跳）复现并验证环检测。

## 参考链接
- lore（RFC cover）: https://lore.kernel.org/all/20260914165455.2126134-1-sh_def@163.com/
- lore（作者追加验证）: https://lore.kernel.org/all/77591907f579598e5cf293e2ac03682a.sh_def@163.com/
