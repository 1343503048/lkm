# sched/core: Push current task from non preferred CPU

## TL;DR

延续 steal_governor v12（13 补丁）。目前v12 复审收尾，目标合并窗口 7.4。- 讨论聚焦偏好 CPU 计数器的比较基准（影响 steal/推送决策）。

## 背景与问题

延续 steal_governor v12（13 补丁）。本日收到 v12 08/13 "sched/core: Push current task from non preferred CPU" 的复审（Re 81260），以及关于 `sched/fair` 中 `nr_pref_llc_running` 应与哪些任务比较的讨论（Re 80977）。

## 技术方案

- v12 08/13：在任务位于非偏好 CPU 时主动将其推送出去。
- `nr_pref_llc_running` 语义讨论围绕「应和哪些任务比较」以判断是否达到偏好 LLC 运行阈值。

## 版本演进与当前进展

- v12 复审收尾，目标合并窗口 7.4。
- 讨论聚焦偏好 CPU 计数器的比较基准（影响 steal/推送决策）。

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
  - [[sched-20260904-012]] steal_governor v12 kcpustat_field_total helper（01/13）。
  - [[sched-20260903-002]] steal_governor v12 偏好 CPU + vCPU 回退。
- 相关代码/commit：
  - `kernel/sched/fair.c` `nr_pref_llc_running` / steal 路径

---
id: sched-20260905-005
date: '2026-09-05'
subject: 'sched/core: Push current task from non preferred CPU'
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=steal_governor+v12+Push+current+task+from+non+preferred+CPU
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v12
generated_at: null
authors:
- Shrikanth Hegde
- Yury Norov
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 3
related_articles:
- sched-20260904-012
- sched-20260903-002
tags:
- sched/core
- sched/fair
- sched/cache
- topology
---
