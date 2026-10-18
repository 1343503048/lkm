---
id: sched-20261018-001
date: 2026-10-18
subject: 'sched_ext: Report a sub-scheduler''s ecaps on attach, detach and cpu hotplug'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261018015952.1499528-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20261018015952.1499528-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
- Andrea Righi
current_version: v3
patch_series:
- version: v1
  msgid: <20261009094356.2852794-1-tj@kernel.org>
  date: 2026-10-09
  summary: 首版，仅覆盖 attach 时上报 ecaps
  review_outcome: 未获取到（不在当日缓存窗口）
- version: v2
  msgid: <20261017164556.4136807-1-tj@kernel.org>
  date: 2026-10-17
  summary: 扩展到 detach 与 CPU 热插拔：detach 同 attach 上报且无视 bypass；cid_pshard 拆分 + grace
    period 释放；仅 root 在线时投递、离线时上报丢失、suspend 排除
  review_outcome: Andrea Righi 提出 5/6 结构空洞、2/6 锁流量等意见
- version: v3
  msgid: <20261018015952.1499528-1-tj@kernel.org>
  date: 2026-10-18
  summary: 从 hard irq work 重调度 queued ecaps syncs 而非 kick；修正 SCX_RQ_ONLINE 与 suspend
    注释
  review_outcome: Andrea Righi 整系列 Reviewed-by，另有 nit 待折入
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 5/6 nr_ecaps_offline 结构布局调整待折入
  - 注释更新
  next_action: Tejun 折入 Andrea 的结构布局与注释 nit 后应用到 sched_ext/for-7.4
contribution_opportunities:
- kind: testing
  description: 在 CONFIG_EXT_SUB_SCHED（尤其 PREEMPT_RT）上做 sub-scheduler attach/detach
    + CPU 热插拔 + suspend 压力测试，验证 ecaps 上报时序与 free 路径无 use-after-free
- kind: review
  description: 复核 2/6 free 路径 grace period 与 5/6 offline 上报的锁/生命周期边界
generated_at: '2026-10-19T09:00:00'
source_email_count: 16
related_articles: []
tags:
- sched_ext
- cgroup
title: 'sched_ext: Report a sub-scheduler''s ecaps on attach, detach and cpu hotplug'
layout: article
---

## TL;DR

Tejun Heo 发往 `sched_ext/for-7.4` 的六补丁系列 v3：补全 sub-scheduler 的 ecaps（effective caps）上报协议——attach 时的授权在 bypass 解除前上报、detach 时的丢失在任务还给父调度器前上报、CPU 离线/回归围绕 root 的 `ops.cpu_offline()/ops.cpu_online()` 上报，suspend/hibernation 排除在外。Andrea Righi 已对整系列给出 `Reviewed-by`，仅剩几处结构布局/nit 级意见待折入。合入前景高。

## 背景与问题

sub-scheduler 通过 `ops.sub_ecaps_updated()` 获知自己持有哪些 cid，但父调度器在 attach 时授予的 cid 只有等它的 enable bypass 解除（同时任务移交给它）之后才上报——于是它先收到第一批 `ops.enqueue()` 调用，却还没被通知过任何一个 cid，必须把任务先攒在某处直到授权到来。

丢失同样不上报：detach 时与 CPU 离线时 caps 消失，却不向 sub-scheduler 或其父调度器投递；CPU 回归后的 reseed 也可能在 root 的 `ops.cpu_online()` 之前就运行它们的 ops。

本系列让 sub-scheduler 的 ecaps 只在「携带上报的投递」下变化：attach 时 caps 在 bypass 解除前上报，detach 时丢失在任务还给父调度器前上报，CPU 的丢失与回归围绕 root 的 `ops.cpu_offline()` 与 `ops.cpu_online()`。suspend/hibernation 被排除在外——它们带走的 CPU 保留最后一次投递的 caps，resume 只上报净变化。

## 技术方案

六补丁（`kernel/sched/ext/`）：

- **1/6 `Factor out cid_pshard()`**：抽出 `cid_pshard()` 供后续复用。
- **2/6 `Free a sub-scheduler a grace period after discarding its ecaps syncs`**：sub-scheduler 丢弃 ecaps syncs 后过一个 grace period 再释放，处理在途 batch 的 use-after-free。
- **3/6 `Report a sub-scheduler's ecaps on attach and detach`**：attach 时在 bypass 解除前、detach 时在任务还给父调度器前，投递 ecaps。
- **4/6 `Deliver ecaps only while the root has the cpu online`**：仅在 root 持有 CPU online 时投递。
- **5/6 `Report the ecaps loss when a cpu goes offline`**：CPU 离线时上报 caps 丢失。
- **6/6 `Leave suspend and hibernation out of the ecaps reports`**：suspend/hibernation 不产生 ecaps 上报，resume 只报净变化。

验证：sub-scheduler 在任务排队、caps 授予/撤销的情况下 attach/detach；CPU 热插拔用 debug 补丁扩大竞态窗口、grants 在 CPU 下线时洪泛；PREEMPT_RT 同样验证；跨 suspend 验证。上报、per-cpu sync、CPU 热插拔、suspend 与 free 路径之间的协议在少量 CPU 下用 TLC 做了模型检查。基于 `sched_ext/for-7.4`（9c0af54cb49c）。

## 版本演进与当前进展

*current_version: v3*（2026-10-18）。

- **v1**（2026-10-09）：首版，仅覆盖 attach 时上报。未在本日缓存窗口内，正文未获取到。
- **v2**（2026-10-17）：扩展到 detach 与 CPU 热插拔——detach 与 attach 一样上报、且无视 bypass 投递（去掉 unbypass 时的 replay，#3）；丢弃 `sync_pcpu_ecaps()` 拆分，改为 `cid_pshard()` 拆分 + 丢弃 syncs 后过一个 grace period 再释放（#1/#2）；仅 root 持有 CPU online 时投递、CPU 离线时上报丢失、suspend/hibernation 排除（#4-#6）。
- **v3**（2026-10-18，本日）：两条改动——(1) 从 hard irq work 在该 CPU 上重新调度其排队的 ecaps syncs 而不是 kick（`dispatch_one()` 只在开始处理 syncs，pick 期间 rq 锁释放时落下的 kick 会随 pick 一起被清掉，回应 sashiko 的 #3/#5 问题）；(2) 修正 `SCX_RQ_ONLINE` 注释（#4）与 suspend down 时为何没有 pending report 的注释（#6），更新注释与描述。

## Maintainer 意见与讨论焦点

Andrea Righi（sched_ext 维护者）对整系列给出 `Reviewed-by: Andrea Righi <arighi@nvidia.com>`，但附了几条非阻塞意见：

- **5/6 结构布局（已采纳）**：`nr_ecaps_offline` 落在两个 8 字节对齐字段之间，产生 4 字节空洞并把其后所有字段（含 `kick_sync`）后移 8 字节；建议把它挪到 `kick_sync_pending` 旁边，让 u32 与 bool 共用既有空洞。Tejun 回复「Will do」。
- **5/6 优化建议（被否决）**：root-only 调度器下 walk 跳过 root、什么都不排队，但 `resched_sync_ecaps()` 仍在每个 online CPU 上跑、白白启动 ext_server 并排队 resched irq work；offline 侧同理。Andrea 建议只在「确实排队了东西」时才 resched。Tejun 拒绝：这些在 CPU 热插拔路径上，本就是冷路径，成本是一次 resched，「不值得为省这点成本增加复杂度」。
- **2/6 无锁前置判断（被否决）**：free 路径为每个 possible CPU 都取 rq 锁（irqs off），大机器上锁流量大；Andrea 建议把 `llist_on_list()` 无锁判断放回锁前。Tejun 解释被替换的循环本就每 rq 取一次锁，attach/detach 也多次遍历所有 rq 锁，不贵；且 `__scx_process_sync_ecaps()` 在写 pcpu 前对每个 node 调 `init_llist_node()`，被处理中的 node 读作 off-list，无锁判断虽仍安全但理由不成立——「这条路径太复杂，我宁愿保持尽可能笨」。

## 合入评估

*likelihood=high*。方向无异议，整系列已获 Andrea `Reviewed-by`，Tejun 是 sched_ext 维护者兼作者，目标 `sched_ext/for-7.4`。*blocking_issues*：仅剩已答应折入的 5/6 `nr_ecaps_offline` 结构布局调整（Andrea 的结构空洞意见）与注释更新。*next_action*：Tejun 折入上述 nit 后应用到 `sched_ext/for-7.4`。

## 效果评估

无 benchmark 数字，属正确性/协议完整性改进。验证工作量大（TLC 模型检查 + debug 补丁扩大竞态窗口 + PREEMPT_RT + suspend），但未给出量化效果数据；「协议在模型检查下无违反」是主要证据。

## 我可以参与的点

- `testing`：在启用 `CONFIG_EXT_SUB_SCHED` 的内核（尤其 PREEMPT_RT）上做 sub-scheduler attach/detach + CPU 热插拔 + suspend 组合压力测试，验证 ecaps 上报时序与 free 路径无 use-after-free；社区对这条复杂路径的独立验证有持续需求。
- `review`：2/6 的 free 路径、5/6 的 offline 上报是全程最微妙的锁/生命周期代码，若熟悉 sched_ext 的 DSQ/ecaps sync 机制，可帮忙复核 grace period 与在途 batch 的边界。

## 参考链接

- v3 封面信：https://lore.kernel.org/all/20261018015952.1499528-1-tj@kernel.org/
- v2 封面信：https://lore.kernel.org/all/20261017164556.4136807-1-tj@kernel.org/
- v1 封面信：https://lore.kernel.org/all/20261009094356.2852794-1-tj@kernel.org/
- Andrea Righi 整系列 Reviewed-by：https://lore.kernel.org/all/atSPMmtaEVJCfZxP@gpd4/
