# sched: Expose writable interface for preferred CPUs mask

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261102-004：Yury Norov 发 6-patch 系列提供 preferred CPUs 运行时可写 sysfs 接口；Peter Zijlstra 对整个手动接口方向 NAK，仅认可 patch 1（PREFERRED_CPU 与 PARAVIRT 解耦）。
- sched-20261105-005 / 20261107-009：hotplug 回退语义与 preferred cpumask 定位的讨论，Yury 给 vCPU 超卖用例，NAK 未变。
- sched-20261110-017：Shrikanth Hegde 从「offline 可替代」角度质疑用例，进一步削弱接口必要性。
- sched-20261112-013（今天）：**Yury 决定把系列拆成 cleanup 与 follow-up 两部分**，writable 接口进 follow-up；Shrikanth 与 Mete Durlu 就「把工作负载 pin 到非 preferred CPU」的 benchmarking 用途展开讨论；**Peter 重申「这正是 cpusets 的用途，它就是为此设计的」**。方向性 NAK 维持。

## 背景与问题

（承接 sched-20261102-004 / 20261105-005 / 20261107-009 / 20261110-017）preferred CPU mask 原本只供 steal governor 在 vCPU 抢占时动态缩减 vCPU 需求；Yury 希望增加运行时手动控制接口。Peter 以「cpusets 已能干这件事」NAK 了 writable 方向。今日讨论从「功能重叠」延伸到「pin 到非 preferred CPU 做 benchmarking」这个新用例。

## 技术方案

（承接 6 补丁系列）今日无代码变更，为路线决策与用例澄清：

- **Yury Norov（作者）**：决定拆分系列——cleanup 部分先行，writable 接口进 follow-up，并在 follow-up 里聚焦这个接口，保留相关反馈者（Maxim）在 Cc。
- **Shrikanth Hegde（IBM）**：追问「pin 到非 preferred CPU 做 benchmarking」的具体语义——为何有人想只跑在非 preferred CPU 上（按定义它们应尽量少用），以及「设 preferred → 起负载 → 收尾恢复 active」两个序列里 offline 是否能替代。
- **Mete Durlu（IBM）**：为用例正名——用户想「把非 preferred 标记 + 把负载 pin 到那里」来阻止其它东西跑在这些 CPU 上，类似动态可配置的隔离 CPU，与 Yury 描述的场景 1-1 吻合。

## 版本演进与当前进展

*current_version: v1*。今日无新版本；作者宣布将拆分为 cleanup + follow-up（writable 接口），是方向上的让步而非推进。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**：重申方向性否定——「这正是我们有 cpusets 的原因，它做可配置隔离 CPU 完全没问题，事实上它就是为此设计的」。
- **Yury Norov（作者）**：接受拆分，writable 接口退居 follow-up（cleanup 先行），承认「pin 到非 preferred CPU」的 benchmarking 用例「有前景，也许更多」。
- **Shrikanth Hegde / Mete Durlu（IBM）**：就 benchmarking 用例的可行性与 offline 的可替代性展开正反讨论。
- 方向性 NAK 未变；分歧集中在「writable 接口是否有 cpusets/offline 无法覆盖的独有价值」。

## 合入评估

*likelihood=rejected*（writable 接口方向）。Peter 的 NAK 与「cpusets 即可」的判断未变；作者已退让为拆分系列、接口进 follow-up，进一步确认该方向短期无法合入。*blocking_issues*：Peter 的 NAK 是根本障碍；benchmarking 用例仍被 Shrikanth 质疑 offline 可替代。*next_action*：聚焦 PREFERRED_CPU 与 PARAVIRT 解耦（被认可的 patch 1）及 cleanup 部分；writable 接口需找到 cpusets/offline 均无法覆盖的硬用例才有复活可能。

## 效果评估

无性能数据。今日为用例与路线讨论，无 benchmark。

## 我可以参与的点

- **discussion**：为「运行时手动 preferred 接口」提供 cpusets 与 offline 均无法覆盖的真实场景（例如不停机在线调整、且不愿承担 offline/online 开销），这是当前唯一可能松动 NAK 的输入，但投入产出低。

## 参考链接

- Peter 的「cpusets 即可」: https://lore.kernel.org/all/20261112100043.GR2668200@noisy.programming.kicks-ass.net/
- Yury 的拆分决定: https://lore.kernel.org/all/avTSC2r61uht9oFK@yury/
- Mete 对 benchmarking 用例的解释: https://lore.kernel.org/all/91823f62-57fe-44ad-9dab-ba91ba3d26d3@linux.ibm.com/

---
id: sched-20261112-013
date: '2026-11-12'
subject: "sched: Expose writable interface for preferred CPUs mask"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261112100043.GR2668200@noisy.programming.kicks-ass.net>"
lore_url: "https://lore.kernel.org/all/20261112100043.GR2668200@noisy.programming.kicks-ass.net/"
authors: [Yury Norov]
maintainers_involved: [Peter Zijlstra]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261101192203.6979-1-ynorov@nvidia.com>"
    date: '2026-11-01'
    summary: "6 补丁提供 preferred CPUs 运行时可写 sysfs 接口"
    review_outcome: "Peter 重申 NAK；作者决定拆分为 cleanup + follow-up"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: rejected
  blocking_issues: ["Peter 对 writable 接口的 NAK 是根本障碍", "benchmarking 用例仍被质疑 offline 可替代"]
  next_action: "聚焦 PREFERRED_CPU 解耦 PARAVIRT 及 cleanup 部分；接口需硬用例"
contribution_opportunities:
  - kind: discussion
    description: "提供 cpusets 与 offline 均无法覆盖的运行时手动 preferred 场景"
generated_at: "2026-11-13T09:00:00+08:00"
source_email_count: 5
related_articles: [sched-20261102-004, sched-20261105-005, sched-20261107-009, sched-20261110-017]
tags: [affinity, cgroup, topology]
---