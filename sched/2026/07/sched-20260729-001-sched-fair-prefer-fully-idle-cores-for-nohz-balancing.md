---
id: sched-20260729-001
date: 2026-07-29
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260728214442.1648483-1-arighi@nvidia.com>"
lore_url: "https://lore.kernel.org/r/20260728214442.1648483-1-arighi@nvidia.com"
authors: [Andrea Righi]
maintainers_involved: [K Prateek Nayak, Shrikanth Hegde, Peter Zijlstra]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260728214442.1648483-1-arighi@nvidia.com>"
    date: 2026-07-29
    summary: "find_new_ilb() 优先选择整个 SMT core 都空闲的 housekeeping CPU 执行 NOHZ idle load balance，找不到时回退到第一个空闲 CPU。"
    review_outcome: "方向获认可；Prateek 提出用 select_rq_mask + cpumask_andnot 剪枝优化大 SMT 系统的扫描开销，作者拟纳入 v2。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - "v2 需吸收 Prateek 的 select_rq_mask 剪枝优化并复测无回退"
  next_action: "作者发 v2：合入剪枝优化 + lockdep_assert_irqs_disabled()，等待 Shrikanth 在 SMT-4/8 平台的测试结果"
contribution_opportunities:
  - kind: testing
    description: "在 SMT-4/SMT-8（如 Power）或其他 SMT 平台上测试 v1/v2，验证 ILB 选核变化没有引入延迟/能耗回退，把数据回帖"
  - kind: new_patch
    description: "PeterZ 认可的独立清理方向：为 select_rq_mask 提供带 lockdep 断言的访问 helper（或用 clang context analysis），可以单独发 patch"
generated_at: "2026-07-30T09:30:00"
source_email_count: 7
related_articles: []
tags: [load_balance, nohz, hyperthreading, perf]
---

## TL;DR

NVIDIA 的 Andrea Righi 让 NOHZ idle load balancer 优先挑"整个物理核都空闲"的 CPU 来执行，避免 ILB 短暂唤醒 SMT 兄弟线程拖累另一个兄弟的单线程性能；GEMM 实测 6.2 → 9.4 TFLOP/s。当天讨论热烈（7 封），Peter Zijlstra 已介入，review 走向正面，值得关注 v2。

## 背景与问题

`find_new_ilb()` 目前选第一个空闲的 housekeeping CPU 执行 idle load balance，不考虑该 CPU 的 SMT 兄弟是否在忙。大多数 SMT 系统上 ILB 是短活动，影响可忽略；但在 NVIDIA Vera 平台的 Olympus 核上代价很大：

> "after the ILB finishes and its CPU enters WFI, full single-thread performance is restored only after the sibling has remained idle for a qualification interval (10 Ki cycles on the tested Vera system). Repeated short sibling wakeups can therefore sustain the interference even with little actual overlap."

即 ILB 唤醒兄弟线程后，即使很快又空闲，另一个兄弟也要等约 10Ki cycle 的"资格期"才能恢复全速，反复的短唤醒会持续压制单线程性能。

## 技术方案

在 `find_new_ilb()` 中优先返回 `is_core_idle()` 为真的空闲 housekeeping CPU；没有完全空闲的核时回退到第一个空闲 CPU，保证 NOHZ balance 不停摆。非 SMT 系统行为不变。作者也如实说明取舍：这可能唤醒一个完全空闲的物理核而不是复用活跃核的空闲兄弟，在某些架构上可能增加 ILB 唤醒延迟或能耗。

## 版本演进与当前进展

当前 v1。K Prateek Nayak 指出 `is_core_idle()` 会遍历所有兄弟线程，在 SMT-4/SMT-8 上开销可见（参考 f8858d96061f 对 `should_we_balance()` 的同类优化），给出了用 `select_rq_mask` + `cpumask_andnot()` 剪枝已确认非全空闲核的改进 diff。作者确认将复测后并入 v2，并计划加 `lockdep_assert_irqs_disabled()`。

## Maintainer 意见与讨论焦点

- **Prateek（AMD）**：方向认可，核心意见是扫描开销优化；确认 tick handler 上下文复用 `select_rq_mask` 是安全的（仅在关中断上下文使用）。
- **Shrikanth Hegde（IBM）**：表示会实测该补丁（Power 平台 SMT-4/8 开销的主要见证者）。
- **Peter Zijlstra**：对 `select_rq_mask` 改名/accessor 的历史议题表态"分开做就行"，还提了可以用新的 clang context analysis——即该清理不阻塞本补丁。
- 无人反对方案本身，无 NAK。

## 合入评估

likelihood: high。方案动机清晰、有硬数据、review 意见集中在实现细节而非方向，PeterZ 已参与且无阻塞性异议。卡点只剩 v2 吸收剪枝优化并证明无回退。

## 效果评估

作者给出 ad hoc GEMM 基准（每 SMT core 绑一个 CPU 密集任务）：约 6.2 TFLOP/s → 9.4 TFLOP/s（+52%）。作者在纳入 Prateek 的优化后自测"results are looking good so far"（暂无具体数字）。

## 我可以参与的点

- 在手头 SMT 平台（尤其 x86 SMT-2 与非 Vera ARM 平台）跑 GEMM/调度延迟类负载对比 v1，验证"优先全空闲核"在普通平台上没有能耗/延迟回退，回帖数据。
- `select_rq_mask` 的 lockdep-guarded accessor 是 PeterZ 认可的独立清理，规模小、边界清晰，适合作为参与调度社区的切入 patch。

## 参考链接

- lore thread: https://lore.kernel.org/r/20260728214442.1648483-1-arighi@nvidia.com
- 参考的历史优化：f8858d96061f ("sched/fair: Optimize should_we_balance() for large SMT systems")
- select_rq_mask 改名历史讨论: https://lore.kernel.org/lkml/20260320114312.GB3558198@noisy.programming.kicks-ass.net/
