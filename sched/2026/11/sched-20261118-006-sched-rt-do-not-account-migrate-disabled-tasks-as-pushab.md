# sched/rt: Do not account migrate-disabled tasks as pushable

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261111-002：Mel Gorman 发三补丁修 RT 类 pushable 记账缺陷——migrate-disabled 任务仍被放进 pushable 列表并置起 `rq->rt.overloaded`，导致其它 CPU 的 pull IPI 反复命中「推不动」的任务、制造无效 IPI。
- sched-20261112-009：折叠为单补丁 v2，Peter 评审（问无条件保留 `is_migration_disabled()` 的副作用、请对 deadline 侧做同样处理）。
- sched-20261113-017：Mel 回应 Peter，宣布 v3 很快发出。
- sched-20261118-006（今天）：**Mel 详细分析为何 deadline 侧不能简单照搬 `is_migration_disabled()`**（deadline 无 RT_PUSH_IPI；即便有 `nr_cpus_allowed > 1` 检查，!IPI 路径在两个类里都假设 migrate-disabled 任务可见），回溯 PREEMPT_RT 历史补丁 e18de5e2e3e9 与 612f769edd06 的来龙去脉，承认「不能证明自己一定对」。

## 背景与问题

（承接 sched-20261111-002 … 20261113-017）`enqueue_task_rt()`/`put_prev_task_rt()` 把 migrate-disabled 任务计为 pushable 并置起 `rq->rt.overloaded` 与 rto_mask，其它 CPU 的 pull IPI 可能只找到不可迁移任务。今日收口在「deadline 侧是否应加同样的 `is_migration_disabled()` 检查」这个跨类一致性问题。

## 技术方案

今日为评审讨论、无新代码（v3 已在途）：

- Mel 详细走读 rt.c 的「!IPI 路径」（`HAVE_RT_PUSH_IPI` 未定义或 `RT_PUSH_IPI` 关闭时的 `pull_rt_task()` 循环）——该路径的 `if (is_migration_disabled(p)) { push_task = get_push_task(src_rq); }` 假设 migrate-disabled 任务**可以**出现在 rto_mask 上，且已如此多年。
- deadline 侧没有 push IPI；若照搬 `is_migration_disabled()` 检查，在多个更早 deadline 可运行任务 + 1 个 migrate-disabled 任务共存的 rq 上，可能把可迁移任务隐藏为 push 候选或反之，难以察觉。
- 回溯：PREEMPT_RT 一度持有 e18de5e2e3e9（"sched/rt: Don't try push tasks if there are none."），约 6.7 被移除（因 612f769edd06 让 rt_rq->pushable_tasks 驱动 rto_mask）；distro 内核里的 PREEMPT_RT 补丁曾干扰该 bug 的观测。

## 版本演进与当前进展

v1（三补丁）→ v2（单补丁）→ v3（2026-11-13 发出，`<20261113160655.2909479-1-mgorman@techsingularity.net>`）。今日为对 v3 的深入讨论，无新版本。

## Maintainer 意见与讨论焦点

- **Mel Gorman（作者）**：详细论证为何 deadline 侧不能简单照搬 `is_migration_disabled()`（无 RT_PUSH_IPI、!IPI 路径的既有假设），并自我声明「不能说这就一定对，只是难以证明」——态度诚实，未强行推进。
- **Peter Zijlstra**（此前）：请对 deadline 侧做同样处理（今日未见新回复，Mel 此封为对更早 Peter 提问的回应）。
- 无 NAK；分歧点仍是「RT 与 DL 是否应完全同步 `migrate-disabled` 可见性语义」。

## 合入评估

*likelihood=high*。系列已收敛为单补丁、维护者持续介入，作者论证充分。*blocking_issues*：RT/DL 两侧语义是否同步仍未完全关闭。*next_action*：v3 落地或 Peter 对 RT/DL 同步性给出定论。

## 效果评估

无今日新增 benchmark；此前结论为消除无效 pull IPI（承接 20261111-002）。

## 我可以参与的点

- **review**：评估 Mel 对 deadline 侧「不应照搬 is_migration_disabled()」的论证是否成立（尤其多 deadline 任务 + migrate-disabled 任务共存的候选隐藏问题）。
- **testing**：在 PREEMPT_RT 构建下测 migrate-disabled 任务是否不再触发无效 pull IPI。

## 参考链接

- lore thread（v3）: https://lore.kernel.org/all/20261113160655.2909479-1-mgorman@techsingularity.net/
- Mel 今日回应: https://lore.kernel.org/all/av1q-2D_tdi9oNEj@techsingularity.net/

---
id: sched-20261118-006
date: '2026-11-18'
subject: "sched/rt: Do not account migrate-disabled tasks as pushable"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261113160655.2909479-1-mgorman@techsingularity.net>"
lore_url: "https://lore.kernel.org/all/20261113160655.2909479-1-mgorman@techsingularity.net/"
authors: [Mel Gorman]
maintainers_involved: [Peter Zijlstra]
current_version: v3
patch_series:
  - version: v2
    msgid: null
    date: '2026-11-12'
    summary: "折叠为单补丁"
    review_outcome: "Peter 问副作用、请 deadline 侧同样处理"
  - version: v3
    msgid: "<20261113160655.2909479-1-mgorman@techsingularity.net>"
    date: '2026-11-13'
    summary: "单补丁，移动 nr_cpus_allowed > 1 检查"
    review_outcome: "今日 Mel 论证 deadline 侧不能照搬"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["RT/DL 两侧同步语义未完全关闭"]
  next_action: "v3 落地或 Peter 对 RT/DL 同步性定论"
contribution_opportunities:
  - kind: review
    description: "评估 deadline 侧不应照搬 is_migration_disabled 的论证"
  - kind: testing
    description: "PREEMPT_RT 构建下验证无效 pull IPI 消失"
generated_at: "2026-11-19T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261113-017]
tags: [rt, rt_bandwidth]
---
