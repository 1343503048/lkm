---
type: feature
status: rfc
severity: none
thread_root_msgid: <2a5dd3fd-a03f-4ffb-827c-2937bf664c75@oss.qualcomm.com>
authors:
- Cong Zhang
maintainers_involved: []
current_version: v1
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - RFC 设计权衡期（broadcast 范围、sysfs 暴露测值）
  next_action: 继续与 Christian 收敛设计后发实现
contribution_opportunities:
- kind: discussion
  description: 评估 sysfs 暴露实测 vs PM QoS 动态值取舍
- kind: testing
  description: 全局定时器平台验证补偿范围
upstream_commit: null
fixes_commit: null
merged_branch: null
source_email_count: 1
related_articles:
- sched-20261016-018
- sched-20261021-016
tags:
- idle
- nohz
id: sched-20261102-026
subject: 'cpuidle: runtime exit latency prediction and timer compensation'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
title: 'cpuidle: runtime exit latency prediction and timer compensation'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/16/sched-20261016-018-cpuidle-runtime-exit-latency-prediction-and-timer-compensati.html">sched-20261016-018</a>：Cong Zhang（高通）发 RFC——运行时测量/预测 CPU idle exit latency 并补偿 hrtimer 回调延迟，取替设备树静态 worst-case。
- <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-016-cpuidle-runtime-exit-latency-prediction-and-timer-compensati.html">sched-20261021-016</a>：作者逐条回应 Christian Loehle 的疑问。
- sched-20261102（今天）：作者再澄清「global/broadcast timer case」——有 always-on 全局定时器时 bc_hrtimer 近似普通 hrtimer、CPU 无法进深 idle、cluster 不进睡、补偿仅作用于 CPU；并提出把「测得的最大 exit latency」经 sysfs 暴露给用户，让用户据此在设备树里设置静态 exit latency，而 PM QoS 仍用静态值。

## 背景与问题

（承接）idle exit latency 静态 worst-case 不反映真实条件。今日聚焦 broadcast timer 下的补偿范围界定与「测值如何为用户使用」。

## 技术方案

（承接）无新代码；作者提出补充设计：sysfs 暴露最大实测 latency，用户据实测+硬件在设备树设置静态值，PM QoS 保持使用静态 latency。

## 版本演进与当前进展

RFC；今日为设计细节收敛（broadcast 范围 + sysfs 暴露测值）。

## Maintainer 意见与讨论焦点

Christian Loehle 前期的问题仍在逐步闭环；无维护者明确 pull。

## 合入评估

likelihood=unknown。RFC 尚在设计权衡期。

## 效果评估

无量化数据；作者强调其目标是「让 devicetree 里的 max exit latency 更可信」。

## 我可以参与的点

- discussion：评估「sysfs 暴露最大实测 latency」vs「PM QoS 用动态值」的取舍。
- testing：在带 always-on 全局定时器的平台验证补偿仅作用 CPU 的行为。

## 参考链接

- lore thread: https://lore.kernel.org/all/2a5dd3fd-a03f-4ffb-827c-2937bf664c75@oss.qualcomm.com/
