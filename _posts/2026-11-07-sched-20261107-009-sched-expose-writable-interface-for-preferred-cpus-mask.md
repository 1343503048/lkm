---
id: sched-20261107-009
date: '2026-11-07'
subject: 'sched: Expose writable interface for preferred CPUs mask'
subsystem: sched
type: feature
status: stalled
severity: none
thread_root_msgid: <20261101192203.6979-1-ynorov@nvidia.com>
lore_url: https://lore.kernel.org/all/au4PfYJkpKLsISqb@yury/
authors:
- Yury Norov
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: rejected
  blocking_issues:
  - Peter 对 writable 接口的方向性 NAK 仍未变
  next_action: 聚焦 PREFERRED_CPU 解耦 PARAVIRT 独立补丁；手动接口需先打动 Peter
contribution_opportunities:
- kind: discussion
  description: 提供 cpusets 无法覆盖的真实生产用例，可能松动 Peter 的 NAK
- kind: testing
  description: 实测两 VM 超卖 + preferred mask 协商的迁移开销，回应 Fushuai 疑问
generated_at: '2026-11-08T09:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261102-004
- sched-20261105-005
tags:
- load_balance
- affinity
- topology
title: 'sched: Expose writable interface for preferred CPUs mask'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/02/sched-20261102-004-sched-expose-writable-interface-for-preferred-cpus-mask.html">sched-20261102-004</a>：Yury Norov 发 6-patch 系列为 preferred CPUs 提供运行时可写 sysfs 接口（`/sys/devices/system/cpu/cpuN/preferred`）；Peter Zijlstra 对整个手动接口方向 NAK（「We already have cpusets... this isn't happening」），仅认可其中 patch 1（PREFERRED_CPU 与 PARAVIRT 解耦）。
- <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-005-sched-expose-writable-interface-for-preferred-cpus-mask.html">sched-20261105-005</a>：讨论转入 patch 3/6 hotplug 移除最后一个 preferred CPU 时恢复所有 active CPU 的语义——Peter 澄清 preferred mask 与 cpusets 的区别（弱边界协作式 steal time 控制环 vs 强边界），Yury 解释 hotplug 回退最安全，Fushuai Wang 追问回退后 steal governor 重新收敛是否引入迁移开销。
- <a class="article-ref" href="/lkm/2026/11/07/sched-20261107-009-sched-expose-writable-interface-for-preferred-cpus-mask.html">sched-20261107-009</a>（今天）：Yury Norov 再补充 preferred cpumask 的定位——「只是让可信用户态能做最终决定，不是欺骗策略」，并给出 vCPU 超卖场景的具体用例：一台宿主机跑 AI 训练（性能关键）与推理（延迟关键）两个 VM，超卖时对称 throttle 会伤害体验，preferred mask 让两个 VM 能协商各自让出多少非 preferred vCPU。方向性 NAK 未变，今日是对用例层的继续澄清。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/02/sched-20261102-004-sched-expose-writable-interface-for-preferred-cpus-mask.html">sched-20261102-004</a> / 20261105-005）现有 preferred CPU mask 只供 steal governor 在 vCPU 抢占时动态缩减 vCPU 需求；Yury 希望增加运行时手动控制。Peter 以「cpusets 已能干这件事」为由 NAK 整个方向，仅认可 PREFERRED_CPU 解耦 PARAVIRT。

今日 Yury 的补充针对「preferred mask 到底解决什么」的定位疑问：它让可信用户态能在了解外部压力、workload 与 VM 优先级的前提下做最终决策，超越 steal time 记账本身能感知的范围；「preferred cpumask 可能有比盲目 vCPU throttle 更广的用例」。

## 技术方案

（承接）系列 6 补丁（Kconfig 解耦 / `reset_preferred_cpumask()` helper / hotplug 恢复 / `cpu_preferred_mutex` 串行化 / governor 告警 / per-CPU sysfs）。今日无技术变更，为用例澄清：Yury 给出「一主跑 AI 训练、一主跑延迟敏感推理的两 VM 超卖」场景，说明对称 throttle 对两边都不利，preferred mask 让两个 VM 相互沟通、决定各自让出多少非 preferred vCPU；steal governor 仍是合理默认，手动接口是对它的补充。

## 版本演进与当前进展

*current_version: v1*。今日无新版本；进展仍集中在语义/用例澄清（Yury 的定位说明）。

## Maintainer 意见与讨论焦点

Peter Zijlstra 对「手动 writable 接口」的方向性 NAK 未变；今日 Yury 是在澄清 preferred mask 的本义与用例（「不是欺骗策略，是让可信用户态做最终决定」），未直接回应 NAK。Fushuai Wang 此前的迁移开销疑问仍无数据支撑答复。

## 合入评估

*likelihood=rejected*（手动 sysfs 接口方向维持不变）。今日用例澄清未改变方向性 NAK。*blocking_issues*：Peter 对 writable 接口的 NAK 仍是根本障碍。*next_action*：若想推进，聚焦「PREFERRED_CPU 解耦 PARAVIRT」这一被认可的独立子补丁（已是 20261106-008 的独立补丁）；手动接口若要复活需先打动 Peter 或找到 cpusets 无法覆盖的硬用例。

## 效果评估

无性能数据。今日为用例层澄清，未涉及 benchmark；Fushuai 的「重新收敛期间迁移开销」仍是主观疑问，未见数据。

## 我可以参与的点

- **discussion**：为「手动 preferred 接口 vs cpusets/isolation」提供真实生产用例（尤其是否真存在 cpusets 无法表达的需求）——这是当前唯一可能松动 Peter NAK 的输入，但投入产出低。
- **testing**：实测「两 VM 超卖 + preferred mask 协商」在 steal governor 与手动接口下的迁移次数与延迟，回应 Fushuai 的疑问。

## 参考链接

- lore thread（今日 Yury 澄清）: https://lore.kernel.org/all/au4PfYJkpKLsISqb@yury/
- lore thread（系列 cover）: https://lore.kernel.org/all/20261101192203.6979-1-ynorov@nvidia.com/
