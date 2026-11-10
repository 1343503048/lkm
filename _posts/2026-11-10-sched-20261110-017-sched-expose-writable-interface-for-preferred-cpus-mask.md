---
id: sched-20261110-017
date: '2026-11-10'
subject: 'sched: Expose writable interface for preferred CPUs mask'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <1d1b22ce-fdf1-47ad-99ec-8c9925ea7275@linux.ibm.com>
lore_url: https://lore.kernel.org/all/1d1b22ce-fdf1-47ad-99ec-8c9925ea7275@linux.ibm.com/
authors:
- Yury Norov
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <20261101192203.6979-1-ynorov@nvidia.com>
  date: '2026-11-01'
  summary: 6 补丁为 preferred CPUs 提供运行时可写 sysfs 接口
  review_outcome: Peter NAK 手动接口方向；今日 Shrikanth 从功能重叠角度追加质疑
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: rejected
  blocking_issues:
  - Peter 对 writable 接口的 NAK 是根本障碍
  - 功能重叠质疑（offline 可替代）未被作者回应
  next_action: 聚焦 PREFERRED_CPU 解耦 PARAVIRT 独立子补丁；手动接口需硬用例
contribution_opportunities:
- kind: discussion
  description: 提供 cpusets 与 offline 均无法覆盖的运行时手动 preferred 场景
generated_at: '2026-11-11T09:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261102-004
- sched-20261105-005
- sched-20261107-009
tags:
- affinity
- cgroup
- topology
title: 'sched: Expose writable interface for preferred CPUs mask'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/02/sched-20261102-004-sched-expose-writable-interface-for-preferred-cpus-mask.html">sched-20261102-004</a>：Yury Norov 发 6-patch 系列为 preferred CPUs 提供运行时可写 sysfs 接口（`/sys/devices/system/cpu/cpuN/preferred`）；Peter Zijlstra 对整个手动接口方向 NAK（「We already have cpusets... this isn't happening」），仅认可 patch 1（PREFERRED_CPU 与 PARAVIRT 解耦）。
- <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-005-sched-expose-writable-interface-for-preferred-cpus-mask.html">sched-20261105-005</a>：讨论转入 hotplug 移除最后一个 preferred CPU 时恢复所有 active CPU 的语义——Peter 澄清 preferred mask 与 cpusets 的区别，Yury 解释 hotplug 回退最安全，Fushuai Wang 追问回退后 steal governor 重收敛是否引入迁移开销。
- <a class="article-ref" href="/lkm/2026/11/07/sched-20261107-009-sched-expose-writable-interface-for-preferred-cpus-mask.html">sched-20261107-009</a>：Yury 再补充 preferred cpumask 定位——「只是让可信用户态做最终决定，不是欺骗策略」，并给 vCPU 超卖场景（AI 训练 + 推理两 VM 协商让出非 preferred vCPU）用例。方向性 NAK 未变。
- <a class="article-ref" href="/lkm/2026/11/10/sched-20261110-017-sched-expose-writable-interface-for-preferred-cpus-mask.html">sched-20261110-017</a>（今天）：**Shrikanth Hegde（IBM，ppc 调度开发者）从侧面质疑用例**——若在启动前就设好 preferred mask，「offline 那些 CPU 也能达到同样效果」，暗示手动 preferred 接口与已存在的 CPU online 状态管理存在重叠。方向性 NAK 依旧。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/02/sched-20261102-004-sched-expose-writable-interface-for-preferred-cpus-mask.html">sched-20261102-004</a> / 20261105-005 / 20261107-009）preferred CPU mask 原本只供 steal governor 在 vCPU 抢占时动态缩减 vCPU 需求；Yury 希望增加运行时手动控制接口。Peter 以「cpusets 已能干这件事」NAK 了整个 writable 方向，仅认可 PREFERRED_CPU 解耦 PARAVIRT。今日 Shrikanth 补充了一个「功能重叠」角度的质疑：启动前设定 preferred mask 时，直接 offline CPU 也能达到同样效果，进一步削弱手动接口的必要性。

## 技术方案

（承接）系列 6 补丁（Kconfig 解耦 / helper / hotplug 恢复 / mutex 串行化 / governor 告警 / per-CPU sysfs）。今日无技术变更，为用例层面的又一质疑：Shrikanth 指出「若在启动前设 preferred，offline CPU 同样有效」，暗示这削弱了「运行时手动 preferred 接口」独有价值——真正的差异只在运行时动态调整期间 preferred 不触发在线/离线开销。

## 版本演进与当前进展

*current_version: v1*。今日无新版本；进展仍在语义/用例澄清，方向性 NAK 未变。

## Maintainer 意见与讨论焦点

Peter Zijlstra 对「手动 writable 接口」的方向性 NAK 未变；今日 Shrikanth Hegde 从功能重叠角度追加质疑（offline 可替代启动前设定场景）。Yury 尚未在当日窗口回应。Fushuai Wang 此前的迁移开销疑问仍无数据支撑答复。

## 合入评估

*likelihood=rejected*（手动 sysfs 接口方向维持不变）。今日的「offline 可替代」质疑进一步削弱了该接口的独有存在价值，不影响此前的方向性判断。*blocking_issues*：Peter 的 NAK 仍是根本障碍，且功能重叠质疑未被作者回应。*next_action*：若想推进，聚焦「PREFERRED_CPU 解耦 PARAVIRT」这一被认可的独立子补丁；手动接口需找到 cpusets/offline 都无法覆盖的硬用例才有复活可能。

## 效果评估

无性能数据。今日为用例层质疑（offline 可替代），无 benchmark 涉及。

## 我可以参与的点

- **discussion**：为「运行时手动 preferred 接口」提供 cpusets 与 offline 均无法覆盖的真实场景（例如不停机在线调整、且不愿承担 offline/online 开销的用例）——这是当前唯一可能松动 NAK 的输入，但投入产出低。

## 参考链接

- Shrikanth 的质疑: https://lore.kernel.org/all/1d1b22ce-fdf1-47ad-99ec-8c9925ea7275@linux.ibm.com/
