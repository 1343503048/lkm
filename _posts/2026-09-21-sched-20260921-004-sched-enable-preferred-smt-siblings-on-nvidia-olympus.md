---
id: sched-20260921-004
date: '2026-09-21'
subject: 'sched: Enable preferred SMT siblings on NVIDIA Olympus'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260917140707.3807229-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260917140707.3807229-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Dietmar Eggemann
current_version: v6
patch_series:
- version: v6
  msgid: <20260917140707.3807229-1-arighi@nvidia.com>
  date: '2026-09-17'
  summary: v6 封面：Enable preferred SMT siblings；patch 1/2 为 Honor asymmetric SMT priority
    in idle selection
  review_outcome: Breno Leitao Tested-by，Dietmar Eggemann 追问 throughput 数据与负载模型
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 缺少实测 throughput 数据，Breno 未测、Dietmar 正在追问 benchmark 负载模型
  next_action: 作者补充 Olympus 平台的吞吐对比数据并回应 Dietmar 关于负载模型的疑问
contribution_opportunities:
- kind: testing
  description: 在非对称 SMT 优先级平台上补测吞吐/延迟并回帖数据（当前最缺 throughput 数字）
- kind: review
  description: 分析 Spatial SMT 下 PE0 单线程模式的吞吐收益模型，回应 Dietmar 的疑问
generated_at: '2026-09-22T01:10:00'
source_email_count: 2
related_articles:
- sched-20260917-018
- sched-20260918-008
tags:
- topology
- idle
- hyperthreading
title: 'sched: Enable preferred SMT siblings on NVIDIA Olympus'
layout: article
---

## TL;DR
增量更新：Andrea Righi 的"在 NVIDIA Olympus 上启用优先 SMT 兄弟"系列（v6，其中 1/2 为 `sched/fair: Honor asymmetric SMT priority in idle selection`）昨日又获两则实质反馈——Breno Leitao 给出完整 Tested-by（实测唤醒重定向 800/800 生效、无 KASAN/lockdep 告警），Dietmar Eggemann 则对 Spatial SMT 收益机制提出技术问题，想确认作者是否持有 88 个持续运行的 benchmark 线程的负载模型。方向获认可，但 throughput 数据仍缺。

## 背景与问题
背景见 <a class="article-ref" href="/lkm/2026/09/17/sched-20260917-018-sched-enable-preferred-smt-siblings-on-nvidia-olympus.html">sched-20260917-018</a> / <a class="article-ref" href="/lkm/2026/09/18/sched-20260918-008-sched-fair-honor-asymmetric-smt-priority-in-idle-selection.html">sched-20260918-008</a>：NVIDIA 的 Spatial SMT 会动态把物理核切分为两个"兄弟"逻辑核，传统 `sched_smt_asym_packing` 语义不适用，需要在 idle 选择路径上优先选择低编号（PE0）兄弟，让 PE0 保持全资源单线程模式、PE1 空闲。

## 技术方案
本日无新代码，仅两条社区反馈进一步验证/拷问既有方案。Breno 测试覆盖了 SMT 域的 `SD_ASYM_PACKING` 标记、域重建后的 override 重放（~400 次热插拔）、以及高编号兄弟向低编号兄弟的唤醒重定向。Dietmar 则从机制层面确认：这套代码"只对 NVIDIA Spatial SMT 这类动态分区物理核有益"，传统 SMT（Power7 等两线程机会性竞争同一资源）不会打开 `sched_smt_asym_packing`，故不会受影响。

## 版本演进与当前进展
- 系列已到 v6（09-17 发出，thread root `<20260917140707.3807229-1-arighi@nvidia.com>`）。
- 09-21：Breno Leitao 给 `sched/fair: Honor asymmetric SMT priority in idle selection`（patch 1/2）补 Tested-by；Dietmar Eggemann 在 v6 cover 下继续讨论。

## Maintainer 意见与讨论焦点
- **Breno Leitao（Tested-by，非维护者）**：在自有两路 NVIDIA Olympus（88 核/路、SMT2、352 CPU、36 NUMA 节点），用 KASAN + PROVE_LOCKING 的 arm64 内核基于 linux-next 20260918 测试：`sched_smt_asym_packing=on` 时 `SD_ASYM_PACKING` 只出现在 SMT 域（MC/NUMA 不受影响），override 每次域重建都会重放；高编号兄弟上唤醒的任务 800/800 被重定向到低编号兄弟（无系列时仅 13/800）；stress-ng 与 perf bench sched 下无 WARN/BUG/KASAN/lockdep。**但明确说"未测吞吐"**。
- **Dietmar Eggemann（ARM 调度维护者）**：认可该代码只惠及 Spatial SMT，但提出关键疑问——收益假设是"88 个持续运行的 benchmark 线程 + 新代码让它们更可能落在 PE0 上"带来吞吐提升，想确认作者的 benchmark 任务模型是否正是如此（以及 NVPL 是否带少量 sleep/wakeup 的同类模型）。

## 合入评估
*likelihood=medium*。功能正确性已有独立平台 Tested-by 背书，无 NAK 与反对；但合入前的关键缺口是**实测吞吐数据**（Breno 未测、Dietmar 也在追问负载模型），以及 Spatial SMT 收益是否足够普适到值得进主线。*blocking_issues*：缺少 throughput 验证数据。*next_action*：作者补充在 Olympus 上的吞吐对比数据并回应 Dietmar 的负载模型问题。

## 效果评估
功能层面：唤醒重定向 800/800 命中（vs 基线 13/800），正确性无告警。性能层面：尚未给出吞吐提升数字，收益仍属"机制推演 + 作者早前主观声称"，未见新的 benchmark 数字支撑。

## 我可以参与的点
- **testing**：在 NVIDIA Spatial SMT（或任何具备非对称 SMT 优先级的平台）上补测吞吐/延迟对比，回帖给出具体数字，这是当前最缺的一块。
- **review**：可围绕 Dietmar 的疑问分析 Spatial SMT 下 PE0 单线程模式带来的真实吞吐收益模型。

## 参考链接
- lore thread: https://lore.kernel.org/all/20260917140707.3807229-1-arighi@nvidia.com/
