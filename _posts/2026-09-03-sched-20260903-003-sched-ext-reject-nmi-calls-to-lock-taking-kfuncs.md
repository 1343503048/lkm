---
id: sched-20260903-003
date: '2026-09-03'
subject: 'sched_ext: Reject NMI calls to lock-taking kfuncs'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched_ext+Reject+NMI+calls+lock-taking+kfuncs
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v3
generated_at: null
authors:
- liwanwu
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
- sched-20260902-004
tags:
- sched_ext
title: 'sched_ext: Reject NMI calls to lock-taking kfuncs'
layout: article
---

## TL;DR

进入评审的「拒 NMI 调用拿锁 kfuncs」审计在 09-03 推进到 v3，并发现两处新的上下文不安全点：NMI 路径下仍可能调用会拿锁的 kfunc，以及 idle 搜索使用的 scratch nodemask 未在 irqsave 下保护。目前复审中，强调 NMI 上下文只能调用不拿锁、不睡眠的 kfunc。- idle 搜索的 scratch nodemask 改用 irqsave 保护，防止与中断抢占产生数据竞争。

## 背景与问题

09-02 进入评审的「拒 NMI 调用拿锁 kfuncs」审计在 09-03 推进到 v3，并发现两处新的上下文不安全点：NMI 路径下仍可能调用会拿锁的 kfunc，以及 idle 搜索使用的 scratch nodemask 未在 `irqsave` 下保护。本系列补齐这些 NMI 上下文安全缺口。

## 技术方案

- `sched_ext`：拒 NMI 调用拿锁 kfuncs（v3，多封 Re 复审）。
- `sched_ext`：NMI kfunc 审计中发现的两处上下文安全修复（0/2，"two more context-safety fixes found in the NMI kfunc audit"）。
- `sched_ext`：Protect the idle-search scratch nodemask with `irqsave`（2/2），避免与中断路径竞争该临时掩码。

## 版本演进与当前进展

- 复审中，强调 NMI 上下文只能调用不拿锁、不睡眠的 kfunc。
- idle 搜索的 scratch nodemask 改用 `irqsave` 保护，防止与中断抢占产生数据竞争。
- 因 UID 映射不稳，0/2 封面正文未能可靠获取，以上依据主题与 `sched-20260902-004` 上下文整理。

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
  - [[sched-20260902-004]] sched_ext 拒 NMI 拿锁 kfuncs（v3 初版）。
- 相关代码/commit：
  - `kernel/sched/ext.c` NMI/kfunc 调用门禁与 idle 搜索路径
