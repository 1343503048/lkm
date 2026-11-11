---
id: sched-20261111-002
date: '2026-11-11'
subject: 'sched/rt: Do not account migrate-disabled tasks as pushable'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261110232057.4144723-1-mgorman@techsingularity.net>
lore_url: https://lore.kernel.org/all/20261110232057.4144723-1-mgorman@techsingularity.net/
authors:
- Mel Gorman
- Yousaf Kaukab
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261110232057.4144723-1-mgorman@techsingularity.net>
  date: '2026-11-10'
  summary: 从 pushable 列表移除 migrate-disabled 任务，资格检查收拢一处，!RT_PUSH_IPI 保留原记账
  review_outcome: 暂无回复
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: 等待 RT/deadline 维护者评审
contribution_opportunities:
- kind: testing
  description: 复现 RT 优先级 spinlock 密集 pgrep 场景并量化 push-IPI 下降
- kind: review
  description: 核对 patch 1 的 -stable warning（单独 backport 是否破坏 !RT_PUSH_IPI）
generated_at: '2026-11-12T09:00:00+08:00'
source_email_count: 3
related_articles: []
tags:
- rt
- affinity
title: 'sched/rt: Do not account migrate-disabled tasks as pushable'
layout: article
---

## TL;DR

Mel Gorman 发三补丁系列修复 RT 类的 pushable 记账缺陷：`dae5c0292080`（"sched/rt,dl: Skip migrate-disabled tasks when picking a push candidate"）虽让 `pick_next_pushable_task()` 不再返回 migrate-disabled 任务，但 `enqueue_task_rt()`/`put_prev_task_rt()` 仍把这些任务放进 pushable 列表并把 rq 标记为 overloaded，导致其它 CPU 的 pull IPI 反复命中「推不动」的 migrate-disabled 任务、制造无效 IPI 风暴。系列把 migrate-disabled 任务从 pushable 列表移除，并把资格检查收拢到一处；同时为「无 RT_PUSH_IPI」的架构保留原记账（此时没有 IPI，pull 必须能找到 off-CPU 的 migrate-disabled 任务）。刚发出，暂无回复。

## 背景与问题

`dae5c0292080` 修掉了 `pick_next_pushable_task()` 返回 migrate-disabled 任务的问题，但其 changelog 自己点明了残留：runqueue 仍被 `enqueue_task_rt()`/`put_prev_task_rt()` 标记为 overloaded，因为被 pinned 的任务仍被通告为 pushable——其它 CPU 在自己的 RT balancing 里继续发 push-IPI，同样的循环不断重演。一个 migrate-disabled 任务会在被抢占时、或带着 migration disabled 醒来时，经这两条路径进入 pushable 列表并置起 `rq->rt.overloaded` 与 rto_mask；一旦置起，其它 CPU 每次 pull 触发的 IPI 可能只找到 migrate-disabled 任务，而这些任务根本不可迁移。触发本补丁的具体场景是一个跑在 RT 优先级、且 spinlock 密集的 `pgrep`（应用本可把它绑到别的 CPU，但底层问题是它不可迁移却又被通告为 pushable）。

## 技术方案

三补丁，RT 类单独处理、明确不动 deadline：

1. `Do not account migrate-disabled tasks as pushable`——`enqueue_task_rt()` 与 `put_prev_task_rt()` 的入列条件补上 `&& !is_migration_disabled(p)`，不再把 migrate-disabled 任务加入 pushable 列表。作者强调这不是启发式（migrate-disabled 任务确实无法移动），并刻意只改 RT：deadline 的 push 是为了把正运行的任务顶走、让 off-CPU 的 migrate-disabled DL 任务先跑，其代价有界且受 EDF 排序约束，需单独论证（作者在 changelog 里详述了 DL 侧两个决策点为何不在本系列范围）。
2. `Check eligibility of pushable task in one place`——把 `enqueue_pushable_task()` 两处调用点重复的资格检查上移到函数内，为 patch 3 铺路，无功能变化。
3. `Treat migrate-disabled tasks as pushable if RT_PUSH_IPI is disabled`——当 `HAVE_RT_PUSH_IPI` 不存在或 `RT_PUSH_IPI` 特性关闭时，没有 IPI，`pull_rt_task()` 必须能找到 off-CPU 的 migrate-disabled 任务的 rq，故在此配置下恢复「把 migrate-disabled 任务计为 pushable」的原记账。

patch 1 带 `-stable warning`：本系列必须整体应用，单独 backport patch 1 会破坏 `!RT_PUSH_IPI` 场景。

## 版本演进与当前进展

*current_version: v1（2026-11-10，`<20261110232057.4144723-1-mgorman@techsingularity.net>` 为 cover，patch 1 为 `<...-2-...>`）*。三封 patch 邮件当日收到，cover（0/3）未在缓存中。刚发出，暂无 review 意见。

## Maintainer 意见与讨论焦点

当日无维护者回复（系列刚发出）。作者在 patch 1 changelog 中主动预告了「为何不动 deadline」的论证与 `-stable` 应用约束，为后续评审做了铺垫。

## 合入评估

*likelihood=unknown*。刚发出、无任何回复，无法判断。*blocking_issues*：无（尚未有评审）。*next_action*：等待 RT/deadline 维护者（Peter Zijlstra / Juri Lelli 等）评审，重点是 DL 侧「是否也应同步移除」的既有分歧。

## 效果评估

作者未给量化数据，仅描述机制性收益：消除「IPI 反复命中不可迁移任务」的无效开销。属正确性/开销修复，未见 benchmark。

## 我可以参与的点

- **testing**：复现「RT 优先级的 spinlock 密集 pgrep」场景，对比补丁前后 push-IPI 计数（`/proc/schedstat` 或 trace），回帖量化无效 IPI 的下降幅度。
- **review**：核对 patch 1 的 `-stable warning`——确认单独 backport patch 1 是否真会破坏 `!RT_PUSH_IPI` 配置，这直接关系 stable 树要不要整套收。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261110232057.4144723-1-mgorman@techsingularity.net/
- patch 1: https://lore.kernel.org/all/20261110232057.4144723-2-mgorman@techsingularity.net/
