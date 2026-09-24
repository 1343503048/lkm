---
id: sched-20260916-016
date: '2026-09-16'
subject: 'sched/fair: Introduce select_task_rq_fair_thin() to select rq when LB_PROMOTE'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20260912040804.3391229-1-jackzxcui1989@163.com>
lore_url: https://lore.kernel.org/all/20260912040804.3391229-1-jackzxcui1989@163.com/
authors:
- Xin Zhao
maintainers_involved: []
current_version: null
patch_series:
- version: v1
  msgid: <20260912040804.3391229-1-jackzxcui1989@163.com>
  date: '2026-09-12'
  summary: LB_PROMOTE 场景引入 select_task_rq_fair_thin() 轻量选核路径
  review_outcome: Kayra 本日置疑能耗去留与测量方式，作者未回应
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 能耗部分被整体移除的正当性未论证
  - 无标准工具性能数据，作者未回应置疑
  next_action: 作者回应 Kayra（标准工具测量 + 能耗取舍论证）
contribution_opportunities:
- kind: review
  description: 用 ftrace 复测 LB_PROMOTE 路径耗时验证收益
- kind: discussion
  description: 论证嵌入式场景能耗与延迟权重，评估 trade-off 可接受性
generated_at: '2026-09-17T09:00:00'
source_email_count: 2
related_articles:
- sched-20260915-007
tags:
- load_balance
title: 'sched/fair: Introduce select_task_rq_fair_thin() to select rq when LB_PROMOTE'
layout: article
---

## TL;DR
本日为增量更新：Xin Zhao 的 RFC（RESEND，10 枚，核心是 `select_task_rq_fair_thin()` 让 LB_PROMOTE 场景选 rq 时走一个去掉能耗部分的轻量路径）。社区 reviewer Kayra Cizmeci 追加两点质疑——去掉能耗部分在嵌入式/能耗敏感场景的影响，以及用一个只服务于单一选项的函数「更像权衡而非优化」。作者尚未公开回应这轮置疑。合入可能性维持中等。完整背景见 related_articles。

## 背景与问题
该 RFC 的动机与主线背景见 <a class="article-ref" href="/lkm/2026/09/15/sched-20260915-007-sched-fair-introduce-select-task-rq-fair-thin-to-select-rq-w.html">sched-20260915-007</a>：在 `LB_PROMOTE` 场景下引入 `select_task_rq_fair_thin()`，跳过能耗相关的选核逻辑以缩短路径，面向嵌入式等场景的负载均衡优化。

## 技术方案
方案主体不变。本轮讨论焦点回到设计取舍：Kayra 认为「去掉整个能耗部分 + 造一个只服务于 LB_PROMOTE 选项的函数」是被绕过去的部分，而且能耗在嵌入式系统上恰恰重要，质疑作者之前「这是优化」的定性——她认为这更像是对特定用例有利的 trade-off。

## 版本演进与当前进展
- RFC RESEND（thread_root `<20260912040804.3391229-1-jackzxcui1989@163.com>`）：本日 Kayra 在 05/10 patch 下追加置疑（105160：质疑作者的自制测量方式、建议改用 ftrace；105542：质疑能耗部分被整体丢弃、函数与单一选项绑定）。
- Vincent Guittot 此前的 review 意见 Kayra 已读过，不再重复。

## Maintainer 意见与讨论焦点
- **Kayra Cizmeci（社区 reviewer）**：①没看懂作者自制的耗时测量，建议用 ftrace 等标准工具；②为何整体丢弃能耗部分、造一个只接单一选项的函数？嵌入式上能耗重要，这与作者「面向嵌入式」自述矛盾；③不认同「优化」定性，认为是 trade-off。
- Vincent Guittot 先前已有 review，本日未再发言。
- 分歧点：能耗部分去留与「优化 vs trade-off」的属性之争无人回应。

## 合入评估
*likelihood=medium*。RFC 性质、有 Vincent 此前 review 与 Kayra 本轮的连续置疑，作者尚未回应；能耗敏感场景的正当性存疑（与「面向嵌入式」动机冲突）。*blocking_issues*：能耗部分被整体移除的正当性未论证、无标准性能数据支撑、作者未回应本轮置疑。*next_action*：作者回应 Kayra（标准工具测量 + 能耗取舍论证），或收紧为特定小众场景的明确定位。

## 效果评估
本日讨论未带新数据；Kayra 明确点出作者自制测量方式存疑。

## 我可以参与的点
- kind=review：用 ftrace 等标准工具复测 LB_PROMOTE 路径耗时，验证 `select_task_rq_fair_thin()` 的实际收益是否成立。
- kind=discussion：论证嵌入式场景下能耗与延迟的权重，评估「去能耗 + 单选项函数」是否为可接受的 trade-off。

## 参考链接
- Kayra 置疑（能耗部分）：https://lore.kernel.org/all/20260915214348.22220-1-kayracizmeci@gmail.com/
- Kayra 置疑（测量方式）：https://lore.kernel.org/all/20260915181959.19936-1-kayracizmeci@gmail.com/
