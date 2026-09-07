---
id: sched-20260829-003
date: '2026-08-29'
subject: Cache-aware scheduling does not work well with amd big/little cores
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: <2180ea5a-eb28-4152-8d4d-cd00b0c24b2e@computerix.info>
lore_url: https://lore.kernel.org/all/2180ea5a-eb28-4152-8d4d-cd00b0c24b2e@computerix.info/
authors:
- Klaus Kusche
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 当日无任何维护者回复，无人接手
  - 报告无 benchmark、无 trace、无内核版本边界，只有主观观察
  - 报告者要求的'容量优先于缓存'策略反转没有对应补丁
  next_action: 社区需给出容量与 LLC 局部性的优先级判据；需要第三方在混合架构上提供量化数据
contribution_opportunities:
- kind: discussion
  description: 用 sched_debug/perf 把'单任务被 CAS 钉在小核域'的判定路径（can_migrate_llc/alb_break_llc/LBF_LLC_PINNED）做成可引用的数据回帖
- kind: extend
  description: 提出目的 LLC 完全空闲且容量更高时让 CAS 放行（返回 mig_unrestricted）的最小改动
- kind: review
  description: 评估 OLK-6.6 上 CAS 与混合架构容量调度并存的策略冲突风险
generated_at: '2026-09-07T22:06:23'
source_email_count: 1
related_articles:
- sched-20260826-010
- sched-20260831-006
tags:
- load_balance
- regression
- x86
title: Cache-aware scheduling does not work well with amd big/little cores
layout: article
---

## TL;DR

Klaus Kusche（8/29 新线程）报告：AMD Ryzen HX 370（Zen 混合架构）上，一个跑满数分钟的 LTO 链接进程**即使大核全空闲也不会被迁走**——因为所有大核构成一个 L3 域、所有小核构成另一个域，任务一旦起在小核域就把它当成了 preferred LLC，CAS 的局部性判定压过了大/小核容量调度。诉求很直接：**长时任务遇到空闲大核时，容量应压过缓存局部性**。当天只有报告本身、无人回复。对任何有混合架构形态的调度栈，这是 CAS 上线后一个可预期的策略冲突，值得跟。

## 背景与问题

- **平台/负载**：AMD Ryzen HX 370（Zen 大核 + 小核），Gentoo，用 Clang full-LTO 编译大量东西（含内核）；LTO 链接的形态是**单个进程连续跑几分钟**，机器其余部分基本空闲。
- **症状**：CAS 引入之前，AMD pstate 驱动把大/小核容量差异告诉调度器，LTO 进程会被挪到大核；CAS 引入后不再挪，"哪怕所有大核空闲几分钟"。
- **为什么在 LTO 上伤两次**（报告者原话整理）：小核 3.3 GHz vs 大核 5.1 GHz；且 LTO 是 cache 密集型，而小核 L3 只有 8 MB、大核 16 MB——聚合的局部性红利也拿不到。
- **影响范围**：所有存在 `SD_ASYM_CPUCAPACITY` 形态、且开启了 cache aware scheduling 的平台（AMD Zen 客户端、Intel 混合架构、ARM big.LITTLE 同理）。
- **严重度自评**：报告者称"not just noticeably, but dramatically"变慢，但未给数字（见"效果评估"）。

## 技术方案

本邮件是 bug 报告，不含补丁。它给出的**期望方案**是策略层的：在"目的域存在空闲且容量更高的 CPU、而源任务已长时间运行"时，让大/小核（容量）调度**覆盖**cache-aware 调度，即使这次移动跨缓存域。

结合主线代码（`/home/zq/code/linux`，v7.2-rc6 量级；以下为我读代码所得，非邮件内容）能定位为什么今天会被拦死，三处叠加：

- `can_migrate_llc()` 在 `to_pref == false`（离开 preferred LLC）时，只要源域还"装得下"（`fits_llc_capacity(src_util, src_cap)`）或目的域没比源域明显更闲（`!util_greater(src_util, dst_util)`），就返回 `mig_forbid`。空闲大核域 util≈0、小核域只有这一个任务，两个条件同时成立 → 禁止外迁。
- `alb_break_llc()` 在 active balance 入口额外兜了一层否决：`env->src_rq->nr_running <= 1` 时直接 `return true`（"唯一可运行任务，不值得破坏局部性"）——这恰好就是"单进程 + 空闲机器"的场景。
- 逃生门被有意关掉了：`migrate_degrades_llc()` 允许在 `sd->nr_balance_failed >= cache_nice_tries + 1` 时忽略 LLC 约束，但主循环里对因 LLC 局部性而没搬成任务的情况带 `LBF_LLC_PINNED` 标志**不累加** `nr_balance_failed`（注释明说这是 expected behavior），所以"失败太多次就放弃局部性"这条路径永远走不到。
- 小核→大核的常规"上迁移"通道是 misfit（`rq->misfit_task_load` / `migrate_misfit`），它要求任务的 util 超出所在 CPU 容量。一个单线程 CPU-bound 任务的 util 会饱和在小核自身容量附近，因此**多数时候不构成 misfit**——这正是报告者看到"没人来救"的原因，也是为什么修复方向落在 misfit 判定而不是给 CAS 加新机制。

相关的上游动作（非本邮件内容）：Tim Chen 8/25 的 `[PATCH] sched/fair: avoid creating misfits during cache-aware balancing` 走的就是"在 CAS 判定里尊重容量、别把任务做成 misfit"这条路，已在 sched-20260826-010 分析过；8/31 Chen Yu 在该报告线程里确认"当前代码里 CAS 覆盖了非对称调度策略"并把这份补丁指向报告者，见 sched-20260831-006。

## 版本演进与当前进展

- 8/29 23:42（北京时间）：Klaus Kusche 发出报告，**当日线程内无任何回复**，也没有 `Reported-by`/补丁被关联。
- 8/31：Chen Yu 确认根因并指向 Tim Chen 的 misfit 补丁；报告者回报实测有效（见 sched-20260831-006）。
- 本报告自身不携带补丁，因此没有版本演进可言；对应修复补丁当日仍是 v1。

## Maintainer 意见与讨论焦点

- 本日内**没有任何维护者表态**（唯一的邮件就是报告本身），这是它当时最大的不确定性：一份来自用户、带清晰策略诉求但没有 trace/benchmark 的报告，很容易被搁置。
- 争议焦点是**优先级顺序**而非代码正确性：CAS 的域划分（大核集合 = 一个 L3 域、小核集合 = 另一个）本身按缓存拓扑是"对"的，问题在于它没有与 capacity 维度建立序关系。报告者主张容量优先；现有实现是局部性优先、只有 misfit 这一例外通道。
- 未被回答的问题：①"长时任务"的判据该用什么（运行时长、util、还是 nr_running 老化）？②除了完全空闲的大核域，部分空闲时怎么办？③`invalid_llc_nr()`/`exceed_llc_capacity()` 这类"CAS 自动放弃聚合"的条件在混合架构上是否本该把容量差异算进去。当日无人讨论。

## 合入评估

**unclear**（就"容量优先于缓存"这一策略诉求而言）。报告本身不产生可合入物。当日能观察到的事实是：问题被完整描述、无人反对、也无人接手；后续（8/31）社区给出的答案是复用 misfit 路线的局部修复，而不是报告者要求的通用优先级反转。因此"报告者的诉求被完整满足"可能性偏低，而"以 misfit 防护的形式部分收口"已在推进（那条补丁的合入评估见 sched-20260831-006，为 likely）。

## 效果评估

**无数据，全部为主观观察**。报告者自述只用每核负载柱状图看现象，比较的是"以前的内核"与"现在"，没有给出耗时数字、内核版本边界或 perf/schedstat 计数（`lb_balance_failed`、`nr_balance_failed`、`lb_imbalance_llc` 一类可以证明"被 LLC 拦住"的数据都没提供）。"LTO 明显变慢"目前属于个案报告，不能当结论引用。

## 我可以参与的点

- **把机制写实并回帖**：本报告缺的是证据链。在任意混合架构（含 ARM big.LITTLE）上开 CAS，跑一个单线程长时间 CPU-bound 任务，用 `perf stat -e 'sched:*'` 或 `sched_debug` 里的 `nr_pref_llc_running`/`lb_*` 计数，配合 trace `can_migrate_llc()`/`alb_break_llc()` 的返回值，就能把"被 LLC 判定拦住"从推测变成数据，同时回答 `nr_balance_failed` 被 `LBF_LLC_PINNED` 屏蔽是否合理。
- **提出"长时"判据的设计**：报告者要的优先级反转至今无人给出具体机制。可以量化一种最小改动（例如在 `can_migrate_llc(to_pref=false)` 分支里，当目的 LLC 完全空闲且容量更高时返回 `mig_unrestricted`），先拿数据再发 RFC。
- **关注 `nr_balance_failed` 这条逃生门**：CAS 把因局部性而未搬家的情况排除在失败计数外，等于取消了原本的软失效兜底；这是一个可独立讨论、可能独立成 patch 的点。
- **回合判断**：OLK-6.6 若有 CAS 回合计划或已在带，混合架构上的这条策略冲突属于必须提前评估的风险；本条与 Tim Chen 的 misfit 补丁应一并纳入回合清单。

## 参考链接

- lore thread（本报告，当日唯一邮件）: https://lore.kernel.org/all/2180ea5a-eb28-4152-8d4d-cd00b0c24b2e@computerix.info/
- 相关修复补丁（Tim Chen，8/25）: https://lore.kernel.org/all/20260825174112.2580942-1-tim.c.chen@linux.intel.com/
- 本报告线程的后续讨论（8/31 分析）: 见 sched-20260831-006
- tip-bot commit: 未获取到
- stable backport: 未获取到
