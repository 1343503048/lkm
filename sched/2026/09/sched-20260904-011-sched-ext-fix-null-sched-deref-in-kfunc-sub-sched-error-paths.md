# sched_ext: Fix NULL sched deref in kfunc sub-sched error paths

## TL;DR

延续 09-03 004，sub-sched 错误路径 NULL deref 修复进入 v3，本日收到复审（Re）。目前v3 复审中；与 09-03 004 同源，本日为版本演进与复审反馈。

## 背景与问题

延续 09-03 004，sub-sched 错误路径 NULL deref 修复进入 v3，本日收到复审（Re）。错误路径（open/enable 失败回滚）访问已释放/未初始化的 `sched` 对象，可能触发 NULL deref crash。

## 技术方案

- `sched_ext`：Fix NULL sched deref in kfunc sub-sched error paths（v3，`Fixes: a5fa0708cbfd`，`Cc: stable`）。
- `sched_ext`：Fix NULL sched deref in `select_cpu_and` sub-sched error path（同源）。

## 版本演进与当前进展

- v3 复审中；与 09-03 004 同源，本日为版本演进与复审反馈。

## Maintainer 意见与讨论焦点

邮件清单中该系列以补丁往返为主，未捕获到维护者明确表态（缓存未含正文，无法给出具体意见）。

## 合入评估

证据不足：邮件缓存未保留正文，无法判断维护者态度与卡点，暂不给合入结论。

## 效果评估

邮件中未提及效果数据（缓存未保留正文，无法确认）。

## 我可以参与的点

证据不足：需结合完整邮件正文再判断参与空间；如该系列进入 review 中后期，可先跑一轮 benchmark 并回帖。

## 参考链接

- 相关文章/系列：
  - [[sched-20260903-004]] sched_ext sub-sched 错误路径 NULL deref（kfunc v3 + select_cpu_and）。
- 相关代码/commit：
  - `kernel/sched/ext.c` sub-sched 错误回滚路径（`Fixes: a5fa0708cbfd`）

---
id: sched-20260904-011
date: '2026-09-04'
subject: 'sched_ext: Fix NULL sched deref in kfunc sub-sched error paths'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched_ext+Fix+NULL+sched+deref+in+kfunc+sub-sched+error+paths+v3
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v3
generated_at: null
authors:
- Wanwu Li
- Tejun Heo
- Andrea Righi
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 6
related_articles:
- sched-20260903-004
tags:
- sched_ext
- crash
---
