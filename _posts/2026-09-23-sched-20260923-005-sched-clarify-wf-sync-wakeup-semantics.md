---
id: sched-20260923-005
subject: 'sched: Clarify WF_SYNC wakeup semantics'
date: '2026-09-23'
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
current_version: v3
patch_series:
- version: v1
  msgid: <20260825-sched-wf-sync-doc-v1-0-f899edb44ff5@gentwo.org>
  date: '2026-08-25'
  summary: 按实现调用流描述 WF_SYNC，新增 sched-wake-affinity.rst
  review_outcome: Vineeth Reddy 指出太实现相关
- version: v2
  msgid: <20260917-sched-wf-sync-doc-v2-0-6d1f107c0596@gentwo.org>
  date: '2026-09-17'
  summary: 两枚：sched 文档 + sched/wait 注释修正
  review_outcome: Peter 质疑独立文档、倾向内联注释
- version: v3
  msgid: <20260922-sched-wf-sync-doc-v3-1-23ebe9e27bef@gentwo.org>
  date: '2026-09-22'
  summary: 单枚：收敛为 WF_SYNC 定义旁内联注释 + 删除过时 waitqueue 措辞
  review_outcome: 采纳 Peter 内联注释路线，待最终审阅
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: Peter 审 v3 注释措辞后收取
contribution_opportunities:
- kind: review
  description: 核对 v3 注释是否精确涵盖三点语义与 locked helper 去重后完整性
generated_at: '2026-09-24T09:00:00'
source_email_count: 2
related_articles:
- sched-20260918-001
- sched-20260903-016
tags:
- cfs
title: 'sched: Clarify WF_SYNC wakeup semantics'
layout: article
---

## TL;DR
- <a class="article-ref" href="/lkm/2026/09/03/sched-20260903-016-sched-document-wf-sync-wakeup-placement-semantics.html">sched-20260903-016</a>：Shubhang Kaushik 的 RFC 1/2 新增 `Documentation/scheduler/sched-wake-affinity.rst`，第一次把 **fair 类**的 `WF_SYNC` 唤醒放置与抢占行为成文：`sync = (wake_flags & WF_SYNC) && !(current->flags & PF_EXITING)`、`WF_SYNC` 不绕过 `wake_wide()`、`wake_affine()` 结果只是候选（还要经 `select_idle_sibling()` 改写）、不保证被唤醒者立即抢占。作者声明「只记录现状、不建立新策略」。唯一回帖来自 Madadi Vineeth Reddy，反对的不是结论而是写法：文档逐字复述实现，易过时。
- <a class="article-ref" href="/lkm/2026/09/18/sched-20260918-001-sched-document-wf-sync-wakeup-placement-semantics.html">sched-20260918-001</a>：v2（去掉实现细节、只描述稳定的 fair 类语义）并修正 waitqueue API 中「wakee 不会被迁移」的错误保证。本日 Peter Zijlstra 质疑整篇文档是「bitrot 温床」、建议改内联注释，Shrikanth Hegde 则支持文档化。核心分歧是「独立文档 vs 内联注释」的形式问题。
- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-005-sched-clarify-wf-sync-wakeup-semantics.html">sched-20260923-005</a>（今天）：Shubhang Kaushik 按 Peter 倾向推出 v3：放弃独立文档页，把 WF_SYNC 的「advisory hint」契约收敛为 flag 定义旁的一条内联注释，删除 waitqueue 里「wakee 不会被迁移」的过时保证，并把系列合并为单补丁（12 插入 / 19 删除）。形式之争以采纳 Peter 意见收敛。

## 背景与问题
- <a class="article-ref" href="/lkm/2026/09/03/sched-20260903-016-sched-document-wf-sync-wakeup-placement-semantics.html">sched-20260903-016</a>：`WF_SYNC` 由「预计很快让出 CPU 的唤醒者」提供，是提示而非放置请求；fair 类把它当启发式，但从 `try_to_wake_up()` 经 `select_task_rq_fair()`、`select_idle_sibling()`、`preempt_sync()` 的整条路径上，它对最终 CPU 选择与抢占的实际影响力从未成文。缺文档的后果是调用方容易把它当成「让被唤醒者跑在我这个 CPU 上」的请求。
- <a class="article-ref" href="/lkm/2026/09/18/sched-20260918-001-sched-document-wf-sync-wakeup-placement-semantics.html">sched-20260918-001</a>：waitqueue API 注释声称同步唤醒的 wakee 不会被迁移到其它 CPU，但当前唤醒路径并不保证；v1 用实现调用流程描述语义被指「太实现相关、易过时」。
- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-005-sched-clarify-wf-sync-wakeup-semantics.html">sched-20260923-005</a>（今天）：背景延续——WF_SYNC 真实语义是「advisory hint：调用者预期 waker 很快 sleep 走」，可影响 placement/preemption，但调用者不得依赖它阻止迁移、保证 CPU 局部性或让 wakee 立即运行。

## 技术方案
- <a class="article-ref" href="/lkm/2026/09/03/sched-20260903-016-sched-document-wf-sync-wakeup-placement-semantics.html">sched-20260903-016</a>：1/2 纯文档，133 行五节（Wakeup paths / Fair-class CPU selection / Idle CPU selection / Fair-class wakeup preemption / Semantics and policy），结论式归纳为「非绑定提示」的五条不保证清单。
- <a class="article-ref" href="/lkm/2026/09/18/sched-20260918-001-sched-document-wf-sync-wakeup-placement-semantics.html">sched-20260918-001</a>：1/2（sched: Document ...）新增 `sched-wake-affinity.rst`（67 行）只描述稳定 fair 类语义；2/2（sched/wait: Clarify ...）修正 `__wake_up_sync_key()` 等 API 注释，删除「wakee 不会被迁移」的错误保证。
- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-005-sched-clarify-wf-sync-wakeup-semantics.html">sched-20260923-005</a>（今天）：v3 收敛为单补丁——在 `kernel/sched/sched.h` 的 `WF_SYNC` 定义旁加注释 `Hint that the caller expects the waker to sleep soon`，点明调用者不得依赖其阻止迁移/保证局部性/保证立即运行；删除 `kernel/sched/wait.c` 中 `__wake_up_sync_key()`/`__wake_up_sync_key_nopoll()` 的过时迁移保证措辞，并让 locked helper 引用 unlocked 变体去重。12 insertions / 19 deletions，纯注释/文档修正，无行为变更。

## 版本演进与当前进展
- v1（08-25）：按实现调用流描述 WF_SYNC，被 Vineeth Reddy 指出太实现相关。
- v2（09-17，两枚：1/2 sched 文档 + 2/2 sched/wait）：Peter 质疑独立文档是「bitrot 温床」、建议内联注释。
- **v3**（09-22，`<20260922-sched-wf-sync-doc-v3-1-23ebe9e27bef@gentwo.org>`，单枚）：采纳内联注释路线、合并系列、删除过时 waitqueue 措辞。作者另回帖（`<e1028918-6421-235e-8407-7fa51adc2f14@gentwo.org>`）向 Peter 说明取舍。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**（此前）：对独立文档「*groan*，为什么不直接给 WF_SYNC 配个注释」——v3 直接回应了这一偏好，收敛为内联注释。
- **Shubhang Kaushik（作者）**：本日说明「意图只是保留『调用者不得把 WF_SYNC 当 no-migration / run-next 保证』这条小而重要的契约」；认同独立文档过重，改为内联注释并去重。
- 形式之争（独立文档 vs 内联注释）以采纳 Peter 意见结束，无遗留分歧。

## 合入评估
*likelihood=high*。修正了一处真实的误导性 API 保证、纯注释/文档改动零风险，且已按维护者偏好收敛为内联注释。*blocking_issues*：无明确项（仅待维护者审 v3 细节）。*next_action*：Peter 审 v3 注释措辞后收取。

## 效果评估
纯文档/注释修正，无性能数据。价值在于消除 waitqueue API 对 WF_SYNC 的误导性保证，属「作者主观判断（消除误解），未见测试数据」。

## 我可以参与的点
- kind=review：核对 v3 内联注释的措辞是否精确涵盖「不保证迁移/局部性/立即运行」三点，以及 locked helper 引用 unlocked 变体后语义是否完整。

## 参考链接
- lore（v3 补丁）: https://lore.kernel.org/all/20260922-sched-wf-sync-doc-v3-1-23ebe9e27bef@gentwo.org/
- lore（作者说明回帖）: https://lore.kernel.org/all/e1028918-6421-235e-8407-7fa51adc2f14@gentwo.org/
- lore（v2 cover）: https://lore.kernel.org/all/20260917-sched-wf-sync-doc-v2-0-6d1f107c0596@gentwo.org/
