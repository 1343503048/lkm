# sched/stats: Fix run_delay over-count for proxy-migrated blocked donors

## TL;DR

修复 proxy execution 下 blocked donor 迁移到 owner CPU 后 `/proc/<tid>/schedstat` 的 run_delay 字段被重复计数的问题。作者 Wei Yang 给出了带测试数据的完整方案，并建议把 DELAY_DEQUEUE 与 proxy 两处修复拆成独立补丁以便 backport。

## 背景与问题

run_delay（`/proc/<tid>/schedstat` 第 2 字段）用于反映任务等待 CPU 的时间。proxy execution 下，被 `is_blocked` 的 donor 迁移到 owner 的 CPU 后，`sched_info_dequeue/enqueue` 的 `last_queued` 记账会把等待时间重复累计。作者分别构造了「proxy exec donor 迁移（约 170ms block）」与「DELAY_DEQUEUE sleeper 跨 CPU 迁移（约 150ms sleep）」两组复现：未打补丁时 run_delay 被多计约 167ms/147ms，打补丁后归零。

## 技术方案

核心改动在 `kernel/sched/core.c` 与 `kernel/sched/stats.h`：1) `ttwu_runnable()` 中在 `wakeup_preempt()` 之后补 `sched_info_enqueue(rq, p)`（覆盖 donor 已回到 `p->wake_cpu` 的场景）；2) `sched_info_dequeue()` 里若 `t->is_blocked` 则先清零 `last_queued`；3) `sched_info_enqueue()` 里若 `!last_queued || t->is_blocked` 则重记 `last_queued = rq_clock(rq)`。作者同时说明 `p==current` 无需调用（`try_to_wake_up()` 对 `se.sched_delayed` 与 `is_blocked` 都会 WARN_ON_ONCE，说明该任务在跑而非等待）。关于 backport：`p->is_blocked` 于 `4c2a20413d7f`（v7.2-rc1）引入，而 DELAY_DEQUEUE 的过度计数可追溯到 v6.12 的 `152e11f6df29`，若合并进同一补丁则无法构建/backport 到 v6.12.y..v7.1.y，故建议拆分。

## 版本演进与当前进展

作者此前已把 DELAY_DEQUEUE 修复作为独立 v4 提交（https://lore.kernel.org/all/20261024042753.2276779-1-albin_yang@163.com/ ），本窗口内的 proxy 修复（`[PATCH] sched/stats: Fix run_delay over-count for proxy-migrated blocked donors`）处于 v1，作者在回帖中贴出完整 diff 与测试结果，并向 reviewers 询问拆分建议。

## Maintainer 意见与讨论焦点

reviewers Prateek、Kayra、Peter（正文仅给名字，Peter 应为维护者）均已 review：Peter 要求补注释，Kayra 追问注释是否已加、并认同拆分合理性（「makes sense to me if the other issue exists on older versions」）。作者接受「`p==current` 无需调用」的意见，并同意在 proxy gate 上弃用自己原来的 `!task_is_blocked()`（Prateek 的版本已覆盖同样范围）。未解决项：原始 PATCH 的拆分方式待定。

## 合入评估

可能性中等（medium）。修复有完整测试数据支撑、review 已多轮，但 Peter 要求的注释尚未补齐、拆分方案待确认。阻塞项：注释补充 + DELAY_DEQUEUE/proxy 拆分方案。作者尚未复现「donor 已回到 p->wake_cpu」的时序敏感路径（`ttwu_runnable()` 调用动机），但表示不阻塞本补丁。

## 效果评估

作者实测（run_delay 为 `/proc/<tid>/schedstat` 第 2 字段）：proxy exec donor 迁移场景未打补丁 167.07–167.09ms（5/5 迁移）、打补丁 0.00ms（20/20 迁移）、same-cpu 0.00ms（0/5 未迁移）；DELAY_DEQUEUE sleeper 迁移未打补丁 147.94–147.99ms（5/20）、打补丁 0.00ms（0/100）。两场景的记账本身保持存活（自校验通过）。

## 我可以参与的点

- testing：复现作者未覆盖的「donor 已回到 p->wake_cpu」时序敏感路径（需 owner 迁移中途 + donor 跟随）。
- review：参与 DELAY_DEQUEUE 与 proxy 两处修复的拆分方案讨论。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261101143101.353033-1-albin_yang@163.com/
- DELAY_DEQUEUE 修复 v4: https://lore.kernel.org/all/20261024042753.2276779-1-albin_yang@163.com/
- 原始 PATCH v1 msgid: 未获取到（补丁发送早于本次拉取窗口）

---
id: sched-20261101-005
subject: "sched/stats: Fix run_delay over-count for proxy-migrated blocked donors"
date: 2026-11-01
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261101143101.353033-1-albin_yang@163.com>"
lore_url: "https://lore.kernel.org/all/20261101143101.353033-1-albin_yang@163.com/"
authors: [Wei Yang]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: null
    date: 2026-11-01
    summary: "修复 proxy 迁移 blocked donor 的 run_delay 过度计数，附完整 diff 与两组复现测试"
    review_outcome: "Prateek/Kayra/Peter 已 review；Peter 要求补注释，拆分方案待定"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "Peter 要求补充的注释尚未加入"
    - "DELAY_DEQUEUE 与 proxy 两处修复的拆分方式待确认"
  next_action: "作者按建议把 DELAY_DEQUEUE 与 proxy 修复拆为独立补丁并补上注释后重发"
contribution_opportunities:
  - kind: testing
    description: "复现作者未覆盖的 donor 已回到 p->wake_cpu 时序敏感路径"
  - kind: review
    description: "参与 DELAY_DEQUEUE 与 proxy 修复的拆分方案讨论"
generated_at: "2026-11-02T09:00:00"
source_email_count: 2
related_articles: []
tags: [proxy_execution, eevdf]
---