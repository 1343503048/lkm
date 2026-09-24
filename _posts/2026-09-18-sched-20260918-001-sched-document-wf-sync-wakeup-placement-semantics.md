---
id: sched-20260918-001
date: '2026-09-18'
subject: 'sched: Document WF_SYNC wakeup placement semantics'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20260917-sched-wf-sync-doc-v2-0-6d1f107c0596@gentwo.org>
lore_url: https://lore.kernel.org/all/20260917-sched-wf-sync-doc-v2-0-6d1f107c0596@gentwo.org/
authors:
- Shubhang Kaushik
maintainers_involved:
- Peter Zijlstra
- Shrikanth Hegde
current_version: v2
patch_series:
- version: v1
  msgid: <20260825-sched-wf-sync-doc-v1-0-f899edb44ff5@gentwo.org>
  date: '2026-08-25'
  summary: 按实现调用流描述 WF_SYNC 语义，新增 sched-wake-affinity.rst
  review_outcome: Vineeth Reddy 指出太实现相关、易过时，建议改述调度层语义
- version: v2
  msgid: <20260917-sched-wf-sync-doc-v2-0-6d1f107c0596@gentwo.org>
  date: '2026-09-17'
  summary: 改述稳定语义，移除实现细节；并修正 wait.c API 注释的错误迁移保证
  review_outcome: Peter 质疑独立文档形式、倾向内联注释；Shrikanth 支持文档化
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 文档形式（独立页 vs 内联注释）未与 Peter 达成一致
  - 2/2 两个函数注释待去重，UP 表述待评估
  next_action: 作者回应 Peter 的形式质疑并决定是否收敛为内联注释，发 v3
contribution_opportunities:
- kind: review
  description: 就独立文档 vs 内联注释给出倾向性意见
- kind: discussion
  description: 评估 UP 上 WF_SYNC 语义注释是否仍有必要
generated_at: '2026-09-19T09:00:00'
source_email_count: 6
related_articles:
- sched-20260903-016
tags:
- cfs
- wake_affine
- docs
title: 'sched: Document WF_SYNC wakeup placement semantics'
layout: article
---

## TL;DR
增量更新：Shubhang Kaushik 的 WF_SYNC 语义文档系列推出 v2（去掉实现细节、只描述稳定的 fair 类语义），并修正 waitqueue API 中"wakee 不会被迁移"的错误保证。本日 Peter Zijlstra 质疑整篇文档是"bitrot 温床"、建议改成内联注释，Shrikanth Hegde 则支持文档化（WF_SYNC 已有 4+ 个改动提案、语义混乱）。核心分歧是"独立文档 vs 内联注释"的形式问题。

## 背景与问题
背景见 <a class="article-ref" href="/lkm/2026/09/03/sched-20260903-016-sched-document-wf-sync-wakeup-placement-semantics.html">sched-20260903-016</a>（v1）：waitqueue API 注释声称同步唤醒的 wakee 不会被迁移到其他 CPU，但当前唤醒路径并不保证这一点；WF_SYNC 在 fair 类的语义从未被文档化。v1 用实现调用流程来描述语义，被 Vineeth Reddy 指出"太实现相关、易过时"。

## 技术方案
- 1/2（sched: Document ...）：新增 `Documentation/scheduler/sched-wake-affinity.rst`（67 行），只描述稳定的 fair 类 WF_SYNC 语义：WF_SYNC 是 advisory hint，可影响 placement 与 preemption，但不保证 CPU 局部性、避免迁移或立即抢占；明确"本文只记录现有行为，不建立新的 placement 策略"。
- 2/2（sched/wait: Clarify ...）：修正 `__wake_up_sync_key()` / `__wake_up_sync_key_nopoll()` 的 API 注释，删除"wakee 不会被迁移"的错误保证，改为说明 WF_SYNC 是 fair 类的 placement/preemption hint；顺带移除 UP 上"避免额外抢占"的旧表述（v2 仍保留该句）。

## 版本演进与当前进展
- v1（2026-08-25，`<20260825-sched-wf-sync-doc-v1-0-f899edb44ff5@gentwo.org>`）：按实现调用流描述 WF_SYNC；Vineeth Reddy（09-03）指出复现 helper 名/谓词/顺序会让文档过时，建议改为调度层策略与可观测结果。
- v2（2026-09-17，`<20260917-sched-wf-sync-doc-v2-0-6d1f107c0596@gentwo.org>`）：移除 helper 名/谓词/CPU 选择细节，改述稳定语义；澄清自定义 wake 函数的处理与 WF_SYNC 的 placement/preemption 限制。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**：对 1/2 明确不满——"*groan*，为什么不直接给 WF_SYNC 配个注释？这些文档就是 bitrot 的温床"；对 2/2 建议两个函数互相引用去重，并质疑"UP 注释还有人关心吗"。
- **Shrikanth Hegde**：支持文档化——"WF_SYNC 已有至少 4 个改动提案、非常混乱"，并指路 Srikar 对 sync API 的滥用案例；认为要么文档化期望、要么修正误用调用点。
- **Shubhang Kaushik（作者）**：解释意图是记录"可观测的 WF_SYNC 语义"（advisory hint，不保证不迁移/立即抢占），已认同 v1 太实现相关、会在 v2 重写。
- 分歧点：独立 Documentation 页 vs WF_SYNC 处内联注释；2/2 两个函数注释的去重；UP 相关表述是否仍值得保留。

## 合入评估
*likelihood=medium*。文档/注释修正本身低风险、无行为变更，且确实修正了一处错误的 API 保证（有实际价值）；但 Peter 作为 sched 维护者对"独立文档"形式持保留态度，倾向内联注释。*blocking_issues*：文档形式（独立页 vs 内联注释）未与 Peter 达成一致；2/2 注释去重与 UP 表述待处理。*next_action*：作者回应 Peter 的意见，决定是否收敛为内联注释、去重 wait.c 两个函数注释、评估 UP 表述的取舍，然后发 v3。

## 效果评估
纯文档/注释修正，无性能数据。价值在于消除 waitqueue API 对 WF_SYNC 的误导性保证（避免调用者误解同步唤醒的迁移行为），属"作者主观判断，未见测试数据"。

## 我可以参与的点
- kind=review：就"独立文档页 vs 内联注释"给出倾向性意见（社区目前没有一致结论，正反意见各一票）。
- kind=discussion：评估 UP 上 WF_SYNC 语义注释是否仍有存在必要（Peter 明确质疑，无人回应）。

## 参考链接
- lore（v2 cover）: https://lore.kernel.org/all/20260917-sched-wf-sync-doc-v2-0-6d1f107c0596@gentwo.org/
- lore（v1 cover）: https://lore.kernel.org/r/20260825-sched-wf-sync-doc-v1-0-f899edb44ff5@gentwo.org/
