---
id: sched-20261004-005
date: '2026-10-04'
subject: 'sched: Add task enqueue/dequeue trace points'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <56972260b9221128d7aaf5bb60f90611ec9d7235.camel@redhat.com>
lore_url: https://lore.kernel.org/all/20261004035714.18140850@fedora/
authors:
- Gabriele Monaco
maintainers_involved:
- Peter Zijlstra
- Steven Rostedt
current_version: v2
patch_series:
- version: v2
  msgid: <56972260b9221128d7aaf5bb60f90611ec9d7235.camel@redhat.com>
  date: '2026-10-01'
  summary: 15 补丁系列 01/15：DECLARE_TRACE sched_enqueue/sched_dequeue
  review_outcome: 10-04 Rostedt 入场表态文档格式与 CC 礼仪，与 Peter 立场相反
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - .c/.dot 工件一致性方案未定
  - 系列动机说明与完整性尚缺
  next_action: LPC Prague 面谈收敛后重整系列
contribution_opportunities:
- kind: discussion
  description: 整理系列 CC 礼仪两方立场对照发列表/文档
generated_at: '2026-10-05T01:00:00'
source_email_count: 2
related_articles:
- sched-20260831-010
- sched-20260929-013
- sched-20261001-011
- sched-20261002-004
- sched-20261003-002
tags:
- tracepoints
- rv
title: 'sched: Add task enqueue/dequeue trace points'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/08/31/sched-20260831-010-sched-add-task-enqueue-dequeue-trace-points.html">sched-20260831-010</a>：Gabriele Monaco（Red Hat）在 20 补丁 RFC 中首发该 tracepoint 补丁——通用 `enqueue_task()`/`dequeue_task()`/`__block_task()` 路径加 `sched_enqueue`/`sched_dequeue` tracepoint 并 GPL 导出。
- <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-013-sched-add-task-enqueue-dequeue-trace-points.html">sched-20260929-013</a>：作为 RV「remaining deadline monitors」系列 05/10 重发。
- <a class="article-ref" href="/lkm/2026/10/01/sched-20261001-011-sched-add-task-enqueue-dequeue-trace-points.html">sched-20261001-011</a>：作为 15 补丁系列 01/15 再发 v2；Peter 回帖「clueless as to why we want this」。
- <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-004-sched-add-task-enqueue-dequeue-trace-points.html">sched-20261002-004</a>：动机之争收敛；Peter 亮「partial series 进 later pile」原则、要求文档折进 .dot、附 rst 吐槽。
- <a class="article-ref" href="/lkm/2026/10/03/sched-20261003-002-sched-add-task-enqueue-dequeue-trace-points.html">sched-20261003-002</a>：Peter 追问 .c 是否仍是 dot2c 产物（表达不了就扩展 format）、约 Prague LPC 面谈；Gabriele 承认事件-tracepoint 映射一直手工、工作量不小。
- <a class="article-ref" href="/lkm/2026/10/04/sched-20261004-005-sched-add-task-enqueue-dequeue-trace-points.html">sched-20261004-005</a>（今天）：**Steven Rostedt（tracing 总维护者）入场，公开与 Peter 分歧**：(1) 对文档格式的吐槽回以「Rant from grumpy old guy that doesn't like the new stuff ;-)」——他自己已「堕入黑暗面」，觉得 docs.kernel.org 的 HTML 阅读体验远好于直接读文本，「I think most people feel the same」；(2) 对 CC 策略给出维护者视角的实操规则——**收到整系列 CC 而其中只有一两片与自己相关时，直接整串删除**（「I hit delete on the entire thing and will not ever see what I was Cc'd for」）：与其让 maintainer 浪费时间在 23 个补丁里找那一片，不如只 CC 相关补丁、想看全系列的人用 lore/b4——「The burden is much higher to read 23 patches to find the one you are looking for than when wanting to see all patches to open a web browser or just using b4」。这直接呼应了 Peter 10-01「你忘了把其余补丁发给我」的来龙去脉，为系列该不该整串发 LKML 提供了另一位顶级 maintainer 的相反实践。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/10/03/sched-20261003-002-sched-add-task-enqueue-dequeue-trace-points.html">sched-20261003-002</a>）补丁缺一对「任务进/出 runqueue」的通用观察点，RV deadline monitor 需要它观测 dl_server 状态与任务跨调度类 runqueue 移动；系列辗转三宿主导致 Peter 上下文丢失。10-03 焦点是 RV 模型工件一致性（.dot 单源 + dot2c 扩展）。今天 Rostedt 的加入把讨论面扩展到两个流程问题：内核文档格式（rst/html vs 纯文本）与 patch 系列 CC 礼仪。

## 技术方案

（承接）tracepoint 补丁本体不变：`DECLARE_TRACE` 声明 + `EXPORT_TRACEPOINT_SYMBOL_GPL` 导出 + 三处路径打点。今天无代码层面新内容——Rostedt 的两封均为流程/工具立场表态：docs.kernel.org（Sphinx 渲染）作为官方阅读入口被广泛接受；b4 + lore 是「想看全系列」的标准工作流。

## 版本演进与当前进展

- 无新版本。系列仍处 v2 01/15；LPC Prague（下周）是 Peter/Gabriele 约定的当面收敛点。

## Maintainer 意见与讨论焦点

- **Steven Rostedt**（tracing 维护者、tracepoint 的最终把关人之一）：文档格式立场与 Peter 相反（HTML 渲染更友好、多数人同感）；CC 礼仪立场同样与「整系列发给我」相反（只 CC 相关补丁，全系列看 lore/b4）。
- **Peter Zijlstra**：暂未回应 Rostedt。tracepoint 补丁的技术方向本就源自 Peter，Rostedt 的表态对收取无阻碍，但对「系列完整性」的流程要求形成对冲。

## 合入评估

*likelihood=medium*。tracing 维护者入场但未对补丁本体表态（未给 R-b 也未反对）；Peter 的流程要求（完整系列 + changelog 动机）与 Rostedt 的 CC 实操建议相互制衡，实际收敛点大概率仍在 LPC 面谈。*blocking_issues*：同 10-03（.c/.dot 工件规范未定、系列动机说明未补齐）。*next_action*：LPC Prague 面谈；Gabriele 按 Peter 要求重整系列。

## 效果评估

无数据讨论（纯流程与文档格式之争）。

## 我可以参与的点

- `discussion`：整理本线程的「系列 CC 礼仪」两方立场（Peter：整系列发 maintainer；Rostedt：只 CC 相关补丁否则整串删）成对照说明发到列表/文档——新人高频踩坑点，有传播价值。

## 参考链接

- lore（Rostedt 文档格式回复）: https://lore.kernel.org/all/20261004034515.3592947c@fedora/
- lore（Rostedt CC 策略回复）: https://lore.kernel.org/all/20261004035714.18140850@fedora/
