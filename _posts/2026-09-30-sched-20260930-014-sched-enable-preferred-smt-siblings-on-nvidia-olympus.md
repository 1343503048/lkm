---
id: sched-20260930-014
date: '2026-09-30'
subject: 'sched: Enable preferred SMT siblings on NVIDIA Olympus'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260929165538.726616-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260929165538.726616-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Vincent Guittot
current_version: v7
patch_series:
- version: v6
  msgid: <20260917140707.3807229-1-arighi@nvidia.com>
  date: '2026-09-17'
  summary: sched_smt_asym_packing={auto,on,off} boot 选项 + idle 选择 honor SD_ASYM_PACKING
  review_outcome: Breno Tested-by；Dietmar 追问吞吐/负载模型；09-29 Andrea 逐条澄清
- version: v7
  msgid: <20260929165538.726616-1-arighi@nvidia.com>
  date: '2026-09-30'
  summary: boot 选项收紧为仅 =on（drop auto/off）；补 OpenBLAS +3.20% / NVPL +6.73% 吞吐数据
  review_outcome: 1/2 集齐 Srikar/Prateek/Vincent/Kayra Reviewed-by；待维护者收取
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 尚未见维护者最终收取
  - 新增内核参数 sched_smt_asym_packing 需最终 ABI/文档评审
  next_action: 等 Vincent/Peter 收取进 tip/sched/core
contribution_opportunities:
- kind: testing
  description: 补测延迟/功耗维度对比（当前有吞吐、缺延迟与功耗）并回帖
- kind: review
  description: 评审新内核参数在 arm64/ppc 自定义 SMT 拓扑回调下的语义边界与文档一致性
generated_at: '2026-10-01T01:00:00'
source_email_count: 3
related_articles:
- sched-20260921-004
- sched-20260929-019
tags:
- topology
- idle
- hyperthreading
title: 'sched: Enable preferred SMT siblings on NVIDIA Olympus'
layout: article
---

> **subject**：`sched: Enable preferred SMT siblings on NVIDIA Olympus`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/21/sched-20260921-004-sched-enable-preferred-smt-siblings-on-nvidia-olympus.html">sched-20260921-004</a>：Andrea Righi 的「在 NVIDIA Olympus 上启用优先 SMT 兄弟」系列（v6）获 Breno Leitao 完整 Tested-by 与 Dietmar Eggemann 对 Spatial SMT 收益机制的追问。
- <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-019-sched-enable-preferred-smt-siblings-on-nvidia-olympus.html">sched-20260929-019</a>：Andrea 逐条回复 Dietmar（POWER7 自设 `SD_ASYM_PACKING` 无需 boot 选项；boot 选项只服务固件不描述偏好的 Olympus），并补充 88 线程 benchmark 负载模型。
- <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-014-sched-enable-preferred-smt-siblings-on-nvidia-olympus.html">sched-20260930-014</a>（今天）：作者发 **v7**——按 Vincent/Shrikanth 意见把 boot 选项收紧为只接受 `sched_smt_asym_packing=on`（去掉 auto/off 冗余模式）；并补上此前最缺的吞吐量化（OpenBLAS +3.20%、NVPL +6.73%），此前的「缺吞吐数据」阻塞点解除。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/21/sched-20260921-004-sched-enable-preferred-smt-siblings-on-nvidia-olympus.html">sched-20260921-004</a>）NVIDIA 的 Spatial SMT 会动态把物理核切分为两个「兄弟」逻辑核，传统 `sched_smt_asym_packing` 语义不适用，需要在 idle 选择路径上优先选择低编号（PE0）兄弟，让 PE0 保持全资源单线程模式、PE1 空闲。Olympus 固件当前不提供描述 sibling 偏好的接口，MIDR 推断又会把平台特定策略写进内核，故 v6 起引入 `sched_smt_asym_packing` boot 选项作为显式 fallback。v7 收紧该选项语义。

## 技术方案

（承接）v7 两补丁不变：1/2 教 fair 的 idle 选择路径在共享容量的 SMT 域上 honor `SD_ASYM_PACKING`（先按既有放置/容量规则选 CPU 与 core，再选 core 内最高优先级可用 sibling，POWER7 既有的硬件线程序也受益）；2/2 加 `sched_smt_asym_packing=on` boot 选项，central 地给 `SD_SHARE_CPUCAPACITY` 域加 `SD_ASYM_PACKING`（覆盖 powerpc 等自定义 SMT 拓扑回调），优先级仍由 `arch_asym_cpu_priority()` 决定、弱默认取低编号逻辑 CPU。

v7 变化：只接受 `sched_smt_asym_packing=on`（省略即保持架构/固件拓扑），去掉 v6 的 auto/off 冗余模式（Vincent Guittot、Shrikanth Hegde）。

## 版本演进与当前进展

- 系列 v6（09-17，`<20260917140707.3807229-1-arighi@nvidia.com>`）。
- v7（09-30，`<20260929165538.726616-1-arighi@nvidia.com>`）：boot 选项收为仅 `=on`；补吞吐 benchmark。1/2 带三 `Reviewed-by`（Srikar Dronamraju、K Prateek Nayak、Vincent Guittot、Kayra Cizmeci）与三 `Tested-by`。

## Maintainer 意见与讨论焦点

- 无 NAK；Vincent Guittot、Shrikanth Hegde 建议收紧 boot 选项（v7 采纳）。1/2 已集齐多位 reviewer 的 `Reviewed-by`（Srikar、Prateek、Vincent、Kayra）与 `Tested-by`（Prateek、Kayra、Breno）。
- 此前 Dietmar Eggemann 追问的吞吐数据今日由作者在 v7 cover 补上。

## 合入评估

*likelihood=high*。功能正确性已有多平台 `Tested-by`，1/2 集齐多位核心 reviewer 的 `Reviewed-by`，v7 补齐了此前唯一明显的阻塞点（吞吐量化）并响应了 boot 选项收紧意见；系列已高度收敛，主要剩 Peter/Vincent 的最终收取与 `sched_smt_asym_packing=` 文档/参数评审。*blocking_issues*：尚未见维护者最终收取；boot 选项属新增 ABI（内核参数），需最终评审。*next_action*：等 Vincent/Peter 收取进 tip/sched/core。

## 效果评估

v7 cover 给出双 benchmark（两节点 Vera 88 线程单精度 GEMM，NUMA node 0 的 88 物理核、两 sibling 均可选，各 5 轮）：OpenBLAS 从 7.11876±0.06734 → 7.34669±0.01936 TFLOP/s（+3.20%）；NVPL 从 9.64742±0.17311 → 10.29695±0.01786 TFLOP/s（+6.73%）；标准差下降表明结果更可预测，且负载一致落到低编号 sibling。此前（v6 讨论）还有唤醒重定向 800/800 命中、ST/SMT 切换下降 ~80%。

## 我可以参与的点

- `testing`：在 NVIDIA Spatial SMT 或非对称 SMT 优先级平台上补测延迟/功耗维度（当前有吞吐、缺延迟与功耗对比），回帖补数据。
- `review`：评审 `sched_smt_asym_packing=` 这一新内核参数在 arm64/ppc 等自定义 SMT 拓扑回调下的语义边界与文档一致性。

## 参考链接

- lore（v7 cover）: https://lore.kernel.org/all/20260929165538.726616-1-arighi@nvidia.com/
- lore（v6 cover）: https://lore.kernel.org/all/20260917140707.3807229-1-arighi@nvidia.com/
