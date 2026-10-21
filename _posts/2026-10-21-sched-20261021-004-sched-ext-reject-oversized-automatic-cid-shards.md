---
id: sched-20261021-004
date: 2026-10-21
subject: 'sched_ext: Reject oversized automatic CID shards'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261021091214.1713830-1-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20261021091214.1713830-1-sh_def@163.com/
authors:
- Hui Su
maintainers_involved:
- Andrea Righi
current_version: v2
patch_series:
- version: v1
  msgid: <20261021064946.1445728-1-sh_def@163.com>
  date: 2026-10-21
  summary: oversized core 加进 shard 前返回 -E2BIG
  review_outcome: Andrea 复现栈损坏，建议加 scx_error() 诊断
- version: v2
  msgid: <20261021091214.1713830-1-sh_def@163.com>
  date: 2026-10-21
  summary: 新增 scx_error() 输出 oversized core 与硬上限
  review_outcome: Andrea 给出 Reviewed-by + Tested-by，无分歧
upstream_commit: null
fixes_commit: e2c841b91bf9
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等 sched_ext 维护者收取
contribution_opportunities: []
generated_at: '2026-10-22T01:30:00'
source_email_count: 4
related_articles: []
tags:
- sched_ext
- cgroup
title: 'sched_ext: Reject oversized automatic CID shards'
layout: article
---

## TL;DR
Hui Su 发往 sched_ext 的单补丁修复：自动拓扑打包在「当前 shard 会超目标大小时」才另起新 shard，但「第一个 core 永远被接受」以保证 core 不可分割——当某个不可分割 core 的 CPU 数超过 `SCX_CID_SHARD_MAX_CPUS`（512）时无法表示，且 `alloc_pshard()` 的固定大小内联 cmask 会被越界初始化，覆盖后续字段导致栈内存损坏。修复在把 core 加进 shard 前即拒绝并返回 `-E2BIG`。Andrea Righi 用 virtme-ng 复现了栈损坏 panic，并给出 Reviewed-by + Tested-by。

## 背景与问题
每个 shard 用固定大小内联 cmask 存储，尺寸为 `SCX_CID_SHARD_MAX_CPUS`（512）。自动打包对「超过目标大小」时另起新 shard，但对「第一个 core」无条件接受（因为 core 不可分割）。若某不可分割 core 的 `cids_in_core > SCX_CID_SHARD_MAX_CPUS`（如 600 个 SMT 兄弟的合成拓扑），把该 oversized shard 传给 `alloc_pshard()` 后，cmask 初始化会覆盖其后的字段。真实硬件不会出现（单 core 不超 512 SMT 兄弟），但合成拓扑（virtme-ng + CONFIG_MAXSMP=y）可触发：Andrea 实测加载 scx_qmap 触发 `__scx_cmask_init()` 的 WARN_ON_ONCE 后在 `scx_bpf_sub_caps()` 栈损坏 panic。

## 技术方案
单补丁（`kernel/sched/ext/cid.c`，v2 为 +6 行）：
- 在给 shard 加 core 前检查 `cids_in_core > SCX_CID_SHARD_MAX_CPUS`，超限即返回 `-E2BIG` 拒绝。
- v2 按 Andrea 建议加 `scx_error(sch, "core with %u cpus exceeds max shard size %d", ...)`，使拒绝可诊断（v1 只报 `scx_root_enable() failed (-7)`，无从知道原因）。

## 版本演进与当前进展
*current_version: v2*。
- v1（`<20261021064946.1445728-1-sh_def@163.com>`）：仅 `return -E2BIG`。
- v2（`<20261021091214.1713830-1-sh_def@163.com>`）：新增 `scx_error()` 诊断输出，其余不变。

## Maintainer 意见与讨论焦点
Andrea Righi（sched_ext 维护者）：确认真实硬件不会命中但合成拓扑可复现，并用 virtme-ng `--cpus 600,sockets=1,cores=1,threads=600` 复现了 WARN_ON_ONCE + 栈损坏；指出 v1 报错信息不足，建议用 `scx_error()` 报出 oversized core 与硬上限；v2 满足后给出 *Reviewed-by* + *Tested-by*。无分歧。

## 合入评估
*likelihood=high*。带 `Fixes:`、已获维护者 Reviewed-by + Tested-by，v2 满足全部评审意见。*blocking_issues*：无。*next_action*：等 sched_ext 维护者收取即可。

## 效果评估
非性能优化。效果证据来自 Andrea 的复现验证：未打补丁时加载 scx_qmap 触发 WARN_ON_ONCE + 栈损坏 panic，打补丁后用 `-E2BIG` 正确拒绝调度器。

## 我可以参与的点
当前阶段已获维护者 review + 实测，暂无明显参与空间，可持续观察其进入 sched_ext 分支。

## 参考链接
- v2 patch：https://lore.kernel.org/all/20261021091214.1713830-1-sh_def@163.com/
- v1 patch：https://lore.kernel.org/all/20261021064946.1445728-1-sh_def@163.com/
- Andrea 复现 + Reviewed/Tested-by：https://lore.kernel.org/all/aths_re-QX5Er4Vq@gpd4/
