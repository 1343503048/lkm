---
id: sched-20261119-002
date: '2026-11-19'
subject: 'sched/rt: Do not account migrate-disabled tasks as pushable'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261113160655.2909479-1-mgorman@techsingularity.net>
lore_url: https://lore.kernel.org/all/20261113160655.2909479-1-mgorman@techsingularity.net/
authors:
- Mel Gorman
maintainers_involved:
- Peter Zijlstra
current_version: v3
patch_series:
- version: v3
  msgid: <20261113160655.2909479-1-mgorman@techsingularity.net>
  date: '2026-11-13'
  summary: 单补丁：修 migrate-disabled 任务被计入 pushable 的记账缺陷
  review_outcome: Peter 追根溯源确认历史成因，倾向「we got it wrong」；Mel 实测坐实
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - v3 最终形态及 deadline 侧是否同步待定
  next_action: Mel 敲定最终补丁，Peter 收取
contribution_opportunities:
- kind: review
  description: 核对 Peter 定位的历史提交与 v3 修复是否严格对应、deadline 侧是否需同步
- kind: testing
  description: PREEMPT_RT 与非 RT 上验证落地后 pull IPI 不再命中 migrate-disabled 任务
generated_at: '2026-11-20T09:00:00+08:00'
source_email_count: 4
related_articles:
- sched-20261111-002
- sched-20261112-009
- sched-20261113-017
- sched-20261118-006
tags:
- rt
- rt_bandwidth
title: 'sched/rt: Do not account migrate-disabled tasks as pushable'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/11/sched-20261111-002-sched-rt-do-not-account-migrate-disabled-tasks-as-pushable.html">sched-20261111-002</a>：Mel Gorman 发补丁修 RT 类 pushable 记账缺陷——migrate-disabled 任务仍被放进 pushable 列表并置起 `rq->rt.overloaded`，导致其它 CPU 的 pull IPI 反复命中「推不动」的任务、制造无效 IPI。
- <a class="article-ref" href="/lkm/2026/11/12/sched-20261112-009-sched-rt-do-not-account-migrate-disabled-tasks-as-pushable.html">sched-20261112-009</a>：折叠为单补丁 v2，Peter 评审（问无条件保留 `is_migration_disabled()` 的副作用、请 deadline 侧做同样处理）。
- <a class="article-ref" href="/lkm/2026/11/13/sched-20261113-017-sched-rt-do-not-account-migrate-disabled-tasks-as-pushable.html">sched-20261113-017</a>：Mel 回应 Peter，宣布 v3 很快发出。
- <a class="article-ref" href="/lkm/2026/11/18/sched-20261118-006-sched-rt-do-not-account-migrate-disabled-tasks-as-pushab.html">sched-20261118-006</a>：Mel 论证 deadline 侧不能简单照搬，回溯 PREEMPT_RT 历史补丁 e18de5e2e3e9 与 612f769edd06，承认「不能证明自己一定对」。
- <a class="article-ref" href="/lkm/2026/11/19/sched-20261119-002-sched-rt-do-not-account-migrate-disabled-tasks-as-pushable.html">sched-20261119-002</a>（今天）：**问题收敛**——Peter 亲自翻 git 历史定位到 2020 年 migrate-disable 重构里 `nr_cpus_allowed` 停止更新的那个 commit，明确表态「**I'm leaning towards "we got it wrong"**」；Mel 用 `WARN_ON_ONCE` 在 PREEMPT_RT + `NO_RT_PUSH_IPI` 下实测复现，证明 !RT_PUSH_IPI 路径上确实会出现 migrate-disabled 任务（`nr_cpus_allowed` 该路径根本不更新）。方向已由历史证据 + 实测双重坐实。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/11/sched-20261111-002-sched-rt-do-not-account-migrate-disabled-tasks-as-pushable.html">sched-20261111-002</a> … 20261118-006）`enqueue_task_rt()`/`put_prev_task_rt()` 把 migrate-disabled 任务计为 pushable 并置起 `rq->rt.overloaded` 与 rto_mask，其它 CPU 的 pull IPI 可能只找到不可迁移任务。争论持续在「是否应无条件排除 `is_migration_disabled()` 任务」以及「deadline 侧是否要同样处理」。今日不再争论语义，而是回到源头查清「为什么当年允许 migrate-disabled 任务出现在 pushable/rto_mask 上」这个设计前提是否本来就有误。

## 技术方案

今日为结论性讨论、无新 v4：

- **Peter 的历史考古**：翻出 2020 年 migrate-disable 系列，指出第一版确实更新了 `nr_cpus_allowed`（`https://patch.msgid.link/20200921163845.769861942%40infradead.org`），但下一版就停止更新（`https://patch.msgid.link/20201005150921.859981475%40infradead.org`），一时找不到改动原因；随后定位到 `https://patch.msgid.link/20200924123527.GJ2628%40hirez.programming.kicks-ass.net`，据此倾向「当年这里就是搞错了」。
- **Mel 的实测**：在 `pull_rt_task()` 的 !RT_PUSH_IPI 路径把 `if (is_migration_disabled(p))` 临时改成 `WARN_ON_ONCE(is_migration_disabled(p))` 并加 printk，在 PREEMPT_RT + `echo NO_RT_PUSH_IPI > /sys/kernel/debug/sched/features` 下运行测试，**警告如期命中**（`WARNING: kernel/sched/rt.c:2350 at pull_rt_task`），证明该路径（`nr_cpus_allowed` 不更新的假设）是错的。

## 版本演进与当前进展

*current_version: v3（2026-11-13，`<20261113160655.2909479-1-mgorman@techsingularity.net>`）*。v1（三补丁）→ v2（单补丁）→ v3。今日无新版本，但「v3 提出的修复方向」获得历史与实测双重确认，等待落地决策。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（调度维护者）**：从「请 deadline 侧同样处理」转为亲自追根溯源，结论「I'm leaning towards "we got it wrong"」——即承认 migrate-disabled 任务被计入 pushable 是当年 migrate-disable 重构遗留的错误，方向与 Mel 的 v3 一致。
- **Mel Gorman（作者）**：以 `WARN_ON_ONCE` 实测坐实 Peter 的判断，并明确「这个假设是错的，`nr_cpus_allowed` 在该路径不更新」。
- 无 NAK；此前「deadline 侧是否同样处理」的跨类一致性争议，被「源头就错了」的结论部分消解（RT 侧记账错误是历史遗留，修复正当）。

## 合入评估

*likelihood=high*。维护者亲自确认了 bug 的历史成因并认可修复方向，加上作者给出现场复现证据，合入门槛基本清除。*blocking_issues*：v3 落地的具体形态（是否还要动 deadline 侧、`WARN_ON_ONCE` 调试代码是否保留）待定。*next_action*：Mel 基于今日结论敲定最终补丁（或澄清 deadline 侧），Peter 收取。

## 效果评估

今日无新 benchmark；验证性数据为 Mel 的 WARN 实测（PREEMPT_RT + NO_RT_PUSH_IPI 下警告如期触发）。修复价值仍是无条件消除无效 pull IPI（承接 20261111-002）。

## 我可以参与的点

- **review**：核对 Peter 定位的三个 2020 提交（尤其 20200924123527 那一版）与 Mel v3 的修复是否严格对应，评估「是否需同步修 deadline 侧」。
- **testing**：在非 PREEMPT_RT 与 PREEMPT_RT 两者上验证 v3 落地后 pull IPI 不再命中 migrate-disabled 任务。

## 参考链接

- lore thread（v3）: https://lore.kernel.org/all/20261113160655.2909479-1-mgorman@techsingularity.net/
- Peter「Tada / we got it wrong」: https://lore.kernel.org/all/20261119152827.GG2669272@noisy.programming.kicks-ass.net/
- Mel 的 WARN_ONCE 实测: https://lore.kernel.org/all/av7Pj6uBsSVAoxbZ@techsingularity.net/
