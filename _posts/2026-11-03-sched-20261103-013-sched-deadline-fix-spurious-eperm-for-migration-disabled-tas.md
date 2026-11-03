---
id: sched-20261103-013
date: 2026-11-03
subject: 'sched/deadline: Fix spurious -EPERM for migration-disabled tasks'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261102135420.244745-1-parri.andrea@gmail.com>
lore_url: https://lore.kernel.org/all/20261102135420.244745-1-parri.andrea@gmail.com/
authors:
- Andrea Parri
maintainers_involved:
- Juri Lelli
- Sebastian Andrzej Siewior
current_version: v1
patch_series:
- version: v1
  msgid: <20261102135420.244745-1-parri.andrea@gmail.com>
  date: 2026-11-02
  summary: cpus_ptr 改 cpus_mask，修 migrate_disable 段内误 -EPERM。
  review_outcome: Juri Ack + 建议挪 reproducer；Sebastian Reviewed + 指出相邻竞态。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - reproducer 需从 changelog 移出
  next_action: 作者把复现程序换成链接后等待收取。
contribution_opportunities:
- kind: review
  description: 跟进 setaffinity/setscheduler 的 dl_task_check_affinity 竞态。
- kind: testing
  description: PREEMPT_RT/无 RT 及非 pow2 CPU 数下复跑 reproducer。
generated_at: '2026-11-04T09:00:00+08:00'
source_email_count: 5
related_articles:
- sched-20261102-001
tags:
- deadline
- affinity
title: 'sched/deadline: Fix spurious -EPERM for migration-disabled tasks'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/11/02/sched-20261102-001-sched-deadline-fix-spurious-eperm-for-migration-disabled-tas.html">sched-20261102-001</a>：Andrea Parri 修复 `sched_setattr(SCHED_DEADLINE)` 在任务处于 `migrate_disable()` 段内时被误判「affinity 未覆盖 root domain」而返回 -EPERM 的问题，根因是 `__sched_setscheduler()` 检查了 `p->cpus_ptr`（会被 `migrate_disable_switch()` 临时指向当前 CPU）而非真正的 affinity `p->cpus_mask`。
- <a class="article-ref" href="/lkm/2026/11/03/sched-20261103-013-sched-deadline-fix-spurious-eperm-for-migration-disabled-tas.html">sched-20261103-013</a>（今天）：Juri Lelli 给出 Acked-by（建议把复现程序挪到其 sched-deadline-tests 仓库）；Sebastian Siewior 给出 Reviewed-by 并发现一个独立但相关的 affinity 竞态（`dl_task_check_affinity()` 在 setaffinity 路径的窗口）；作者同意挪复现、并将单独跟进该竞态——合入门槛已被维护者认可。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/02/sched-20261102-001-sched-deadline-fix-spurious-eperm-for-migration-disabled-tas.html">sched-20261102-001</a>）`sched_setattr()` 在任务被调度出去、处于 `migrate_disable()` 段内时，`migrate_disable_switch()` 把 `p->cpus_ptr` 指向当前 CPU 直到 `migrate_enable()`；而 `__sched_setscheduler()` 用 `p->cpus_ptr` 判断任务能否进 SCHED_DEADLINE（要求 affinity 覆盖整个 root domain），于是即便真实 affinity 覆盖 root domain 也被错误地以 -EPERM 拒绝。PREEMPT_RT 上每个 spinlock 持有者都在该段内，普通内核工作即可打开窗口。

## 技术方案

（承接 <a class="article-ref" href="/lkm/2026/11/02/sched-20261102-001-sched-deadline-fix-spurious-eperm-for-migration-disabled-tas.html">sched-20261102-001</a>）把检查改为测试 `p->cpus_mask`（任务真实 affinity，也是 `sched_getaffinity()` 报告的来源），安全性论证：已准入任务其 `cpus_mask` 覆盖 root domain，故 `migrate_enable()` 恢复 `cpus_ptr` 时 `set_cpus_allowed_dl()` 无需移动带宽。今日无代码变更，仅收集 Ack/Reviewed 与一个相邻竞态的确认。

## 版本演进与当前进展

*current_version: v1（2026-11-02 发出，msgid 20261102135420.244745-1-parri.andrea@gmail.com；今日仍在 v1）*。今日 Juri、Sebastian、Aaron 均表态，作者准备把复现程序从 changelog 移出。

## Maintainer 意见与讨论焦点

Juri Lelli（SCHED_DEADLINE 维护者）Acked：「fix makes sense to me」，只建议把 reproducer 挪到 https://github.com/jlelli/sched-deadline-tests。Sebastian Siewior Reviewed：「The task's cpus_ptr must share at least one CPU of cpus_mask... while in migrate_disable() it sees only one CPU via ->cpus_ptr while span may have two」，并指出 `sched_setaffinity()` 里 `dl_task_check_affinity()` 存在一个独立竞态窗口（setaffinity 见非 DL 任务、setscheduler 随后按旧宽 cpus_mask 准入、setaffinity 最后收缩），建议在 setaffinity 路径也到 rq lock 下检查。作者回应：竞态独立于本补丁（对 `p->cpus_ptr` 同样成立），`__set_cpus_allowed_ptr()` 第二次调用应保持不检查，将单独跟进。

## 合入评估

*likelihood=high*。维护者 Ack + Reviewed 已齐，方向无异议；只剩「reproducer 挪走」这一 changelog 层面的收尾。*next_action*：作者把复现程序换成链接（或移入 Juri 的测试仓库）后即可被收取。

## 效果评估

（承接 <a class="article-ref" href="/lkm/2026/11/02/sched-20261102-001-sched-deadline-fix-spurious-eperm-for-migration-disabled-tas.html">sched-20261102-001</a>）作者实测 4-CPU PREEMPT_RT guest 被拒率 55.4%/45.4%/42.5%、无 RT 时 23.6%/21.7%/23.7%，补丁后归 0。

## 我可以参与的点

- review：跟进 Sebastian 提出的 setaffinity/setscheduler affinity 竞态，评估把 `dl_task_check_affinity()` 移入 rq lock 后对 cpuset 交互的影响。
- testing：在 PREEMPT_RT / 无 RT、非 pow2 CPU 数下复跑 reproducer。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261102135420.244745-1-parri.andrea@gmail.com/
