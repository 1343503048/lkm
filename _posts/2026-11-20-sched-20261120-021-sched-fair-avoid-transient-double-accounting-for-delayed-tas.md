---
id: sched-20261120-021
date: '2026-11-20'
subject: 'sched/fair: Avoid transient double accounting for delayed tasks'
subsystem: sched
type: regression
status: under_review
severity: high
thread_root_msgid: <20261112083447.25603-1-kprateek.nayak@amd.com>
lore_url: https://lore.kernel.org/all/CA+V-a8tunjWx9j47pZybGjBwiHzQzsxXWzrc0+3E4h+APGFk8w@mail.gmail.com/
authors:
- K Prateek Nayak
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261112083447.25603-1-kprateek.nayak@amd.com>
  date: '2026-11-12'
  summary: 原补丁修 delayed-dequeue 瞬时双记账，合入 486c3d06b902
  review_outcome: 合入版漏掉 h_nr_runnable = 1;，Lad 报 Renesas 性能回归
upstream_commit: 486c3d06b90240860e99686d29ed9f15637dc314
fixes_commit: null
merged_branch: tip/sched/urgent
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 补回补丁未发出
  next_action: K Prateek（或维护者）补回 h_nr_runnable = 1 并发 follow-up
contribution_opportunities:
- kind: review
  description: 核对原补丁与 486c3d06b902 是否还有其它丢失/改动的行
- kind: new_patch
  description: 若原作者未跟进，代发补回 h_nr_runnable = 1 的 follow-up
generated_at: '2026-11-21T09:00:00+08:00'
source_email_count: 216
related_articles:
- sched-20261112-004
- sched-20261118-023
tags:
- cfs
- regression
title: 'sched/fair: Avoid transient double accounting for delayed tasks'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/18/sched-20261118-023-sched-fair-avoid-transient-double-accounting-for-delayed-t.html">sched-20261118-023</a>：K Prateek Nayak 的 delayed-dequeue 记账修复合入 tip/sched/urgent（commit `486c3d06b902`）。
- <a class="article-ref" href="/lkm/2026/11/20/sched-20261120-021-sched-fair-avoid-transient-double-accounting-for-delayed-tas.html">sched-20261120-021</a>（今天）：**Lad Prabhakar 报告合入版引入回归**——merge 时 `dequeue_hierarchy()` 里 `h_nr_runnable = 1;` 被漏掉（原补丁有、合入版丢了），在 Renesas SoC 上测试出现性能下降。

## 背景与问题

原补丁修 delayed-dequeue 的「先多减、再纠正」瞬时双记账。但 Lad 发现合入 commit `486c3d06b902` 与原补丁的 diff 差了一行：`dequeue_hierarchy()` 里本应 `h_nr_runnable = 1;`，合入版漏掉（变为 0），在 Renesas SoC 上运行测试时出现性能下降。属「合入时引入的回归」，原补丁作者（K Prateek Nayak）的版本是完整的。

## 技术方案

Lad 给出原补丁（[0] `https://lore.kernel.org/all/20261112083447.25603-1-kprateek.nayak@amd.com/`）与 tip-bot2 合入版（[1]）的 diff 对照：`dequeue_hierarchy()` 里 `- int h_nr_runnable = 0; + int h_nr_runnable = 1;` 这一行在合入时丢失。修法即补回该行（待后续补丁）。

## 版本演进与当前进展

*current_version: 已合入（`486c3d06b902`）→ 今日报回归*。今日为回归报告，补回修复尚未在当日缓存中见到。

## Maintainer 意见与讨论焦点

- **Lad, Prabhakar（报告者）**：指出合入版丢失 `h_nr_runnable = 1;`、Renesas SoC 性能下降，给出 diff 对照。
- 无 NAK；属合入漏改的明确回归，待原作者/维护者补丁。

## 合入评估

*likelihood=medium*。回归原因明确（合入时漏一行）、修复即补回该行，但补丁尚未发出；且提示合入流程里这一行变更的丢失需要确认根因。*blocking_issues*：补回补丁未发出。*next_action*：K Prateek（或维护者）补回 `h_nr_runnable = 1;` 并发 follow-up。

## 效果评估

Lad 报告在 Renesas SoC 上「性能下降」（未见具体数字），并给出源码级 diff 佐证；属合入版相对原补丁的行为差异。

## 我可以参与的点

- **review**：核对原补丁与 `486c3d06b902` 是否还有其它被合入时丢失/改动的行；确认 `h_nr_runnable = 1` 的语义在 delayed-dequeue 路径正确。
- **new_patch**：若原作者未及时跟进，可代发补回该行的 follow-up 补丁。

## 参考链接

- lore thread（Lad 回复）: https://lore.kernel.org/all/CA+V-a8tunjWx9j47pZybGjBwiHzQzsxXWzrc0+3E4h+APGFk8w@mail.gmail.com/
- 原补丁: https://lore.kernel.org/all/20261112083447.25603-1-kprateek.nayak@amd.com/
