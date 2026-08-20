---
id: sched-20260818-002
date: 2026-08-18
subsystem: sched
type: feature
status: under_review
severity: high
thread_root_msgid: <aoJ5q7HbSUOxlC1H@slm.duckdns.org>
lore_url: https://lore.kernel.org/r/20260817013458.xxxxxxx-arighi@nvidia.com
authors:
- Andrea Righi
maintainers_involved:
- Tejun Heo
current_version: v12
patch_series:
- version: v12
  msgid: <20260817013458.xxxxxxx-arighi@nvidia.com>
  date: 2026-08-17
  summary: 17 patch 系列：让 proxy execution 与 sched_ext 共存，通过 SCX_OPS_ENQ_BLOCKED 逐调度器能力把
    blocked donor 交给 BPF 调度器。
  review_outcome: Tejun 对 patch 12/17 和 14/17 详细 review；Andrea 逐条回应并同意多项调整。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Tejun 对 owner CPU-pinned 行为有疑问待澄清；reject_dsq 与 core-sched deferred work 交互需进一步论证；系列体量巨大需多轮打磨
  next_action: 等待 Andrea 出 v13 吸收本日 review 调整（去掉 SCX_TASK_ENQ_WAKEUP、内联条件、提前 PF_EXITING
    等）。
contribution_opportunities:
- kind: review
  description: 评审 reject_dsq 与 generic deferred work flag 的交互设计，可提出更简洁方案。
- kind: testing
  description: 在开启 CONFIG_SCHED_PROXY_EXEC + CONFIG_SCHED_CLASS_EXT 的内核上跑 enq_blocked
    selftest 验证。
generated_at: '2026-08-19T00:10:00'
source_email_count: 6
related_articles:
- sched-20260817-001
tags:
- proxy_execution
- sched_ext
- sched/core
title: 'sched_ext: proxy execution v12 — review discussion (patches 12/17, 14/17)'
layout: article
---

## TL;DR
本文为增量更新。Andrea Righi 的 v12 proxy-exec + sched_ext 共存系列（17 patch）本日继续收到 Tejun Heo 对 patch 12/17（remote DSQ transfers）和 14/17（proxy donor admission）的详细 review，Andrea 逐条回应并承诺调整。关键进展：Tejun 同意去掉 `SCX_TASK_ENQ_WAKEUP`、改用 `WF_ON_RQ` 直接传递；reject_dsq 处理讨论引入 generic deferred work flag 话题。完整背景见前日文章。

## 背景与问题
（完整背景见 sched-20260817-001）proxy-exec 与 sched_ext 当前构建期互斥。v12 通过 `SCX_OPS_ENQ_BLOCKED` 能力位让 BPF 调度器控制 blocked donor 的接纳与排序，使二者运行时共存。

## 技术方案
本日讨论集中在两个子 patch：

**patch 14/17（Delegate proxy donor admission to BPF schedulers）**：
- Tejun 质疑 proxy 执行期间 donor 上下文是否真的不能离开 owner 的 last CPU——"It's a bit odd that the owner becomes essentially CPU-pinned"。
- Andrea 回应：去掉多余注释、内联条件判断并加注释解释 WAKEUP 排除、`PF_EXITING` 测试提前。
- Tejun 建议去掉 `SCX_TASK_ENQ_WAKEUP`，直接从 `ttwu_runnable()` 传 `WF_ON_RQ`；Andrea 同意并承诺在 v13 实现。

**patch 12/17（Handle proxy-exec races in remote DSQ transfers）**：
- Tejun 问：reject_dsq 初始插入能否复用 `schedule_deferred_locked()` 而不设 proxy-specific flag？
- Andrea 建议重命名为 `SCX_RQ_PROXY_RETRY` 反映新语义。
- Tejun 指出这是 core-sched 的通用问题（core-sched 可以 zap deferred work callback），建议引入 generic deferred work pending flag——但认为"probably something to do for another patch series"。

## 版本演进与当前进展
- v12 当前。本日（08-18）讨论集中在 patch 12/17 和 14/17 的 review 交互。
- Andrea 已同意多项调整：去掉 `SCX_TASK_ENQ_WAKEUP`、内联条件、提前 `PF_EXITING` 测试。预计 v13 将反映这些变更。

## Maintainer 意见与讨论焦点
- Tejun Heo：
  - 对 owner CPU-pinned 行为有疑问，但方向认可。
  - 要求去掉 `SCX_TASK_ENQ_WAKEUP`，用 `WF_ON_RQ` 替代——Andrea 已同意。
  - 指出 reject_dsq / deferred work 是 core-sched 通用问题，建议另起系列处理。
  - 要求注释说明为何此 site 需要不同条件集。
- 整体尚未给 ack，但 review 走向积极，逐 patch 收敛中。

## 合入评估
方向已被 maintainer 接受，但 2024 行的大系列需多轮打磨。v13 预计将吸收本日讨论的多项调整。核心 sched/core 部分可能先于 sched_ext 部分拆分合入。

## 效果评估
暂无本日新数据。前日 v12 自带 enq_blocked selftest 数据（same-cpu -20%、cross-cpu -13% 等待时间）。

## 我可以参与的点
- 评审 reject_dsq 与 generic deferred work flag 的交互设计，可提出更简洁方案。
- 在开启 CONFIG_SCHED_PROXY_EXEC + CONFIG_SCHED_CLASS_EXT 的内核上跑 enq_blocked selftest 验证 v13。

## 参考链接
- lore thread (v12): https://lore.kernel.org/r/20260817013458.xxxxxxx-arighi@nvidia.com
- tip-bot commit: 未获取到
- stable backport: 未获取到
