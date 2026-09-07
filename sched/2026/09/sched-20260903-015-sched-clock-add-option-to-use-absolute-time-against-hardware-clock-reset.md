# sched_clock: Add option to use absolute time against hardware clock reset

## TL;DR

部分平台的硬件时钟会在复位/暂停后回绕或清零，使基于它的 sched_clock() 出现跳变，影响调度时间基准与 trace 一致性。目前本日有多封复审（Re）讨论复位检测与补偿语义、对不同平台的影响。- 与 sched-20260902-013 同系列，仍在讨论收敛中。

## 背景与问题

部分平台的硬件时钟会在复位/暂停后回绕或清零，使基于它的 `sched_clock()` 出现跳变，影响调度时间基准与 trace 一致性。本系列增加一个选项，使 `sched_clock` 在该硬件时钟复位时使用「绝对时间」语义，削弱复位造成的可见跳变。

## 技术方案

- 新增配置/选项，让 `sched_clock` 在检测到硬件时钟复位时采用绝对时间补偿，而不是简单复用会回绕的计数器。

## 版本演进与当前进展

- 本日有多封复审（Re）讨论复位检测与补偿语义、对不同平台的影响。
- 与 `sched-20260902-013` 同系列，仍在讨论收敛中。

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
  - [[sched-20260902-013]] sched_clock 绝对时间选项（初版）。
- 相关代码/commit：
  - `kernel/time/sched_clock.c`

---
id: sched-20260903-015
date: '2026-09-03'
subject: 'sched_clock: Add option to use absolute time against hardware clock reset'
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched_clock+Add+option+to+use+absolute+time+against+hardware+clock+reset
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: null
authors:
- Yao Yuan
- Feng Tang
- Marc Zyngier
- Thomas Gleixner
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 6
related_articles:
- sched-20260902-013
tags:
- sched_clock
---
