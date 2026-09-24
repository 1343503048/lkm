---
id: sched-20260914-005
date: '2026-09-14'
subject: 'sched/cache: Keep nr_pref_llc_running in the runnable domain'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260910220331.1209469-1-kayracizmeci@gmail.com>
lore_url: https://lore.kernel.org/all/aqdVpO66OfmHvvqB@chenyu-dev/
authors:
- Kayra Cizmeci
maintainers_involved:
- Chen Yu
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Tim Chen 对注释版 patch 1 的复核未回
  - 随 Fixes 系列 v2 打包推进，PeterZ 对系列整体意见仍是前提
  next_action: 等 Tim 复核注释版 patch 1；随 Fixes v2 一并推进合入
contribution_opportunities:
- kind: review
  description: 核对 case 2 的 DO-NOT-DECREASE/DO-NOT-INCREASE 与 account_llc_* 实现一致性
- kind: testing
  description: DELAY_DEQUEUE + active balance 压力下验证计数不重不漏
generated_at: '2026-09-15T09:30:00'
source_email_count: 2
related_articles:
- sched-20260911-003
- sched-20260828-004
tags:
- cfs
- load_balance
title: 'sched/cache: Keep nr_pref_llc_running in the runnable domain'
layout: article
---

## TL;DR
增量更新。Kayra Cizmeci 09-10 投出的「把 nr_pref_llc_running 收进 runnable 域」补丁（4 补丁系列 patch 1/4）今日获 Chen Yu 回复：Chen Yu 实测了 Kayra 建议的「在 h_nr_runnable 更新点顺带维护」方案，结论是更复杂、角落案例更多，维持现有较简版本，改为补注释与调整 clear_delayed() 代码顺序；Kayra 认可 "Yeah, I think this is cleaner"。这是对 sched-20260911-003 中 Kayra 质疑的延续收口。

## 背景与问题
承 sched-20260828-004（原 nr_pref_llc_running 计数口径 bug：DELAY_DEQUEUE 下 nr_pref_llc_running 跟随 queued 语义、cfs.h_nr_runnable 扣除 delay-dequeued 任务，两计数集合不同导致 alb_break_llc() 判断失效）与 sched-20260911-003（Tim Chen 的 Fixes 系列 patch 1）。Kayra 曾在 Fixes 讨论中质疑：既然 nr_pref_llc_running 是 h_nr_runnable 的子集，为何不在前者的更新点顺带维护，省掉独立判据与四处调用。Tim 以 set_delayed() 顺序约束和 per-rq/per-cfs_rq 作用域差异自辩后，Kayra 09-10 自投了带改动建议的 patch 1/4。

## 技术方案
Chen Yu 实测 Kayra 方案后（自述 "It seems that the code becomes more complex and brings more headache :-( due to several corner cases"），给出替代 Version：

- 在 `account_llc_dequeue()` 处补注释，说明 nr_pref_llc_running 随 h_nr_runnable 变化、涉及 set_delayed()/clear_delayed()/account_llc_enqueue()/account_llc_dequeue() 四个维护点；
- 注释画两个典型时序：case 1 wakeup delayed task（set_delayed 在 CPU0 减计数、跨 CPU1 的 try_to_wake_up 里 clear_delayed 加回）；case 2 LB for delayed task（detach/attach 迁移时 account_llc_dequeue/account_llc_enqueue 均 DO-NOT-DECREASE / DO-NOT-INCREASE，避免双计）；
- 调整 clear_delayed() 代码顺序以更易读；
- 结论：维持较简版本 + 注释，并请 Tim 复核 "if this makes sense"。

## 版本演进与当前进展
- 08-27/08-28：Zhan Xusheng 提问、Tim Chen 给出原始修复（sched-20260828-004）。
- 09-10/09-11：Kayra 质疑并入 Fixes 系列，自投带改动建议的 patch 1/4（sched-20260911-003）。
- 09-14（本文窗口）：Chen Yu 实测 Kayra 方案、维持较简版本 + 注释；Kayra 认可，无新版本发出。

## Maintainer 意见与讨论焦点
- **Chen Yu（Intel）**：认可 Kayra 建议的意图，但实测后认为合并维护点更复杂，选较简版本 + 注释，请 Tim 复核。
- **Kayra Cizmeci**：认可 "Yeah, I think this is cleaner"（但自陈 "in a hurry"、尚未细读注释）。
- **Tim Chen**：尚待对注释版表态。
- 分歧/未闭合处：Tim 对 Chen Yu 注释版 patch 1 的复核未回；设计取舍（单判据 vs 顺带维护）最终由 Tim 定夺。

## 合入评估
*likelihood=medium*（承 Fixes 系列整体 medium）：本线程 patch 1 设计已收敛（Chen Yu 与 Kayra 就「维持较简版本 + 注释」达成一致），但随 Fixes 系列 v2 一起打包推进，Tim 复核与 PeterZ 对系列整体的意见仍是前提。*blocking_issues*：无独立卡点，随 sched-20260911-003 的 v2 推进。*next_action*：等 Tim 对注释版 patch 1 的复核；该计数口径随 Fixes v2 一并合入。

## 效果评估
无性能数据。计数正确性靠注释内两个时序图（case 1/2）推演，未见运行测试报告。

## 我可以参与的点
- kind=review：核对注释版中 case 2（LB for delayed task）的 DO-NOT-DECREASE/DO-NOT-INCREASE 与 account_llc_* 实际实现是否一致。
- kind=testing：DELAY_DEQUEUE + active balance 压力下验证计数不重不漏（承 sched-20260911-003 的验证点）。

## 参考链接
- Chen Yu 注释版回帖：https://lore.kernel.org/all/aqdVpO66OfmHvvqB@chenyu-dev/
- Kayra 认可回帖：https://lore.kernel.org/all/20260914052703.1286495-1-kayracizmeci@gmail.com/
