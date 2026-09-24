---
id: sched-20260917-015
date: '2026-09-17'
subject: 'sched: Add sched_ext hooks for proxy execution'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260831134338.1531664-8-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260831134338.1531664-8-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Peter Zijlstra
current_version: v13
patch_series:
- version: v13
  msgid: <20260831134338.1531664-1-arighi@nvidia.com>
  date: '2026-08-31'
  summary: proxy execution 兼容 sched_ext 系列（18 枚）之 07/18；本日确认 donor/curr put_prev_task
    语义
  review_outcome: Peter 语义确认收敛，准备 v14
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 08/18 WF_ON_RQ 语义与 09/18 清理时机仍待对齐
  next_action: Andrea 发 v14 并对齐 08/18
contribution_opportunities:
- kind: review
  description: 核对 v14 中 07/18 的 donor/curr put_prev_task 语义落地
generated_at: '2026-09-18T09:00:00'
source_email_count: 1
related_articles:
- sched-20260916-002
tags:
- proxy_execution
- sched_ext
title: 'sched: Add sched_ext hooks for proxy execution'
layout: article
---

## TL;DR
增量更新：Andrea Righi 的 proxy execution 兼容 sched_ext 系列（v13，18 枚）继续与 Peter Zijlstra 就 07/18（`sched: Add sched_ext hooks for proxy execution`）交换意见。Peter 承认自己把 donor/curr 的 put_prev_task 处理搞混了，随后确认 `rq->donor` 有 `put_prev_task()` 兜底、而 `rq->curr` 没有，最终"Fair enough"收敛。属对 v14 收尾的点状确认，无 NAK。

## 背景与问题
背景见 <a class="article-ref" href="/lkm/2026/09/16/sched-20260916-002-sched-make-proxy-execution-compatible-with-sched-ext.html">sched-20260916-002</a>：让 proxy execution（执行上下文与调度上下文拆分）与 sched_ext 兼容。本日为 07/18 补丁的细化确认，不涉及新方案。

## 技术方案
无方案变化。本日交换聚焦一处语义：`rq->donor` 会经 `put_prev_task()` 处理来理顺，而 `rq->curr` 没有对等机制——这是 Andrea 与 Peter 在 07/18 设计讨论中厘清的一点。

## 版本演进与当前进展
- v13（08-31，`<20260831134338.1531664-1-arighi@nvidia.com>`）：当前版本。
- 09-17：Peter 对 07/18 的 put_prev_task donor/curr 语义给出最终确认，准备进入 v14 收尾。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra（07/18）**：先承认之前把 D（donor）与 O 搞混；然后确认 `rq->donor` 有 `put_prev_task()` 接手、`rq->curr` 没有，接受 Andrea 的说法（"Fair enough"）。
- 无新分歧；该点收敛。

## 合入评估
*likelihood=medium*。系列整体仍受 08/18 的 WF_ON_RQ 语义开放项牵制（见 <a class="article-ref" href="/lkm/2026/09/16/sched-20260916-002-sched-make-proxy-execution-compatible-with-sched-ext.html">sched-20260916-002</a>），本日仅 07/18 点状收敛，不改变整体格局。*blocking_issues*：08/18 语义与 09/18 清理时机仍待对齐。*next_action*：Andrea 发 v14，落实此前承诺的 05/07/09/14/15 改动并与 Peter 对齐 08/18。

## 效果评估
无性能数据；属设计评审与语义确认。

## 我可以参与的点
- kind=review：核对 v14 中 07/18 是否按"donor 有 put_prev_task、curr 无"的语义落地注释与实现。

## 参考链接
- lore（07/18 patch）: https://lore.kernel.org/all/20260831134338.1531664-8-arighi@nvidia.com/
- Peter 本日回复: https://lore.kernel.org/all/20260917103507.GJ776954@noisy.programming.kicks-ass.net/
