# [REGRESSION] sched/rt: NO_RT_PUSH_IPI causes multi-second PI-boost starvation in pro-audio workloads (dd29c017aed6)

## TL;DR

提交 dd29c017aed6（"sched/rt: Have RT_PUSH_IPI be default off for non PREEMPT_RT"）在非 PREEMPT_RT 桌面引入可复现的多秒级音频掉帧。目前已被标记为 tracked regression。- 受影响对象为普通非 PREEMPT_RT 桌面（音频实时性敏感负载）。

## 背景与问题

提交 `dd29c017aed6`（"sched/rt: Have RT_PUSH_IPI be default off for non PREEMPT_RT"）在非 PREEMPT_RT 桌面引入可复现的多秒级音频掉帧。报告人 Martin King 在 DAW（数字音频工作站）场景中观察到 PI-boost 饥饿。Steven Rostedt 于 09-03 就该回归发信询问进展，已纳入 tracked regression。

## 技术方案

- 当前为回归追踪/讨论阶段，尚无修复 patch。
- 需评估：是否修正 `NO_RT_PUSH_IPI` 路径下的 PI 推举（push）逻辑，或恢复该默认行为。

## 版本演进与当前进展

- 已被标记为 tracked regression。
- 受影响对象为普通非 PREEMPT_RT 桌面（音频实时性敏感负载）。
- 尚无明显修复提交，等待维护者/作者回应。

## Maintainer 意见与讨论焦点

邮件清单中该系列以补丁往返为主，未捕获到维护者明确表态（缓存未含正文，无法给出具体意见）。

## 合入评估

证据不足：邮件缓存未保留正文，无法判断维护者态度与卡点，暂不给合入结论。

## 效果评估

邮件中未提及效果数据（缓存未保留正文，无法确认）。

## 我可以参与的点

证据不足：需结合完整邮件正文再判断参与空间；如该系列进入 review 中后期，可先跑一轮 benchmark 并回帖。

## 参考链接

- 相关代码/commit：
  - `dd29c017aed6` "sched/rt: Have RT_PUSH_IPI be default off for non PREEMPT_RT"
  - `kernel/sched/rt.c` RT push/IPI 与 PI 提升路径

---
id: sched-20260903-006
date: '2026-09-03'
subject: '[REGRESSION] sched/rt: NO_RT_PUSH_IPI causes multi-second PI-boost starvation in pro-audio workloads (dd29c017aed6)'
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=REGRESSION+sched/rt+NO_RT_PUSH_IPI+PI-boost+starvation
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: null
authors:
- Steven Rostedt
- Martin King
- Thorsten Leemhuis
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 3
related_articles: []
tags:
- rt
- regression
---
