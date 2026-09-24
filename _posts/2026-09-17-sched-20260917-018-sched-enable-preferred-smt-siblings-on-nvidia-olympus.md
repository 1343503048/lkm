---
id: sched-20260917-018
date: '2026-09-17'
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
- Will Deacon
- Vincent Guittot
current_version: v6
patch_series:
- version: v5
  msgid: <20260909062649.469633-1-arighi@nvidia.com>
  date: '2026-09-09'
  summary: MIDR 特判启用 SD_ASYM_PACKING，删 olympus_prefer_pe0 状态
  review_outcome: Will/Vincent 要求改通用接口
- version: v6
  msgid: <20260917140707.3807229-1-arighi@nvidia.com>
  date: '2026-09-17'
  summary: 弃 MIDR 特判，加 sched_smt_asym_packing boot 选项，用 sched_smt_active()
  review_outcome: 回应 Will/Vincent，待维护者评审
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - boot 选项命名/语义待更上层维护者评审
  - v6 当日无回帖
  next_action: 等待 sched 维护者评审 v6
contribution_opportunities:
- kind: testing
  description: 在其它 SMT 平台（尤其 powerpc）验证 sched_smt_asym_packing 语义与回归
- kind: review
  description: 评估 boot 选项命名与 auto/on/off 语义、与既有 SD_ASYM_PACKING 冲突
generated_at: '2026-09-18T09:00:00'
source_email_count: 3
related_articles:
- sched-20260911-017
tags:
- topology
- idle
- hyperthreading
title: 'sched: Enable preferred SMT siblings on NVIDIA Olympus'
layout: article
---

## TL;DR
增量更新：Andrea Righi 推出 v6，重大转向——弃用 arm64 MIDR 硬编码与 arch_asym_cpu_priority() 覆盖（回应 Will Deacon），改为通用 `sched_smt_asym_packing={auto,on,off}` boot 选项 + 默认 -cpu 优先级排序，并去掉 SMT 专属 static key 改用 sched_smt_active()（回应 Vincent Guittot）。OpenBLAS sgemm +3.20%、NVPL +6.73%、方差显著下降。方向从"平台特判"改为"通用可开关"，合入前景改善。

## 背景与问题
背景见 <a class="article-ref" href="/lkm/2026/09/11/sched-20260911-017-sched-enable-preferred-smt-siblings-on-nvidia-olympus.html">sched-20260911-017</a>：NVIDIA Olympus 的 SMT 双 PE 对短暂兄弟激活特别敏感，从双线程模式回落到单线程模式并非即时；普通任务放置可能反复切换活跃 PE，让核心长期停留在双线程模式。此前版本靠 MIDR 平台特判启用 SD_ASYM_PACKING，被维护者要求改为通用接口。

## 技术方案
- patch 1（sched/fair: Honor asymmetric SMT priority in idle selection）：让 fair 的 idle 选择路径在共享容量 SMT 层尊重 SD_ASYM_PACKING——先按既有放置/容量规则选 CPU 与核心，再选核心内最高优先级可用兄弟；同时补全 POWER7 的 SD_ASYM_PACKING 硬线程排序行为。
- patch 2（sched/topology: Add asymmetric SMT packing override）：新增 `sched_smt_asym_packing=` boot 选项（auto/on/off）。on/off 强制 SMT 域 SD_ASYM_PACKING，优先级仍由 arch_asym_cpu_priority() 定义，弱默认按 -cpu 选最低编号逻辑 CPU；auto 保持架构自带拓扑策略（含 powerpc）。居中应用到带 SD_SHARE_CPUCAPACITY 的域，覆盖自定义 SMT 拓扑回调的架构。

## 版本演进与当前进展
- v1–v5：见 <a class="article-ref" href="/lkm/2026/09/11/sched-20260911-017-sched-enable-preferred-smt-siblings-on-nvidia-olympus.html">sched-20260911-017</a> 及早期（v2 Dietmar、v3/v4 Prateek/Srikar、v5 删 olympus_prefer_pe0 状态）演进。
- v6（09-17，`<20260917140707.3807229-1-arighi@nvidia.com>`）：弃 MIDR 特判与优先级覆盖（Will）、加 boot 选项、默认 -cpu 排序、弃 SMT static key 改用 sched_smt_active()（Vincent）。patch 1 带 Srikar + K Prateek 的 Reviewed-by 与 K Prateek 的 Tested-by。

## Maintainer 意见与讨论焦点
- **Will Deacon（v5→v6）**：要求去掉 arm64 MIDR 特判与 arch_asym_cpu_priority() 覆盖，避免厂商私有约定侵入内核——v6 已落实为通用 boot 选项。
- **Vincent Guittot（v5→v6）**：建议用 sched_smt_active() 替代 SMT 专属 asymmetric-packing static key——v6 已落实。
- **Srikar Dronamraju / K Prateek Nayak**：给出 patch 1 的 Reviewed-by / Tested-by。
- 无 NAK；方向获多位维护者认可。

## 合入评估
*likelihood=medium*。v6 把争议最大的 MIDR 特判改为通用、可显式开关的 boot 选项，回应了核心反对意见，前景较 v5（low）明显改善；但新 boot 选项的命名/语义仍待 sched 维护者（Peter/Ingo）最终评审，且尚无 v6 当日回帖。*blocking_issues*：boot 选项语义待维护者评审；v6 当日无回帖。*next_action*：等待 sched 维护者对 v6 的评审。

## 效果评估
双节点 Vera（NUMA node 0 的 88 物理核，88-thread sgemm，允许选任一兄弟，各 5 次运行）：OpenBLAS sgemm 7.11876→7.34669 TFLOP/s（+3.20%）；NVPL 9.64742→10.29695 TFLOP/s（+6.73%）；标准差显著下降（结果更可预测）。

## 我可以参与的点
- kind=testing：在其它 SMT2/SMT4 平台（尤其 powerpc）验证 sched_smt_asym_packing=on 的默认 -cpu 排序语义与回归。
- kind=review：评估 boot 选项命名与 auto/on/off 语义是否清晰、与现有 SD_ASYM_PACKING 路径是否冲突。

## 参考链接
- lore（v6 cover）: https://lore.kernel.org/all/20260917140707.3807229-1-arighi@nvidia.com/
- v5 参考: https://lore.kernel.org/r/20260909062649.469633-1-arighi@nvidia.com/
