---
id: sched-20260801-005
date: 2026-08-01
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <uid-13761@qq-imap>
lore_url: https://lore.kernel.org/all/20260729163225.1987068-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Mete Durlu
- K Prateek Nayak
- Shrikanth Hegde
current_version: v3
patch_series:
- version: v1
  msgid: unknown
  date: 2026-07-28
  summary: find_new_ilb() 在选择 idle load balancer CPU 时优先选择整个 core 都空闲的 CPU，避免在繁忙 SMT
    core 的空闲兄弟上跑 ILB 而挤占其兄弟的算力；保留第一个空闲 CPU 作为 fallback
  review_outcome: K Prateek Nayak 指出在宽 SMT 系统上会产生大量重复的 is_core_idle() 检查
- version: v2
  msgid: unknown
  date: 2026-07-29
  summary: 回应 Prateek：对部分繁忙的 core 剪掉其剩余兄弟线程，避免宽 SMT 系统上重复的 is_core_idle() 调用
  review_outcome: Mete Durlu 进一步指出剪枝还可以更彻底
- version: v3
  msgid: <uid-13761@qq-imap>
  date: 2026-08-01
  summary: 回应 Mete Durlu：找到 idle fallback 之后，一旦遇到繁忙 CPU 即跳过其所有兄弟线程，避免对已知繁忙的 core 做逐
    CPU 遍历。实现上改用 per-CPU select_rq_mask（依赖关中断保证互斥）承载候选集合，以便在遍历中就地剪枝
  review_outcome: v3 当日发出，暂无新的 review 意见
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 整个系列三个版本均未见任何量化效果数据，缺少能证明『ILB 挤占兄弟线程算力』这一动机的实测数字
  next_action: 补充 benchmark 数据证明优先选择全空闲 core 的实际收益，并确认复用 select_rq_mask 在 find_new_ilb()
    调用上下文中的安全性
contribution_opportunities:
- kind: testing
  description: 在宽 SMT 机器（POWER SMT8 / s390）上测量 ILB 跑在繁忙 core 空闲兄弟上时对该 core 上任务的实际影响，补上这个系列自始至终缺失的量化动机数据
- kind: review
  description: 核对复用 per-CPU select_rq_mask 的安全性——注释称『本 CPU 上由关中断保护免于并发使用』，需要确认 find_new_ilb()
    的所有调用路径确实都在关中断上下文，且不会与同一 CPU 上其他 select_rq_mask 使用者嵌套冲突
generated_at: '2026-08-02T00:55:00'
source_email_count: 1
related_articles:
- sched-20260731-007
tags:
- cfs
- load_balance
- nohz
- idle
- hyperthreading
title: 'sched/fair: Prefer fully idle cores for NOHZ balancing'
layout: article
---

## TL;DR

Andrea Righi 让 NOHZ idle load balancer 优先挑选整个 core 都空闲的 CPU，避免 ILB 跑在繁忙 SMT core 的空闲兄弟线程上而挤占其算力。方案本身简单合理、已经过三轮 reviewer 打磨，但**三个版本自始至终没有给出任何效果数据**，这是它目前唯一的明显短板。

## 背景与问题

`find_new_ilb()` 负责为 NOHZ idle balancing 挑一个 CPU 来执行。原实现很直接：遍历 `nohz.idle_cpus_mask` 与 housekeeping mask 的交集，返回第一个 `idle_cpu()` 为真的 CPU。

问题在于 SMT：一个 CPU 空闲不代表它所在的 core 空闲。如果 ILB 落在一个繁忙 core 的空闲兄弟线程上，运行 ILB 本身会消耗该 core 的共享执行资源，从而**减少其兄弟线程可用的算力**——而那个兄弟上正跑着真实工作负载。ILB 是周期性的后台工作，为它付出干扰前台任务的代价并不划算。

## 技术方案

在 `find_new_ilb()` 中优先选择「整个 core 都空闲」的 CPU，同时保留第一个找到的空闲 CPU 作为 fallback，保证在系统里根本不存在全空闲 core 时 idle balancing 仍能推进——这个 fallback 设计是必要的，否则在高负载下 ILB 会直接失效。

实现上的关键取舍是**如何避免剪枝本身带来的开销**。朴素做法是对每个候选 CPU 调 `is_core_idle()`，在宽 SMT（如 SMT8）系统上会产生大量重复检查——同一个 core 的 8 个兄弟会被各检查一遍。v2、v3 两轮迭代都在解决这件事：

- v2：遇到部分繁忙的 core 时，剪掉它剩余的兄弟线程；
- v3：更进一步——**一旦已经有了 idle fallback，再遇到任何繁忙 CPU，就直接 `cpumask_andnot()` 掉它整个 `cpu_smt_mask()`**。逻辑依据很干净：一个繁忙 CPU 就足以证明它所在的 core 不可能全空闲，那么这个 core 的所有兄弟都不必再考虑（fallback 已经有了，不需要它们来兜底）。

为了能在遍历过程中就地修改候选集合，v3 不再用 `for_each_cpu_and()` 直接迭代两个只读 mask，而是改为复用 per-CPU 的 `select_rq_mask`：先 `cpumask_and(ilb_cpus, nohz.idle_cpus_mask, housekeeping_cpumask(HK_TYPE_KERNEL_NOISE))` 得到候选集，再在其上遍历并剪枝。函数开头新增了 `lockdep_assert_irqs_disabled()`，注释说明该 per-CPU mask 在本 CPU 上靠关中断保证不被并发使用。

改动规模：`kernel/sched/fair.c` 单文件 47 增 9 删。

## 版本演进与当前进展

- **v1**（07-28）：基本方案——优先全空闲 core，保留 fallback。
- **v2**（07-29）：回应 K Prateek Nayak——对部分繁忙的 core 剪掉剩余兄弟，避免宽 SMT 上重复的 `is_core_idle()` 检查。
- **v3**（08-01 03:19）：回应 Mete Durlu——找到 idle fallback 之后遇到繁忙 CPU 即跳过其全部兄弟，彻底避免对已知繁忙 core 的逐 CPU 遍历；配套引入 per-CPU mask 与 irqs-disabled 断言。

Cc 列表为 Mete Durlu、K Prateek Nayak、Shrikanth Hegde——三位都是 SMT / 负载均衡方向的常见 reviewer。v3 当日发出后暂无新回复。

需要说明的是，本系列在 07-31 的日报中已作为 v2 增量记录过（见 related_articles），本文对应 v3。

## Maintainer 意见与讨论焦点

到目前为止的 review 意见**全部集中在实现效率上，没有人质疑方向**：

- **K Prateek Nayak**（v1→v2）：宽 SMT 系统上 `is_core_idle()` 会被重复调用，需要剪枝。
- **Mete Durlu**（v2→v3）：剪枝可以做得更彻底——不只是跳过部分繁忙 core 的剩余兄弟，而是在有 fallback 之后对任何繁忙 CPU 都跳过整个 core。

没有 NAK，没有关于「是否应该优先全空闲 core」这一前提的争论。这是一个方向已获默认认可、只在打磨实现的系列。

但有一个**没有人提出、却客观存在的空白**：三个版本都没有给出任何效果数据。「ILB 挤占兄弟线程算力」这个动机在理论上成立，但实际影响有多大、优先选全空闲 core 之后收益是多少，完全没有数字支撑。reviewer 们讨论的都是「怎么让剪枝更快」，而没有人问「这个优化本身值多少」。

## 合入评估

合入可能性 **high**。理由：方向无争议、改动局限在单个函数、两位 reviewer 的意见都已被采纳且 v3 的实现相当干净、作者是活跃贡献者。

主要软肋是缺少效果数据。对于一个纯优化类改动，maintainer 在合入前很可能会要求至少一组能说明问题的数字。此外 v3 新引入的 `select_rq_mask` 复用需要确认调用上下文的安全性——虽然作者加了 `lockdep_assert_irqs_disabled()`，但这只在开启 lockdep 时生效，值得 reviewer 人工核对一遍所有调用路径。

## 效果评估

**暂无效果数据**。v1 到 v3 的邮件中均未出现任何 benchmark、微基准或实测数字。「ILB 跑在繁忙 core 的空闲兄弟上会减少其兄弟可用算力」是机制层面的合理推断，但按模板要求应标注为**作者主观判断，未见测试数据**。v2、v3 的两轮优化目标（减少 `is_core_idle()` 调用次数）同样没有给出优化前后的调用次数或耗时对比。

## 我可以参与的点

- **测试（填补本系列最明显的空白）**：在宽 SMT 机器（POWER SMT8、s390）上构造「core 部分繁忙 + 频繁 NOHZ idle balancing」的场景，测量 ILB 落在繁忙 core 空闲兄弟上时，对该 core 上前台任务的实际影响（吞吐 / 延迟）。这正是整个系列自始至终缺失的动机数据，补上它对推动合入有直接价值。也可以顺带用 perf 统计 v2 与 v3 在 SMT8 上 `is_core_idle()` 的实际调用次数差异，为剪枝优化本身提供数字。
- **Review**：核对复用 per-CPU `select_rq_mask` 的安全性。注释称「本 CPU 上由关中断保护免于并发使用」，需要确认 `find_new_ilb()` 的所有调用路径确实都在关中断上下文中，并且不会与同一 CPU 上 `select_rq_mask` 的其他使用者（唤醒路径、`select_task_rq_fair()` 等）发生嵌套冲突。

## 参考链接

- lore thread (v2): https://lore.kernel.org/all/20260729163225.1987068-1-arighi@nvidia.com/
- lore thread (v1): https://lore.kernel.org/r/20260728214442.1648483-1-arighi@nvidia.com/
- lore thread (v3): 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到
