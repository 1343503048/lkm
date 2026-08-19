# sched/fair: Allow load balancing between CPUs of identical capacity

# sched/fair: NOHZ 均衡优先选 fully idle core

## TL;DR
NOHZ 负载均衡选 ilb（idle load balancer）CPU 时优先选「整核全 idle」的 CPU，避免把已运行兄弟线程的 SMT 核心当 ilb 损失吞吐。作者实测无调频噪声下 6.2→9.4 TFLOP/s，但加 ibs 噪声后提升消失。v3 已获 Vincent R-b，合入可能性高。

## 背景与问题
NOHZ 下只有一个 idle CPU 被选中做 idle load balancing（ilb）。当前选 ilb 的逻辑可能选中一个 SMT 核心中「仅一个兄弟线程 idle、另一兄弟正忙」的 CPU，导致 ilb 在该核心上与其他线程共享资源，降低 balancer 自身吞吐，进而影响整体均衡质量。在 SMT 开启的机器上尤为明显。

## 技术方案
在挑选 ilb CPU 时，优先选择 fully idle 的 core（core 内所有 SMT 兄弟姐妹都 idle）。若找不到 fully idle core，再退回到常规 idle 选择。核心改动在 `nohz_balancer_kick()` / ilb 候选扫描处加 fully-idle 偏好。

## 版本演进与当前进展
当前 v4（2026-08-04）。v3 已获 Vincent Guittot Reviewed-by。作者在 08-04 回帖补充实测数据。

## Maintainer 意见与讨论焦点
Vincent Guittot：v3 已 R-b，认可方向。讨论焦点转向实测稳健性——作者给出的 benchmark 在「无 ibs 调频噪声」时提升显著（6.2→9.4 TFLOP/s），但加了 ibs 噪声后提升消失，说明收益对环境敏感。

## 合入评估
合入可能性 high（v3 R-b）。需确认带调频噪声的真实负载下收益稳定，无架构反对。

## 效果评估
邮件提供量化 benchmark（MIR fluence RT + native：6.2→9.4 TFLOP/s），属「有实证」的优化。但作者自己指出在加 ibs 调频噪声后提升消失，是效果稳健性的关键 caveats。

## 我可以参与的点
- 在更多 SMT 机型上以 MIR-style 负载复测 fully-idle-core ilb 的吞吐，并验证带调频噪声场景，回帖对比数据（作者已提示噪声敏感性，正需更广验证）。

## 参考链接
- lore thread: 未获取到

---
subject: "sched/fair: Allow load balancing between CPUs of identical capacity"
id: sched-20260804-005
date: 2026-08-04
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<unknown>"
lore_url: "unknown"
authors: [Pratyush Kumar]
maintainers_involved: [Vincent Guittot, Peter Zijlstra, Ingo Molnar]
current_version: v4
patch_series:
  - version: v4
    msgid: "<unknown>"
    date: 2026-08-04
    summary: "NOHZ 负载均衡在选 ilb（idle load balancer）CPU 时优先选 fully idle（core 内所有 SMT 兄弟均 idle）的 CPU，而非任意 idle CPU，避免把一个已运行兄弟线程的 SMT 核心当作 ilb，损失吞吐。"
    review_outcome: "Pratyush 回帖实测：MIR fluence RT + native 下 6.2 → 9.4 TFLOP/s；但加了 ibs 调频 noise 后提升消失。Vincent Guittot 此前 v3 已给 Reviewed-by。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["需确认在带调频噪声的真实负载下提升是否稳定；benchmark 仅在『无 ibs 噪声』时显著"]
  next_action: "等待 maintainer 对『fully idle core 选择 + 实测数据』的最终认可；v3 已 R-b。"
contribution_opportunities:
  - kind: testing
    description: "可在更多机型（尤其 SMT 开启的 Intel/AMD）上以 MIR-style 负载复测 fully-idle-core ilb 选择的吞吐提升，并验证带调频噪声场景是否仍为正收益，回帖数据补强。"
generated_at: "2026-08-05T00:25:00"
source_email_count: 1
related_articles: []
tags: [cfs, load_balance, nohz, topology, hyperthreading]
---
