# sched/rt: Do not account migrate-disabled tasks as pushable

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261111-002：Mel Gorman 发补丁修 RT 类 pushable 记账缺陷（migrate-disabled 任务被计入 pushable → 无效 pull IPI）。
- sched-20261112-009 … 20261119-002：v2 单补丁，Peter 追根溯源定位到 2020 年 migrate-disable 重构里 `nr_cpus_allowed` 停止更新的 commit，表态「we got it wrong」；Mel 用 `WARN_ON_ONCE` 实测坐实。
- sched-20261120-016（今天）：**修复方案进一步收窄**——Peter 指出改 `nr_cpus_allowed` 语义需处理 `set_cpus_allowed_ptr()` 并发、不 trivial，「眼下最简单是到处撒 `is_migration_disabled()`」；Mel 长篇论证 `RT_PUSH_IPI` 检查必须保留（deadline 根本没有 PUSH_IPI）、改 `nr_cpus_allowed` 语义会波及 `mm_init_cid`/`update_misfit_status`/`is_per_cpu_kthread` 等多处「用 nr_cpus_allowed 判 pin」的代码。

## 背景与问题

（承接）migrate-disabled 任务仍被计入 RT pushable/rto_mask，其它 CPU 的 pull IPI 可能只找到推不动的任务。问题根源已查清：2020 年 migrate-disable 重构让 `nr_cpus_allowed` 在该路径停止更新，属历史遗留错误。今日讨论从「是否错」转入「怎么修才安全」。

## 技术方案

今日为方向收敛、无新 patch：

- **Peter**：`nr_cpus_allowed` 的现行规则是「`p->cpus_mask` 的位数」，改它要面对并发 `set_cpus_allowed_ptr()`；「不确信改起来 trivial」，主张眼下就「多撒 `is_migration_disabled()`」。
- **Mel**：长篇辨析改 `nr_cpus_allowed` 语义的代价——`set_cpus_allowed_ptr` 用 `cpus_ptr` 只免掉 `cpumask_copy`/`cpumask_weight`/`mm_update_cpus_allowed`；但 `mm_init_cid`（mm 域非 task 域，有竞态）、`update_misfit_status`（用 `nr_cpus_allowed==1` 判 pinning）、`is_per_cpu_kthread()`、以及「把运行中任务推走给 migrate-disabled 任务腾 CPU」的 helper 都隐含依赖该语义，逐个 audit 成本高。结论：`RT_PUSH_IPI` 检查必须保留（deadline 没有 PUSH_IPI，单独引入会被拒），对「无效 IPI」的简单修复保留该检查即可。

## 版本演进与当前进展

*current_version: v3（2026-11-13，`<20261113160655.2909479-1-mgorman@techsingularity.net>`，后续见 related）*。今日无新版本，但修复方案由「改 `nr_cpus_allowed`」收窄为「保留 `RT_PUSH_IPI` + 多撒 `is_migration_disabled()`」。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（调度维护者）**：明确改 `nr_cpus_allowed` 不 trivial（并发 set_cpus_allowed_ptr），眼下用「撒 is_migration_disabled()」简单方案。
- **Mel Gorman（作者）**：长篇论证 `RT_PUSH_IPI` 检查的必要性与改 `nr_cpus_allowed` 语义的连带风险。
- 无 NAK；「问题确实错了」已定论，分歧仅在修复的最小形态。

## 合入评估

*likelihood=medium*。方向已由历史证据 + 实测双重坐实，但「简单方案」（撒 is_migration_disabled vs 保留 RT_PUSH_IPI 检查）的具体形态尚未落成新版。*blocking_issues*：修复最终形态未定、尚未出新版。*next_action*：Mel/Peter 就最小修复形态达成一致后出 v4。

## 效果评估

无新数据；此前 Mel 的 `WARN_ON_ONCE` 实测已证明 `nr_cpus_allowed` 在 !RT_PUSH_IPI 路径不更新（见 related）。

## 我可以参与的点

- **review**：核对「保留 RT_PUSH_IPI 检查 + 撒 is_migration_disabled()」是否覆盖 pushable/rto_mask 记账的全部入口；评估 deadline 侧是否需要对称处理。
- **discussion**：就 Mel 列的 `nr_cpus_allowed` 语义依赖点（mm_init_cid/update_misfit_status/is_per_cpu_kthread）逐一给出是否受影响的判断。

## 参考链接

- lore thread（Peter 回复）: https://lore.kernel.org/all/20261119164050.GJ1922751@noisy.programming.kicks-ass.net/
- Mel 回复: https://lore.kernel.org/all/av9x3iMaKhtByVzM@techsingularity.net/

---
id: sched-20261120-016
date: '2026-11-20'
subject: "sched/rt: Do not account migrate-disabled tasks as pushable"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261113160655.2909479-1-mgorman@techsingularity.net>"
lore_url: "https://lore.kernel.org/all/av9x3iMaKhtByVzM@techsingularity.net/"
authors: [Mel Gorman]
maintainers_involved: [Peter Zijlstra]
current_version: v3
patch_series:
  - version: v3
    msgid: "<20261113160655.2909479-1-mgorman@techsingularity.net>"
    date: '2026-11-13'
    summary: "单补丁：修 migrate-disabled 任务被计入 pushable 的缺陷"
    review_outcome: "Peter/Mel 收窄修复形态为「保留 RT_PUSH_IPI + 撒 is_migration_disabled」"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["修复最终形态未定", "尚未出新版"]
  next_action: "Mel/Peter 就最小修复形态一致后出 v4"
contribution_opportunities:
  - kind: review
    description: "核对撒 is_migration_disabled 是否覆盖 pushable/rto_mask 全部入口及 deadline 侧对称性"
  - kind: discussion
    description: "就 nr_cpus_allowed 语义依赖点逐一给出是否受影响判断"
generated_at: "2026-11-21T09:00:00+08:00"
source_email_count: 216
related_articles: [sched-20261111-002, sched-20261112-009, sched-20261113-017, sched-20261118-006, sched-20261119-002]
tags: [rt]
---