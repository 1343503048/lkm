# sched/rt,dl: Remove unreachable migration-disabled push checks

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261015-008：Shubhang Kaushik（Ampere）v2 清理 `push_rt_task()`/`push_dl_task()` 里不可达的 migration-disabled 分支（候选由 `pick_next_pushable_task()` 选出、本就跳过 migration-disabled 任务），并移除只服务该分支的 `@pull` 参数；无行为变化，v2 刚发暂无 review。
- sched-20261019-009（今天）：Christian Loehle（Arm）回帖「FWIW I also cannot reproduce the code path」并给出 `Tested-by`，同时表示「仍想说服自己这确实成立、或查清这段代码当初为何引入」——正面但保留态度，尚无 RT/DL 维护者表态。

## 背景与问题

（承接 20261015-008）`push_rt_task()` 用 `pick_next_pushable_task()` 选 `next_task`（不返回 migration-disabled 任务），`find_lock_lowest_rq()` 掉锁重取后重新检查并拒绝状态变化任务，故 push 侧的 migration-disabled fallback 不可达。v2 删除 RT/DL 两处死代码与 `@pull` 参数，无明显收益、属代码清理。

## 技术方案

（承接 20261015-008）今日无新补丁，为 review 反馈：Christian 无法复现该代码路径、给出 Tested-by，但明确还在「说服自己论证成立 / 查清代码引入原因」——即死代码结论尚未被第三方完全背书。

## 版本演进与当前进展

*current_version: v2*。v2（20261014 发出）首位 reviewer（Christian Loehle）今日表态：无法复现 + Tested-by，但保留式评价。

## Maintainer 意见与讨论焦点

Christian Loehle（Arm，资深 reviewer，非 RT/DL 维护者）：「我也无法复现这条代码路径」+ `Tested-by`，并补充「想先说服自己它确实成立，或弄清这段代码最初为何引入」。RT/DL 维护者（Steven Rostedt、Juri Lelli）仍未表态。关键不变量「持锁期间任务不改变 migration-disabled 状态」仍需 RT/DL 维护者确认。

## 合入评估

*likelihood=unknown*。有 Tested-by 与「无法复现」佐证，但论证的不变量尚未获 RT/DL 维护者确认，且 reviewer 本人保留态度。*blocking_issues*：RT/DL 维护者无表态、死代码论证未被完全背书。*next_action*：等 Steven Rostedt / Juri Lelli 确认死代码判断。

## 效果评估

无性能差异（死代码清理），Christian 侧复现/验证为「无法复现该路径」，即无负面行为证据。

## 我可以参与的点

- `review`：独立验证「push 侧 migration-disabled fallback 不可达」论证，特别是 `find_lock_lowest_rq()` 掉锁重取后的重检查是否覆盖全部路径，帮 Christian 完成「说服自己」那一环。

## 参考链接

- Christian 回帖：https://lore.kernel.org/all/da0b23f4-78f5-4dea-b588-af19f1c77fcb@arm.com/
- v2 patch：https://lore.kernel.org/all/20261014-sched-rt-dead-md-push-v2-1-9f57f1a530dc@gentwo.org/

---
id: sched-20261019-009
subject: "sched/rt,dl: Remove unreachable migration-disabled push checks"
date: 2026-10-19
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: "<20261014-sched-rt-dead-md-push-v2-1-9f57f1a530dc@gentwo.org>"
lore_url: "https://lore.kernel.org/all/20261014-sched-rt-dead-md-push-v2-1-9f57f1a530dc@gentwo.org/"
authors: ["Shubhang Kaushik"]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v1
    msgid: "<20261014-sched-rt-dead-md-push-v1-1-5f9757be3c80@gentwo.org>"
    date: 2026-10-14
    summary: "删除 push_rt_task() 不可达的 migration-disabled fallback 与 @pull 参数"
    review_outcome: "暂无 review"
  - version: v2
    msgid: "<20261014-sched-rt-dead-md-push-v2-1-9f57f1a530dc@gentwo.org>"
    date: 2026-10-14
    summary: "扩展删除 push_dl_task() 的对应检查"
    review_outcome: "Christian Loehle 无法复现 + Tested-by，但保留式评价（见今）"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["RT/DL 维护者无表态", "死代码论证未获 reviewer 完全背书"]
  next_action: "等 Steven Rostedt/Juri Lelli 确认死代码判断与不变量"
contribution_opportunities:
  - kind: review
    description: "独立验证 push 侧 migration-disabled fallback 不可达论证的完整性"
generated_at: "2026-10-20T01:30:00"
source_email_count: 1
related_articles: ["sched-20261015-008"]
tags: [rt, deadline]
---