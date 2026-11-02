# sched: Fix cpuset_mutex double unlock in __sched_setscheduler()

## TL;DR

Andrea Parri 修复 `__sched_setscheduler()` 在重入（recheck label）路径上对 `cpuset_mutex` 的二次解锁：`sched_setattr(SCHED_FLAG_KEEP_POLICY)` 作用在 SCHED_DEADLINE 任务上、且并发改策略时会 drop 锁并 restart，但 `cpuset_locked` 标志未清，导致出口二次 `cpuset_unlock()`。DEBUG_MUTEXES 下报 bad unlock balance，PREEMPT_RT 下几秒内 crash；会破坏 cpuset_mutex 的 owner 语义。修复为 drop 锁时同时清 `cpuset_locked`。

## 背景与问题

`__sched_setscheduler()` 在取任何锁之前采样 `p->policy`，若在 rq lock 下发现 `p->policy` 已变化就从 recheck label 重来。重来会 drop `cpuset_mutex` 却不清 `cpuset_locked` 标志，于是后续一轮不再需要该锁的路径也照样在出口 `cpuset_unlock()`：`CONFIG_DEBUG_MUTEXES` 报 bad unlock balance，`PREEMPT_RT` 上二次解锁清空 owner 字段、使其他任务在其临界区内丢失 `cpuset_mutex`，作者称「seconds 内 crash」。进入 SCHED_DEADLINE 需要 CAP_SYS_NICE，但一个拥有该任务（采样到非 DEADLINE 策略）的并发调用者不需要。

## 技术方案

在 drop mutex 的 restart 处清 `cpuset_locked`。安全性：该标志只在下一轮离开时的路径上被测试，而下一轮若取了锁会重新置位。

## 版本演进与当前进展

v1 刚发出（2026-11-02），暂无 review。

## Maintainer 意见与讨论焦点

尚无表态。本补丁与同一天 Parri 的另两封（spurious -EPERM、uclamp clamp 校验）同批发布，均属 SCHED_DEADLINE/sched_setattr 边界正确性修复，等待维护者集中 review。

## 合入评估

likelihood=medium。根因清晰、修复最小，但尚无 maintainer 确认；PREEMPT_RT 上会 crash 使其具备较高优先级，作者宜补充 `Fixes:` 指向引入 recheck 路径的 commit。

## 效果评估

作者程序（root）复现 splat，应用补丁后消失；PREEMPT_RT 下的 kernel crash 也随之修复。

## 我可以参与的点

- testing：在 PREEMPT_RT（CONFIG_DEBUG_RT_MUTEXES）与常规 DEBUG_MUTEXES 配置下复现并验证。
- review：确认 recheck 路径是否还存在其它「drop 锁但状态未复位」的资源（如 rq lock / raw_spinlock 的嵌套）。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261102134606.242743-1-parri.andrea@gmail.com/

---
type: fix
status: under_review
severity: high
thread_root_msgid: <20261102134606.242743-1-parri.andrea@gmail.com>
authors:
- Andrea Parri
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261102134606.242743-1-parri.andrea@gmail.com>
  date: '2026-11-02'
  summary: recheck 路径 drop cpuset_mutex 时清 cpuset_locked，避免出口二次解锁
  review_outcome: 暂无 review
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 暂无 maintainer 回帖、Fixes 未标注
  next_action: 补 Fixes 标签并等 sched 维护者确认
contribution_opportunities:
- kind: testing
  description: PREEMPT_RT/DEBUG_MUTEXES 配置下复现验证
- kind: review
  description: 排查 recheck 路径其它锁状态未复位隐患
upstream_commit: null
fixes_commit: null
merged_branch: null
source_email_count: 1
related_articles: []
tags:
- cgroup
- deadline
- rt
id: sched-20261102-003
subject: 'sched: Fix cpuset_mutex double unlock in __sched_setscheduler()'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
---
