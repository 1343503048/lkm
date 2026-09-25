# psi: charge pressure to the task's active cgroup

## TL;DR

Shakeel Butt 的 RFC 系列（「把内核为某 cgroup 做的活计费到该 cgroup」）中的 3/7：让 `task_psi_group()` 改用 active cgroup，使内核线程在 `set_active_cgroup()` 下的 stall（如内存回收）计入该 cgroup 的 PSI 压力。纯 RFC、无人回帖。

## 背景与问题

PSI（Pressure Stall Information）按任务归属的 cgroup 统计压力。但内核线程经 `set_active_cgroup()` 暂时为某个 cgroup 干活时，它的 stall（典型是内存回收、直接的页面回收）仍被记到默认 cgroup 或系统级，而不是记到它正在服务的那个 cgroup。结果：被服务 cgroup 的 PSI 被低估，无法反映「内核替它做回收」带来的真实压力。

## 技术方案

`task_psi_group()` 里把 `cgroup_psi(task_dfl_cgroup(task))` 改为 `cgroup_psi(task->active_cgroup ?: task_dfl_cgroup(task))`。并新增 `psi_set_active_cgroup(task, cgrp)`：在 active cgroup 变化时，用 `psi_task_change()` 把任务的压力状态从旧 group 移到新 group（与真实 cgroup move 的 `cgroup_move_task()` 同一做法），从而保持 PSI 记账的连续性。调用点：`kernel/sched/core.c` 的 `set_active_cgroup()` 里 `p->active_cgroup = cgrp` 替换为 `psi_set_active_cgroup(p, cgrp)`。共 32 insertions(+), 2 deletions(-)。

## 版本演进与当前进展

- RFC v1（2026-09-24，封面 `<20260924184714.912181-1-shakeel.butt@linux.dev>`，7 补丁）：本枚 3/7，msgid `<20260924184714.912181-4-shakeel.butt@linux.dev>`。
- 09-25：落盘缓存，无回帖。

## Maintainer 意见与讨论焦点

RFC 刚发出，今日无人回帖。PSI 记账的 active cgroup 归属属于语义变更，是否会与 cgroup v1/v2 的 psi 语义或 `psi_cgroup_restart()` 等路径冲突，待 cgroup/psi 维护者（Johannes Weiner 等）review。

## 合入评估

*likelihood=unknown*。纯 RFC、无表态。*blocking_issues*：无 review。*next_action*：等 cgroup/psi 维护者 review active cgroup 归属语义。

## 效果评估

暂无效果数据；RFC 邮件未附 benchmark。

## 我可以参与的点

- `review`：审读 `psi_set_active_cgroup()` 拿 rq lock 的调用上下文与 active cgroup 快速切换时的压力状态迁移正确性。
- `testing`：构造内核线程在 set_active_cgroup 下长时间内存回收的场景，对照 cgroup PSI 记录是否正确归属。

## 参考链接

- RFC 3/7 补丁: https://lore.kernel.org/all/20260924184714.912181-4-shakeel.butt@linux.dev/
- RFC 封面: https://lore.kernel.org/all/20260924184714.912181-1-shakeel.butt@linux.dev/

---
id: sched-20260925-016
date: 2026-09-25
subject: "psi: charge pressure to the task's active cgroup"
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: "<20260924184714.912181-4-shakeel.butt@linux.dev>"
lore_url: "https://lore.kernel.org/all/20260924184714.912181-4-shakeel.butt@linux.dev/"
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: "2026-09-26T01:15:00"
authors:
  - "Shakeel Butt"
maintainers_involved: []
patch_series:
  - version: v1
    msgid: "<20260924184714.912181-4-shakeel.butt@linux.dev>"
    date: 2026-09-24
    summary: "task_psi_group 改用 active cgroup，新增 psi_set_active_cgroup 做压力状态迁移"
    review_outcome: "无回帖"
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - "纯 RFC，无 review"
  next_action: "等 cgroup/psi 维护者 review active cgroup 归属语义"
contribution_opportunities:
  - kind: review
    description: "审读 psi_set_active_cgroup 拿 rq lock 的调用上下文与 active cgroup 快速切换时的压力状态迁移正确性"
  - kind: testing
    description: "构造内核线程在 set_active_cgroup 下长时间回收场景，对照 cgroup PSI 记录是否正确归属"
source_email_count: 1
related_articles: []
tags:
  - psi
  - cgroup
---