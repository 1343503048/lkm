---
id: sched-20260923-011
subject: 'sched/mmcid: Fix affinity-triggered switch back to per-task mode'
date: '2026-09-23'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260915155953.2856524-1-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20260915155953.2856524-1-sh_def@163.com/
authors:
- Hui Su
maintainers_involved:
- Mathieu Desnoyers
current_version: v1
patch_series:
- version: v1
  msgid: <20260915155953.2856524-1-sh_def@163.com>
  date: '2026-09-15'
  summary: 修复 affinity 变化触发 mmcid 切回 per-task 模式的问题
  review_outcome: Mathieu 认可方向、要求补 selftest；作者本日确认将补 affinity-expansion 场景 selftest
    并发 v2
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - selftest 尚未提交，v2 未发
  next_action: 作者提交带 selftest 的 v2
contribution_opportunities:
- kind: testing
  description: 构造 affinity 触发 per-CPU→per-task 切换的 rseq 用例验证修复
- kind: review
  description: 梳理 mm_cid 全部转换路径，确认 selftest 覆盖完整
generated_at: '2026-09-24T09:00:00'
source_email_count: 1
related_articles:
- sched-20260916-014
tags:
- affinity
title: 'sched/mmcid: Fix affinity-triggered switch back to per-task mode'
layout: article
---

## TL;DR
- sched-20260916-014：Hui Su 的修复补丁——sched/mmcid（rseq 使用的 per-mm/per-task 内存上下文 ID）在 CPU affinity 变化触发时错误切回 per-task 模式。rseq 维护者 Mathieu Desnoyers 回复态度正面（「you're onto something」），但要求用 `tools/testing/selftests/rseq/` 覆盖这些状态转换，并询问 Thomas 当年重写 rseq mm_cid 时的转换测试是否已上游。合入可能性中等，方向被认可。
- sched-20260923-011（今天）：作者 Hui Su 回应 Mathieu 的 selftest 要求——确认 Thomas 当年 [0/4] 系列的 thread-pool emulator 没有对应 selftest、上游 `tools/testing/selftests/rseq/` 也缺 affinity-expansion（per-CPU 切回 per-task）场景的转换覆盖，决定为此补一个聚焦 selftest 并发 v2，并向 Thomas 征询 emulator 是否可作参考。

## 背景与问题
- sched-20260916-014：`sched/mmcid` 是 rseq 使用的内存上下文 ID（mm-cid / mmcid）机制，rseq 的 `mm_cid` 有 per-mm 与 per-task 两种模式。补丁修复：任务因 CPU affinity 变化触发某些状态转换时错误切回 per-task 模式。补丁原文 09-15 发出（`20260915155953.2856524-1-sh_def@163.com`），16 日仅有 Mathieu 回复可见。
- sched-20260923-011（今天）：背景无新增。

## 技术方案
- sched-20260916-014：补丁体不在 16 日缓存，具体方案未获取到；从 Mathieu 回复可反推，修复针对 affinity-triggered 的 mmcid 模式切换路径、需覆盖多个状态转换场景。
- sched-20260923-011（今天）：补丁体细节仍在作者侧。本日进展是测试覆盖层面的方案——为「affinity-expansion 使 ownership 从 per-CPU 切回 per-task」这一特定场景新增一个聚焦 selftest，并作为 v2 的一部分。

## 版本演进与当前进展
- v1（09-15）：修复 affinity 变化触发的 mmcid 状态转换错误（`20260915155953.2856524-1-sh_def@163.com`）。
- 本日（09-23）：作者回应 Mathieu，宣布将补 selftest 并发 v2；尚无 v2 实测邮件。

## Maintainer 意见与讨论焦点
- **Hui Su（作者）**：核对 rseq selftests 与 MM CID 历史后确认——Thomas 的 [0/4] 系列提及 thread-pool emulator 用于压测 ownership 转换，但该系列未含 selftest patch，当前上游 `tools/testing/selftests/rseq/` 中也找不到等价的转换覆盖，尤其缺 affinity-expansion（per-CPU→per-task）场景；除非漏看，将为此补一个聚焦 selftest 并发 v2，并询问 Thomas emulator 是否可用作参考。
- **Mathieu Desnoyers**（此前）：认可方向（「you're onto something」），要求用 `tools/testing/selftests/rseq/` 覆盖这些状态转换。
- 无 NAK；分歧仅在测试覆盖的完备性上，作者已正面接住。

## 合入评估
likelihood=medium。方向获 rseq 维护者认可，作者已承诺补 selftest 并发 v2；但 v2 与测试尚未落地，未见最终 Ack。blocking_issues：selftest 尚未提交；v2 未发。next_action：作者提交带 selftest 的 v2，回应 Mathieu 关于既有测试的询问。

## 效果评估
无性能/复现数据，属正确性修复与测试覆盖讨论。

## 我可以参与的点
- kind=testing：构造 affinity 变化触发 mmcid per-CPU→per-task 模式切换的 rseq 用例，验证修复前后行为（作者正要补的正是此场景，可提供参考实现或独立验证）。
- kind=review：梳理 `mm_cid` per-mm/per-task 模式切换的全部转换路径，确认作者补的 selftest 覆盖完整。

## 参考链接
- lore（作者回应）: https://lore.kernel.org/all/20260923T134123Z.0cf608bd5d42e07f@163.com/
- lore（Mathieu 此前回复）: https://lore.kernel.org/all/10d3d3bc-ef34-4b48-8dff-f544266181a9@efficios.com/
- lore（v1 补丁）: https://lore.kernel.org/all/20260915155953.2856524-1-sh_def@163.com/
