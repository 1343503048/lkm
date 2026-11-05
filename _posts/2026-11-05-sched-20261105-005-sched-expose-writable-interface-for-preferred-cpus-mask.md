---
id: sched-20261105-005
date: 2026-11-05
subject: 'sched: Expose writable interface for preferred CPUs mask'
subsystem: sched
type: feature
status: stalled
severity: none
thread_root_msgid: <20261101192203.6979-1-ynorov@nvidia.com>
lore_url: https://lore.kernel.org/all/20261101192203.6979-1-ynorov@nvidia.com/
authors:
- Yury Norov
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <20261101192203.6979-1-ynorov@nvidia.com>
  date: 2026-11-01
  summary: 6 补丁：writable preferred mask sysfs + PREFERRED_CPU 解耦 PARAVIRT + hotplug
    恢复 + cpu_preferred_mutex。
  review_outcome: Peter 方向性 NAK 手动接口；今日澄清 preferred mask 语义并讨论 patch 3 hotplug 回退。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: rejected
  blocking_issues:
  - Peter 对手动 writable sysfs 接口的方向性 NAK
  next_action: 聚焦 PREFERRED_CPU 解耦 PARAVIRT 独立子补丁；回应 patch 3 hotplug 回退的迁移开销疑问
contribution_opportunities:
- kind: new_patch
  description: 基于 HAVE_CPUTIME_STEAL 示例整理 PREFERRED_CPU 解耦 PARAVIRT 的独立补丁
- kind: testing
  description: 实测 hotplug 移除唯一 preferred CPU 后 steal governor 收敛期的迁移开销
generated_at: '2026-11-06T09:00:00+08:00'
source_email_count: 4
related_articles:
- sched-20261102-004
tags:
- load_balance
- affinity
- topology
title: 'sched: Expose writable interface for preferred CPUs mask'
layout: article
---

## TL;DR

- <a class="article-ref" href="/lkm/2026/11/02/sched-20261102-004-sched-expose-writable-interface-for-preferred-cpus-mask.html">sched-20261102-004</a>：Yury Norov 发 6-patch 系列为 preferred CPUs 提供运行时可写 sysfs 接口（`/sys/devices/system/cpu/cpuN/preferred`）；Peter Zijlstra 对整个手动接口方向 NAK（「We already have cpusets... this isn't happening」），仅认可其中 patch 1（PREFERRED_CPU 与 PARAVIRT 解耦）。
- sched-20261105-XXX（今天）：讨论转入 patch 3/6「hotplug 移除最后一个 preferred CPU 时恢复所有 active CPU」的行为语义——Peter 澄清 preferred mask 与 cpusets 的区别（前者是弱边界/协作式 steal time 控制环，后者是强边界），Yury 解释 hotplug 回退是最安全的选择，Fushuai Wang 追问回退后 steal governor 重新收敛是否引入额外任务迁移开销。

## 背景与问题

- <a class="article-ref" href="/lkm/2026/11/02/sched-20261102-004-sched-expose-writable-interface-for-preferred-cpus-mask.html">sched-20261102-004</a>：现有 preferred CPU mask 只供 steal governor 在 vCPU 抢占时动态缩减 vCPU 需求；作者希望增加运行时手动控制（类似 `isolcpus=domain` 的运行时版），Peter 以「cpusets 已能干这件事」为由 NAK 整个方向，仅认可 PREFERRED_CPU 解耦 PARAVIRT。

今天的新内容围绕 patch 3/6（`sched: Restore preferred CPUs when hotplug removes the last one`）：该补丁在 `sched_cpu_deactivate()` 里检测到 hotplug 移除的恰好是最后一个 preferred CPU 时，把所有仍 active 的 CPU 恢复为 preferred，避免 preferred mask 变成空集。Fushuai Wang 提出疑问：若被 offline 的是唯一 preferred CPU，`reset_preferred_cpumask()` 之后 steal governor 仍需若干迭代才重新收紧 mask，期间可能只剩一个 preferred CPU，是否会带来额外迁移开销。

## 技术方案

- <a class="article-ref" href="/lkm/2026/11/02/sched-20261102-004-sched-expose-writable-interface-for-preferred-cpus-mask.html">sched-20261102-004</a>：系列 6 补丁（Kconfig 解耦 / `reset_preferred_cpumask()` helper / hotplug 恢复 / `cpu_preferred_mutex` 串行化 / governor 告警 / per-CPU sysfs）。
- 今天：Peter 澄清 preferred mask 的定位——它是一个简单的「宿主过载 → vcpu steal time → guest 观察 steal time 降低 vcpu 利用率」的协作式控制环，与 guest 工作负载无关；参与者必须行为一致否则「bad actor can game the system」；这与 cpusets 语义不同（cpusets 是你对自己工作负载的强约束，preferred mask 是外部压力下的弱边界），机制上「与 ACPI idle injection 差别不大」。Yury 回应 patch 3/6：从调度器视角这是最安全的回退；当前 steal governor 需多次迭代回到旧均衡点，若真成问题可让 governor 收敛更快或检测 mask reset。

## 版本演进与当前进展

*current_version: v1*。今日无新版本。进展集中在 patch 3/6 的回退语义澄清：Yury 给出回退理由，Fushuai 提出迁移开销疑问（尚未有直接回应），Peter 从机制层面澄清 preferred mask 与 cpusets/steal time 的关系。

## Maintainer 意见与讨论焦点

Peter Zijlstra 仍未改变对「手动 writable 接口」的方向性拒绝，今日发言是在澄清 preferred mask 的本义（协作式、弱边界、与 cpusets 不同层）。Yury 对 patch 3/6 的回退设计做技术辩护。Fushuai Wang 的迁移开销疑问待答。

## 合入评估

*likelihood=rejected*（手动 sysfs 接口方向维持不变）。今日讨论未改变方向性 NAK；仅 patch 3/6 的回退语义得到澄清。*blocking_issues*：Peter 对 writable 接口的 NAK 仍是根本障碍。*next_action*：作者若仍想推进，聚焦「PREFERRED_CPU 解耦 PARAVIRT」这个被认可的独立子补丁；patch 3/6 的迁移开销疑问需数据支撑答复。

## 效果评估

无性能数据。今日为控制面语义讨论，未涉及 benchmark；Fushuai 提出的「重新收敛期间迁移开销」目前是主观疑问，未见数据。

## 我可以参与的点

- new_patch：基于 Peter 的 `HAVE_CPUTIME_STEAL` 示例，把「PREFERRED_CPU ↔ PARAVIRT 解耦」整理为独立可合入补丁（这是唯一有合入可能的部分）。
- testing：在 hotplug 移除唯一 preferred CPU 的场景实测 steal governor 重新收敛期间的迁移次数与延迟，回应 Fushuai 的疑问。
- discussion：就「手动 preferred 接口 vs cpusets/isolation」用例与 Peter 讨论（方向已被否，投入产出低）。

## 参考链接

- lore thread（系列 cover）: https://lore.kernel.org/all/20261101192203.6979-1-ynorov@nvidia.com/
- Peter 澄清 preferred mask 语义: https://lore.kernel.org/all/20261105145537.GP1813469@noisy.programming.kicks-ass.net/
