# sched/autogroup: Fix task_group UAF during thread creation

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261023-004：Daehyeon Ko 修 autogroup use-after-free（`sched_cgroup_fork()` 在 CLONE_THREAD 子进程发布前指向旧 `autogroup->tg`，与 `ksys_setsid()` 竞态）。
- sched-20261026-003：Peter 质疑 NULL deref，建议把复杂度移到 `ksys_setsid()`。
- sched-20261030-008：Daehyeon 论证无 NULL deref、单挪 tasklist_lock 不关窗；Peter 收回否定、提议 `autogroup_move_group()` 也持 `cgroup_threadgroup_rwsem`。
- sched-20261031-012：Tejun 介入——`cgroup_threadgroup_rwsem` 是全局 percpu rwsem，常写持很贵；建议把 autogroup 赋值挪到 fork 更晚、不与 setsid 竞态的位置。
- sched-20261102（今天）：Peter 回应 Tejun——`setsid()` 不比 cgroup 任务迁移更 critical、且几乎没人用 autogroup（systemd 走 cgroup）；「两种规则分别管 `p->sched_task_group`（cgroup vs autogroup）」没吸引力，还会增加 fork 回调。

## 背景与问题

（承接）竞态时序不变。今日焦点继续围绕「autogroup 侧是否值得为跟 setsid 串行化引入额外复杂度」。

## 技术方案

（承接）无新代码；分歧从「要不要 rwsem」进一步到「is it even worth the complexity」——Peter 明确反对为 autogroup 引入与 cgroup 不同的 `sched_task_group` 规则。

## 版本演进与当前进展

v1 未更新；方案走向出现方向性再讨论。

## Maintainer 意见与讨论焦点

Peter 观点：autogroup 使用率极低、`setsid()` 非 critical，为它加 fork 回调与双规则不划算。Tejun 的主张（晚赋值、不串行化）尚未被 Peter 直接接受，也未拒绝。

## 合入评估

likelihood=low（偏 unknown）。作者原补丁方向被维护者不断提出更简单替代，方案未收敛。

## 效果评估

（承接）UAF 修复本身无性能数据。

## 我可以参与的点

- review：评估「fork 晚赋值」方案是否真能消除与 setsid 的竞态、代价几何。
- discussion：就 autogroup 是否值得单独维护 `sched_task_group` 规则给出论据。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261023013631.881730-1-4ncienth@gmail.com/

---
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261023013631.881730-1-4ncienth@gmail.com>
authors:
- Daehyeon Ko
maintainers_involved:
- Peter Zijlstra
- Tejun Heo
current_version: v1
patch_series: []
merge_assessment:
  likelihood: low
  blocking_issues:
  - 维护者偏好更简单替代（fork 晚赋值），作者补丁方向未收敛
  next_action: 作者按 Tejun/fork 晚赋值方向重探或论证原方案必要性
contribution_opportunities:
- kind: review
  description: 评估 fork 晚赋值是否消除与 setsid 竞态及代价
- kind: discussion
  description: 论证 autogroup 单度维护 sched_task_group 规则的必要性
upstream_commit: null
fixes_commit: null
merged_branch: null
source_email_count: 1
related_articles:
- sched-20261023-004
- sched-20261026-003
- sched-20261030-008
- sched-20261031-012
tags:
- autogroup
- cgroup
id: sched-20261102-020
subject: 'sched/autogroup: Fix task_group UAF during thread creation'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
---
