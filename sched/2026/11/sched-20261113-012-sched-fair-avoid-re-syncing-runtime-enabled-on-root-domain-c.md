# sched/fair: Avoid re-syncing runtime_enabled on root domain changes

## TL;DR
本文为增量更新，完整脉络见下。

- sched-20261112-003：Qiliang Yuan 发两补丁削掉 sched domain rebuild 里按「CPU 数 × task group 数」膨胀的逐组清理（`rq_offline_fair()`/`rq_online_fair()` 全 group 遍历）；其中 patch 2 即 `Avoid re-syncing runtime_enabled on root domain changes`（用 per-rq flag 跳过 `update_runtime_enabled()` 遍历）。作者给 4000 cgroup/32 核实测，Peter 建议「加 boolean 参数」替代方向。
- sched-20261113-012（今天）：**Peter Zijlstra 自发的同题 2/2 补丁被 K Prateek Nayak 评审**——K Prateek 提出更根本的问题：fair 没有与 rd 关联的记账，为何 active CPU 在 cpuset 触发的 domain rebuild 里还要走 `rq_offline_fair()`+`rq_online_fair()`，建议把 offline/online 与 root domain 切换拆开，并给出 `rq_attach_root_domain()` 的实现方向。

## 背景与问题
（承接 sched-20261112-003）sched domain rebuild 会把每个 active CPU 经 `rq_attach_root()` 移到新 root domain，`rq_offline_fair()`/`rq_online_fair()` 在持锁关中断下遍历全部 task group，成本 O(nr_cpus × nr_task_groups)。此前系列聚焦于「active CPU 是否要重跑这些遍历」；今日 K Prateek 把问题再往前提：fair/ext 类根本不在 root domain 切换时维护任何记账，为何要整套走一遍 offline/online。

## 技术方案
今日为设计讨论（K Prateek 评审 Peter 的 2/2）。K Prateek 提出：把 `set_rq_online()`/`set_rq_offline()` 的「online 位 + `rq_online` 回调」与「root domain 切换」拆成独立回调 `rq_attach_root_domain()`/`rq_detach_root_domain()`（active CPU 只走 attach/detach，不再全 class 走 online/offline；真正上下线的 CPU 仍走 set_rq_online/offline）。好处是 hotplug 不变快，但 cpuset 触发的 domain rebuild 变快。并附「在 tip:sched/core d7e670601af6 上轻测」的示意 diff。

## 版本演进与当前进展
Peter 的 2/2 补丁（2026-11-12）→ 今日 K Prateek 评审提出拆分 offline/online 与 root-domain 切换的更根本方向。无新版本。

## Maintainer 意见与讨论焦点
- **K Prateek Nayak（AMD）**：评审并质疑 active CPU 在 cpuset domain rebuild 里走 offline/online 的必要性，建议拆分回调（轻测示意 diff）。
- **Peter Zijlstra**：当日未回帖（其补丁为被评审方）。
- 无 NAK；分歧点在于「per-rq flag 跳过」（原系列）vs「拆 offline/online 与 rd 切换」（K Prateek 新方向）两条实现路线的取舍。

## 合入评估
设计讨论深化，合入概率中等；待 Peter 回应拆分回调方向是否采纳，以及两路线如何统一。

## 效果评估
无今日新增 benchmark；此前系列有 4000 cgroup/32 核数据（partition 切换 -91%、cpu offline -70%、online -65%，承接 20261112-003）。

## 我可以参与的点
- **review**：评估「拆分 rq_attach_root_domain/rq_detach_root_domain 回调」对 deadline/rt 的 `rq_online`/`rq_offline` 记账（带宽记账、rto_mask）是否仍被正确触发。
- **testing**：在大量 cgroup + cpuset partition 切换场景测量拆分回调后 domain rebuild 的耗时改善。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261112125947.GZ1813469@noisy.programming.kicks-ass.net/
- 前序系列（Qiliang Yuan）: https://lore.kernel.org/all/20261111-bug-sched-fair-offline-active-v1-0-4f54523c5a70@linux.dev/

---
id: sched-20261113-012
subject: "sched/fair: Avoid re-syncing runtime_enabled on root domain changes"
date: 2026-11-13
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261112125947.GZ1813469@noisy.programming.kicks-ass.net>"
lore_url: "https://lore.kernel.org/all/20261112125947.GZ1813469@noisy.programming.kicks-ass.net/"
authors: [Peter Zijlstra]
maintainers_involved: [K Prateek Nayak]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261112125947.GZ1813469@noisy.programming.kicks-ass.net>"
    date: 2026-11-12
    summary: "2/2 避免在 root domain 变更时重同步 runtime_enabled"
    review_outcome: "K Prateek 评审：建议拆分 offline/online 与 root-domain 切换"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "「per-rq flag 跳过」与「拆分 rd 切换回调」两条路线待统一"
  next_action: "等待 Peter 回应 K Prateek 的拆分回调方向"
contribution_opportunities:
  - kind: review
    description: "评估拆分 rq_attach_root_domain/rq_detach_root_domain 对 deadline/rt 记账的影响"
  - kind: testing
    description: "在大量 cgroup + cpuset partition 切换场景测量 rebuild 耗时改善"
generated_at: "2026-11-14T01:30:00"
source_email_count: 1
related_articles: [sched-20261112-003]
tags: [cfs, load_balance, topology, perf]
---