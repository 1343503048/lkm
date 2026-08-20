---
id: sched-20260809-003
date: 2026-08-09
subsystem: sched
type: discussion
status: under_review
severity: low
thread_root_msgid: <20260809.is_core_idle@mete>
lore_url: 未获取到
authors:
- Mete Durlu
maintainers_involved:
- Peter Zijlstra
- Vincent Guittot
current_version: v1
patch_series:
- version: v1
  msgid: <20260809.is_core_idle@mete>
  date: 2026-08-09
  summary: '对 8/8 发出的 [PATCH] sched/fair: Make is_core_idle() check all cpus in a
    core 的回复/追问，讨论 is_core_idle() 是否应遍历 core 内所有 CPU。'
  review_outcome: 邮件链仍在进行，属于对原 patch 的讨论延续，暂无最终结论。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: 等待原 patch 作者与维护者对 is_core_idle() 遍历范围的最终定论。
contribution_opportunities:
- kind: discussion
  description: 参与讨论 is_core_idle() 的语义边界（hypertreading/core scheduling 场景下的正确性）。
generated_at: '2026-08-10T00:15:00'
source_email_count: 1
related_articles:
- sched-20260808-001（同日 is_core_idle 原 patch 系列，具体 id 见 08-08 日期索引）
tags:
- sched/fair
- core_sched
title: 'sched/fair: Make is_core_idle() check all cpus in a core'
layout: article
---

## TL;DR
Mete Durlu 在 2026-08-09 对前一天（08-08）提交的 `is_core_idle()` 修改 patch 发起讨论/追问，延续该系列。属 discussion，尚无定论。

## 背景与问题
`is_core_idle()` 用于判断一个 core 是否完全空闲（core scheduling / SMT 场景下决定是否可让兄弟线程运行）。原 patch（08-08 发出）试图让该函数遍历 core 内所有 CPU 而非仅首 CPU。本邮件是对该改动的进一步讨论。

## 技术方案
本邮件为讨论性回复，未提出独立代码改动；核心议题是 `is_core_idle()` 在 SMT/core scheduling 语义下应检查的范围，以及遍历全部 CPU 是否引入不必要的开销。

## 版本演进与当前进展
当前为该讨论的 v1 回复，挂在 08-08 原 patch 之下。尚无合入或定论。

## Maintainer 意见与讨论焦点
讨论焦点集中在 `is_core_idle()` 语义正确性 vs 性能开销的权衡，属于该系列原有争议点的延续，详见 08-08 原 patch 文章。

## 合入评估
取决于原 patch 的最终走向，当前 unknown。

## 效果评估
暂无效果数据（讨论性邮件）。

## 我可以参与的点
- 在 core scheduling 开启的机器上分析 `is_core_idle()` 遍历全部 CPU 的实际开销，提供数据帮助收敛讨论。

## 参考链接
- lore thread: 未获取到
- 关联原系列: 见 2026-08-08 日期索引
