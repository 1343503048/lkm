---
id: sched-20260904-007
date: '2026-09-04'
subject: 'sched: Make proxy execution compatible with sched_ext'
subsystem: sched
type: discussion
status: under_review
severity: high
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched+Make+proxy+execution+compatible+with+sched_ext+v13
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v13
generated_at: null
authors:
- Andrea Righi
- Tejun Heo
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 3
related_articles:
- sched-20260902-001
tags:
- sched_ext
- proxy_execution
title: 'sched: Make proxy execution compatible with sched_ext'
layout: article
---

## TL;DR

让代理执行（proxy execution）与 sched_ext 兼容的系列推进到 v13。目前v13，Tejun 基本认可（scx POV），待 Peter 决定。- 属代理执行主线，直接影响 sched_ext 在代理执行下的正确性。

## 背景与问题

让代理执行（proxy execution）与 sched_ext 兼容的系列推进到 v13。Tejun 从 scx 视角给出 "looks okay ... ready to merge and iterate in tree"，并询问 Peter Zijlstra 的意见，等待其拍板。

## 技术方案

- 代理执行与 scx 的兼容层：在代理执行下正确维护 scx 的调度/分派（DSQ/dispatch）语义，使被代理（donor 阻塞、替他人执行）的 scx 任务行为正确。
- 随版本演进修正了多轮 review nits。

## 版本演进与当前进展

- v13，Tejun 基本认可（scx POV），待 Peter 决定。
- 属代理执行主线，直接影响 sched_ext 在代理执行下的正确性；与同日 008（reject DSQ reenqueue 泛化）协同。

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
  - [[sched-20260902-001]] Proxy Exec 批合入 tip（主线起点）。
- 相关代码/commit：
  - `kernel/sched/ext.c` 代理执行兼容路径
