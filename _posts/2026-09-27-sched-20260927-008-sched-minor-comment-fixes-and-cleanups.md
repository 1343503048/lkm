---
id: sched-20260927-008
date: 2026-09-27
subject: 'sched: Minor comment fixes and cleanups'
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: <20260927123507.39074-1-kayracizmeci@gmail.com>
lore_url: https://lore.kernel.org/all/20260927123507.39074-1-kayracizmeci@gmail.com/
authors:
- Kayra Cizmeci
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260927123507.39074-1-kayracizmeci@gmail.com>
  date: 2026-09-27
  summary: 3 枚注释/清理补丁：修 sched_info_enqueue 注释、改 elegibility 拼写、删未用 autogroup.h include（fair.c
    +3/-4）。
  review_outcome: 无回帖。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无 review 回帖
  - 1/3 与 Wei 在开发补丁的时序耦合（Wei 落地后注释需再改）
  next_action: 等维护者 pickup；若 Wei 补丁先落地则按新代码文本更新 1/3 注释
contribution_opportunities:
- kind: review
  description: 核对 sched_info_depart 是否确调用 sched_info_enqueue，以及 autogroup.h 是否确为未使用
    include
generated_at: '2026-09-28T09:00:00'
source_email_count: 4
related_articles: []
tags:
- cfs
title: 'sched: Minor comment fixes and cleanups'
layout: article
---

## TL;DR

Kayra Cizmeci 发出的 3 枚调度子系统注释/清理小补丁（`kernel/sched/fair.c` 与 `kernel/sched/stats.h`，合计 +3/-4）：修正 `sched_info_enqueue()` 的过时注释、改正 `requeue_delayed_entity()` 注释拼写（elegibility→eligibility）、删除 fair.c 未使用的 `autogroup.h` include。纯 cleanup、无功能改动，刚发出、无 review。其中 1/3 依赖 Wei 尚在开发的补丁，若其落地则注释需再改。

## 背景与问题

作者在阅读调度代码时陆续攒下的三处注释/清理问题，之前零星单独发过但「旧贴均未获回应」，这次整理成系列重发：

- `sched_info_enqueue()` 的注释只写「仅由 enqueue_task() 调用」，但实际 `sched_info_depart()` 也会调用它，注释过时（1/3，出自审阅 Wei 的补丁时发现）。
- `requeue_delayed_entity()` 注释中 `elegibility` 是 `eligibility` 的拼写错误（2/3）。
- `fair.c` 引入 `autogroup.h` 但未使用（3/3）。

## 技术方案

三处均为纯文本/死代码清理，无逻辑改动：1/3 更新 `stats.h` 注释措辞、2/3 改正拼写、3/3 删除未使用 include。作者在 cover 里特别注明：1/3 的注释与 Wei 仍在开发中的补丁相关，若 Wei 的补丁最终改动该处代码文本，注释也需随之调整。

## 版本演进与当前进展

- v1（2026-09-27，cover `<20260927123507.39074-1-kayracizmeci@gmail.com>`，3 补丁）。cover 给出三枚补丁此前的单独发送链接（1/3 出自 20260920、2/3 出自 20260822、3/3 出自 20260726），说明是「重发成系列」。本日无 review 回帖。

## Maintainer 意见与讨论焦点

本日无任何维护者/社区回帖。唯一可留意的点是作者自述「旧贴均未获回应」，说明这类 trivial cleanup 在 LKML 上未必会被及时 pickup。

## 合入评估

*likelihood=unknown*。纯注释/清理、无功能风险，但无任何回帖，无法判断是否有维护者愿意收取。*blocking_issues*：无 review；1/3 与 Wei 补丁的时序耦合（Wei 补丁落地后注释需再改）可能让维护者等 Wei 补丁先定。*next_action*：等维护者（Peter/Vincent）pickup；若 Wei 补丁先落地，作者需按新代码文本更新 1/3 注释。

## 效果评估

无性能数据（注释/清理类，无运行时影响）。

## 我可以参与的点

- `review`：核对 1/3 注释修正的准确性（`sched_info_depart()` 是否确会调用 `sched_info_enqueue()`），以及 3/3 的 `autogroup.h` 是否确为未使用 include，避免误删。

## 参考链接

- cover: https://lore.kernel.org/all/20260927123507.39074-1-kayracizmeci@gmail.com/
- 1/3: https://lore.kernel.org/all/20260927123507.39074-2-kayracizmeci@gmail.com/
- 2/3: https://lore.kernel.org/all/20260927123507.39074-3-kayracizmeci@gmail.com/
- 3/3: https://lore.kernel.org/all/20260927123507.39074-4-kayracizmeci@gmail.com/
