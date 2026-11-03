# sched: Fix cpuset_mutex double unlock in __sched_setscheduler()

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261102-003：Andrea Parri 修复 `__sched_setscheduler()` 在 recheck 路径上对 `cpuset_mutex` 的二次解锁：drop 锁重来却不清 `cpuset_locked` 标志，导致出口二次 `cpuset_unlock()`（DEBUG_MUTEXES 报 bad unlock balance，PREEMPT_RT 下几秒内 crash）。
- sched-20261103-014（今天）：Juri Lelli 给出 Reviewed-by（仅建议把 reproducer 挪到其测试仓库）；作者同意——合入门槛满足。

## 背景与问题

（承接 sched-20261102-003）`__sched_setscheduler()` 取锁前采样 `p->policy`，在 rq lock 下发现策略已变就从 recheck label 重来；重来会 drop `cpuset_mutex` 却不清 `cpuset_locked`，于是下一轮不需要该锁的路径也照样在出口 `cpuset_unlock()`：`CONFIG_DEBUG_MUTEXES` 报 bad unlock balance，`PREEMPT_RT` 上二次解锁清空 owner 字段、使其他任务在自己临界区丢锁，作者称几秒内 crash。

## 技术方案

（承接 sched-20261102-003）在 drop mutex 的 restart 处清 `cpuset_locked`；该标志只在下一轮出口路径被测试，下一轮若取锁会重新置位。今日无代码变更，仅收集 Reviewed-by。

## 版本演进与当前进展

*current_version: v1（2026-11-02 发出，msgid 20261102134606.242743-1-parri.andrea@gmail.com；今日仍 v1）*。今日 Juri 表态并准备把 reproducer 挪走。

## Maintainer 意见与讨论焦点

Juri Lelli（SCHED_DEADLINE 维护者）Reviewed：「The fix looks good to me」，同样建议 reproducer 是否放进 sched-deadline-tests 仓库更易运行。无分歧。

## 合入评估

*likelihood=high*。维护者 Reviewed 已到，PREEMPT_RT crash 使其具备高优先级；只剩 changelog 里 reproducer 去留的收尾。*next_action*：作者把 reproducer 换成链接（或纳入 Juri 测试仓库），可选补 `Fixes:` 指向引入 recheck 路径的 commit。

## 效果评估

（承接 sched-20261102-003）作者程序复现 splat、应用补丁后消失，PREEMPT_RT 下 crash 随之修复。

## 我可以参与的点

- review：确认 recheck 路径是否还有其它「drop 锁但状态未复位」的资源。
- testing：PREEMPT_RT（DEBUG_RT_MUTEXES）与常规 DEBUG_MUTEXES 配置下复现验证。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261102134606.242743-1-parri.andrea@gmail.com/

---
id: sched-20261103-014
date: 2026-11-03
subject: "sched: Fix cpuset_mutex double unlock in __sched_setscheduler()"
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: "<20261102134606.242743-1-parri.andrea@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261102134606.242743-1-parri.andrea@gmail.com/"
authors: [Andrea Parri]
maintainers_involved: [Juri Lelli]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261102134606.242743-1-parri.andrea@gmail.com>"
    date: 2026-11-02
    summary: "recheck 路径 drop cpuset_mutex 时同步清 cpuset_locked。"
    review_outcome: "Juri Reviewed + 建议挪 reproducer。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["reproducer 去留收尾"]
  next_action: "reproducer 换成链接，可选补 Fixes 标签后等待收取。"
contribution_opportunities:
  - kind: review
    description: "确认 recheck 路径无其它 drop 锁未复位资源。"
  - kind: testing
    description: "PREEMPT_RT / DEBUG_MUTEXES 配置下复现验证。"
generated_at: "2026-11-04T09:00:00+08:00"
source_email_count: 3
related_articles: [sched-20261102-003]
tags: [deadline, cgroup]
---