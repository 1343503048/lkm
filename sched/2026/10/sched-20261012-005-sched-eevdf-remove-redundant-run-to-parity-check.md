# sched/eevdf: Remove redundant RUN_TO_PARITY check

## TL;DR

Elif Topuz 提交一个 EEVDF 小清理：`update_protect_slice()` 只在 `RUN_TO_PARITY` 特性开启时被调用，函数内部的 `sched_feat(RUN_TO_PARITY)` 判断是冗余的；直接改用 `cfs_rq_min_slice()`。当日 Vincent Guittot 已 `Reviewed-by`，是低风险的确定性清理。

## 背景与问题

`update_protect_slice()` 唯一调用点是 `wakeup_preempt_fair()`，且该调用已被 `RUN_TO_PARITY` 特性门控。函数内部又用 `sched_feat(RUN_TO_PARITY)` 决定 slice 取 `cfs_rq_min_slice(cfs_rq)` 还是归一化后的 `sched_base_slice`——外层已保证只有开了该特性才会进来，内层判断恒真，属于死分支。

## 技术方案

删除内层 `if (sched_feat(RUN_TO_PARITY))` 分支，`slice` 直接取 `cfs_rq_min_slice(cfs_rq)`（`kernel/sched/fair.c` +2/-7）。语义无变化，仅移除不可达分支。

## 版本演进与当前进展

v1 当日新发（2026-10-12，ARM Elif Topuz）。Vincent Guittot 同日回帖 `Reviewed-by: Vincent Guittot`。

## Maintainer 意见与讨论焦点

无争议，VM 直接 R-b。

## 合入评估

*likelihood=high*。纯死分支清理、维护者 R-b。*blocking_issues*：无。*next_action*：等待收取。

## 效果评估

无性能影响（代码等价清理），邮件未附 benchmark。

## 我可以参与的点

改动极小且已 R-b，暂无明显参与空间。

## 参考链接

- lore（本补丁）: https://lore.kernel.org/all/20261012105001.131311-1-elif.topuz@arm.com/
- lore（Vincent Reviewed-by）: https://lore.kernel.org/all/CAKfTPtA_TkR3bmhknaZtJ0VUWtAM=05tHK1i5ixL9cuutGNsBA@mail.gmail.com/

---
id: sched-20261012-005
date: '2026-10-12'
subject: 'sched/eevdf: Remove redundant RUN_TO_PARITY check'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261012105001.131311-1-elif.topuz@arm.com>
lore_url: https://lore.kernel.org/all/20261012105001.131311-1-elif.topuz@arm.com/
authors:
- Elif Topuz
maintainers_involved:
- Vincent Guittot
current_version: v1
patch_series:
- version: v1
  msgid: <20261012105001.131311-1-elif.topuz@arm.com>
  date: '2026-10-12'
  summary: 删掉 update_protect_slice() 内冗余的 RUN_TO_PARITY 判断，直接用 cfs_rq_min_slice()
  review_outcome: Vincent Guittot 给出 Reviewed-by
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 已获 Vincent Reviewed-by，等待 Peter/维护者收取
contribution_opportunities: []
generated_at: '2026-10-13T01:40:00'
source_email_count: 2
related_articles: []
tags:
- eevdf
---
