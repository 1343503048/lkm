---
id: sched-20261105-011
date: 2026-11-05
subject: 'sched: ITMT + DELAY_DEQUEUE: woken task waits ~1 ms behind another task
  on the preferred CPU while allowed CPUs are idle'
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: <20261103154603.1893325-1-nigro.fra@gmail.com>
lore_url: https://lore.kernel.org/all/20261103154603.1893325-1-nigro.fra@gmail.com/
authors:
- Francesco Nigro
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261103154603.1893325-1-nigro.fra@gmail.com>
  date: 2026-11-03
  summary: REPORT：ITMT + DELAY_DEQUEUE 下唤醒任务等约 1ms 而其它 CPU 空闲。
  review_outcome: K Prateek 诊断为 idle 平衡竞态并给试验 diff；根因仍在收敛。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 根因（idle 平衡竞态 vs active balance）未收敛
  - 试验性 diff 未充分验证
  next_action: K Prateek 周末复现并验证 diff2，必要时拉入 DELAY_DEQUEUE/ITMT 作者对齐
contribution_opportunities:
- kind: testing
  description: 在 ITMT + DELAY_DEQUEUE 环境复现并验证 can_migrate_task diff2 的效果
- kind: discussion
  description: 协助厘清 asym_active_balance 在单任务 CPU 上触发的原因
generated_at: '2026-11-06T09:00:00+08:00'
source_email_count: 4
related_articles: []
tags:
- cfs
- load_balance
- x86
title: 'sched: ITMT + DELAY_DEQUEUE: woken task waits ~1 ms behind another task on
  the preferred CPU while allowed CPUs are idle'
layout: article
---

## TL;DR

Francesco Nigro 报告的 bug：在启用 ITMT（Intel Turbo Boost Max 3.0，非对称算力）+ DELAY_DEQUEUE 的环境里，被唤醒任务会在首选 CPU 上等约 1ms 落在另一任务之后，即便允许的其它 CPU 全部空闲。K Prateek Nayak（AMD）初步定位为 idle 平衡器把 delayed 任务迁到首选 CPU、与同一 CPU 上并发唤醒之间的竞态，已给出两版试验性补丁并承诺周末自行复测；尚未有最终修复。

## 背景与问题

报告场景（`[REPORT]` 邮件）：ITMT 使不同 CPU 算力不等，调度器会优先把任务放到「preferred CPU」；DELAY_DEQUEUE 让被唤醒的任务延迟出队以等待可能复用。两者叠加时出现：被唤醒任务在 preferred CPU 上等约 1ms 才在另一任务之后运行，而允许的其它 CPU（4/5/7）这段时间 98% 空闲。Francesco 用 `perf sched timehist` 观察到一个 0.5ms+ 的等待样本里「两个 worker 谁都没离开 CPU 6」，怀疑是 active balance 把「正在运行的任务」迁走了。

## 技术方案

K Prateek Nayak 的初步诊断与实验性补丁（基于 v7.4-rc1，轻度测试）：

- 判断是 idle/newidle 平衡器（此时才看 asym 优先级）与落在同一 CPU 的唤醒之间的竞态，导致任务瞬时堆叠到同一 idle CPU。他回溯与 Vincent（OSPM）曾讨论过「应在 idle 迁移时 block 掉 delayed 任务，并用 wakelist 把激活卸载到远端 idle CPU」。
- 试验 diff 1：在 `include/linux/sched.h` 里为 delayed 任务迁移加开关/屏蔽。
- follow-up diff 2：改 `can_migrate_task()`，允许 delayed dequeue 任务在「迁移到 idle CPU」时也参与迁移（原注释只允许 migrate-load 时迁 delayed 任务）。

Francesco 反馈：`perf sched` 显示被迁的是「正在运行」的任务（经 active balance），并非 idle/newidle 路径的 delayed 任务；270/286 次 ≥0.5ms 的等待里两 worker 都没离开 CPU 6。K Prateek 表示难以理解为何 `asym_active_balance()` 会在 worker 482 block 前触发（此时 482 是 CPU 上唯一任务不应被延迟），继续跟进。

## 版本演进与当前进展

*current_version: 无正式补丁（诊断 + 试验性 diff）*。报告（11-03）→ K Prateek 初诊与 diff1（今日）→ Francesco 提供 perf sched 反证 active balance 路径 → K Prateek 补 diff2 并称周末自行复测。

## Maintainer 意见与讨论焦点

无调度维护者直接表态。讨论在报告人（Francesco Nigro）与 AMD 调度工程师 K Prateek Nayak 之间，核心分歧：竞态到底发生在 idle/newidle 平衡（K Prateek 初判）还是 active balance（Francesco 的 perf sched 证据）。delayed 任务迁移到 idle CPU 是否应放开的 `can_migrate_task()` 改动尚未定论。

## 合入评估

*likelihood=unknown*。尚无正式修复与根因定论，诊断仍在进行。*blocking_issues*：① 根因（idle 平衡竞态 vs active balance）尚未收敛；② 试验性 diff 未经充分验证。*next_action*：K Prateek 周末自行复现并验证 diff2，必要时拉入 DELAY_DEQUEUE/ITMT 相关作者对齐根因。

## 效果评估

Francesco 提供量化症状：约 1ms 的唤醒延迟（preferred CPU 上等 1.006ms，sch delay 0.224ms）；270/286 次 ≥0.5ms 等待中 worker 未离开 CPU 6 且 CPU 4/5/7 至少 98% 空闲。复现脚本放于 github（itmt-delay-dequeue-repro）。暂无修复后的对比数据。

## 我可以参与的点

- testing：在 ITMT + DELAY_DEQUEUE 环境下复现并验证 K Prateek 的 `can_migrate_task()` diff2 是否消除 1ms 等待。
- discussion：协助厘清 `asym_active_balance()` 在单任务 CPU 上为何会触发（Francesco 的 perf sched 证据与 K Prateek 的期望冲突之处）。

## 参考链接

- lore thread（报告）: https://lore.kernel.org/all/20261103154603.1893325-1-nigro.fra@gmail.com/
- Francesco 的 trace 摘要仓库: https://github.com/franz1981/itmt-delay-dequeue-repro/tree/827b6b2
