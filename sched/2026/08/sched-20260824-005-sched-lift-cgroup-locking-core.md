# sched: 提升 cgroup 更新锁到核心层（增量更新）

## TL;DR
本文为增量更新，完整背景见 related_articles 中的文章。v3 获得 Andrea Righi 的 `Reviewed-by`，但 Andrea 指出带宽参数的并发序列化问题仍存在（不阻塞本补丁），建议后续单独处理。

## 版本演进与当前进展
- **v3**（Tao Cui）：将 cgroup 控制文件写入路径的锁提升到调度核心层，防止 CFS/SCX 状态发散
- **Andrea Righi review**：给出 `Reviewed-by`，但指出遗留问题

Andrea 的关键评论：
> IIUC the bandwidth read-modify-write paths still snapshot the unchanged parameters before taking cpu_max_mutex, so concurrent writes to different bandwidth knobs can overwrite each other.
> However, this shouldn't be a blocker for this patch. The serialization aspect could be addressed in a separate patch.

## Maintainer 意见与讨论焦点
- **Andrea Righi**：`Reviewed-by`，认可方向，但指出带宽并发写仍有竞态（可作为后续改进）
- **之前 Peter Zijlstra**（08-22 讨论）：建议将锁重命名为更通用的名称

当前无阻塞性分歧。

## 合入评估
合入可能性 **high**：
- 已获得 Reviewed-by
- 问题真实（CFS/SCX 状态发散）
- 遗留的并发序列化问题不阻塞本补丁
- `next_action`：等待 Peter Zijlstra 或 Ingo Molnar 最终确认并合入

## 效果评估
无性能数据；属于正确性修复，防止并发写入导致的调度器状态不一致。

## 我可以参与的点
- 可以帮忙分析带宽并发写的竞态场景，为后续补丁提供输入
- 如果有 CFS + SCX 混用的测试环境，可以验证修复效果

## 参考链接
- lore thread: 未获取到

---
id: sched-20260824-005
date: 2026-08-24
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<unknown>"
lore_url: "未获取到"
authors:
- Tao Cui
maintainers_involved:
- Peter Zijlstra
- Andrea Righi
- Michal Koutny
current_version: v3
patch_series:
  - version: v3
    msgid: "<unknown>"
    date: 2026-08-24
    summary: "提升 cgroup 更新锁到核心层"
    review_outcome: "Andrea Righi Reviewed-by，指出带宽并发遗留问题"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待 Peter Zijlstra / Ingo Molnar 确认合入"
contribution_opportunities:
  - kind: review
    description: "分析带宽并发写的竞态场景，为后续补丁提供输入"
generated_at: "2026-08-25T10:40:00"
source_email_count: 2
related_articles: [sched-20260822-005]
tags: [sched/core, cgroup, sched_ext, race_condition]
---
