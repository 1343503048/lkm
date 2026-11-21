# sched/fair: Cut per-group work from sched domain rebuilds

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261112-003：Qiliang Yuan 的 v1 针对「sched domain 重建时 `rq_offline_fair()`/`rq_online_fair()` 对每个 CPU 遍历全部 task group」的 O(nr_cpus × nr_task_groups) 开销做优化；Dietmar Eggemann 在 f60a631ab9ed 评审时就点出 offline 侧问题；痛点场景是 AI agent harness 主机上千个 cpu cgroup、VM 运行中 hot-add vCPU。
- sched-20261119-004（v2）：给 `rq_online()/rq_offline()` 回调加 `hotplug` 布尔参告知 CPU 是否真改变状态，据此跳过 fair 侧全量 walk；Li kunyu 质疑该参数在 fair 实现里看似未被使用。
- sched-20261121-010（今天）：**v3 换方案**——不再加 `hotplug` 参数，而是给 root domain 迁移专门的 `sched_class` 回调 `rq_attach_root()/rq_detach_root()`（仅 rt/dl 实现，patch 1），让保持 active 的 CPU 在线、只迁移 root domain 状态（patch 2），并删掉由此死掉的 fair 侧 active-CPU 检查（patch 3）。实测 partition root -93%、cpu offline -68%、cpu online -64%，且 `rq_attach_root()` 单次耗时（关中断）中位/上限均大幅下降。

## 背景与问题

（承接 sched-20261112-003 … 20261119-004）sched domain 重建（CPU hotplug 或 cpuset 分区变更）通过 `rq_attach_root()` 把每个 active CPU 移到新 root domain，每颗 CPU 都要在持有 rq lock、关中断下跑 `rq_offline_fair()` + `rq_online_fair()` 遍历所有 task group，开销 O(nr_cpus × nr_task_groups)。承载上千 cpu cgroup、运行中 hot-add vCPU 的 AI 主机上，重建路径放大为可观测卡顿。v2 的 `hotplug` 参数方案被评「声明了却看似没用」，v3 改为更贴合语义的专用回调。

## 技术方案

v3（3 补丁）：
- **patch 1**：给 `struct sched_class` 新增 `rq_attach_root()/rq_detach_root()` 回调，用于 root domain 状态迁移；把 rt（overload mask、cpupri、cpudl、RT runtime）与 dl 转换到这两个回调，`set_rq_online()/set_rq_offline()` 逐类同时调用两套回调，保持调用点与顺序不变。fair 完全不管这些（其 task group 状态不依赖 root domain）。
- **patch 2**：重建时让保持 active 的 CPU 一直 online，只用 `rq_attach_root()/rq_detach_root()` 迁移其 root domain 状态；真正上线由 `sched_cpu_activate()`、下线由 `sched_cpu_deactivate()` 完成。
- **patch 3**：删掉 `unthrottle_offline_cfs_rqs()` 里的 active-CPU 提前返回检查——重建不再把 active CPU 拉下线，该检查恒为假（承 commit af98d8a36a96）。

## 版本演进与当前进展

*current_version: v3（2026-11-21，`<20261120-bug-sched-fair-offline-active-v3-0-325e9eefa56d@linux.dev>`，3 补丁）*。v2 → v3：放弃 `hotplug` 布尔参数方案，改用专用 `rq_attach_root()/rq_detach_root()` 回调，直接回应 Li kunyu「参数看似未用」的质疑。

## Maintainer 意见与讨论焦点

- **Li kunyu**（前情，对 v2）：质疑 `hotplug` 参数在 fair 回调里看似未被消费。v3 通过移除该参数并以专用回调替代解决。
- **Dietmar Eggemann**（历史线索）：f60a631ab9ed 评审点出 offline 侧问题，本系列承接其建议；patch 1 的 `Suggested-by` 为 K Prateek Nayak。
- 当日无新 review；调度维护者（Peter/Ingo）尚未就 v3 表态。无 NAK。

## 合入评估

*likelihood=medium*。v3 结构更贴合语义、量化收益扎实，但属核心 hotplug/topology 路径改动，仍需调度维护者评审与大规模复现背书。*blocking_issues*：无调度维护者 review；rt/dl 专用回调与 hotplug 常规路径的交互需确认。*next_action*：等维护者（Peter/Dietmar）评审 v3，必要时补第三方大规模复测。

## 效果评估

作者实测（4000 cpu cgroup / 32 CPU VM / rt_group_sched=0，20 次分区切换 + 16 次 hotplug 中位数，同轮对比）：
- partition root：15.97 → 1.19 ms（-93%）
- cpu offline：49.66 → 15.74 ms（-68%）
- cpu online：37.39 → 13.33 ms（-64%）
- `rq_attach_root()` 单次（关中断）：中位 229 us、p90 265、max 1335（baseline），改后有大幅下降。

为作者自测，未见第三方独立复现。

## 我可以参与的点

- **review**：核对 rt/dl 改用 `rq_attach_root()/rq_detach_root()` 后与原有 `rq_online/offline` 的调用顺序、状态一致性在 cpuset 分区重建 + hotplug 交织下是否安全。
- **testing**：在大规模 cgroup（>1000）+ 频繁 hot-add vCPU 的 VM 上复测 v3 重建耗时与功能回归。

## 参考链接

- lore thread（v3 cover）: https://lore.kernel.org/all/20261120-bug-sched-fair-offline-active-v3-0-325e9eefa56d@linux.dev/
- v2 cover: https://lore.kernel.org/all/20261118-bug-sched-fair-offline-active-v2-0-b6ede596c6a6@linux.dev/

---
id: sched-20261121-010
date: '2026-11-21'
subject: "sched/fair: Cut per-group work from sched domain rebuilds"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261120-bug-sched-fair-offline-active-v3-0-325e9eefa56d@linux.dev>"
lore_url: "https://lore.kernel.org/all/20261120-bug-sched-fair-offline-active-v3-0-325e9eefa56d@linux.dev/"
authors: [Qiliang Yuan]
maintainers_involved: []
current_version: v3
patch_series:
  - version: v2
    msgid: "<20261118-bug-sched-fair-offline-active-v2-0-b6ede596c6a6@linux.dev>"
    date: '2026-11-18'
    summary: "给 rq_online/offline 回调加 hotplug 布尔参，状态未变时跳过 fair 全量 walk"
    review_outcome: "Li kunyu 质疑 hotplug 参数看似未用"
  - version: v3
    msgid: "<20261120-bug-sched-fair-offline-active-v3-0-325e9eefa56d@linux.dev>"
    date: '2026-11-21'
    summary: "改专用 rq_attach_root()/rq_detach_root() 回调（rt/dl），保持 active CPU 在线，删死代码"
    review_outcome: "暂无新 review"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["无调度维护者 review", "rt/dl 专用回调与 hotplug 常规路径交互待确认"]
  next_action: "等 Peter/Dietmar 评审 v3，必要时补第三方大规模复测"
contribution_opportunities:
  - kind: review
    description: "核对 rt/dl 专用回调在 cpuset 分区重建 + hotplug 交织下的一致性"
  - kind: testing
    description: "大 cgroup 数 + 频繁 hot-add vCPU 的 VM 复测 v3 重建耗时与功能回归"
generated_at: "2026-11-22T01:00:00+08:00"
source_email_count: 91
related_articles: [sched-20261112-003, sched-20261119-004]
tags: [cfs, topology, perf]
---