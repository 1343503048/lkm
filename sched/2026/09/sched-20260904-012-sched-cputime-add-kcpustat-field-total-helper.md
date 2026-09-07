# sched/cputime: Add kcpustat_field_total helper

## TL;DR

延续 09-03 002 的 steal_governor v12（13 补丁系列），本日收到第 01/13 补丁 "sched/cputime: Add kcpustat_field_total helper" 的复审（Re）。目前v12 复审中，目标合并窗口 7.4；整体延续偏好 CPU + vCPU 抢占回退框架。

## 背景与问题

延续 09-03 002 的 steal_governor v12（13 补丁系列），本日收到第 01/13 补丁 "sched/cputime: Add kcpustat_field_total helper" 的复审（Re）。该 helper 供 steal_governor 统计 steal time 总量使用，便于在虚拟化场景对 vCPU steal time 设上限并驱动更优的 CPU 选择。

## 技术方案

- 新增 `kcpustat_field_total` helper（v12 01/13），为后续 steal time 汇总提供基础设施。

## 版本演进与当前进展

- v12 复审中，目标合并窗口 7.4；整体延续偏好 CPU + vCPU 抢占回退框架。

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
  - [[sched-20260903-002]] steal_governor v12 偏好 CPU + vCPU 回退。
- 相关代码/commit：
  - `kernel/sched/cputime.c` `kcpustat_field_total`
  - `kernel/sched/fair.c` steal / 偏好 CPU 选择

---
id: sched-20260904-012
date: '2026-09-04'
subject: 'sched/cputime: Add kcpustat_field_total helper'
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=steal_governor+v12+kcpustat_field_total
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v12
generated_at: null
authors:
- Yury Norov
- Shrikanth Hegde
- Frederic Weisbecker
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 4
related_articles:
- sched-20260903-002
tags:
- sched/core
- sched/fair
- sched/cache
- topology
---
