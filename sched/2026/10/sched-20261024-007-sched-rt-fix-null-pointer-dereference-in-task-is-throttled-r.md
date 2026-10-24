# sched/rt: Fix NULL pointer dereference in task_is_throttled_rt()

## TL;DR
Aamir Ahmed 提交的 RT 类空指针解引用修复：当 `CONFIG_RT_GROUP_SCHED=y` 但运行时禁用（`rt_group_sched=0` 或默认禁用）时，`alloc_rt_sched_group()` 提前返回使非 root 任务组的 `tg->rt_rq` 为 NULL，而 `task_is_throttled_rt()` 仍无条件解引用 `task_group(p)->rt_rq[cpu]`，在 `CONFIG_SCHED_CORE=y` 下对带 core cookie 的 RT 任务触发持 rq 锁的 oops。修复改用 root rt_rq 并删掉无意义的 WARN_ON。带 `Fixes:` 与 `Cc: stable # v6.16+`，v1 刚发、尚无 review。

## 背景与问题
当 `CONFIG_RT_GROUP_SCHED=y` 但 RT 组调度在运行时被禁用（`rt_group_sched=0` 或 `CONFIG_RT_GROUP_SCHED_DEFAULT_DISABLED=y`）时，`alloc_rt_sched_group()` 提前返回、不为非 root 任务组分配 `rt_rq`，所有 RT 实体都排到 root rt_rq 上（见 `set_task_rq()`）。但 `task_is_throttled_rt()` 无条件解引用 `task_group(p)->rt_rq[cpu]`，后面的 `WARN_ON()` 又再次解引用同一结果。在 `CONFIG_SCHED_CORE=y` 下，该函数会被 `sched_core_find()`/`sched_core_next()`（pick、balance、steal 路径）对 cookie 匹配的任务调用，因此一个在非 root cpu cgroup 里带 core cookie 的 RT 任务会持 rq 锁触发 NULL 指针解引用 oops。

## 技术方案
单补丁（`kernel/sched/rt.c`，+8/-2）：在 `CONFIG_RT_GROUP_SCHED` 分支内，若 `rt_group_sched_enabled()` 为真则用 `task_group(p)->rt_rq[cpu]`，否则改用 `&cpu_rq(cpu)->rt`（root rt_rq），与 `set_task_rq()` 及 `!CONFIG_RT_GROUP_SCHED` 情形对齐；并删除不再检查任何东西的 `WARN_ON(!rt_group_sched_enabled() && rt_rq->tg != &root_task_group)`。作者在注释里提到可考虑加 `task_rt_rq()` 辅助函数（见 `sched_rt_period_rt_rq`）。

## 版本演进与当前进展
*current_version: v1*（`<AS8P251MB000128A749C33C6B0758F934C8632@AS8P251MB0001.EURP251.PROD.OUTLOOK.COM>`）。当日发出，暂无 review。

## Maintainer 意见与讨论焦点
暂无维护者回帖。系列带 `Fixes: d6809c2f606c`（"sched: Do not construct nor expose RT_GROUP_SCHED structures if disabled"）与 `Cc: stable@vger.kernel.org # v6.16+`，暗示作者认为该空指针问题自该提交引入且值得回合 stable。

## 合入评估
*likelihood=medium*。真实 oops 修复、带 Fixes 与 stable Cc，方向明确；但涉及 core sched 的 RT throttle 路径、v1 刚发且尚无 sched 维护者 review。*blocking_issues*：无 review；需确认 `task_rt_rq()` 辅助函数（作者注释中作为 TODO）是否应一并引入。*next_action*：等 Peter/sched 维护者 review 并决定是否引入辅助函数后收取。

## 效果评估
无量化数据。作者描述了触发条件与 oops 症状（持 rq 锁 NULL 解引用），未提供复现或性能数据。

## 我可以参与的点
- *kind: review*：核对 `task_is_throttled_rt()` 各调用点（core sched pick/balance/steal）在两种 rt_rq 选择下语义是否一致。
- *kind: testing*：在 `CONFIG_RT_GROUP_SCHED=y` + 运行时禁用 + `CONFIG_SCHED_CORE=y` + core cookie 的配置下复现并验证修复。

## 参考链接
- patch: https://lore.kernel.org/all/AS8P251MB000128A749C33C6B0758F934C8632@AS8P251MB0001.EURP251.PROD.OUTLOOK.COM/

---
id: sched-20261024-007
date: 2026-10-24
subject: 'sched/rt: Fix NULL pointer dereference in task_is_throttled_rt()'
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: '<AS8P251MB000128A749C33C6B0758F934C8632@AS8P251MB0001.EURP251.PROD.OUTLOOK.COM>'
lore_url: 'https://lore.kernel.org/all/AS8P251MB000128A749C33C6B0758F934C8632@AS8P251MB0001.EURP251.PROD.OUTLOOK.COM/'
authors:
  - 'Aamir Ahmed'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<AS8P251MB000128A749C33C6B0758F934C8632@AS8P251MB0001.EURP251.PROD.OUTLOOK.COM>'
    date: 2026-10-24
    summary: '运行时禁用 RT 组调度时改用 root rt_rq，删除无意义 WARN_ON'
    review_outcome: '暂无 review'
upstream_commit: null
fixes_commit: 'd6809c2f606c'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - '无维护者 review'
    - '是否引入 task_rt_rq() 辅助函数未定'
  next_action: '等 sched 维护者 review 并决定是否引入辅助函数后收取'
contribution_opportunities:
  - kind: review
    description: '核对 core sched 各调用点在两种 rt_rq 选择下语义一致'
  - kind: testing
    description: '在 RT_GROUP_SCHED=y + 运行时禁用 + SCHED_CORE=y + core cookie 配置下复现验证'
generated_at: '2026-10-25T01:00:00'
source_email_count: 1
related_articles: []
tags:
  - rt
  - crash
  - core_sched
---