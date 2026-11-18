---
id: sched-20261118-014
date: '2026-11-18'
subject: 'sched/isolation: Publish new HK_TYPE_DOMAIN cpumask under cpuset_mutex'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261117083915.2971979-1-ridong.chen@linux.dev>
lore_url: https://lore.kernel.org/all/20261117083915.2971979-1-ridong.chen@linux.dev/
authors:
- Ridong Chen
maintainers_involved:
- Tejun Heo
- Waiman Long
- Frederic Weisbecker
current_version: v1
patch_series:
- version: v1
  msgid: <20261117083915.2971979-1-ridong.chen@linux.dev>
  date: '2026-11-17'
  summary: 新 HK_TYPE_DOMAIN cpumask 改在 cpuset_mutex 下发布
  review_outcome: Tejun/Waiman Acked，Frederic 追问根源
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 两竞争方案择一未定
  - Frederic 追问锁谜题根源
  next_action: 维护者择一方案，作者回应 Frederic 根源追问
contribution_opportunities:
- kind: review
  description: 对比两方案正确性/复杂度，帮助择一
- kind: discussion
  description: 分析 cpuset_handle_hotplug 改隔离分区的根源
generated_at: '2026-11-19T09:00:00+08:00'
source_email_count: 4
related_articles: []
tags:
- nohz
- cgroup
title: 'sched/isolation: Publish new HK_TYPE_DOMAIN cpumask under cpuset_mutex'
layout: article
---

## TL;DR

Ridong Chen 发补丁修复 housekeeping（isolcpus=domain）与 cpuset 之间的 cpumask 发布竞态：新的 `HK_TYPE_DOMAIN` cpumask 改在 `cpuset_mutex` 保护下发布，避免与 cpuset 的 sched domain 重建/hotplug 交错时读到不一致的 housekeeping 视图。Tejun Heo 与 Waiman Long 均给 Acked-by（Waiman 同时指出还有他的另一条「先 cpuset_mutex/cpus_read_lock 同步再释放旧 cpumask」的替代方案，交由他人决定取舍）；Frederic Weisbecker 追问「为何 cpuset_handle_hotplug 会改隔离分区」这一锁谜题的根源。

## 背景与问题

`HK_TYPE_DOMAIN`（housekeeping domain，即 `isolcpus=domain` 隔离出的 CPU 集）的 cpumask 需要与 cpuset 的 sched domain 管理同步。此前新 cpumask 的发布时机与 cpuset 的锁不一致，读者可能拿到「旧指针内容被释放/半更新」的视图。作者方案是把新 `HK_TYPE_DOMAIN` cpumask 的发布纳入 `cpuset_mutex` 保护。

## 技术方案

作者补丁（2026-11-17 发出，`<20261117083915.2971979-1-ridong.chen@linux.dev>`）：把新 `HK_TYPE_DOMAIN` cpumask 的发布/切换放在 `cpuset_mutex` 下进行。同日存在 Waiman Long 的替代方案（见 <a class="article-ref" href="/lkm/2026/11/18/sched-20261118-015-sched-isolation-enable-cpuset-mutex-cpus-read-lock-sync.html">sched-20261118-015</a>「先 `cpuset_mutex`/`cpus_read_lock` 同步再释放旧 housekeeping cpumask」），两者解决同一问题的不同切法。

## 版本演进与当前进展

*current_version: v1（2026-11-17 发出，`<20261117083915.2971979-1-ridong.chen@linux.dev>`）*。今日：Tejun 与 Waiman 给 Acked-by，Frederic 追问锁谜题根源。

## Maintainer 意见与讨论焦点

- **Tejun Heo（cpuset/sched_ext 维护者）**：`Acked-by`。
- **Waiman Long（cpuset 维护者）**：`Acked-by`（「Yes, that should work too」），但指出他另有「先同步再释放旧 cpumask」的替代方案，「让其他人决定要哪一个」。
- **Frederic Weisbecker（nohz/隔离 维护者）**：追问这套锁谜题的根源——「cpuset_handle_hotplug() 为何会改隔离分区？cpuset.cpus 本不该关心 offline CPU」；回忆 Waiman 曾说长期可以修，但细节不记得了。
- 无 NAK；两个竞争方案并存，等待维护者择一。

## 合入评估

*likelihood=medium*。已获 Tejun + Waiman 双 Acked-by，但存在 Waiman 的竞争方案未定夺，且 Frederic 对锁谜题根源的追问暗示可能需要更根本的修法。*blocking_issues*：① Ridong 与 Waiman 两方案择一未定；② Frederic 追问 cpuset_handle_hotplug 改隔离分区的根源。*next_action*：维护者就两方案择一，作者回应 Frederic 的根源追问。

## 效果评估

无数据；属 housekeeping/cpuset 并发正确性修复，未给复现。

## 我可以参与的点

- **review**：对比 Ridong「cpuset_mutex 下发布新 cpumask」与 Waiman「先同步再释放旧 cpumask」两方案的正确性/复杂度，帮助维护者择一。
- **discussion**：就 Frederic 提出的「cpuset_handle_hotplug 为何改隔离分区」这一根源问题提供分析。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261117083915.2971979-1-ridong.chen@linux.dev/
- Tejun 的 Ack: https://lore.kernel.org/all/1475d2102374ff6ed54c888d65edd640@kernel.org/
- Waiman 的 Ack: https://lore.kernel.org/all/36d49371-31de-4305-89c4-2ce64dd6848c@redhat.com/
- Frederic 的追问: https://lore.kernel.org/all/av20QrLUdOC_ysS0@localhost.localdomain/
