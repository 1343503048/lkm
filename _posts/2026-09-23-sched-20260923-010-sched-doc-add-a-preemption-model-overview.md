---
id: sched-20260923-010
subject: 'sched/doc: add a preemption model overview'
date: '2026-09-23'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260923083903.616271-1-quchaosheng000406@163.com>
lore_url: https://lore.kernel.org/all/20260923083903.616271-1-quchaosheng000406@163.com/
authors:
- Quchaosheng
maintainers_involved:
- Sebastian Andrzej Siewior
current_version: v4
patch_series:
- version: v1
  msgid: null
  date: '2026-09-20'
  summary: 按 resched_curr_lazy()/scheduler_tick() 代码走读的 120 行概述
  review_outcome: Sebastian 要求鸟瞰视角
- version: v2
  msgid: <20260922083101.99685-1-quchaosheng000406@163.com>
  date: '2026-09-22'
  summary: 重写为调度请求视角，删测量段与 yield 措辞
  review_outcome: Sebastian 认可
- version: v3
  msgid: <20260923075304.584348-1-quchaosheng000406@163.com>
  date: '2026-09-22'
  summary: 把 such a call 明确写为 cond_resched()
  review_outcome: 回应 Sebastian 要求，Reviewed-by 保留
- version: v4
  msgid: <20260923083903.616271-1-quchaosheng000406@163.com>
  date: '2026-09-22'
  summary: diff 无变化，仅因第二枚 patch 更新而重发
  review_outcome: 等待收取
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待文档维护者收取
contribution_opportunities:
- kind: review
  description: 核对四种抢占模型描述与 preempt=/debugfs 实际行为的一致性
generated_at: '2026-09-24T09:00:00'
source_email_count: 2
related_articles:
- sched-20260922-016
- sched-20260920-003
tags:
- preempt
title: 'sched/doc: add a preemption model overview'
layout: article
---

## TL;DR
- <a class="article-ref" href="/lkm/2026/09/20/sched-20260920-003-sched-doc-add-a-preemption-model-overview.html">sched-20260920-003</a>：Quchaosheng 提交文档补丁 1/2——新增 `Documentation/scheduler/sched-preemption.rst`，系统介绍内核四种抢占模型（none/voluntary/full/lazy）及其运行时选择方式，并澄清最易误解的 PREEMPT_LAZY 机制。首发，暂无 review。
- <a class="article-ref" href="/lkm/2026/09/22/sched-20260922-016-sched-doc-add-a-preemption-model-overview.html">sched-20260922-016</a>：v2——按 Sebastian 意见把文档重写为「围绕调度请求」的鸟瞰视角（wakeup → 决定谁让出 CPU → 置 TIF_NEED_RESCHED[LAZY] → 抢占模型决定在哪兑现），删掉错误测量段与 yield 措辞，debugfs 段并入运行时选择小节。Sebastian 建议合入。
- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-010-sched-doc-add-a-preemption-model-overview.html">sched-20260923-010</a>（今天）：Quchaosheng 快速迭代——v3 按 Sebastian 要求把「such a call」明确写为 `cond_resched()`（保留其 Reviewed-by），随后仅因第二枚 patch 变化而重发 v4（diff 无变化）。文档已获 Suggested-by/Reviewed-by 维护者认可，等待收取。

## 背景与问题
- <a class="article-ref" href="/lkm/2026/09/20/sched-20260920-003-sched-doc-add-a-preemption-model-overview.html">sched-20260920-003</a>：现有调度文档只讲各调度类和调优旋钮，没有任何一处系统描述「抢占模型」本身；唯一提到的地方是 `preempt=` 内核启动参数的 kernel-parameters 条目，但它只解释启动参数、不解释其选中的模型。作者希望补上这块空缺。
- <a class="article-ref" href="/lkm/2026/09/22/sched-20260922-016-sched-doc-add-a-preemption-model-overview.html">sched-20260922-016</a>：背景不变——调度文档缺抢占模型概述。
- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-010-sched-doc-add-a-preemption-model-overview.html">sched-20260923-010</a>（今天）：背景无新增。

## 技术方案
- <a class="article-ref" href="/lkm/2026/09/20/sched-20260920-003-sched-doc-add-a-preemption-model-overview.html">sched-20260920-003</a>：新增 `sched-preemption.rst`（120 行）并在 `index.rst` 挂条目。定义四种模型：none（仅 cond_resched()/阻塞点）、voluntary（none + might_sleep()）、full（未显式关抢占处可抢占）、lazy（同 full 但 fair 类 resched 请求不打断目标 CPU，返回用户态或下一 tick 提交）；CONFIG_PREEMPT_DYNAMIC 下可用 `preempt=` 启动时选择；澄清 lazy 不发送跨 CPU resched IPI。
- <a class="article-ref" href="/lkm/2026/09/22/sched-20260922-016-sched-doc-add-a-preemption-model-overview.html">sched-20260922-016</a>：v2 改为沿「调度请求」主线叙述（84→85 行），覆盖四模型、各模型下请求如何兑现、哪些可运行时选择。
- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-010-sched-doc-add-a-preemption-model-overview.html">sched-20260923-010</a>（今天）：v3 唯一实质变化——把指代不清的「such a call」明确写为 `cond_resched()`；v4 diff 无变化（仅因第二枚 patch 变化而重发）。

## 版本演进与当前进展
- v1（09-20）：代码走读式概述（按 `resched_curr_lazy()`/`scheduler_tick()` 代码走读，120 行）。
- v2（09-22）：重写为「调度请求」视角（wakeup → 决定谁让出 CPU → 置 TIF_NEED_RESCHED[LAZY] → 抢占模型决定在哪兑现），删错误测量段。
- **v3**（09-22 22:53 UTC，`<20260923075304.584348-1-quchaosheng000406@163.com>`）：把「such a call」改写为 `cond_resched()`，Sebastian 要求，Reviewed-by 保留（仅该段变化）。
- **v4**（09-22 23:39 UTC，`<20260923083903.616271-1-quchaosheng000406@163.com>`）：diff 无变化，仅因第二枚 patch 变化而重发。

## Maintainer 意见与讨论焦点
维护者 Sebastian Andrzej Siewior（Suggested-by、Reviewed-by 本人）此前已认可（「looks good... please add it」），v3 的措辞修正即回应其要求。无争议、无 NAK。

## 合入评估
*likelihood=high*。纯文档补丁、Suggested-by/Reviewed-by 维护者已给、无争议。*blocking_issues*：无。*next_action*：等待文档维护者（或 sched 侧）收取合入。

## 效果评估
纯文档，无性能数据；澄清了 lazy 抢占真实动机（run-to-completion，非省 IPI，见 v2 分析）。

## 我可以参与的点
- kind=review：核对四种抢占模型描述与 `preempt=`/debugfs 实际行为的一致性（承前作验证点）。

## 参考链接
- lore（v4 补丁）: https://lore.kernel.org/all/20260923083903.616271-1-quchaosheng000406@163.com/
- lore（v3 补丁）: https://lore.kernel.org/all/20260923075304.584348-1-quchaosheng000406@163.com/
- lore（v2）: https://lore.kernel.org/all/20260922083101.99685-1-quchaosheng000406@163.com/
