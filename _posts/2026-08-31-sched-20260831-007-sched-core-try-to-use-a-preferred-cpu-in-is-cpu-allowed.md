---
id: sched-20260831-007
date: '2026-08-31'
subject: 'sched/core: Try to use a preferred CPU in is_cpu_allowed'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260825103855.721013-1-sshegde@linux.ibm.com>
lore_url: https://lore.kernel.org/all/53035ba4-53ec-4907-93b8-c8b957d1fa61@linux.ibm.com/
authors:
- Shrikanth Hegde
- Yury Norov
- Dietmar Eggemann
- Vincent Guittot
maintainers_involved:
- Vincent Guittot
- Dietmar Eggemann
current_version: v11
patch_series:
- version: v11
  msgid: <20260825103855.721013-6-sshegde@linux.ibm.com>
  date: 2026-08-25
  summary: is_cpu_allowed()/select_fallback_rq() 在受限时优先挑选仍允许的 preferred CPU；仅 FAIR
    任务生效；亲和性变更中忽略 preferred 状态；处理架构特定 CPU 掩码
  review_outcome: Yury 建议按已实测架构收窄 Kconfig 使能并质疑 likely() 用法；Vincent 反对按架构收窄；Dietmar
    提出 arm64 32 位 EL0 execve 窗口待验证
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: possible
  blocking_issues:
  - arm64 是否现在就使能该 driver 存在维护者分歧（Vincent Guittot vs Yury Norov）
  - Dietmar Eggemann 提出的 arm64 32 位 EL0 execve() 窗口未有结论，可能演变为正确性问题
  - cpumask_intersects_and() helper 化与 likely() 用法两条建议未被作者接受或拒绝
  next_action: 等 Dietmar 的 arm64 测试结果与 Vincent/Yury 就使能范围达成一致，再出 v12
contribution_opportunities:
- kind: review
  description: 给出 cpuset 收窄到非 preferred 集合时 preferred CPU 与 cpus_ptr 优先级的行为验证结论（本系列尚未有人覆盖
    cpuset 交叉场景）
- kind: testing
  description: 在 arm64（尤其 allow_mismatched_32bit_el0）上复现/排除 32 位 EL0 execve 窗口，回应
    Dietmar 的未决问题
- kind: testing
  description: 在 KVM/XEN guest 中验证 steal-time 驱动的 preferred CPU 生效性，补上作者只测了 PPC+powervm
    与 x86+kvm 的空缺
generated_at: '2026-09-07T21:16:22'
source_email_count: 2
related_articles:
- sched-20260810-008
tags:
- affinity
- numa_balancing
- cgroup
- arm64
title: 'sched/core: Try to use a preferred CPU in is_cpu_allowed'
layout: article
---

## TL;DR

本文为增量更新（完整背景见 sched-20260810-008）。Shrikanth Hegde（IBM）的 preferred-CPU / steal-governor 系列已到 **v11（12 补丁）**，`05/12` 让 `is_cpu_allowed()`/`select_fallback_rq()` 在受限时优先挑仍被允许的 preferred CPU。8/31 的争点从代码本身转到**该在哪些架构上启用**：Yury Norov 主张只在已实测过的 PPC+xPVM / x86+KVM 上开，Vincent Guittot 当晚明确反对——"It's always better to support all arch by default, unless something is missing which is not the case here."，作者目前把 arm64 决定权押在 Dietmar/Vincent 回复上。这条与 cpuset/亲和性交互，值得盯。

## 背景与问题

任务可以有一个"preferred CPU"集合（该系列引入的机制，服务于 steal-time 驱动的 vCPU 摆放）。麻烦在于**偏好与硬约束的交叉**：任务被固定在某个 CPU 上、而该 CPU 恰好不再是 preferred 时，调度器该不该把它推走？如果推，会不会把用户显式设置的亲和性破坏掉？

`05/12` 要覆盖的具体路径是"任务当前 CPU 不允许它跑"时的兜底选点：push 机制用 stopper 线程调 `select_fallback_rq()`，这里要能挑到一个 preferred CPU；FAIR 任务的 wakeup 路径同样受益——`is_cpu_allowed()` 保证唤醒落在 preferred CPU 上之后，`available_idle_cpu()` 里额外的判断就不再需要。

## 技术方案

`is_cpu_allowed()` 侧新增 `task_can_sched_on_preferred()`：

```
+       if (cpu_preferred(cpu))
+               return false;
+       /* Only FAIR tasks honor preferred CPU state */
+       if (unlikely(p->sched_class != &fair_sched_class))
+               return false;
+       /* Ignore preferred state if task affinity is changing */
+       if (unlikely(!cpumask_test_cpu(task_cpu(p), p->cpus_ptr)))
+               return false;
+       valid_mask = task_cpu_possible_mask(p);
+       if (likely(valid_mask == cpu_possible_mask))
+               return cpumask_intersects(p->cpus_ptr, cpu_preferred_mask);
+       /* Tasks with arch-specific CPU masks. e.g. 32-bit tasks on arm64. */
+       for_each_cpu_and(i, p->cpus_ptr, cpu_preferred_mask) {
+               if (cpumask_test_cpu(i, valid_mask))
+                       return true;
+       }
```

关键设计取舍（均来自 commit message 与讨论）：

- **用户亲和性优先于偏好**：非用户触发的偏好变化不应该把被 pin 的任务挪走。
- **正在改亲和性时忽略偏好**：若任务新 mask 已不包含它当前所在 CPU，就不再用 preferred 状态判断，避免 `migration_cpu_stop()` 中止、把任务遗留在允许的亲和集合之外。
- **架构掩码特例**：arm64 上跑 32 位任务这类"架构可见 CPU 集合 ≠ cpu_possible_mask"的情况必须三方求交，否则会挑到该任务实际不能跑的 CPU。
- **复杂度**：绝大多数情况 `select_fallback_rq()` 保持 O(N)——`cpumask_intersects()` 只在 `!cpu_preferred` 时调用；只有"被 pin 死在纯非 preferred CPU 上"才退化到 O(N²)，作者称这是罕见场景。

被讨论过的备选实现：Dietmar 建议直接 `return cpumask_first_and_and(p->cpus_ptr, cpu_preferred_mask, task_cpu_possible_mask(p)) < nr_cpu_ids;` 取代手写循环；Yury 认同"更有效"，但要求包一层 `cpumask_intersects_and()` 语义化 helper；若这段真成为性能热点，可引入 `arch_task_can_sched_on_preferred()` 绕开通用路径。

## 版本演进与当前进展

- 8/10 前后的 v9 为 11 补丁（该 patch 当时是 `04/11`，见 sched-20260810-008）；8/25 的 **v11 已是 12 补丁**，该 patch 变 `05/12`（`<20260825103855.721013-6-sshegde@linux.ibm.com>`）。
- 8/28 Dietmar Eggemann 指出 arm64 32 位 EL0 场景并给出 `cpumask_first_and_and()` 写法；8/30 Yury Norov 提出 helper 化、`likely()` 用法与"只在实测过的架构上启用"三点；8/31 作者逐条回复并抛出 arm64 是否现在就使能的问题；8/31 晚 Vincent Guittot 表态反对按架构收窄。
- 尚未确认的改动：三方交集 helper 是否采用（作者态度是"只有 ARM64 现在就要使能才需要，否则可以退回 `cpumask_intersects()`，等 ARM 生态使能时再加"）；`likely()` 的用法作者未表态修改。
- 当前 Kconfig 使能清单：`PPC_SPLPAR`、`S390`、`X86_64`，作者写明确实"在等 Dietmar/Vincent 关于 ARM 的意见"。

## Maintainer 意见与讨论焦点

- **Vincent Guittot（linaro，sched/fair 维护者）**——当日最新且与 Yury 直接对立：默认支持所有架构更好，除非确实有东西缺失，"which is not the case here"。
- **Yury Norov**：主张按已验证范围启用——"governor is really tested in 2 configurations: PPC+powervm and x86+kvm"，且认为 DOM0 与 arm64 compat task 已经暴露了两个 corner case，逐架构交给领域专家使能、把 API 稳定前的架构决策推后更稳妥。此外他不喜欢该补丁对 `likely()` 的用法（x86 上 `possible == task_possible` 显然成立，aarch64/el0-32 上永远不成立，会导致 aarch64 上的次优代码生成）。
- **Dietmar Eggemann（arm，未在本日回帖但为焦点人物）**：8/28 指出 arm64 上带 `allow_mismatched_32bit_el0` 时，64→32 位 `execve()` 存在一个窗口——在 `arch_setup_new_exec()` 调用 `force_compatible_cpus_allowed_ptr()` 收窄亲和性之前，任务的 arch mask 与实际允许集合不一致；他说"Let me run more test on this"，本日内**没有后续结论**。
- **作者 Shrikanth Hegde**：接受"更安全"的方向，认同该函数只在非 preferred CPU 上被调、除非被 pin 住任务本来就会挪走，所以性能上"we are okay here I guess"。
- 未解决：arm64 现在使能还是延后（Vincent 与 Yury 相左）；32 位 EL0 execve 窗口是否真的构成缺陷；`likely()` 与 helper 化两条建议是否采纳。

## 合入评估

**possible**。有利：系列已迭代到 v11、评论集中在实现细节与使能范围而非"该不该有这个机制"，且 FAIR wakeup 路径复用 `is_cpu_allowed()` 顺带删掉了 `available_idle_cpu()` 里的额外检查（说明作者在做减法而非堆补丁）。卡点：Dietmar 的 arm64 32 位 EL0 窗口尚无结论，这是唯一可能的正确性问题；架构使能范围存在维护者之间的实质分歧（Vincent vs Yury），而作者明确表示等他们的答复，意味着 v12 大概率还要动 Kconfig；此外该 patch 属于 12 补丁系列，需要整体一起被 accept。

## 效果评估

暂无效果数据。本日线程里出现的量化都是**复杂度论证**（`select_fallback_rq()` 通常保持 O(N)，仅"pin 在纯非 preferred CPU"退化 O(N²)）而非实测；没有任何 steal-time 改善、vCPU 放置命中率或基准测试数字。

## 我可以参与的点

- **cpuset 视角的语义评审（与你的主线最贴近）**：preferred CPU 与 `cpus_ptr`/root domain 的优先级顺序在本补丁里体现为"亲和性变更中忽略偏好"这一条特例。可以在 cpuset 与 preferred CPU 冲突（例如 `cpuset` 把任务收窄到非 preferred 集合）的场景下给出行为验证并回帖，这类场景目前没人覆盖。
- **补 arm64 侧数据**：Dietmar 说要继续测的 32 位 EL0 窗口、以及 Yury 关心的 aarch64 上 `likely()` 误判，都需要 arm64 机器上的实测；有 arm64 环境的话这是最容易产生价值的回帖。
- **steal-time governor 的虚拟化验证**：作者称已在 PPC+powervm 与 x86+KVM 测过，而 XEN 与 ARM 工程师有兴趣但无人出数据；KVM guest 内核对 `kvm_steal_time` 的处理与 preferred CPU 生效性可以直接测。

## 参考链接

- lore thread（05/12）: https://lore.kernel.org/all/20260825103855.721013-6-sshegde@linux.ibm.com/
- 系列 cover（v11）: https://lore.kernel.org/all/20260825103855.721013-1-sshegde@linux.ibm.com/
- 本日作者回复（含 arm64 提问）: https://lore.kernel.org/all/53035ba4-53ec-4907-93b8-c8b957d1fa61@linux.ibm.com/
- Vincent Guittot 当日表态: https://lore.kernel.org/all/CAKfTPtA5Bdw89hezn1wi_p0m0dJgJJ1GYg8H93PsvsMC4bVJxA@mail.gmail.com/
- Yury Norov 意见（本线程前序）: https://lore.kernel.org/all/apMziCV_8y0xeIBT@yury/
- Dietmar Eggemann 的 arm64 32 位掩码意见（本线程前序）: https://lore.kernel.org/all/8262d2f9-9f2f-4821-8497-991d7c8448a3@arm.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到
