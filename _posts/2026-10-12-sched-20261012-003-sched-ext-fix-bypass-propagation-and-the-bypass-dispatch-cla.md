---
id: sched-20261012-003
date: '2026-10-12'
subject: 'sched_ext: Fix bypass propagation and the bypass dispatch claim for overlapping
  bypasses'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261011214028.743546-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20261011214028.743546-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20261011214028.743546-2-tj@kernel.org>
  date: '2026-10-12'
  summary: 1/2 每次 propagate 祖先 bypass 深度变化到所有后代
  review_outcome: 自述模型检验（TLC）覆盖修复序列
- version: v1
  msgid: <20261011214028.743546-3-tj@kernel.org>
  date: '2026-10-12'
  summary: 2/2 为被祖先 bypass 覆盖的子调度器正确 claim/release bypass dispatch
  review_outcome: 自述模型检验（TLC）覆盖修复序列
fixes_commit: aa2a0a19686c
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 作者即为 sched_ext 维护者，标记 for-7.3-fixes，等待合入该分支
contribution_opportunities: []
generated_at: '2026-10-13T01:40:00'
source_email_count: 3
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Fix bypass propagation and the bypass dispatch claim for overlapping
  bypasses'
layout: article
---

## TL;DR

sched_ext 维护者 Tejun Heo 发 2 补丁修复补丁（挂 `sched_ext/for-7.3-fixes`）：`scx_bypass()` 只在自身 depth 跨零时才 propagate 给后代并 claim bypass dispatch，导致「子调度器自身的 bypass 与祖先的 bypass 重叠」时后代提前退逼、claim 泄漏或从未取得；PM suspend 覆盖子调度器 enable/disable 会触发 WARN 或让任务滞留父级 bypass DSQ。当日新发，模型检验（TLC）覆盖修复序列。

## 背景与问题

`scx_bypass()` 把某调度器进逼时 propagate 到所有后代、并在宿主上 claim bypass dispatch，但只在该调度器自身 depth「跨零」时才做。子调度器自身的 bypass 若与祖先的 bypass 重叠：depth 不跨零 → 后代收不到 propagate → 祖先先退逼时后代提前离开 bypass；claim 要么泄漏（PM suspend 覆盖子 enable 时，下次 bypass 触发 `enable_bypass_dsp()` 的 `WARN_ON_ONCE()`）、要么从未取得（PM suspend 覆盖子 disable 时，resume 后任务滞留父级 bypass DSQ 无人消费）。

## 技术方案

两处改动（`kernel/sched/ext/ext.c`，+33/-21）：

- **Patch 1**：`scx_bypass()` 无论自身 depth 是否跨零都 propagate 每一层 depth 变化给后代，使后代 depth = 自身 + 祖先之和；并把「未变化即早退」移到 propagate 之后（祖先 depth 至少等于自身，只有自身状态变才会变）。
- **Patch 2**：propagate 时对「depth 从 0→1」的每个后代 `enable_bypass_dsp()` claim；并在 `!bypass` 且任务已移出 bypass DSQ 后，释放子树中 depth 归零的每个调度器的 claim。

作者用调试补丁把子 enable 的 bypass 保持跨 PM suspend 周期验证：修复前随后的 disable 必触发 WARN，修复后不再触发、子调度器任务每次 resume 后正常运行；claim 协议还经 TLC 模型检验。

## 版本演进与当前进展

v1 当日新发（`[PATCHSET sched_ext/for-7.3-fixes]`），基于 `sched_ext/for-7.3-fixes`（069403dff337），分支 `tj/sched_ext bypass-claim-fixes`。`Fixes:` c7f0e467a27a（1/2，Prepare bypass mode）与 aa2a0a19686c（2/2，Separate bypass dispatch enabling），均 `Cc: stable # v7.1+`。暂无他人回帖。

## Maintainer 意见与讨论焦点

作者即 sched_ext 维护者自提修复，方向明确、有 TLC 模型检验背书；无第三方异议点。

## 合入评估

*likelihood=high*。属维护者针对自己分支的 fix，标 `for-7.3-fixes` 且 `Cc: stable`，预期很快合入。*blocking_issues*：无。*next_action*：等待合入 `sched_ext/for-7.3-fixes` 分支。

## 效果评估

作者给出的验证：持有子 enable bypass 跨 PM suspend 周期，未修复内核在随后的 disable 上必触发 WARN，修复后不触发且任务每次 resume 后正常执行；claim 协议经 TLC 模型检验覆盖了本次修复序列。无性能数字。

## 我可以参与的点

维护者自提的确定性修复、有模型检验覆盖，当前阶段暂无明显参与空间。

## 参考链接

- lore（cover）: https://lore.kernel.org/all/20261011214028.743546-1-tj@kernel.org/
- lore（1/2）: https://lore.kernel.org/all/20261011214028.743546-2-tj@kernel.org/
- lore（2/2）: https://lore.kernel.org/all/20261011214028.743546-3-tj@kernel.org/
