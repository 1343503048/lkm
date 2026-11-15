# sched/fair: Avoid re-syncing runtime_enabled on root domain changes

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261112-003：Qiliang Yuan 两补丁削掉 sched domain rebuild 里按「CPU 数 × task group 数」膨胀的逐组清理；其中 patch 2 即 `sched/fair: Avoid re-syncing runtime_enabled on root domain changes`（用 per-rq flag 跳过 update_runtime_enabled() 遍历）。作者给 4000 cgroup/32 核实测，Peter 建议改「加 boolean 参数」的方向。
- sched-20261113-012：Peter Zijlstra 自发同题 2/2 补丁获 K Prateek Nayak 评审，后者提出更根本方向——把 `set_rq_online/offline` 与 root domain 切换拆成独立回调 `rq_attach_root_domain()`/`rq_detach_root_domain()`。
- sched-20261115-006（今天）：Qiliang Yuan 回复同意「仅 active CPU 换 root domain 时 fair 无需重做」，给出按 Peter 早前建议实现的 v2 及更全 benchmark（partition root -94%、offline -71%、online -65%），并与 Prateek 拆分方案对比，询问 Peter 选哪条路线。

## 背景与问题

sched domain rebuild 会把每个 active CPU 经 `rq_attach_root()` 移到新 root domain，`rq_offline_fair()`/`rq_online_fair()` 在持锁关中断下遍历全部 task group，成本 O(nr_cpus × nr_task_groups)。此前系列聚焦 active CPU 是否要重跑这些遍历；K Prateek 又把问题往前提：fair 没有与 root domain 关联的记账，为何 active CPU 在 cpuset 触发的 rebuild 里还要整套走 offline/online。今日 Qiliang 确认「active CPU 只换 root domain 时 fair 确实无事可做」。

## 技术方案

今日 Qiliang 给出两条路线对比：

- **其 v2**：让 `rq_online()`/`rq_offline()` 接收一个 boolean 表示 CPU 是否真正改变状态，fair 在状态不变时跳过两次遍历；hotplug 也因此变快（每次 hotplug 都 rebuild domains 并移动其它 active CPU）。
- **Prateek 的拆分方案**：把 root domain 切换移出 `rq_online()`/`rq_offline()`，结果相同、读起来更干净。差别在于 CPU 上来时 `rq_online()` 的调用时机：Prateek 方案在 rebuild 后经 `sched_set_rq_online()`，而其 v2/当前实现是在 rebuild 中经 `rq_attach_root()`。

## 版本演进与当前进展

无新版本贴出；Qiliang 描述其 v2 已就绪（未贴出），并与 Prateek 拆分方案做对比，待 Peter 取舍。

## Maintainer 意见与讨论焦点

- **Qiliang Yuan（作者）**：回复征询 Peter 选哪条路线，表示可原样贴 v2 或基于 Prateek patch 重做。
- **Peter Zijlstra**：当日未回帖。
- 无 NAK；分歧仍是两条实现路线（boolean 跳过 vs 拆分 rd 回调）的取舍。

## 合入评估

设计讨论深化，两条路线待 Peter 拍板，合入概率中等。*blocking_issues*：路线未统一，等待 Peter 选择。*next_action*：Peter 选定路线后，作者贴出 v2 或基于 Prateek patch 重做。

## 效果评估

Qiliang v2 新 benchmark（4000 cgroup / 32-CPU VM，切换 4-CPU cpuset 到 partition root + offline/online 各一 CPU，20 次 partition 切换 + 16 次 hotplug 的中位数）：partition root 19.73→1.19ms（-94%）、cpu offline 44.93→12.83ms（-71%）、cpu online 37.03→12.94ms（-65%）。作者称 Prateek 拆分方案应给出相同结果。

## 我可以参与的点

- **review**：评估两条路线对 deadline/rt 的 `rq_online`/`rq_offline` 记账差异（带宽记账、rto_mask），尤其 Prateek 方案里 `rq_online()` 调用时机从 rebuild 内移到 rebuild 后是否有语义影响。
- **testing**：在大量 cgroup + cpuset partition 切换场景实测两条路线的 rebuild 耗时改善。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261115035906.1185642-1-qiliang.yuan@linux.dev/
- 前序（Peter 2/2）: https://lore.kernel.org/all/20261112125947.GZ1813469@noisy.programming.kicks-ass.net/

---
id: sched-20261115-006
date: '2026-11-15'
subject: "sched/fair: Avoid re-syncing runtime_enabled on root domain changes"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261112125947.GZ1813469@noisy.programming.kicks-ass.net>"
lore_url: "https://lore.kernel.org/all/20261115035906.1185642-1-qiliang.yuan@linux.dev/"
authors: [Qiliang Yuan, Peter Zijlstra]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261112125947.GZ1813469@noisy.programming.kicks-ass.net>"
    date: '2026-11-12'
    summary: "Peter 自发 2/2：避免 root domain 变更时重同步 runtime_enabled"
    review_outcome: "K Prateek 评审建议拆分 offline/online 与 rd 切换；Qiliang 给出 v2 boolean 方案对比"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "两条路线（boolean 跳过 vs 拆分 rd 回调）待 Peter 拍板"
  next_action: "Peter 选定路线后，作者贴出 v2 或基于 Prateek patch 重做"
contribution_opportunities:
  - kind: review
    description: "评估两条路线对 deadline/rt 的 rq_online/offline 记账，尤其 rq_online 调用时机变化"
  - kind: testing
    description: "在大量 cgroup + cpuset partition 切换场景实测两条路线耗时"
generated_at: "2026-11-16T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261112-003, sched-20261113-012]
tags: [cfs, load_balance, topology, perf]
---