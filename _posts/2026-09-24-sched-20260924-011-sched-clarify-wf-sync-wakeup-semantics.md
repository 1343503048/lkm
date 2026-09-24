---
id: sched-20260924-011
date: '2026-09-24'
subject: 'sched: Clarify WF_SYNC wakeup semantics'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260922-sched-wf-sync-doc-v3-1-23ebe9e27bef@gentwo.org>
lore_url: https://lore.kernel.org/all/20260922-sched-wf-sync-doc-v3-1-23ebe9e27bef@gentwo.org/
authors:
- Shubhang Kaushik
maintainers_involved:
- Peter Zijlstra
- Shrikanth Hegde
current_version: v3
patch_series:
- version: v3
  msgid: <20260922-sched-wf-sync-doc-v3-1-23ebe9e27bef@gentwo.org>
  date: '2026-09-22'
  summary: WF_SYNC 定义旁内联注释 + 删除过时 waitqueue 措辞（单补丁）
  review_outcome: Peter Thanks + Shrikanth Reviewed-by（changelog 排版 nit）
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 作者按 nit 修正 changelog 后维护者收取
contribution_opportunities:
- kind: review
  description: 确认 v3 注释三点语义精确覆盖且单补丁无信息丢失
generated_at: '2026-09-25T09:00:00'
source_email_count: 2
related_articles:
- sched-20260923-005
- sched-20260918-001
- sched-20260903-016
tags:
- cfs
title: 'sched: Clarify WF_SYNC wakeup semantics'
layout: article
---

## TL;DR
- <a class="article-ref" href="/lkm/2026/09/03/sched-20260903-016-sched-document-wf-sync-wakeup-placement-semantics.html">sched-20260903-016</a>：Shubhang Kaushik 的 RFC 1/2 新增 `Documentation/scheduler/sched-wake-affinity.rst`，首次把 fair 类的 `WF_SYNC` 唤醒放置与抢占行为成文；唯一回帖 Vineeth Reddy 反对的不是结论而是「文档逐字复述实现、易过时」。
- <a class="article-ref" href="/lkm/2026/09/18/sched-20260918-001-sched-document-wf-sync-wakeup-placement-semantics.html">sched-20260918-001</a>：v2（去掉实现细节、修正 waitqueue API「wakee 不会被迁移」的错误保证）；Peter Zijlstra 质疑整篇文档是「bitrot 温床」、建议改内联注释，Shrikanth Hegde 支持文档化。核心分歧「独立文档 vs 内联注释」。
- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-005-sched-clarify-wf-sync-wakeup-semantics.html">sched-20260923-005</a>：v3 采纳 Peter 的内联注释路线——在 `WF_SYNC` flag 定义旁加一条注释，删除 waitqueue 过时保证，合并为单补丁（12 插入/19 删除）。
- <a class="article-ref" href="/lkm/2026/09/24/sched-20260924-011-sched-clarify-wf-sync-wakeup-semantics.html">sched-20260924-011</a>（今天，增量更新）：Peter Zijlstra 简短回复「Thanks!」，Shrikanth Hegde 给出 `Reviewed-by`（附一个 nit：不要把 `---` 放在 tag 前，其后内容通常会被 changelog 丢弃）。v3 基本获得维护者认可，离合入只差收尾。

## 背景与问题
- <a class="article-ref" href="/lkm/2026/09/03/sched-20260903-016-sched-document-wf-sync-wakeup-placement-semantics.html">sched-20260903-016</a>：`WF_SYNC` 是「预计很快让出 CPU 的唤醒者」提供的提示而非放置请求；fair 类把它当启发式，但整条唤醒路径上它对最终 CPU 选择与抢占的实际影响力从未成文，调用方易误把它当「让被唤醒者跑在我这个 CPU 上」的请求。
- <a class="article-ref" href="/lkm/2026/09/18/sched-20260918-001-sched-document-wf-sync-wakeup-placement-semantics.html">sched-20260918-001</a>：waitqueue API 注释声称同步唤醒的 wakee 不会被迁移，但当前唤醒路径并不保证；v1 描述实现调用流程被指「太实现相关」。
- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-005-sched-clarify-wf-sync-wakeup-semantics.html">sched-20260923-005</a>：背景延续——WF_SYNC 真实语义是「advisory hint：调用者预期 waker 很快 sleep 走」，可影响 placement/preemption，但调用者不得依赖它阻止迁移/保证局部性/保证立即运行。
- <a class="article-ref" href="/lkm/2026/09/24/sched-20260924-011-sched-clarify-wf-sync-wakeup-semantics.html">sched-20260924-011</a>（今天）：无新增背景。

## 技术方案
- <a class="article-ref" href="/lkm/2026/09/03/sched-20260903-016-sched-document-wf-sync-wakeup-placement-semantics.html">sched-20260903-016</a>：1/2 纯文档 133 行五节，结论式归纳「非绑定提示」五条不保证清单。
- <a class="article-ref" href="/lkm/2026/09/18/sched-20260918-001-sched-document-wf-sync-wakeup-placement-semantics.html">sched-20260918-001</a>：1/2（sched: Document ...）新增 `sched-wake-affinity.rst`（67 行）；2/2（sched/wait: Clarify ...）修正 API 注释。
- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-005-sched-clarify-wf-sync-wakeup-semantics.html">sched-20260923-005</a>：v3 收敛为单补丁——`kernel/sched/sched.h` 的 `WF_SYNC` 定义旁加注释 `Hint that the caller expects the waker to sleep soon`，删除 `kernel/sched/wait.c` 的过时迁移保证措辞，locked helper 引用 unlocked 变体去重。12 insertions / 19 deletions，纯注释/文档修正。
- <a class="article-ref" href="/lkm/2026/09/24/sched-20260924-011-sched-clarify-wf-sync-wakeup-semantics.html">sched-20260924-011</a>（今天）：无代码变化；Shrikanth 的 nit 只涉及 changelog 排版（`---` 与 Signed-off-by/Reviewed-by tag 的位置）。

## 版本演进与当前进展
- v1（08-25）→ v2（09-17）→ **v3**（09-22，`<20260922-sched-wf-sync-doc-v3-1-23ebe9e27bef@gentwo.org>`，单枚）。本日（09-24）Peter「Thanks!」+ Shrikanth Reviewed-by，进入收取前阶段。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**（本日）：「Thanks!」——对自己此前「用内联注释替代独立文档」意见被采纳的正面确认。
- **Shrikanth Hegde（IBM）**（本日）：`Reviewed-by`，附带一个 nit（「Don't keep `---` before the tag. Anything after is usually dropped from the changelog.」）。
- 形式之争（独立文档 vs 内联注释）已以采纳 Peter 意见结束，无遗留技术分歧，仅剩 changelog 排版 nit。

## 合入评估
*likelihood=high*。修正了真实误导性 API 保证、纯注释/文档零风险，已获 Reviewer 的 Reviewed-by 与维护者「Thanks!」。*blocking_issues*：无实质项，仅 changelog 中 `---` 与 tag 位置的排版 nit 待作者顺手修正。*next_action*：作者按 nit 修正 changelog 后，维护者收取入树。

## 效果评估
纯文档/注释修正，无性能数据。价值在于消除 waitqueue API 对 WF_SYNC 的误导性保证，属「消除误解」，未见测试数据。

## 我可以参与的点
- kind=review：确认 v3 内联注释措辞（不保证迁移/局部性/立即运行三点）已精确覆盖，且合并单补丁后无信息丢失。

## 参考链接
- lore (v3 补丁): https://lore.kernel.org/all/20260922-sched-wf-sync-doc-v3-1-23ebe9e27bef@gentwo.org/
- Peter「Thanks!」: https://lore.kernel.org/all/20260924100513.GE4121339@noisy.programming.kicks-ass.net/
- Shrikanth Reviewed-by: https://lore.kernel.org/all/c5d4c422-3f25-4053-bd0b-176024811760@linux.ibm.com/
