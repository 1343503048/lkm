---
id: sched-20260828-006
date: '2026-08-28'
subject: 'sched/core: Try to use a preferred CPU in is_cpu_allowed'
subsystem: sched
type: discussion
status: rfc
severity: medium
thread_root_msgid: <20260825103855.721013-6-sshegde@linux.ibm.com>
lore_url: https://lore.kernel.org/all/8262d2f9-9f2f-4821-8497-991d7c8448a3@arm.com/
authors:
- Dietmar Eggemann
- Vincent Guittot
- Shrikanth Hegde
maintainers_involved:
- Dietmar Eggemann
- Vincent Guittot
current_version: v11
patch_series:
- version: v11
  msgid: <20260825103855.721013-6-sshegde@linux.ibm.com>
  date: '2026-08-25'
  summary: is_cpu_allowed()/select_fallback_rq() 在受限时优先选择仍被允许的 preferred CPU
  review_outcome: 8/28 Dietmar 指出判据漏了 task_cpu_possible_mask，提出三求交写法；Vincent +1；作者确认并入
    v12（排在 7.3-rc1 之后）
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - v12 显式排在 7.3-rc1 之后，本轮 merge window 赶不上
  - arm64 32-bit EL0 时间窗仍停在需要更多测试，未定性
  - 该系列另有 preferred CPU 应按哪些架构启用的分歧未收口
  next_action: v12 带上三求交改动；Dietmar 的 arm64 测试结论；架构默认开关讨论收口
contribution_opportunities:
- kind: discussion
  description: 从 cpuset 收紧时序角度评估 cpus_ptr 与 cpu_preferred_mask/possible_mask 三求交的边界情况
- kind: testing
  description: 在 arm64 + allow_mismatched_32bit_el0 环境验证 exec 期间的 compat 亲和窗口是否可观测
generated_at: '2026-09-07T22:08:24'
source_email_count: 3
related_articles:
- sched-20260825-001
- sched-20260810-008
- sched-20260830-004
- sched-20260831-007
tags:
- affinity
- cgroup
- load_balance
- arm64
title: 'sched/core: Try to use a preferred CPU in is_cpu_allowed'
layout: article
---

## TL;DR

**本文为增量更新**（完整背景见 sched-20260825-001 与 sched-20260810-008）。Shrikanth Hegde（IBM）的 steal_governor / preferred CPU 系列 `v11 05/12` 在 8/28 被 Dietmar Eggemann（ARM）指出判据**漏了第三个 cpumask**：`task_can_sched_on_preferred()` 只测 `cpus_ptr ∩ cpu_preferred_mask` 是否非空，没有再与 `task_cpu_possible_mask(p)` 求交；他怀疑 arm64 上 32-bit EL0 任务（`allow_mismatched_32bit_el0`）在 `arch_setup_new_exec()` 调 `force_compatible_cpus_allowed_ptr()` 收紧亲和性之前存在一个时间窗。给出的替代写法 `cpumask_first_and_and(...) < nr_cpu_ids` 得到 Vincent Guittot 明确 "+1"，作者当天答复会并入 **v12，并可能在 7.3-rc1 落地后再发**。这条与 cpuset/亲和性直接相关，值得跟。

## 背景与问题

`05/12` 处理的是"任务偏好 CPU"与"任务硬约束"交叉时的兜底选点：当任务当前所在 CPU 已不允许它运行时，push/`select_fallback_rq()` 与 FAIR 任务的唤醒路径要尽量挑一个仍是 preferred 的 CPU。判据函数是 `task_can_sched_on_preferred()`，v11 版本对"这个任务是否有任何 preferred CPU 可用"用的是二求交：

```
- return cpumask_intersects(p->cpus_ptr, cpu_preferred_mask);
```

`cpus_ptr` 是任务的软亲和（受 cpuset 收紧后的结果），`cpu_preferred_mask` 是 steal 驱动的偏好集合，但**任务能不能真正跑在某 CPU 上还取决于 `task_cpu_possible_mask(p)`**——例如带 `cpus_share_cache`/非对称能力（32/64-bit、特定 erratum）限定时，possible mask 会是全体 CPU 的真子集。Dietmar 认为漏掉这一维会给出"有 preferred CPU 可用"的假阳性。

## 技术方案

Dietmar 的建议是把判断换成三求交后测存在性：

```
+ return cpumask_first_and_and(p->cpus_ptr, cpu_preferred_mask,
+                              task_cpu_possible_mask(p)) < nr_cpu_ids;
```

他的问句即设计理由："IMHO, you want to know whether there is at least one CPU that belongs to all three CPU masks?"

Shrikanth 当天给出并入 v12 后的完整函数形态：

```
static inline bool task_can_sched_on_preferred(int cpu, struct task_struct *p)
{
        if (cpu_preferred(cpu))
                return false;

        /* Only FAIR tasks honor preferred CPU state */
        if (unlikely(p->sched_class != &fair_sched_class))
                return false;

        /* Ignore preferred state if task affinity is changing */
        if (unlikely(!cpumask_test_cpu(task_cpu(p), p->cpus_ptr)))
                return false;

        return cpumask_first_and_and(p->cpus_ptr, cpu_preferred_mask,
                             task_cpu_possible_mask(p)) < nr_cpu_ids;
}
```

即三求交只作用于最后一道"整体上还有没有可用 preferred CPU"的判定，前面三条否决（本 CPU 已是 preferred、非 FAIR 任务、亲和性正在变更）保持不变。

## 版本演进与当前进展

- v9/v10（8/10、8/14、8/17 站内有记录）→ **v11（8/25，12 补丁）**，作者当时称系列已收敛、请求在 7.3-rc 周期考虑纳入 sched/core。
- **8/28（本日）**：Dietmar 提出三求交与 arm64 窗口疑问 → Vincent "+1" → 作者确认改法并入 v12，时间点在 7.3-rc1 之后。
- 本日为纯 review 迭代，无新代码投递；v12 直到 9/03 才出现（站内后续报道），本日无该信息。

## Maintainer 意见与讨论焦点

- **Dietmar Eggemann（ARM，sched/cpuset 侧活跃 reviewer）**：两条意见，一条是**具体正确性**（漏 `task_cpu_possible_mask`），一条是**平台相关的潜在时间窗**——arm64 上跑 32-bit EL0 任务且内核为 64-bit 时，在 `arch_setup_new_exec()` 调 `force_compatible_cpus_allowed_ptr()` 收紧亲和性之前存在一个窗口。他当时**没有下结论**，明说 "Let me run more test on this ..."，8/28 当日没有后续。
- **Vincent Guittot（Linaro）**：对三求交写法明确背书："**+1** This is the best way to check that there is a valid cpu"。
- **Shrikanth Hegde（作者）**：全盘接受，"The three-way cpumask check you suggested will handle that case safely. I will put that in v12 and probably send it out after 7.3-rc1 lands."

未解决点（本日线程里没人回答的问题）：arm64 compat-el0 那个窗口**是否真的可观测**，仍停在"需要更多测试"；邮件里没有把 `cpus_ptr` 在 exec 期间的具体取值链讲清楚，所以三求交究竟是修掉了那个窗口、还是只修掉了"能力子集"这类更静态的场景，两种解读都还在。

## 合入评估

**likelihood: likely**。

- 有利：改动是一行判据收紧，无新增状态、无 uapi；提出者是 ARM 侧维护者且得到 Linaro 另一位 reviewer 明确背书；作者当场接受并给出 v12 计划；系列此前已推进到 v11 且作者声称功能层面已收敛。
- 卡点：v12 的发版被显式排在 **7.3-rc1 之后**，也就是本轮 merge window 赶不上；arm64 那条时间窗尚未定性，若 Dietmar 后续测试表明还有更深的 exec 期竞态，可能牵出额外改动；此前站内 sched-20260831-007 记录显示"该在哪些架构上启用 preferred CPU"这一争论仍在继续（Yury Norov 主张只在实测过的 PPC+xPVM / x86+KVM 上开，Vincent 反对），说明该系列的外部争议不止本日这一处。
- `next_action`：v12 带上三求交改动；Dietmar 的 arm64 测试结果；架构默认开关之争收口。

## 效果评估

本日线程为纯正确性讨论，**无数据、无 benchmark**。steal_governor 系列自身的收益数字不在本 threads 内（站内 sched-20260814-004 / sched-20260817-005 / sched-20260822-003 记过该系列此前的基准与一次 3.5% 回退讨论）。

## 我可以参与的点

- **直接可做的一件事：把 `cpuset` 视角补进这个判据**。`cpus_ptr` 本身就是 cpuset 收紧后的产物，`task_cpu_possible_mask()` 又与 `cpuset_cpus_allowed()`/`__cpuset_cpus_allowed_locked()` 的返回集合相互作用。用户对 cpuset 侧取集合的时序（`callback_lock`、热插拔期间的 `effective_cpus` 滞后）比多数 reviewer 熟，可以就"cpuset 收紧与 preferred mask 同时变化时三求交会不会给出假阴性/假阳性"回帖——这正好也是站内 sched-20260828-002 那条 cpuset GPF 的同一块代码邻域。
- **arm64 compat-el0 那条线索目前没人验**。如果手上有 64-bit arm64 + 32-bit 用户态 + `allow_mismatched_32bit_el0` 的环境，跑一遍 exec 期间读 `/proc/PID/status` 的 `Cpus_allowed_list` 变化并观察是否落到非 possible CPU，就是 Dietmar 说"Let me run more test on this"缺的那份数据。
- **回合判断**：OLK-6.6 无 preferred CPU 框架，本补丁不可直接回合；但 `task_can_sched_on_preferred()` 的教训（凡"任务是否有可运行的 preferred CPU"的判断都必须带上 `task_cpu_possible_mask()`）对任何自研亲和/优选 CPU 逻辑都适用——检查内部是否有 `cpumask_intersects(cpus_ptr, 自定义掩码)` 而漏 possible_mask 的地方。

## 参考链接

- v11 05/12 原始补丁: https://lore.kernel.org/all/20260825103855.721013-6-sshegde@linux.ibm.com/
- Dietmar Eggemann 的三求交建议与 arm64 窗口疑问: https://lore.kernel.org/all/8262d2f9-9f2f-4821-8497-991d7c8448a3@arm.com/
- Vincent Guittot 的 "+1": https://lore.kernel.org/all/CAKfTPtB27-eFXGG9GcXdm4=YLZy6-vQMAQqoCbHa5xZxA3YBpw@mail.gmail.com/
- Shrikanth Hegde 确认并入 v12: https://lore.kernel.org/all/621386ee-7147-4110-a027-6f2f83b4f1cc@linux.ibm.com/
- 相关文章: [[sched-20260825-001]]（v11 全量分析）、[[sched-20260810-008]]（更早版本）、[[sched-20260831-007]]（后续架构开关之争）
- tip-bot commit: 未获取到
- stable backport: 未获取到
