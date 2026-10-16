---
id: sched-20261016-019
date: 2026-10-16
subject: 'sched_ext: Support RT task within sched_ext'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <6b295276-4f42-4f46-b5a2-50c3ac83b412@oss.qualcomm.com>
lore_url: https://lore.kernel.org/all/6b295276-4f42-4f46-b5a2-50c3ac83b412@oss.qualcomm.com/
authors:
- Tengfei Fan
maintainers_involved:
- Tejun Heo
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - Tejun/Prateek 质疑 RT 任务进入 sched_ext 的必要性
  next_action: 作者回应为何不能直接降级 non-RT 或用现有机制
contribution_opportunities:
- kind: discussion
  description: 论证/反驳这些 RT 线程能否降级为 SCHED_OTHER/nice -20 且满足 RT 语义
generated_at: '2026-10-17T01:30:00'
source_email_count: 2
related_articles:
- sched-20261015-003
tags:
- sched_ext
- rt
title: 'sched_ext: Support RT task within sched_ext'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/15/sched-20261015-003-sched-ext-support-rt-task-within-sched-ext.html">sched-20261015-003</a>：Tengfei Fan（高通）重发 RFC，探讨让 RT 任务（SCHED_FIFO/SCHED_RR）与 sched_ext 在 CPU 放置、CPU 平衡、向 schedutil 上报负载三方面协同，避免 RT 任务抢占重要 SCX 任务造成帧率抖动；Andrea Righi 此前建议不改核心调度器、走 BPF ops。
- <a class="article-ref" href="/lkm/2026/10/16/sched-20261016-019-sched-ext-support-rt-task-within-sched-ext.html">sched-20261016-019</a>（今天）：Tejun Heo 与 K Prateek Nayak 上线回应，均对「在 sched_ext 里调度 RT 任务」的整个前提提出质疑——Tejun 反问「直接把它们降成 non-RT 不是更显然吗」；Prateek 长篇论证应靠 SCHED_OTHER demotion、UCLAMP、cpu affinities、`ops.cpu_release()` 等现有机制，而非把 RT 拉进 SCX。

## 背景与问题
（承接 20261015-003）Android 游戏/视频/直播里 RT 线程（display HAL、SurfaceFlinger 等）与非 RT 线程协作构帧，作者希望 sched_ext 能调度部分「显式选定」的 RT 任务以减少抢占干扰。今天的反馈聚焦一个更根本的问题：**这些线程到底该不该是 RT**。

## 技术方案
（承接 20261015-003）无代码。今天的讨论给出了两条替代路线（都避免改核心调度器）：
- Tejun：「isn't an obvious option to just make them non-RT?」——如果这些线程本就不想永远压过其他类任务，定义上就不该是 RT。
- Prateek：用 BPF Map 把需要 promotion/demotion 的 pid 报给 userspace，临时把任务降到 SCHED_OTHER、时机合适再升回 RT；或让自定义调度器足够好后把这些任务都改成 nice -20 的 SCX 任务；用 UCLAMP 避免不必要的频率上跳；用 `ops.cpu_release()` 做 re-enqueue 完成 CPU 平衡；cpu affinities 也可作为选项。

## 版本演进与当前进展
RFC（重发）→ 今天 Tejun/Prateek 上线质疑前提。无代码版本演进。

## Maintainer 意见与讨论焦点
Tejun Heo（sched_ext 维护者）质疑 RT 前提：「fundamental problem seems like you don't want these threads to be always prioritized over some of the OTHER class tasks, which definitionally means that they shouldn't be RT」。Prateek 则批评「doing everything in sched-ext and eBPF 的态度需要改变」，主张回归 SCHED_OTHER/UCLAMP/affinity 等现有机制。两位都未认可「在 sched_ext 里调度 RT 任务」的必要性。

## 合入评估
*likelihood=low*。维护者（Tejun）质疑问题定义，社区倾向用现有机制替代，作者尚未回应。*blocking_issues*：Tejun/Prateek 均质疑「RT 任务进入 sched_ext」的必要性，作者需重新论证或转向前述替代路线。*next_action*：作者回应 Tejun/Prateek，说明为何不能直接降级为 non-RT 或用现有机制。

## 效果评估
无量化数据。

## 我可以参与的点
- *discussion*：帮助论证或反驳「这些 RT 线程能否直接降级为 SCHED_OTHER/nice -20」——尤其 RT 语义（PI、优先级）在降级后是否仍满足场景需求。

## 参考链接
- Tejun 的回复：https://lore.kernel.org/all/atEBWwXSt4D8befY@slm.duckdns.org/
- Prateek 的回复：https://lore.kernel.org/all/52e9ca5e-0147-4450-928e-5b1c56e5d1a5@amd.com/
- RFC：https://lore.kernel.org/all/6b295276-4f42-4f46-b5a2-50c3ac83b412@oss.qualcomm.com/
