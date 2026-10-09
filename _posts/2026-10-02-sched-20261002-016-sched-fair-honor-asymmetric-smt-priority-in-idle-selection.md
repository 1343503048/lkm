---
id: sched-20261002-016
date: '2026-10-02'
subject: 'sched/fair: Honor asymmetric SMT priority in idle selection'
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: <20260929165538.726616-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260929165538.726616-2-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Peter Zijlstra
- Vincent Guittot
- Srikar Dronamraju
- K Prateek Nayak
current_version: v7
patch_series:
- version: v6
  msgid: <20260917140707.3807229-1-arighi@nvidia.com>
  date: '2026-09-17'
  summary: sched_smt_asym_packing={auto,on,off} boot 选项 + idle 选择 honor SD_ASYM_PACKING
  review_outcome: Breno Tested-by；Dietmar 追问吞吐/负载模型；Andrea 逐条澄清
- version: v7
  msgid: <20260929165538.726616-1-arighi@nvidia.com>
  date: '2026-09-30'
  summary: boot 选项收紧为仅 =on；补 OpenBLAS +3.20% / NVPL +6.73% 吞吐数据
  review_outcome: 1/2 集齐 Srikar/Prateek/Vincent/Kayra Reviewed-by；10-01 合入 tip/sched/core
upstream_commit: c8fc4136fd3c58458592b77168f0916d08dbea5a
fixes_commit: null
merged_branch: tip/sched/core
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 随 tip 树进下个合并窗口；关注与 2/2 topology override 的联动
contribution_opportunities:
- kind: testing
  description: 在 POWER7 等更宽 SMT 平台验证部分忙碌核按优先级填充路径并回帖补数据
generated_at: '2026-10-03T01:00:00'
source_email_count: 1
related_articles:
- sched-20260912-008
- sched-20260918-008
- sched-20260930-014
tags:
- topology
- idle
- hyperthreading
title: 'sched/fair: Honor asymmetric SMT priority in idle selection'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/12/sched-20260912-008-sched-fair-honor-asymmetric-smt-priority-in-idle-selection.html">sched-20260912-008</a>：Andrea Righi 确认 Dietmar Eggemann 的实现意见已就地落实——`select_idle_smt_cpu()` 改为直接取最低调度域（`rcu_dereference_all(cpu_rq(cpu)->sd)`），将随下一版发出。
- <a class="article-ref" href="/lkm/2026/09/18/sched-20260918-008-sched-fair-honor-asymmetric-smt-priority-in-idle-selection.html">sched-20260918-008</a>：系列（重构为 2 补丁）获 Vincent Guittot 与 Kayra Cizmeci 对 1/2 的 Reviewed-by（Kayra 另附 Tested-by）；Shrikanth Hegde 对 2/2 的 kernel 参数设计提出三点疑问。
- <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-014-sched-enable-preferred-smt-siblings-on-nvidia-olympus.html">sched-20260930-014</a>：作者发 v7，boot 选项收紧为仅 `sched_smt_asym_packing=on`，并补上吞吐量化（OpenBLAS +3.20%、NVPL +6.73%），此前「缺吞吐数据」的阻塞点解除；1/2 集齐多位 reviewer 的 Reviewed-by。
- <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-016-sched-fair-honor-asymmetric-smt-priority-in-idle-selection.html">sched-20261002-016</a>（今天）：**v7 系列 1/2 已被 Peter Zijlstra 合入 tip/sched/core**（commit `c8fc4136fd3c58458592b77168f0916d08dbea5a`，CommitterDate 2026-10-01，tip-bot 于 10-02 回帖公告）。合入版本带 Srikar Dronamraju、K Prateek Nayak、Vincent Guittot、Kayra Cizmeci 四个 Reviewed-by 与 Prateek/Kayra/Breno Leitao 三个 Tested-by。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-014-sched-enable-preferred-smt-siblings-on-nvidia-olympus.html">sched-20260930-014</a>）NVIDIA 的 Spatial SMT 会动态把物理核切分为两个「兄弟」逻辑核，传统 `sched_smt_asym_packing` 语义不适用，需要在 idle 选择路径上优先选择低编号（PE0）兄弟，让 PE0 保持全资源单线程模式、PE1 空闲。Olympus 固件当前不提供描述 sibling 偏好的接口，MIDR 推断又会把平台特定策略写进内核，故 v6 起引入 `sched_smt_asym_packing` boot 选项作为显式 fallback。idle 选择不查询该顺序时，任务可能唤醒到任意 sibling 并滞留到负载均衡纠正，阻碍物理核进入首选的低线程资源模式，造成大的持续性性能损失。

POWER7 在共享容量 SMT 域上用 `SD_ASYM_PACKING` 排序硬件线程，同样受益于本修复。

## 技术方案

（承接）1/2 教 fair 的 idle 选择路径在共享容量的 SMT 域上 honor `SD_ASYM_PACKING`：

- 新增 `select_idle_smt_cpu()` helper：在任务亲和约束下，把 CPU 重定向到其 SMT 域内最高优先级的可用 sibling（`sched_asym_prefer()` 比较）；要求两 CPU 共享最低调度域 span，因为 isolcpus 可能把硬件 sibling 拆到不同调度域。
- `select_idle_sibling()` 的所有命中路径（target/prev/recent_used 快路径、`select_idle_capacity()` 非对称容量扫描、`select_idle_smt()`/`select_idle_cpu()` 慢路径）统一改为 `goto select_smt_priority` 收口，再经 `select_idle_smt_cpu()` 做最终 sibling 选择。
- 物理核容量选择与 SMT sibling 排序保持独立：`SD_ASYM_CPUCAPACITY` 先在不同最大容量的核间选，`SD_ASYM_PACKING` 再在选定核内选首选可用 sibling。
- SMT2 Olympus 上仅改变完全 idle 核的选择；更宽 SMT 系统（如 POWER7）在核部分忙碌时也按优先级顺序填充可用 sibling。

## 版本演进与当前进展

- v6（09-17，`<20260917140707.3807229-1-arighi@nvidia.com>`）：`sched_smt_asym_packing={auto,on,off}` boot 选项 + idle 选择 honor `SD_ASYM_PACKING`。
- v7（09-30，`<20260929165538.726616-1-arighi@nvidia.com>`）：boot 选项收紧为仅 `=on`；补 OpenBLAS +3.20% / NVPL +6.73% 吞吐数据。
- 10-01 合入 tip/sched/core（commit `c8fc4136fd3c58458592b77168f0916d08dbea5a`，`kernel/sched/fair.c` +68/−17），10-02 tip-bot 公告。补丁链接 `https://patch.msgid.link/20260929165538.726616-2-arighi@nvidia.com`。

## Maintainer 意见与讨论焦点

- 无 NAK。v7 1/2 集齐 Srikar Dronamraju、K Prateek Nayak、Vincent Guittot、Kayra Cizmeci 四个 `Reviewed-by`（合入 commit 中完整保留）与 Prateek、Kayra、Breno Leitao 三个 `Tested-by`。
- 此前 Vincent Guittot 与 Shrikanth Hegde 对 boot 选项取值的收紧意见已在 v7 采纳（见 2/2 文章 <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-017-sched-topology-add-asymmetric-smt-packing-override.html">sched-20261002-017</a>）。
- Peter Zijlstra 直接收取，未提额外意见。

## 合入评估

*likelihood=merged*。系列已合入 `tip/sched/core`（commit `c8fc4136fd3c58458592b77168f0916d08dbea5a`），将随 tip 树进下个合并窗口。*blocking_issues*：无。*next_action*：关注其与 2/2（topology override）在主线化后的联动，以及后续 stable 回合诉求（feature 类，回合可能性低）。

## 效果评估

v7 cover 数据（承接 <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-014-sched-enable-preferred-smt-siblings-on-nvidia-olympus.html">sched-20260930-014</a>）：两节点 Vera 88 线程单精度 GEMM，OpenBLAS 从 7.11876±0.06734 → 7.34669±0.01936 TFLOP/s（+3.20%）；NVPL 从 9.64742±0.17311 → 10.29695±0.01786 TFLOP/s（+6.73%），标准差下降、负载一致落到低编号 sibling。此前（v6 讨论）另有唤醒重定向 800/800 命中、ST/SMT 切换下降 ~80%。

## 我可以参与的点

- `testing`：在 POWER7 等更宽 SMT 平台验证合入版本行为（补丁声明的部分忙碌核按优先级填充路径在 Olympus SMT2 上不触发），回帖补数据。

## 参考链接

- lore（v7 cover）: https://lore.kernel.org/all/20260929165538.726616-1-arighi@nvidia.com/
- lore（1/2 补丁）: https://lore.kernel.org/all/20260929165538.726616-2-arighi@nvidia.com/
- tip commit: https://git.kernel.org/tip/c8fc4136fd3c58458592b77168f0916d08dbea5a
