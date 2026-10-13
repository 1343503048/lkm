---
id: sched-20261013-016
subject: 'sched_ext: Fix bypass propagation and the bypass dispatch claim for overlapping
  bypasses'
date: 2026-10-13
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <20261011214028.743546-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20261011214028.743546-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
- Andrea Righi
current_version: v1
patch_series:
- version: v1
  msgid: <20261011214028.743546-1-tj@kernel.org>
  date: 2026-10-11
  summary: propagate + claim 修复重叠 bypass
  review_outcome: Andrea Reviewed-by，Tejun 应用到 sched_ext/for-7.3-fixes
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.3-fixes
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 随 sched_ext for-7.3-fixes pull request 进入 7.3 主线
contribution_opportunities: []
generated_at: '2026-10-14T01:00:00+08:00'
source_email_count: 2
related_articles:
- sched-20261012-003
tags:
- sched_ext
title: 'sched_ext: Fix bypass propagation and the bypass dispatch claim for overlapping
  bypasses'
layout: article
---

> **subject**：sched_ext: Fix bypass propagation and the bypass dispatch claim for overlapping bypasses

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-003-sched-ext-fix-bypass-propagation-and-the-bypass-dispatch-cla.html">sched-20261012-003</a>：sched_ext 维护者 Tejun Heo 发 2 补丁修复（挂 `sched_ext/for-7.3-fixes`）：`scx_bypass()` 只在自身 depth 跨零时才 propagate 并 claim，导致子调度器 bypass 与祖先 bypass 重叠时后代提前退逼、claim 泄漏或从未取得（PM suspend 覆盖子 enable/disable 会触发 WARN 或任务滞留父级 bypass DSQ）。
- <a class="article-ref" href="/lkm/2026/10/13/sched-20261013-016-sched-ext-fix-bypass-propagation-and-the-bypass-dispatch-cla.html">sched-20261013-016</a>（今天）：Andrea Righi 对整系列给 `Reviewed-by`；Tejun Heo 已把 1-2 **Applied 到 sched_ext/for-7.3-fixes** 并给两个补丁都追加 `Reviewed-by: Andrea Righi` 标签。

## 背景与问题
（承接 20261012-003）`scx_bypass()` 把调度器进逼 propagate 到所有后代并在宿主上 claim bypass dispatch，但只在自身 depth「跨零」时执行；子调度器自身 bypass 与祖先 bypass 重叠时 depth 不跨零 → 后代收不到 propagate → 祖先先退逼时后代提前离开 bypass；claim 要么泄漏（PM suspend 覆盖子 enable，下次 bypass 触发 `enable_bypass_dsp()` 的 `WARN_ON_ONCE()`）、要么从未取得（PM suspend 覆盖子 disable，resume 后任务滞留父级 bypass DSQ 无人消费）。

## 技术方案
（承接 20261012-003）两补丁（`kernel/sched/ext/ext.c`）：
- **Patch 1**：`scx_bypass()` 无论自身 depth 是否跨零都 propagate 每层 depth 变化；「未变化即早退」移到 propagate 之后。
- **Patch 2**：propagate 时对 depth 0→1 的各后代 `enable_bypass_dsp()` claim；`!bypass` 且任务移出 bypass DSQ 后释放子树中 depth 归零的调度器 claim。

作者此前用「子 enable 的 bypass 跨 PM suspend 周期」的调试补丁验证：修复前 disable 必触发 WARN、修复后不再触发；claim 协议经 TLC 模型检验。今日无代码变化，仅完成 review 流程并合入。

## 版本演进与当前进展
v1（`<20261011214028.743546-1-tj@kernel.org>`）。今日 Andrea Righi 全系列 `Reviewed-by`，Tejun 应用 1-2 到 `sched_ext/for-7.3-fixes`。

## Maintainer 意见与讨论焦点
- **Tejun Heo**（sched_ext 维护者/作者）：已应用 1-2 到 `for-7.3-fixes`。
- **Andrea Righi**（sched_ext 维护者）：对整系列 `Reviewed-by`。
- 无异议；流程已走完。

## 合入评估
*likelihood=merged*。已合入 `sched_ext/for-7.3-fixes`，可从 sched_ext 修复分支/后续 pull request 进入 7.3。*blocking_issues*：无。*next_action*：随 sched_ext for-7.3-fixes 的 pull request 进入主线（关注 7.3 最终版）。

## 效果评估
作者此前给出验证：修复前 PM suspend 覆盖子 enable 后随后的 disable 必触发 `enable_bypass_dsp()` WARN，修复后不再触发、子调度器任务每次 resume 后正常运行；claim 协议经 TLC 模型检验。无性能数字（属正确性修复）。

## 我可以参与的点
当前阶段暂无明显参与空间（已合入修复分支）；可持续观察是否随 7.3 pull request 进入主线及 stable。

## 参考链接
- 系列 cover lore：https://lore.kernel.org/all/20261011214028.743546-1-tj@kernel.org/
- 合入回帖：https://lore.kernel.org/all/03d78d3346d0a0aacdae06c07550775d@kernel.org/
