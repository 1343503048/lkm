# sched/isolation: Enable cpuset_mutex/cpus_read_lock synchronization before freeing old housekeeping cpumask

## TL;DR

Waiman Long 的 v2 补丁（与 Ridong Chen 的 sched-20261118-014 是同一 housekeeping/cpuset 竞态的两个竞争方案）：在释放旧 housekeeping cpumask 之前先做 `cpuset_mutex`/`cpus_read_lock` 同步，保证旧指针被使用时不会被释放。今日 Waiman 回帖解释设计取舍——housekeeping cpumask 的访问要么拿到旧指针、要么拿到新指针、不会拿到「半更新」的错乱版本，所以锁保护本质是「防止旧指针内容使用中被释放」；并说明选「先同步再释放」而非「扩展到大段代码」是因其更局部化。

## 背景与问题

housekeeping cpumask（`isolcpus` 隔离出的 CPU 集）在 hotplug/cpuset 变更时会切换到新 cpumask。切换后旧 cpumask 一旦被释放，仍在持旧指针的读者会 use-after-free。Waiman 的方案是在释放旧 cpumask 前先取得 `cpuset_mutex`/`cpus_read_lock` 同步，确保读者完成访问后再释放；Ridong 的方案（sched-20261118-014）则是把新 cpumask 的发布纳入 `cpuset_mutex`。

## 技术方案

v2 在释放旧 housekeeping cpumask 前做 `cpuset_mutex`/`cpus_read_lock` 同步。Waiman 解释：

- 访问语义是「要么旧指针、要么新指针」，不会出现半更新版本，因此锁的关键不是防止读到乱版本、而是「旧指针使用期间不得被 free」。
- 选择「先同步再释放」而非把保护扩散到大段代码，是因为这样更局部化（localized），改动面小。

## 版本演进与当前进展

*current_version: v2（2026-11-17 发出，`<20261117051853.2429410-1-longman@redhat.com>`）*。今日为 Waiman 对方案取舍的补充说明，无新版本。

## Maintainer 意见与讨论焦点

- **Waiman Long（cpuset 维护者，作者）**：解释访问语义（旧/新指针二选一）与「先同步再释放」的局部化取舍。
- 与 Ridong 方案（sched-20261118-014）并存，Waiman 在那边已表态「让其他人决定要哪一个」。
- 无 NAK；两方案择一未定。

## 合入评估

*likelihood=medium*。作者即 cpuset 维护者、方案合理，但与 Ridong 方案竞争，需上层维护者择一。*blocking_issues*：与 014 的竞争方案择一未定。*next_action*：Peter/Thomas 等就 014 与 015 两方案择一。

## 效果评估

无数据；属 housekeeping/cpuset 并发正确性修复。

## 我可以参与的点

- **review**：评估「先同步再释放」与「发布纳入 cpuset_mutex」两方案在 housekeeping 读者路径上的等价性与内存序完备性，帮助择一。

## 参考链接

- lore thread（v2）: https://lore.kernel.org/all/20261117051853.2429410-1-longman@redhat.com/
- Waiman 今日说明: https://lore.kernel.org/all/090384c2-c15f-4357-a7dd-4330972c8c51@redhat.com/

---
id: sched-20261118-015
date: '2026-11-18'
subject: "sched/isolation: Enable cpuset_mutex/cpus_read_lock synchronization before freeing old housekeeping cpumask"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261117051853.2429410-1-longman@redhat.com>"
lore_url: "https://lore.kernel.org/all/20261117051853.2429410-1-longman@redhat.com/"
authors: [Waiman Long]
maintainers_involved: [Waiman Long]
current_version: v2
patch_series:
  - version: v2
    msgid: "<20261117051853.2429410-1-longman@redhat.com>"
    date: '2026-11-17'
    summary: "释放旧 housekeeping cpumask 前先做 cpuset_mutex/cpus_read_lock 同步"
    review_outcome: "与 014 竞争方案并存，待择一"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["与 014 的竞争方案择一未定"]
  next_action: "上层维护者就 014 与 015 择一"
contribution_opportunities:
  - kind: review
    description: "评估两方案等价性与内存序完备性，帮助择一"
generated_at: "2026-11-19T09:00:00+08:00"
source_email_count: 1
related_articles: []
tags: [nohz, cgroup]
---
