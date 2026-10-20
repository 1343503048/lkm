# sched_ext: Report a sub-scheduler's ecaps on attach, detach and cpu hotplug

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261018-001：Tejun Heo 发往 `sched_ext/for-7.4` 的六补丁系列 v3——补全 sub-scheduler 的 ecaps 上报协议（attach 时 bypass 解除前上报、detach 时任务还给父调度器前上报、CPU 离线/回归围绕 root 的 `ops.cpu_offline()/ops.cpu_online()` 上报、suspend/hibernation 排除）；Andrea Righi 已对整系列给 `Reviewed-by`，仅剩几处结构布局/nit 意见待折入。
- sched-20261020-008（今天）：Tejun 应用 1-6 到 `sched_ext/for-7.4-fixes`，改动两处：第 5 片用的是「作为回复发出的更新版」，并对全部补丁加 `Reviewed-by: Andrea Righi`。

## 背景与问题

（承接 20261018-001）sub-scheduler 通过 `ops.sub_ecaps_updated()` 获知自己持有哪些 cid，但父调度器 attach 时授予的 cid 只等 enable bypass 解除后才上报，导致它先收到 `ops.enqueue()` 却还没被通知过任何 cid；detach/CPU 离线时 caps 消失也不上报，CPU 回归后的 reseed 可能早于 root 的 `ops.cpu_online()` 就运行 sub 的 ops。本系列让 ecaps 只在「携带上报的投递」下变化，并把 suspend/hibernation 排除在外。今天合入。

## 技术方案

（承接，今日为合入）六补丁：1/6 抽 `cid_pshard()`；2/6 丢弃 ecaps syncs 后过 grace period 再释放；3/6 attach/detach 时投递 ecaps；4/6 仅 root 持有 CPU online 时投递；5/6 CPU 离线时上报丢失；6/6 suspend/hibernation 排除。今日 Tejun 应用 1-6 到 `sched_ext/for-7.4-fixes`，其中第 5 片采用「作为回复发出的更新版」（即此前回应 Andrea 5/6 结构布局意见后的修订版）。

## 版本演进与当前进展

*current_version: v3*（已应用）。

- v1（20261009）：仅覆盖 attach 时上报。
- v2（20261017）：扩展到 detach 与 CPU 热插拔、grace period 释放、suspend 排除。
- v3（20261018）：从 hard irq work 重调度 queued ecaps syncs、修正注释。
- 今日：Tejun 应用 1-6 到 `sched_ext/for-7.4-fixes`（第 5 片用更新版），全系列加 `Reviewed-by: Andrea Righi`。

## Maintainer 意见与讨论焦点

Tejun Heo（作者兼维护者）今日收取。此前 Andrea Righi 的 5/6 结构布局意见（`nr_ecaps_offline` 产生 4 字节空洞）已按「更新版第 5 片」折入；Tejun 对被否决的两条优化（5/6 冷路径 resched、2/6 无锁前置判断）维持原判。无剩余分歧。

## 合入评估

*likelihood=merged*。已应用到 `sched_ext/for-7.4-fixes`，整系列获 Andrea `Reviewed-by`。*blocking_issues*：无（已合入维护者树）。*next_action*：随 for-7.4 合入主线。

## 效果评估

无 benchmark 数字，属协议完整性改进。此前验证工作量大（TLC 模型检查 + debug 补丁扩大竞态窗口 + PREEMPT_RT + suspend），「协议在模型检查下无违反」是主要正确性证据。

## 我可以参与的点

- `testing`：在 `CONFIG_EXT_SUB_SCHED`（尤其 PREEMPT_RT）上做 sub-scheduler attach/detach + CPU 热插拔 + suspend 组合压力测试，验证合入后无 use-after-free。
- `review`：2/6 free 路径 grace period 与 5/6 offline 上报的锁/生命周期边界仍是全程最微妙处，可继续复核。

## 参考链接

- Tejun 今日回帖（Applied 1-6）：https://lore.kernel.org/all/ff1b8bf830af30639173e949e8c1be74@kernel.org/
- v3 封面信：https://lore.kernel.org/all/20261018015952.1499528-1-tj@kernel.org/

---
id: sched-20261020-008
date: 2026-10-20
subject: "sched_ext: Report a sub-scheduler's ecaps on attach, detach and cpu hotplug"
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: "<20261018015952.1499528-1-tj@kernel.org>"
lore_url: "https://lore.kernel.org/all/20261018015952.1499528-1-tj@kernel.org/"
authors: ["Tejun Heo"]
maintainers_involved: ["Tejun Heo", "Andrea Righi"]
current_version: v3
patch_series:
  - version: v1
    msgid: "<20261009094356.2852794-1-tj@kernel.org>"
    date: 2026-10-09
    summary: "首版，仅覆盖 attach 时上报 ecaps"
    review_outcome: "未获取到（不在当日缓存窗口）"
  - version: v2
    msgid: "<20261017164556.4136807-1-tj@kernel.org>"
    date: 2026-10-17
    summary: "扩展到 detach 与 CPU 热插拔：grace period 释放、仅 root 在线时投递、离线时上报丢失、suspend 排除"
    review_outcome: "Andrea 提出 5/6 结构空洞、2/6 锁流量等意见"
  - version: v3
    msgid: "<20261018015952.1499528-1-tj@kernel.org>"
    date: 2026-10-18
    summary: "从 hard irq work 重调度 queued ecaps syncs 而非 kick；修正注释"
    review_outcome: "Andrea 整系列 Reviewed-by；Tejun 今日应用 1-6 到 for-7.4-fixes"
upstream_commit: null
fixes_commit: null
merged_branch: "sched_ext/for-7.4-fixes"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "随 for-7.4 合入主线"
contribution_opportunities:
  - kind: testing
    description: "在 CONFIG_EXT_SUB_SCHED（尤其 PREEMPT_RT）上做 attach/detach + 热插拔 + suspend 压力测试"
  - kind: review
    description: "复核 2/6 grace period 与 5/6 offline 上报的锁/生命周期边界"
generated_at: "2026-10-21T01:30:00"
source_email_count: 1
related_articles: ["sched-20261018-001"]
tags: [sched_ext, cgroup]
---