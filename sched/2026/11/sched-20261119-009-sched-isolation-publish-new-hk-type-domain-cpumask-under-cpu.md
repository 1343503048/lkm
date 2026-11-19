# sched/isolation: Publish new HK_TYPE_DOMAIN cpumask under cpuset_mutex

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261118-014：Ridong Chen 发补丁修复 housekeeping（isolcpus=domain）与 cpuset 之间的 cpumask 发布竞态——把新 `HK_TYPE_DOMAIN` cpumask 的发布纳入 `cpuset_mutex` 保护。Tejun Heo 与 Waiman Long 已 Acked-by；Frederic Weisbecker 追问「为何 `cpuset_handle_hotplug` 会改隔离分区」这一锁谜题的根源。
- sched-20261119-009（今天）：**Waiman Long 正面回答 Frederic 的疑问**——`cpuset_handle_hotplug()` 必须把新 offline 的 CPU 移除、或把新 online 的 CPU 加回到「所有包含该 CPU 的 cpuset」的 `effective_cpus`（无论隔离还是 root 分区）；最坏情况下隔离分区最后一颗在线 CPU 被 offline，必须整体 disable 该分区。这就是 hotplug 会影响隔离分区的根本原因。

## 背景与问题

（承接 sched-20261118-014）`HK_TYPE_DOMAIN`（housekeeping domain，即 `isolcpus=domain` 隔离出的 CPU 集）的 cpumask 发布需与 cpuset 的 sched domain 管理同步，作者把新 cpumask 的发布纳入 `cpuset_mutex` 保护。Frederic Weisbecker 追问的锁谜题是：hotplug 为什么必须触达隔离分区（从而需要与 housekeeping 侧同步）。

## 技术方案

今日为答疑、无新补丁。Waiman 解释锁耦合的必要性：hotplug 对 `effective_cpus` 的维护是**全局**的，隔离分区也在其列——`cpuset_handle_hotplug()` 要同步增删所有受影响 cpuset 的 `effective_cpus`，无法跳过隔离分区；极端情况（隔离分区最后在线 CPU 下线）还需 disable 该分区。因此 housekeeping 的 `HK_TYPE_DOMAIN` 发布确实与 cpuset 的 hotplug 路径相互交织，`cpuset_mutex` 是必要的共享保护。

## 版本演进与当前进展

*current_version: v1（2026-11-17，`<20261117083915.2971979-1-ridong.chen@linux.dev>`）*。今日无新版本；Frederic 的锁谜题获得解答，讨论趋于闭合。

## Maintainer 意见与讨论焦点

- **Waiman Long（cgroup 维护者）**：已 Ack（承接 20261118-014），今日补充 hotplug 作用于隔离分区的根本原因，并澄清「不记得说过这能长期修复」「也许并不完全相关」——即承认该耦合是现状约束，而非本补丁要解决的长期问题。
- **Tejun Heo**：此前已 Acked-by。
- **Frederic Weisbecker**：此前追问锁谜题根源（今日由 Waiman 解答）。
- 无 NAK；讨论从「为何耦合」收敛为「该耦合是现状、补丁只是在其上正确同步」。

## 合入评估

*likelihood=high*。两位维护者（Tejun、Waiman）已 Ack，Frederic 的疑问也已澄清，方向无争议。*blocking_issues*：无硬阻塞；若 Waiman 的「替代方案」（先 cpuset_mutex/cpus_read_lock 同步再释放旧 cpumask）仍需取舍。*next_action*：作者按最终取舍落地补丁，维护者收取。

## 效果评估

无性能数据；价值在正确性——消除 housekeeping 与 cpuset 之间 cpumask 发布的竞态（承接 20261118-014）。

## 我可以参与的点

- **review**：评估 Waiman 的替代方案与 Ridong 当前 `cpuset_mutex` 方案在 hotplug/重建交错下的等价性与锁序。
- **testing**：在 isolcpus=domain + cpuset 分区 + 频繁 hotplug 场景下验证 cpumask 视图一致。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261117083915.2971979-1-ridong.chen@linux.dev/
- Waiman 答疑: https://lore.kernel.org/all/a27dac16-f5c0-459b-9153-7caec3feb8a1@redhat.com/

---
id: sched-20261119-009
date: '2026-11-19'
subject: "sched/isolation: Publish new HK_TYPE_DOMAIN cpumask under cpuset_mutex"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261117083915.2971979-1-ridong.chen@linux.dev>"
lore_url: "https://lore.kernel.org/all/20261117083915.2971979-1-ridong.chen@linux.dev/"
authors: [Ridong Chen]
maintainers_involved: [Waiman Long, Tejun Heo]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261117083915.2971979-1-ridong.chen@linux.dev>"
    date: '2026-11-17'
    summary: "HK_TYPE_DOMAIN cpumask 发布纳入 cpuset_mutex 保护"
    review_outcome: "Tejun/Waiman Ack；Frederic 疑问由 Waiman 澄清"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["Waiman 替代方案取舍未定"]
  next_action: "作者按取舍落地补丁，维护者收取"
contribution_opportunities:
  - kind: review
    description: "评估替代方案与当前方案在锁序上的等价性"
  - kind: testing
    description: "isolcpus=domain + cpuset + 频繁 hotplug 下验证 cpumask 一致性"
generated_at: "2026-11-20T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261118-014]
tags: [cgroup, topology]
---