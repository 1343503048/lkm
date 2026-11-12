# sched: ITMT + DELAY_DEQUEUE: woken task waits ~1 ms behind another task on the preferred CPU while allowed CPUs are idle

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261105-011：Francesco Nigro 报告的 bug——ITMT + DELAY_DEQUEUE 下被唤醒任务在 preferred CPU 上等约 1ms 而其它允许的 CPU 空闲；K Prateek Nayak 初诊为 idle 平衡器迁移 delayed 任务与并发唤醒之间的竞态，但根因未收敛。
- sched-20261112-020（今天）：**根因被 Francesco 的 raw perf trace 证实为 migration 线程把任务迁到 idle CPU**（`sched_migrate_task 481 orig_cpu=7 dest_cpu=6` 后 `swapper/6 → 481`）；**Vincent Guittot 提出修复方向**——在 `can_migrate_task()` 里禁止 newly_idle 平衡迁移 delayed 任务；**Peter Zijlstra 更进一步**——迁移到新 idle CPU 时直接 dequeue 它、把 lag 丢掉。修复方向收敛，尚无正式补丁。

## 背景与问题

（承接 sched-20261105-011）ITMT 使不同 CPU 算力不等、调度器优先把任务放「preferred CPU」；DELAY_DEQUEUE 让被唤醒任务延迟出队。两者叠加时，delayed 任务在 newly_idle 负载均衡里被迁到 preferred CPU，瞬时让该 CPU 对并发唤醒的任务不再 idle。Francesco 今日给出 raw perf 证据：`sched_migrate_task 481 orig_cpu=7 dest_cpu=6` 之后 `swapper/6 → 481`，证实是 migration 线程把任务 481 迁到 CPU 6（而非此前推测的 active balance 迁「正在运行」任务）。

## 技术方案

修复方向（尚无正式补丁，维护者口头达成）：

- **Vincent Guittot**：在 `can_migrate_task()` 里，对 delayed 任务禁止 newly_idle 情形的迁移——「把 delayed 任务迁到 newly idle CPU 不合理：它会是唯一被迁的任务且会被立即 dequeue」。附带给出 `if ((p->se.sched_delayed) && (env->migration_type != migrate_load))` 的改动示意。
- **Peter Zijlstra**：更进一步——「干脆当场就把它 dequeue。它如果真 runnable 就会在新 idle CPU 上跑；因此它不再 contended，lag 可以直接丢掉」。
- **Vincent**：认同「可以更进一步」。

## 版本演进与当前进展

*current_version: 无正式补丁（诊断 + 修复方向）*。今日从「根因之争」收敛为「迁移 delayed 任务治本」——Francesco 的 raw trace 钉死迁移路径，Vincent/Peter 对修复方式达成一致。

## Maintainer 意见与讨论焦点

- **Vincent Guittot（sched/fair 维护者）**：提出在 `can_migrate_task()` 禁 newly_idle 迁移 delayed 任务，并认可 Peter 的「直接 dequeue」更彻底。
- **Peter Zijlstra（sched 维护者）**：主张迁移时直接 dequeue 并丢 lag（「若它真 runnable 就会跑起来」）。
- **Francesco Nigro（报告者）**：补 raw perf 数据钉死 migration 路径（`migration/7` 迁 481 到 CPU 6）。
- 无 NAK；此前的根因分歧（idle/newidle vs active balance vs migration 线程）已收敛。

## 合入评估

*likelihood=medium*。根因已收敛、维护者修复方向一致，但尚无正式补丁，且「迁移时 dequeue 丢 lag」对 DELAY_DEQUEUE 记账的影响需在 patch 里严谨处理。*blocking_issues*：正式补丁待发；dequeue 与 DELAY_DEQUEUE 的 lag/记账交互需验证。*next_action*：Vincent/Peter 发正式补丁（can_migrate 禁迁 + 迁移时 dequeue），并在 ITMT + DELAY_DEQUEUE 环境验证 1ms 等待消除。

## 效果评估

Francesco 提供量化症状（承接 20261105-011）：约 1ms 唤醒延迟（sch delay 0.224ms），270/286 次 ≥0.5ms 等待中 worker 未离开 CPU 6 且 CPU 4/5/7 至少 98% 空闲。今日补充 raw perf 事件序列钉死 `migration/7` 迁 481 到 CPU 6。暂无修复后对比数据。

## 我可以参与的点

- **testing**：在 ITMT + DELAY_DEQUEUE 环境验证「can_migrate 禁迁 delayed 任务」与「迁移时 dequeue」两个方案是否消除 1ms 等待且无跨 NUMA 迁移回归。
- **review**：复核「迁移时 dequeue 丢 lag」对 EEVDF 记账（`h_nr_runnable`/lag）的影响——这是 Peter 方案落地前的关键正确性点。

## 参考链接

- lore thread（报告）: https://lore.kernel.org/all/20261103154603.1893325-1-nigro.fra@gmail.com/
- Vincent 的修复方向: https://lore.kernel.org/all/CAKfTPtCGmZQ9XVYJL_5f603qTf6_CdeKsq_pAYM_Ldqs3NaXaA@mail.gmail.com/
- Peter 的「直接 dequeue」: https://lore.kernel.org/all/20261112093613.GJ2668804@noisy.programming.kicks-ass.net/

---
id: sched-20261112-020
date: '2026-11-12'
subject: "sched: ITMT + DELAY_DEQUEUE: woken task waits ~1 ms behind another task on the preferred CPU while allowed CPUs are idle"
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: "<20261103154603.1893325-1-nigro.fra@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261103154603.1893325-1-nigro.fra@gmail.com/"
authors: [Francesco Nigro]
maintainers_involved: [Vincent Guittot, Peter Zijlstra]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261103154603.1893325-1-nigro.fra@gmail.com>"
    date: '2026-11-03'
    summary: "REPORT：ITMT + DELAY_DEQUEUE 下唤醒任务等约 1ms 而其它 CPU 空闲"
    review_outcome: "根因收敛为迁移 delayed 任务；Vincent/Peter 修复方向一致，待正式补丁"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["正式补丁待发", "dequeue 与 DELAY_DEQUEUE 的 lag/记账交互需验证"]
  next_action: "Vincent/Peter 发正式补丁并在 ITMT + DELAY_DEQUEUE 环境验证"
contribution_opportunities:
  - kind: testing
    description: "ITMT + DELAY_DEQUEUE 环境验证两个修复方案消除 1ms 等待且无回归"
  - kind: review
    description: "复核迁移时 dequeue 丢 lag 对 EEVDF 记账的影响"
generated_at: "2026-11-13T09:00:00+08:00"
source_email_count: 4
related_articles: [sched-20261105-011]
tags: [cfs, load_balance, x86]
---