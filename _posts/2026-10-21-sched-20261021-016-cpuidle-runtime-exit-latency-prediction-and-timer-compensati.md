---
id: sched-20261021-016
date: 2026-10-21
subject: 'cpuidle: runtime exit latency prediction and timer compensation'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/428a0bae-adad-4cbf-b551-fa0f0ab4e694@oss.qualcomm.com/
authors:
- Cong Zhang
maintainers_involved: []
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 代码未发布
  - 功耗影响的量化证据缺失
  next_action: 作者清理代码后发布并补收益/功耗数据
contribution_opportunities:
- kind: discussion
  description: 提供 C-state pre-wake 共存与功耗影响实测输入
- kind: testing
  description: 代码发布后在非高通平台验证预测有效性
generated_at: '2026-10-22T01:30:00'
source_email_count: 1
related_articles:
- sched-20261016-018
tags:
- idle
title: 'cpuidle: runtime exit latency prediction and timer compensation'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/10/16/sched-20261016-018-cpuidle-runtime-exit-latency-prediction-and-timer-compensati.html">sched-20261016-018</a>：Cong Zhang（高通）发 RFC——运行时测量并预测 CPU idle exit latency，并用预测补偿 hrtimer 到期与回调实际执行之间的延迟（hrtimer rooster 方案），取代设备树静态 worst-case；想法源自 2026 LPC。Christian Loehle 抛出一串关键问题（与硬件 C-state pre-wake 的共存、cluster-off 双峰延迟、收益与功耗、采样方法论、是否动 QoS）。
- <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-016-cpuidle-runtime-exit-latency-prediction-and-timer-compensati.html">sched-20261021-016</a>（今天）：Cong Zhang 逐条回应 Christian——C-state pre-wake 与本 RFC 目标相似时可直接退化到「只采样不补偿」；高通能拿到准确的 cluster-off 信息；广播可视为更激进的补偿但会增功耗；并澄清采样可保留、real rooster irq 时间已知、双 CPU 恢复时间差等疑问，同时宣布代码清理中、完成即分享。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/10/16/sched-20261016-018-cpuidle-runtime-exit-latency-prediction-and-timer-compensati.html">sched-20261016-018</a>）CPU idle 时 hrtimer 到期，从收到 IRQ 到内核开始执行的「idle exit latency」目前用设备树静态 worst-case 描述，不反映真实条件。作者主张运行时动态测量并预测，减少误判与功耗影响。今日补充更多实现语境：高通平台可从 cluster sleep driver 拿到准确 cluster-off 信息；若固件决定 cluster 何时入眠，则需要一个接口来获取该信息。

## 技术方案
（承接 RFC 方向，无新完整代码）运行时测量/预测 idle exit latency 并补偿 hrtimer 回调延迟。今日澄清关键取舍：若与硬件 C-state pre-wake 功能重叠，可回退为「只采样、不补偿」；「全局时间帧」理论上不增功耗，而「广播」更激进但可能增功耗；采样保持开启时仍知道 rooster irq 的真实唤醒时间，二者之差即为 exit latency；预测正确但提前唤醒时，CPU 用 WFI 短暂 idle 等 timer 到期。

## 版本演进与当前进展
*current_version: RFC*（代码清理中，暂无正式补丁版本发布）。

## Maintainer 意见与讨论焦点
Christian Loehle（Arm）此前抛出的共存/功耗/采样/QoS 疑问，今日被作者逐条回应，但仍需实际代码与数据支撑「全局时间帧不增功耗」等主张（作者自述「We still need more data for that」）。无维护者结论。

## 合入评估
*likelihood=unknown*。仍处 RFC 早期，无补丁代码、无线索确认的实现效果数据，评审问题部分待数据支撑。*blocking_issues*：代码未发布；功耗影响的量化证据缺失。*next_action*：作者清理代码后发布，并补收益/功耗数据。

## 效果评估
无量化数据。作者定性说明「高通的 cluster-off 信息准确」「最坏情况 exit latency 通常是估计值，可保留最高观测值用于 QoS」，但明确仍需更多数据。多为主观判断，未见数据。

## 我可以参与的点
- `discussion`：与硬件 C-state pre-wake 的共存、以及「全局时间帧是否真的不增功耗」是悬而未决的关键点，可提供平台实测输入。
- `testing`：代码发布后在非高通平台（x86/arm 其他 idle 路径）验证 runtime exit latency 预测的有效性。

## 参考链接
- Cong Zhang 的逐条回应：https://lore.kernel.org/all/428a0bae-adad-4cbf-b551-fa0f0ab4e694@oss.qualcomm.com/
