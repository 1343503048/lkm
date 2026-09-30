# sched_ext: Hold DSQ refs for deferred reenqueues

> **subject**：`sched_ext: Hold DSQ refs for deferred reenqueues`

## TL;DR

Hui Su 的 sched_ext use-after-free 修复：`scx_bpf_dsq_reenq()` 的 deferred reenqueue 路径上，被 deferral 的用户 DSQ 节点可能在 RCU 回调 `exit_dsq()` 到达前就被 detach，之后 deferred 路径仍在释放 `deferred_reenq_lock` 后继续用裸 DSQ 指针，回调可能先释放 DSQ，导致 KASAN 报 slab-use-after-free（`run_deferred` 中）。补丁在 `deferred_reenq_lock` 下 detach 节点**前**先取一个引用，回调与 deferred 路径各自释放自己的引用，保证对象存活到所有 detach 后的 reenqueue 完成。带 `Fixes: 84b1a0ea0b7c` 与 `Cc: stable # v7.1+`；Andrea Righi 认为 race 属实，但建议避免反复排队 RCU 回调地持引用，作者尚未回应。

## 背景与问题

用户 DSQ 的 deferred reenqueue 机制（`scx_bpf_dsq_reenq()` 引入于 84b1a0ea0b7c）下，被 defer 的用户 DSQ 节点可在 RCU 回调到达 `exit_dsq()` 之前就被 `process_deferred_reenq_users()` detach 走。一旦 detach，`exit_dsq()` 就找不到该节点，而 deferred 路径在放弃 `deferred_reenq_lock` 之后仍使用裸 DSQ 指针（检查其 ID、调用 `reenq_user()`）。RCU 宽限期只延迟「存量 RCU 读侧临界区」的回收，无法保护「已 detach 节点并继续裸用指针」的 deferred reenqueue，回调可能先释放 DSQ。KASAN 回归测试在 pre-fix 内核上报 `BUG: KASAN: slab-use-after-free in run_deferred+0x1312/0x1710`。

## 技术方案

在 `deferred_reenq_lock` 保护下、detach 节点之前先取 DSQ 引用；RCU 回调在 `exit_dsq()` 之后放弃基础引用，deferred 路径在最后一次访问 DSQ 之后放弃自己的引用。这样对象存活到所有 detach 后的 reenqueue 完成，同时保留「DSQ 被 invalidate」的原有行为。补丁内核跑同一回归测试无 KASAN 报告。

## 版本演进与当前进展

v1 刚发出（`<20260930101722.2468434-1-sh_def@163.com>`）。当日 Andrea Righi 回复：race 属实（Sashiko 的 ordering 疑虑在 for-7.4 上他认为是误报，序列与 `exit_dsq()` 列表检查均受 `deferred_reenq_lock` 保护），并提出两个改进点，作者尚未回应。

## Maintainer 意见与讨论焦点

- **Andrea Righi**（sched_ext 维护者）：
  1. 请作者分享复现测试或步骤，以便验证修复并评估 stable 回退；
  2. 建议避免「detached reenqueue 持引用期间反复排队 RCU 回调」——当前回调在存在活跃 detach reenqueue 时保留基础引用、再开一个宽限期只为重查计数，一个长 `reenq_user()` 可能往复多次；提议首个回调即放弃基础引用，由「最后释放引用的那一侧」安排 free，避免反复轮询。
- 无 NAK；核心分歧在引用管理方式的优化（作者未回应）。

## 合入评估

*likelihood=medium*。这是一处真实 memory-safety bug（KASAN UAF）的修复、带 `Fixes:`/`Cc: stable`，方向正确且维护者认可 race；但 Andrea 建议的引用管理优化（避免反复排队 RCU 回调）尚未落地/回应，且尚未提供可复现测试以便评估 stable。*blocking_issues*：Andrea 的引用管理优化意见待作者回应；复现测试未附上。*next_action*：作者回应 Andrea 的引用计数优化，分享复现测试，随后发 v2。

## 效果评估

KASAN 回归测试：pre-fix 内核报 `BUG: KASAN: slab-use-after-free in run_deferred`（`swapper/3/0` 读取 8 字节于 `ffff8880087009b0`，经 `run_deferred → ttwu_do_activate → try_to_wake_up`）；修复后同一测试无 KASAN 报告。无性能数据。

## 我可以参与的点

- `testing`：复现该 deferred reenqueue 的 UAF 场景（用户 DSQ + `scx_bpf_dsq_reenq()`），验证补丁消除 KASAN 报告且无 DSQ 提前释放/泄漏。
- `review`：评估 Andrea 提出的「首个回调放弃基础引用、最后由释放最后一侧引用者负责 free」方案的 busy-wait/生命周期边界是否完备。

## 参考链接

- lore（补丁）: https://lore.kernel.org/all/20260930101722.2468434-1-sh_def@163.com/
- Andrea 的回复: https://lore.kernel.org/all/ar0qLeKls0oBUEKO@gpd4/

---
id: sched-20260930-002
date: '2026-09-30'
subject: 'sched_ext: Hold DSQ refs for deferred reenqueues'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: '<20260930101722.2468434-1-sh_def@163.com>'
lore_url: 'https://lore.kernel.org/all/20260930101722.2468434-1-sh_def@163.com/'
authors:
  - 'Hui Su'
maintainers_involved:
  - 'Andrea Righi'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260930101722.2468434-1-sh_def@163.com>'
    date: '2026-09-30'
    summary: '在 detach 节点前先取 DSQ 引用，回调与 deferred 路径各自释放，防 deferred reenqueue 的 UAF'
    review_outcome: 'Andrea 认可 race 属实，建议避免反复排队 RCU 回调与分享复现测试'
upstream_commit: null
fixes_commit: '84b1a0ea0b7c'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'Andrea 建议的引用管理优化（首个回调放弃基础引用）待作者回应'
    - '复现测试/步骤尚未附上'
  next_action: '作者回应引用计数优化、分享复现测试后发 v2'
contribution_opportunities:
  - kind: testing
    description: '复现 deferred reenqueue UAF 场景，验证补丁消除 KASAN 报告且无提前释放/泄漏'
  - kind: review
    description: '评估「最后释放引用者负责 free」方案的 busy-wait/生命周期边界'
generated_at: '2026-10-01T01:00:00'
source_email_count: 2
related_articles: []
tags:
  - sched_ext
---