# sched_ext: Reject oversized automatic CID shards

## TL;DR
本文为增量更新，完整脉络见下。

- sched-20261021-004：Hui Su 发往 sched_ext 的单补丁修复：自动拓扑打包在「当前 shard 会超目标大小时」才另起新 shard，但「第一个 core 永远被接受」——当某不可分割 core 的 CPU 数超过 `SCX_CID_SHARD_MAX_CPUS`（512）时无法表示，固定大小内联 cmask 被越界初始化、覆盖后续字段导致栈内存损坏。修复在加 core 进 shard 前即返回 `-E2BIG`。Andrea Righi 用 virtme-ng 复现栈损坏 panic，给 Reviewed-by + Tested-by。
- sched-20261022-013（今天）：sched_ext 维护者 Tejun Heo 将其**应用到 sched_ext/for-7.4-fixes**，并在描述中补注「该 bug 仅在人工 VM 拓扑下可复现」。

## 背景与问题
（承接 sched-20261021-004）每个 shard 用固定大小内联 cmask 存储（`SCX_CID_SHARD_MAX_CPUS`=512）。自动打包对「超过目标大小」另起 shard，但对「第一个 core」无条件接受；若某不可分割 core 的 `cids_in_core > 512`（如 600 个 SMT 兄弟的合成拓扑），oversized shard 传入 `alloc_pshard()` 后 cmask 初始化会覆盖其后字段。真实硬件单 core 不超 512 SMT 兄弟，但合成拓扑（virtme-ng + CONFIG_MAXSMP=y）可触发栈损坏 panic。

## 技术方案
（承接 v2）单补丁（`kernel/sched/ext/cid.c`）：在给 shard 加 core 前检查 `cids_in_core > SCX_CID_SHARD_MAX_CPUS`，超限 return `-E2BIG` 拒绝；v2 加 `scx_error(sch, "core with %u cpus exceeds max shard size %d", ...)` 使拒绝可诊断。今日仅由 Tejun 收取并在描述里补注「仅人工 VM 拓扑可复现」。

## 版本演进与当前进展
*current_version: v2*（`<20261021091214.1713830-1-sh_def@163.com>`）。当日被应用到 sched_ext/for-7.4-fixes。

## Maintainer 意见与讨论焦点
sched_ext 维护者 Tejun Heo 直接收取（Applied to sched_ext/for-7.4-fixes），无额外质疑，仅补注 bug 的复现条件说明。

## 合入评估
*likelihood=merged*。已进入 sched_ext/for-7.4-fixes（`merged_branch=sched_ext/for-7.4-fixes`），等待随 7.4 修复流汇入主线。

## 效果评估
修复栈损坏 panic（合成拓扑下可复现）；真实硬件不受影响。

## 我可以参与的点
当前阶段已合入，暂无明显参与空间。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261021091214.1713830-1-sh_def@163.com/
- Tejun 今日回帖：https://lore.kernel.org/all/f742ae35affc8c9a1ae0ec61f58dd5d6@kernel.org/

---
id: sched-20261022-013
date: 2026-10-22
subject: "sched_ext: Reject oversized automatic CID shards"
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: "<20261021091214.1713830-1-sh_def@163.com>"
lore_url: "https://lore.kernel.org/all/20261021091214.1713830-1-sh_def@163.com/"
authors: ["Hui Su"]
maintainers_involved: ["Tejun Heo"]
current_version: v2
patch_series:
  - version: v2
    msgid: "<20261021091214.1713830-1-sh_def@163.com>"
    date: 2026-10-21
    summary: "加 core 进 shard 前拒绝 oversized，返回 -E2BIG + 诊断日志"
    review_outcome: "Andrea Righi Reviewed+Tested；Tejun Heo 应用到 sched_ext/for-7.4-fixes"
upstream_commit: null
fixes_commit: null
merged_branch: "sched_ext/for-7.4-fixes"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已合入 sched_ext/for-7.4-fixes，等待随修复流进主线"
contribution_opportunities: []
generated_at: "2026-10-23T01:20:00"
source_email_count: 1
related_articles: ["sched-20261021-004"]
tags: [sched_ext, cgroup]
---