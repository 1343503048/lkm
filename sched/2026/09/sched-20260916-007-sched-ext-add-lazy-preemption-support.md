# sched_ext: Add lazy preemption support

## TL;DR
Andrea Righi 的 v5：给 sched_ext 增加懒惰抢占语义——新增 `SCX_ENQ_PREEMPT_LAZY` / `SCX_KICK_PREEMPT_LAZY` / `SCX_OPS_LAZY_SLICE_EXPIRY` 与 `scx_bpf_task_set_slice_expiry()`，让 BPF 调度器能像 fair class 一样把调度边界推迟到返回用户态或下一次 tick。v5 只做了一处 kselftest 修正（静态懒抢占检测，回应 Cheng-Yang Chou）。整套 selftest 在 `preempt=lazy` 与 `nohz_full` 下全绿，合入概率高。

## 背景与问题
fair class 能通过 lazy rescheduling 推迟内核内的调度边界，但 sched_ext 目前只暴露立即抢占，BPF 调度器无法做同样的权衡取舍。目标是补齐这一能力，同时覆盖 `NO_HZ_FULL` 上无限 slice 任务 tick 已停的场景。

## 技术方案
新增一组懒抢占原语：`SCX_ENQ_PREEMPT_LAZY` 与 `SCX_KICK_PREEMPT_LAZY` 会清掉当前 sched_ext 任务的 slice 但请求懒 reschedule；立即抢占、WAIT 与普通 kick 在组合请求时优先。`SCX_OPS_LAZY_SLICE_EXPIRY` 作为新启用任务的默认 expiry 策略，`scx_bpf_task_set_slice_expiry()` 允许调度器逐任务覆盖。关键细节：对无限 slice 的 `NO_HZ_FULL` 任务，懒请求会先恢复 tick 依赖（`scx_resched_curr_lazy()`）以保证由真实 tick 提升为立即抢占，避免前向进展丢失。

## 版本演进与当前进展
- **v5**（本日 105386，`<20260915194611.2674127-1-arighi@nvidia.com>`）：仅修正 kselftest——当 `CONFIG_PREEMPT_DYNAMIC` 关闭且 `sched/preempt` debugfs 不可用时检测静态懒抢占（Cheng-Yang Chou）。
- v4→v3→v2 回顾：v4 处理了 `SCX_KICK_WAIT` 与 `SCX_KICK_PREEMPT_LAZY` 组合的同步、tick 依赖恢复、selftest 规范（Sashiko）；v2 按 Tejun Heo 意见把懒 slice expiry 做成逐任务属性、恢复 `NO_HZ_FULL` tick 依赖、独立累积并解析 kick 优先级。完整背景见 sched-20260914-006 / sched-20260915-002。

## Maintainer 意见与讨论焦点
- 设计核心由 **Tejun Heo** 在 v2 阶段定型（逐任务 expiry、tick 依赖恢复、kick 优先级解析）。
- **Sashiko**、**Cheng-Yang Chou** 在 v3~v5 持续提 selftest 与语义修正意见，均已落实到 v5。
- 无 NAK；本日 v5 尚未见新的反对意见。

## 合入评估
*likelihood=high*。功能方向明确、selftest 覆盖全面（含 `NO_HZ_FULL` 无限 slice 前向进展、非法 flag 与优先级组合），改动已收敛到只有 kselftest 层面的 v5 修正，merget 窗口面向 sched_ext/for-7.4。*blocking_issues*：无。*next_action*：待 Tejun 评审 v5 并收入 for-7.4。

## 效果评估
selftest 结果（cover）：`vng -a "preempt=lazy"` 下 kick 组 6 PASSED / 0 FAILED；`preempt=lazy nohz_full=8-15` 下 nohz_tick PASSED，CPU8 收到 7 个有限 slice tick。属功能验证，无性能对比数据。

## 我可以参与的点
- kind=testing：在真实 `NO_HZ_FULL` 生产配置下跑 nohz_tick，验证懒 enqueue/kick 对无限 slice 任务的 tick 重启与前向进展。
- kind=review：核对 `scx_resched_curr_lazy()` 恢复 tick 依赖后与 `rq->clock_update_flags` 的交互是否正确（避免冗余 rq clock 更新）。

## 参考链接
- v5 cover：https://lore.kernel.org/all/20260915194611.2674127-1-arighi@nvidia.com/

---
id: sched-20260916-007
date: '2026-09-16'
subject: 'sched_ext: Add lazy preemption support'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20260915194611.2674127-1-arighi@nvidia.com>'
lore_url: 'https://lore.kernel.org/all/20260915194611.2674127-1-arighi@nvidia.com/'
authors:
  - 'Andrea Righi'
maintainers_involved:
  - 'Tejun Heo'
current_version: v5
patch_series:
  - version: v5
    msgid: '<20260915194611.2674127-1-arighi@nvidia.com>'
    date: '2026-09-15'
    summary: 'kselftest 修正：CONFIG_PREEMPT_DYNAMIC 关闭时检测静态懒抢占'
    review_outcome: '回应 Cheng-Yang Chou 意见，selftest 全绿'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: '待 Tejun 评审 v5 并收入 for-7.4'
contribution_opportunities:
  - kind: testing
    description: '在真实 NO_HZ_FULL 配置下验证无限 slice 任务的 tick 重启与前向进展'
  - kind: review
    description: '核对 scx_resched_curr_lazy() 恢复 tick 依赖与 rq clock 更新的交互'
generated_at: '2026-09-17T09:00:00'
source_email_count: 3
related_articles:
  - sched-20260915-002
tags:
  - sched_ext
  - preempt
---