# sched: Clarify WF_SYNC wakeup semantics

## TL;DR
本文为增量更新，完整背景见 sched-20260918-001（该系列前作主题为「Document WF_SYNC wakeup placement semantics」）。Shubhang Kaushik 按 Peter Zijlstra 的倾向推出 v3：放弃独立文档页，把 WF_SYNC 的「advisory hint」契约收敛为 flag 定义旁的一条内联注释，删除 waitqueue 里「wakee 不会被迁移」的过时保证，并把系列合并为单补丁（12 插入 / 19 删除）。形式之争（独立文档 vs 内联注释）以采纳 Peter 意见而收敛。

## 背景与问题
背景见 sched-20260918-001 与 sched-20260903-016：waitqueue API 注释声称同步唤醒的 wakee 不会被迁移到其它 CPU，但当前唤醒路径并不保证这一点；WF_SYNC 的真实语义是「advisory hint——调用者预期 waker 很快 sleep 走」，可影响 placement/preemption，但调用者不得依赖它阻止迁移、保证 CPU 局部性或让 wakee 立即运行。

## 技术方案
v3 把系列收敛为单补丁（不再拆分 sched 文档 + sched/wait 两枚）：

- 在 `kernel/sched/sched.h` 的 `WF_SYNC` 定义旁加注释：`Hint that the caller expects the waker to sleep soon`，点明调度类可据此做 placement/preemption 决策，但调用者不得依赖其阻止迁移/保证局部性/保证立即运行。
- 删除 `kernel/sched/wait.c` 中 `__wake_up_sync_key()`/`__wake_up_sync_key_nopoll()` 的过时迁移保证措辞，并让 locked helper 引用 unlocked 变体去重。
- 整体 12 insertions / 19 deletions，纯注释/文档修正，无行为变更。

## 版本演进与当前进展
- v1（08-25）：按实现调用流描述 WF_SYNC，被 Vineeth Reddy 指出太实现相关。
- v2（09-17，两枚：1/2 sched 文档 + 2/2 sched/wait）：Peter 质疑独立文档是「bitrot 温床」、建议内联注释。
- **v3**（09-22，`<20260922-sched-wf-sync-doc-v3-1-23ebe9e27bef@gentwo.org>`，单枚）：采纳内联注释路线、合并系列、删除过时 waitqueue 措辞。作者另回帖（`<e1028918-6421-235e-8407-7fa51adc2f14@gentwo.org>`）向 Peter 说明取舍。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**（此前）：对独立文档「*groan*，为什么不直接给 WF_SYNC 配个注释」——v3 直接回应了这一偏好，收敛为内联注释。
- **Shubhang Kaushik（作者）**：本日说明「意图只是保留『调用者不得把 WF_SYNC 当 no-migration / run-next 保证』这条小而重要的契约」；认同独立文档过重，改为内联注释并去重。
- 形式之争（独立文档 vs 内联注释）以采纳 Peter 意见结束，无遗留分歧。

## 合入评估
likelihood=high。修正了一处真实的误导性 API 保证、纯注释/文档改动零风险，且已按维护者偏好收敛为内联注释。blocking_issues：无明确项（仅待维护者审 v3 细节）。next_action：Peter 审 v3 注释措辞后收取。

## 效果评估
纯文档/注释修正，无性能数据。价值在于消除 waitqueue API 对 WF_SYNC 的误导性保证，属「作者主观判断（消除误解），未见测试数据」。

## 我可以参与的点
- kind=review：核对 v3 内联注释的措辞是否精确涵盖「不保证迁移/局部性/立即运行」三点，以及 locked helper 引用 unlocked 变体后语义是否完整。

## 参考链接
- lore（v3 补丁）: https://lore.kernel.org/all/20260922-sched-wf-sync-doc-v3-1-23ebe9e27bef@gentwo.org/
- lore（作者说明回帖）: https://lore.kernel.org/all/e1028918-6421-235e-8407-7fa51adc2f14@gentwo.org/
- lore（v2 cover，见前作）: https://lore.kernel.org/all/20260917-sched-wf-sync-doc-v2-0-6d1f107c0596@gentwo.org/

---
id: sched-20260923-005
subject: 'sched: Clarify WF_SYNC wakeup semantics'
date: '2026-09-23'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20260922-sched-wf-sync-doc-v3-1-23ebe9e27bef@gentwo.org>'
lore_url: 'https://lore.kernel.org/all/20260922-sched-wf-sync-doc-v3-1-23ebe9e27bef@gentwo.org/'
authors:
  - 'Shubhang Kaushik'
maintainers_involved:
  - 'Peter Zijlstra'
current_version: v3
patch_series:
  - version: v1
    msgid: '<20260825-sched-wf-sync-doc-v1-0-f899edb44ff5@gentwo.org>'
    date: '2026-08-25'
    summary: '按实现调用流描述 WF_SYNC，新增 sched-wake-affinity.rst'
    review_outcome: 'Vineeth Reddy 指出太实现相关'
  - version: v2
    msgid: '<20260917-sched-wf-sync-doc-v2-0-6d1f107c0596@gentwo.org>'
    date: '2026-09-17'
    summary: '两枚：sched 文档 + sched/wait 注释修正'
    review_outcome: 'Peter 质疑独立文档、倾向内联注释'
  - version: v3
    msgid: '<20260922-sched-wf-sync-doc-v3-1-23ebe9e27bef@gentwo.org>'
    date: '2026-09-22'
    summary: '单枚：收敛为 WF_SYNC 定义旁内联注释 + 删除过时 waitqueue 措辞'
    review_outcome: '采纳 Peter 内联注释路线，待最终审阅'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 'Peter 审 v3 注释措辞后收取'
contribution_opportunities:
  - kind: review
    description: '核对 v3 注释是否精确涵盖三点语义与 locked helper 去重后完整性'
generated_at: '2026-09-24T09:00:00'
source_email_count: 2
related_articles:
  - sched-20260918-001
  - sched-20260903-016
tags:
  - cfs
---