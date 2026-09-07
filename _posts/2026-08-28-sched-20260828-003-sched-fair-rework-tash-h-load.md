---
id: sched-20260828-003
date: '2026-08-28'
subject: 'sched/fair: Rework tash_h_load()'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260828074059.232353141@infradead.org>
lore_url: https://lore.kernel.org/all/20260828074059.232353141@infradead.org/
authors:
- Peter Zijlstra
maintainers_involved:
- Peter Zijlstra
- Vincent Guittot
current_version: null
patch_series:
- version: v1
  msgid: <20260828074059.232353141@infradead.org>
  date: '2026-08-28'
  summary: task_tick 参数改名 queued->hrtick；for_each_sched_entity() 吸收 cfs_rq_of() 并新增
    cfs_rq->backlink；task_h_load() 重做为在持 rq->lock 的记账点更新、限流改用 PELT 段
  review_outcome: 当日无回帖；作者自评 Lightly tested...；2/4 非 group-sched 分支有 cfs_of_of 笔误
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 当日无 review；作者自评 Lightly tested...
  - 无 Fixes 标签，且原始缺陷讨论走了私邮、公开侧无复现
  - backlink 引入每 cfs_rq 额外指针与热路径 store，代价未评估
  next_action: 等 Vincent Guittot 评审；作者补充错算 h_load 的可观测症状与 debug 输出对比
contribution_opportunities:
- kind: review
  description: 回帖指出 2/4 在 !CONFIG_FAIR_GROUP_SCHED 分支的 cfs_of_of 笔误（全树无该符号）
- kind: testing
  description: 补 !CONFIG_FAIR_GROUP_SCHED 编译验证与 /proc/sched_debug 里 h_load 新鲜度前后对比
- kind: testing
  description: 多层 cpu.weight 悬殊 + cpu.max 限流场景下验证负载均衡决策是否改变
generated_at: '2026-09-07T22:08:24'
source_email_count: 5
related_articles:
- sched-20260824-009
- sched-20260831-003
tags:
- cfs
- cgroup
- load_balance
- sched_debug
title: 'sched/fair: Rework tash_h_load()'
layout: article
---

## TL;DR

Peter Zijlstra 8/28 发出 4 补丁系列（cover letter 标题里的 `tash_h_load` 是作者自己的笔误），重做 cgroup 层级负载 `cfs_rq->h_load` 的计算。他给 `task_h_load()` 定了三条罪名：**层级遍历对 rq->lock 的依赖从未被断言、因而本质上是有竞态的"broken"**；限流用的是 jiffies（=HZ）而不是 PELT 衰减；更新时机绑在 `task_h_load()` 被调用那一刻，导致 `sched/debug` 里打印的 `h_load` 几乎永远是过期值。手法是把 back-link 追踪塞进 `for_each_sched_entity()` 宏，再在 enqueue/dequeue/set_next/tick 这些**确定持 rq->lock** 的位置顺手把 `h_load` 算新。作者自评 "Lightly tested..."。当日无回帖；8/31 起 Vincent Guittot 与 Chen Yu 介入讨论（站内 sched-20260831-003 记录）。对用 cgroup CPU 负载均衡的用户，这块是直接影响迁移决策正确性的。

## 背景与问题

Cover letter 只给了动机不给细节："So task_h_load() has been known buggered for a while [1], and while looking at [2] I ran into it again."，其中 [1] 他注明是一封**最终走了私有邮件、没上列表的讨论**（"email that unfortunately ended up private with Vincent"），[2] 是 `https://lore.kernel.org/all/aoxah90s0bQ4tcUW@three-body/`。也就是说这个 bug 的公开讨论历史本身不完整，PZ 是在处理另一件事时又撞到它。

`4/4` 的 commit message 是问题清单的正式版本：

- 层级遍历"is racy to the point of being broken"——原本设计是在 `rq->lock` 下用，但**缺少断言**，于是用法扩散并违反了这个前提，结果是 back-link 状态易受竞态影响。
- 限流基于 jiffies，粒度是 HZ，而不是底层 PELT 衰减。
- 由于更新绑在 `task_h_load()` 的调用上，`cfs_rq->h_load` 大多不是"新鲜值"，"rendering their output in sched/debug near useless"。

`h_load` 的用途是负载均衡时估算某 task group 层级在一个 CPU 上的等效负载（`task_h_load()` 被 `task_h_load_calc()`/`can_migrate_task()` 的 group 相关判断使用），错了会直接影响"要不要把这个组里的任务搬走"。

## 技术方案

四步递进，前三步是为第四步铺路：

1. **1/4 `sched: Rename/clarify sched_class::task_tick(.queued) argument`**：把 `task_tick()` 第三个参数 `@queued` 全量改名 `@hrtick`（fair/rt/dl/scx/idle 与 `sched.h`）。PZ 的原话："For some reason the sched_class::task_tick() argument that indicates it being an hrtick, is called @queued. I'm sure naming is hard and all, but lets fix this." 这一步是语义准备：后面的 h_load 更新要挂在 tick 上，先把 tick 的两个入口（周期 tick 与 hrtick）区分清楚。
2. **2/4 `sched/fair: Fold cfs_rq_of(se) into for_each_sched_entity()`**：宏签名从 `for_each_sched_entity(se)` 改为 `for_each_sched_entity(se, cfs_rq)`，把"几乎每个循环第一句都是 `cfs_rq = cfs_rq_of(se)`"吸收进宏，37 增 44 删。目的是让宏能**透明地**记录 back-link。
3. **3/4 `sched/fair: Extend for_each_sched_entity() with a back-link`**：`struct cfs_rq` 新增 `struct sched_entity *backlink;`，宏在每次迭代把上一个 `se` 写进 `(cfs_rq)->backlink`，从而可以**自顶向下走回来**；同时新增反向遍历宏 `for_each_sched_entity_bl(se, cfs_rq)`。作者注明 "No actual users yet, but split out because its a bit tricky."
4. **4/4 `sched/fair: Rework/fix task_h_load()`**：新增 `__update_cfs_rq_h_load()`/`update_cfs_rq_h_load()`——root cfs_rq 直接取 `cfs_rq->avg.load_avg`，否则用父层 `p_cfs_rq->h_load * se->avg.load_avg / (p_cfs_rq->avg.load_avg + 1)` 递推，并 `WRITE_ONCE()` 发布。限流判据从 jiffies 换成 **PELT 段**：

   ```
   if ((cfs_rq->last_h_load_update & ~PELT_SEGMENT_MASK) ==
       (cfs_rq->avg.last_update_time & ~PELT_SEGMENT_MASK))
           return false;
   ```

   即"自上次以来没有发生衰减就不重算"。更新点挂在 `enqueue_hierarchy()`、`dequeue_hierarchy()`、`set_next_entity()` 与 tick（都是持 `rq->lock` 的位置），另外让 `__update_blocked_fair()` 在为 leaf cfs_rq 做衰减时顺带更新整条链上的 `h_load`。旧的 `update_cfs_rq_h_load()`（先正向走一遍记 `h_load_next`、再倒回来的那套）被整体删除。

关键取舍：**不加锁、不新增同步**，而是把"何时算得对"收敛到本来就有 `rq->lock` 的少数几个记账点，用 `backlink` 换取"能从上往下重算"的能力。被放弃的路线（隐含在 commit message 里）是"在 `task_h_load()` 里补断言/补锁"——PZ 选择让数据常年保持新鲜，而不是让读取端去证明安全。

## 版本演进与当前进展

- 8/28 15:40 首发，subject 不带版本号（PZ 习惯）。作者自述 "Lightly tested..."。
- 当日（8/28）无任何回帖。
- 后续：8/31 站内 sched-20260831-003 记录了 Vincent Guittot 与 Peter Zijlstra 就"两个可为 NULL 的参数需要注释"的收口式讨论，方向已无异议。

## Maintainer 意见与讨论焦点

当日**无人回帖**，因此没有可归类的社区意见。可以确定的两点：

- 作者本人把该函数判定为"broken"而不是"imprecise"，并公开承认"known buggered for a while"且相关讨论曾落到私邮——这对评审者是负面信号：缺少一份能说明"错到哪个程度"的公开复现。
- 1/4 是纯改名，2/4/3/4 是接口重构，真正的行为变化集中在 4/4。这种"把一个 fix 藏在 4 个 prep patch 之后"的拆法，容易被要求把 fix 与 cleanup 分开或至少单独带 `Fixes:`——本系列**没有任何 `Fixes:` 标签**。

## 合入评估

**likelihood: possible**。

- 有利：作者是 sched 维护者；重构方向（把易竞态的即时计算改成常驻新鲜的记账）能同时解决 `sched/debug` 输出无用的问题，收益清晰；改名/宏折叠这类 prep patch 争议成本低。
- 卡点：没有 `Fixes:`、没有公开的缺陷复现、作者自评 "Lightly tested..."；`backlink` 是每 `cfs_rq` 一个指针（group-sched 下随 task_group 数与 CPU 数乘积放大），且写入点在**每次** `for_each_sched_entity()` 遍历中，属于热路径新增 store；`h_load` 更新点扩散到 enqueue/dequeue/tick/blocked-update，需要验证与 PELT 的 `propagate`、与 burstable 组 `cpu.max.burst` 那类改动不互相打架。
- `next_action`：等 Vincent Guittot（唯一在原始讨论里的另一方）review；作者补一句"错算 h_load 会看到什么症状"，或者给出 `sched/debug` 前后对比。

## 效果评估

无性能数字。唯一可归为"效果"的表述是作者对现状的定性判断：`cfs_rq->h_load` 在 `sched/debug` 里"near useless"，以及本系列将"确保活跃 cgroup 的 `cfs_rq->h_load` 有 reasonably up-to-date 的值"——**作者主观判断，未见测试数据**。`Lightly tested...` 说明连功能覆盖面都有限。

## 我可以参与的点

- **回帖指出一个笔误**（成本最低、确定性最高）：2/4 在 `!CONFIG_FAIR_GROUP_SCHED` 分支里把宏写成了

  ```
  +#define for_each_sched_entity(se, cfs_rq)   +	for (; (se) && ((cfs_rq) = cfs_of_of(se)); (se) = NULL)
  ```

  `cfs_of_of` 全树不存在（主线 `grep -rn cfs_of_of` 无命中），该宏在非 group-sched 配置下被展开时必然编译失败。配合作者 "Lightly tested..." 的自述，这条对上游有实际价值。
- **补 `!CONFIG_FAIR_GROUP_SCHED` / `CONFIG_SCHED_DEBUG` 的 allmodconfig 编译与 `sched/debug` 输出对比**：`h_load` 是否真的常年新鲜，是这条系列最容易验证也最缺的证据；把前后 `/proc/sched_debug` 里各 cfs_rq 的 `hbfs`/`h_load` 打出来回帖即可。
- **cgroup 场景的正确性验证**：用户主线正是 cgroup。可以在多层 `cpu.shares`/`cpu.weight` 悬殊的层级上，配合 `cpu.max` 限流，观察负载均衡是否还会把任务从被高估的组里搬走；这类"重构是否改变迁移决策"的实测是 Vincent/Peter 判断能否收口的关键输入。
- **回合评估**：OLK-6.6 有 `task_h_load()` 的同一份实现（`h_load_next` + jiffies 限流那版）。这套改动依赖 `enqueue_hierarchy()`/`dequeue_hierarchy()`（那是 6.6 之后的重构产物）与 `PELT_SEGMENT_MASK`，不能直接回合；但 4/4 的两个独立可分点——把 jiffies 限流换成 PELT 段、以及 `WRITE_ONCE()` 发布 `h_load`——是可以单独本地化的小改动。

## 参考链接

- cover letter: https://lore.kernel.org/all/20260828074059.232353141@infradead.org/
- 1/4: https://lore.kernel.org/all/20260828075558.320346065@infradead.org/
- 2/4: https://lore.kernel.org/all/20260828075558.438093356@infradead.org/
- 3/4: https://lore.kernel.org/all/20260828075558.542761795@infradead.org/
- 4/4: https://lore.kernel.org/all/20260828075558.660152190@infradead.org/
- 作者引用的相关讨论（[2]，cover letter 原文给出）: https://lore.kernel.org/all/aoxah90s0bQ4tcUW@three-body/
- tip-bot commit: 未获取到
- stable backport: 未获取到
