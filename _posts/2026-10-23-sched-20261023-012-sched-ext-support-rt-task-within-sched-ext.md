---
id: sched-20261023-012
date: 2026-10-23
subject: 'sched_ext: Support RT task within sched_ext'
subsystem: sched
type: discussion
status: rfc
severity: none
thread_root_msgid: <6b295276-4f42-4f46-b5a2-50c3ac83b412@oss.qualcomm.com>
lore_url: https://lore.kernel.org/all/6b295276-4f42-4f46-b5a2-50c3ac83b412@oss.qualcomm.com/
authors:
- Tengfei Fan
maintainers_involved:
- Tejun Heo
- Andrea Righi
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无代码
  - metadata 方案验证结果未产出
  next_action: 作者完成 metadata 验证并回帖结果后评估是否成补丁
contribution_opportunities:
- kind: discussion
  description: 就 metadata 与调度属性一致性（转 non-RT 后 priority 变更同步）给出设计建议
- kind: testing
  description: 在 Android 类场景验证 RT metadata 放置偏好的实际效果
generated_at: '2026-10-24T09:11:00'
source_email_count: 3
related_articles:
- sched-20261015-003
- sched-20261016-019
tags:
- sched_ext
- rt
title: 'sched_ext: Support RT task within sched_ext'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/10/15/sched-20261015-003-sched-ext-support-rt-task-within-sched-ext.html">sched-20261015-003</a>：Tengfei Fan（高通）重发 RFC，探讨让 RT 任务（SCHED_FIFO/SCHED_RR）与 sched_ext 在 CPU 放置、CPU 平衡、向 schedutil 上报负载三方面协同，避免 RT 任务抢占重要 SCX 任务造成帧率抖动；Andrea Righi 此前建议不改核心调度器、走 BPF ops。
- <a class="article-ref" href="/lkm/2026/10/16/sched-20261016-019-sched-ext-support-rt-task-within-sched-ext.html">sched-20261016-019</a>：Tejun Heo 与 K Prateek Nayak 上线回应，均质疑「在 sched_ext 里调度 RT 任务」的前提——Tejun 反问「直接降成 non-RT 不是更显然吗」；Prateek 主张用 SCHED_OTHER demotion、UCLAMP、cpu affinity、`ops.cpu_release()` 等现有机制。
- <a class="article-ref" href="/lkm/2026/10/23/sched-20261023-012-sched-ext-support-rt-task-within-sched-ext.html">sched-20261023-012</a>（今天）：Tengfei Fan 接受 Andrea 的「保留 RT policy/prio 作 metadata、转 non-RT」方向，明确不再走「把原生 RT 任务放进 sched_ext dispatch 路径」，并给出具体验证流（config 按 PID → 存 RT policy/prio → 转 non-RT → sched_ext），同时提出 metadata 与调度属性一致性等开放问题。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/10/15/sched-20261015-003-sched-ext-support-rt-task-within-sched-ext.html">sched-20261015-003</a> → <a class="article-ref" href="/lkm/2026/10/16/sched-20261016-019-sched-ext-support-rt-task-within-sched-ext.html">sched-20261016-019</a>）Android 游戏/视频/直播里 RT 线程（display HAL、SurfaceFlinger 等）与非 RT 线程协作构帧，作者希望 sched_ext 能调度部分「显式选定」的 RT 任务以减少抢占干扰。上轮 Tejun/Prateek 质疑「这些线程是否本该是 RT」。今天作者澄清：并非建议让 SCHED_OTHER 任务优先于 RT 任务，而是要的是「CPU 选择的放置偏好」——多个合适 CPU 可选时，RT 任务优先抢占「不重要的 SCX 任务」而非「重要的」；无可选时才抢占重要任务；「timing needs」措辞被撤回（SCHED_FIFO/RR 除 policy/prio 外并无独立时序要求）。

## 技术方案
（承接 + 今日更新）无代码。今天的收敛路径（遵循 Andrea Righi 建议，不再改核心调度器）：

- 不再考虑把原生 RT 任务经 sched_ext dispatch 路径放到其他 CPU（LPC 上的建议来自 Andrea，作者明确不采纳原生 RT 直放）。
- 改为：把选定应用线程的请求 RT policy/priority **作为 metadata 保留**、把这些线程转成 **non-RT**，在 sched_ext 内部用该 metadata 做放置/排序决策；需要原生 RT 行为的线程仍留在 RT 类。
- 初始验证用简单 userspace 机制：`config（按 PID）→ 识别选定 RT 线程 → 存 RT policy/prio 作 metadata → 转 non-RT → sched_ext`；选择机制尚未定型（仅为验证手段）。
- 开放问题（作者主动提出）：转 non-RT 后，若 userspace 再改任务优先级，如何保持 metadata 与调度属性一致；`ops.cpu_release()` 是否足以处理该场景尚未评估；schedutil 频率上跳（SCX 负载接近频率转换点、附加 RT 负载触发频率 bump）是否能用合适 uclamp 配置避免尚未验证。

## 版本演进与当前进展
RFC（重发）→ 方向收敛：不再改核心调度器、改走「metadata + 转 non-RT」。无代码版本演进。

## Maintainer 意见与讨论焦点
- Tejun Heo / K Prateek Nayak（上轮）质疑前提后，作者今日实质接受了「不把原生 RT 拉进 SCX」这一方向，转而采纳 Andrea 的 metadata 方案。
- 作者强调这是「generic placement 问题」，当前只是在 sched_ext 里做实验，若有成效愿回馈社区讨论更通用方案。
- 未决项：metadata 一致性、`ops.cpu_release()` 是否够用、频率上跳的 uclamp 对策——均待作者验证后回帖。

## 合入评估
*likelihood=unknown*。仍处 RFC 设计探索阶段，无补丁、无合并目标；方向刚收敛到「metadata + 转 non-RT」的验证路径。*blocking_issues*：无代码；验证结果（metadata 方案能否给出所需放置行为）尚未产出。*next_action*：作者完成基于 PID config 的 metadata 验证并回帖结果，再评估是否形成补丁。

## 效果评估
无性能数据。作者描述了观测到的现象（SCX 负载接近频率转换点时附加 RT 负载触发频率 bump）但未给量化数字，且明确「未验证 uclamp 能否避免」。

## 我可以参与的点
- *kind: discussion*：就「metadata 与任务调度属性的一致性」问题（转 non-RT 后 priority 变更如何同步）给出设计建议。
- *kind: testing*：在 Android 类场景验证「RT metadata 放置偏好」能否在避免抢占重要 SCX 任务的同时保住 RT 任务性能。

## 参考链接
- Tengfei Fan 回帖（最详）: https://lore.kernel.org/all/8da9b59f-324b-439e-839d-bad024c8b988@oss.qualcomm.com/
- Tengfei Fan 回帖 2: https://lore.kernel.org/all/6c17505f-e5a1-4505-a6b4-08b0c88a6dfb@oss.qualcomm.com/
- Tengfei Fan 回帖 3: https://lore.kernel.org/all/4de40ae2-3661-4fc3-85a6-63eede38e7c0@oss.qualcomm.com/
- 前文: <a class="article-ref" href="/lkm/2026/10/15/sched-20261015-003-sched-ext-support-rt-task-within-sched-ext.html">sched-20261015-003</a> / <a class="article-ref" href="/lkm/2026/10/16/sched-20261016-019-sched-ext-support-rt-task-within-sched-ext.html">sched-20261016-019</a>
