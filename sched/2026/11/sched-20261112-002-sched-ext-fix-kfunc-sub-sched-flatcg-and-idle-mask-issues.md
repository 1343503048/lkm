# sched_ext: fix kfunc, sub-sched, flatcg and idle-mask issues

## TL;DR

Tao Cui 发六补丁系列修 sched_ext core、scx_flatcg 示例调度器与 CID helper 的六个问题，最严重的是两个 DSQ 迭代 kfunc 可被 tracing 程序调用、在 DSQ 锁已被持有时递归自旋导致整机锁死；另有 scx_bpf_cid_node() 对非法 cid 直接 abort 调度器、sub-scheduler 声明的 cid_online/cid_offline 回调永远不触发、scx_flatcg 在 ENQ_RACE 路径把 cgroup 甩出 rbtree 直到 watchdog 杀掉调度器、以及 hotplug 时内置 idle mask 不清导致离线 CPU 仍被报为 idle。刚发出，尚无维护者回复。

## 背景与问题

作者在 `sched_ext/for-next`（5b740a72b55c）上逐个修复六个独立缺陷：

1. `bpf_iter_scx_dsq_next()`/`bpf_iter_scx_dsq_destroy()` 拿用户 DSQ 的 raw spinlock，却注册在 `scx_kfunc_ids_any`（对 `BPF_PROG_TYPE_TRACING` 也开放）。tracing 程序在该锁已持有时调用（如调度器在 `scx_dispatch_enqueue()` 持锁时触发 `scx_error()` → `trace_sched_ext_exit`）会递归获取同一 raw spinlock 锁死 CPU。
2. `scx_bpf_cid_node()` 文档声称非法 cid 返回 `NUMA_NO_NODE`，实际却 abort 调度器。
3. sub-scheduler 可在 `ops.init_cids()` 里读自己的 caps，但此时 caps 存储尚未发布，`scx_bpf_sub_caps()` 会直接杀掉正在初始化的调度器。
4. sub-scheduler 声明 `ops.cid_online()/cid_offline()` 后 has_op 位被置起，但 hotplug 回调只投递给 root 调度器，回调永不执行。
5. `scx_flatcg` 的 `cgrp_enqueued()` 在 ENQ_RACE 路径 `bpf_kptr_xchg()` 返回 NULL 时直接 bail，可能把 cgroup 甩出 rbtree 且后续 enqueue 全被跳过，直到 watchdog 以 `SCX_EXIT_ERROR_STALL` 杀掉调度器。
6. 内置 idle mask 只由 `__scx_update_idle()`（任务驱动）与 `reset_idle_masks()`（load）维护，hotplug 时不清，离线 CPU 的 stale 位持续被 `scx_bpf_pick_idle_cpu()` 报为 idle 候选。

## 技术方案

六补丁：0001 在验证期拒绝两个迭代 kfunc 用于 tracing（保留给 struct_ops/syscall 程序），扩展 `b07a7450f6ef`/`4c2e0751d5e6` 的既有「拒绝 rq 锁类 kfunc」覆盖；0002 把 `scx_bpf_cid_node()` 改成良性查找、非法 cid 返回 `NUMA_NO_NODE`；0003 让 `scx_bpf_sub_caps()` 在 pre-init 自读时返回 `-EBUSY` 而非杀调度器（镜像 cid 路径「查表指针返回 -EINVAL」的既有处理）；0004 在 load 期拒绝 sub-scheduler 声明 hotplug 回调并更新 kerneldoc；0005 让 `scx_flatcg` 在 ENQ_RACE 时等待 picker 结算后重试而非 bail；0006 在 `handle_hotplug()` 里从内置 idle mask 清掉 CPU、并把 claim 路径 `scx_idle_test_and_clear_cpu()` 用 `cpu_online()` 门控（claim 是唯一必经点，保证离线 CPU 不会被分发出去）。

## 版本演进与当前进展

*current_version: v1（2026-11-12，`<20261112130934.563321-1-cui.tao@linux.dev>`）*。当日发出，无版本演进；基于 `sched_ext/for-next`。系列 2/6（`Make scx_bpf_cid_node() a benign lookup for invalid cids`）未在当日缓存中，其余五封已收到。

## Maintainer 意见与讨论焦点

当日无维护者回复（系列刚发出）。作者在 cover 中注明 core.c 相关修复走单独系列（见 sched-20261112-001）。

## 合入评估

*likelihood=unknown*。刚发出、无回复，无法判断。*blocking_issues*：无（尚未有评审）。*next_action*：等待 sched_ext 维护者（Tejun Heo 等）评审；部分补丁带 `Fixes:` 标签，若被接受存在进 sched_ext/for-7.4-fixes 的可能。

## 效果评估

作者在 qemu 上 A/B 验证：0005 在 CPU 饱和下驱动 `ops.enqueue()` 竞态，stock 上 6/10 轮会把 cgroup 甩成调度器级 stall、打补丁后 0/10；0006 用 idle-probe 调度器每次 dispatch 探测 `scx_bpf_pick_idle_cpu()`，15/15 次 offline/online 周期探测到 0 个 stale 条目。0001 无独立复现（`bpf_iter_scx_dsq_destroy()` 的 cursor 需先经至少一次成功 next() 才挂进 DSQ，而 next() 在同一窗口先死锁），为对称性一并修。属正确性/健壮性修复，无性能数据。

## 我可以参与的点

- **testing**：用带 tracing BPF 程序的真实调度器验证 0001 在 DSQ 锁竞争窗口下不再死锁；在 hotplug 密集场景验证 0006 后 `scx_bpf_pick_idle_cpu()` 不再返回离线 CPU。
- **review**：核对 0005 的「等待 picker 结算后重试」是否覆盖 `bpf_kptr_xchg()` 返回 NULL 的全部竞态窗口（作者承认仍残留一个极窄的 picker 持有节点在飞窗口，比例远低于 stock）。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261112130934.563321-1-cui.tao@linux.dev/
- patch 1/6: https://lore.kernel.org/all/20261112130934.563321-2-cui.tao@linux.dev/

---
id: sched-20261112-002
date: '2026-11-12'
subject: "sched_ext: fix kfunc, sub-sched, flatcg and idle-mask issues"
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: "<20261112130934.563321-1-cui.tao@linux.dev>"
lore_url: "https://lore.kernel.org/all/20261112130934.563321-1-cui.tao@linux.dev/"
authors: [Tao Cui]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261112130934.563321-1-cui.tao@linux.dev>"
    date: '2026-11-12'
    summary: "六个修复：拒绝 tracing 调 DSQ 迭代 kfunc、cid_node 良性化、sub_caps 返回 -EBUSY、拒绝 sub-sched hotplug 回调、flatcg ENQ_RACE 重试、hotplug 清 idle mask"
    review_outcome: "暂无回复"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: "等待 sched_ext 维护者（Tejun Heo）评审"
contribution_opportunities:
  - kind: testing
    description: "用带 tracing BPF 程序的调度器验证 0001 不死锁、hotplug 下 0006 不再报离线 CPU 为 idle"
  - kind: review
    description: "核对 0005 的重试是否覆盖 ENQ_RACE 全部竞态窗口"
generated_at: "2026-11-13T09:00:00+08:00"
source_email_count: 5
related_articles: []
tags: [sched_ext, bpf]
---
