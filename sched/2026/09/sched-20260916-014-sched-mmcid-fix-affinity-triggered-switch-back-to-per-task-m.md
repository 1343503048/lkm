# sched/mmcid: Fix affinity-triggered switch back to per-task mode

## TL;DR
Hui Su 的修复补丁：sched/mmcid（rseq 使用的 per-mm/per-task 内存上下文 ID）在 CPU affinity 变化触发时错误地切回 per-task 模式。rseq 维护者 Mathieu Desnoyers 本日回复态度正面（「you're onto something」），但要求用 selftests（`tools/testing/selftests/rseq/`）覆盖这些状态转换，并询问 Thomas 当年重写 rseq mm_cid 时的转换测试是否已上游。合入可能性中等，方向被认可。

## 背景与问题
`sched/mmcid` 是 rseq 使用的内存上下文 ID（mm-cid / mmcid）机制。rseq 的 `mm_cid` 有 per-mm 与 per-task 两种模式。该补丁修复的是：当任务因 CPU affinity 变化触发某些状态转换时，错误地切回 per-task 模式。补丁原文不在今日邮件缓存（Hui Su 09-15 发出，见 `20260915155953.2856524-1-sh_def@163.com`），今日仅有 Mathieu 的回复可见。

## 技术方案
补丁体不在今日缓存，具体方案未获取到。从 Mathieu 回复可反推：修复针对 affinity-triggered 的 mmcid 模式切换路径，需要覆盖多个状态转换场景。

## 版本演进与当前进展
- v1（2026-09-15，`<20260915155953.2856524-1-sh_def@163.com>`）：本日 Mathieu Desnoyers 首次回复，未要求代码改动，但提出用 selftests 覆盖。

## Maintainer 意见与讨论焦点
- **Mathieu Desnoyers**（rseq 负责人）：认可方向（「I think you're onto something.」）；要求把相关场景覆盖进 `tools/testing/selftests/rseq/`；并就「重写 rseq mm_cid 时的状态转换测试是否已上游」咨询 Thomas。
- 分歧点：暂无实质分歧，主要是补测试的要求。

## 合入评估
likelihood=medium。方向被 rseq 维护者认可，但尚需补 selftests 覆盖状态转换、确认与既有 rseq 测试的关系，未见最终 Ack。blocking_issues：需要补 rseq selftest。next_action：作者补充 selftests 并回应 Mathieu 关于既有测试的询问。

## 效果评估
本日回复未涉及性能或复现数据，属正确性修复与测试覆盖讨论。

## 我可以参与的点
- kind=testing：在 rseq 场景下构造 affinity 变化触发 mmcid 模式切换的用例，验证修复前后行为。
- kind=review：梳理 rseq mm_cid per-mm/per-task 模式切换的全部转换路径，确认该修复是否覆盖完整。

## 参考链接
- Mathieu 回复：https://lore.kernel.org/all/10d3d3bc-ef34-4b48-8dff-f544266181a9@efficios.com/
- 原补丁（未在本日缓存，msgid 真实）：https://lore.kernel.org/all/20260915155953.2856524-1-sh_def@163.com/

---
id: sched-20260916-014
date: '2026-09-16'
subject: 'sched/mmcid: Fix affinity-triggered switch back to per-task mode'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260915155953.2856524-1-sh_def@163.com>'
lore_url: 'https://lore.kernel.org/all/20260915155953.2856524-1-sh_def@163.com/'
authors:
  - 'Hui Su'
maintainers_involved:
  - 'Mathieu Desnoyers'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260915155953.2856524-1-sh_def@163.com>'
    date: '2026-09-15'
    summary: '修复 affinity 变化触发 mmcid 切回 per-task 模式的问题'
    review_outcome: 'Mathieu Desnoyers 认可方向，要求补 rseq selftests'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - '需要补 rseq selftest 覆盖状态转换'
  next_action: '作者补 selftests 并回应既有 rseq 测试的询问'
contribution_opportunities:
  - kind: testing
    description: '构造 affinity 变化触发 mmcid 模式切换的 rseq 用例验证修复'
  - kind: review
    description: '梳理 mm_cid per-mm/per-task 全部转换路径，确认覆盖完整'
generated_at: '2026-09-17T09:00:00'
source_email_count: 1
related_articles: []
tags:
  - affinity
---