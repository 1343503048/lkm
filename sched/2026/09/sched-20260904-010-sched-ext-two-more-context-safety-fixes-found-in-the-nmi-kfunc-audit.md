# sched_ext: two more context-safety fixes found in the NMI kfunc audit

## TL;DR

延续 09-03 003 的 NMI kfunc 审计，本日收到 0/2 封面的复审（Re）。目前复审中；强调 NMI 上下文只能调用不拿锁、不睡眠的 kfunc。

## 背景与问题

延续 09-03 003 的 NMI kfunc 审计，本日收到 0/2 封面的复审（Re）。该系列补齐 NMI 上下文下调用会拿锁/未加保护的 kfunc 路径，防止 NMI 与正常上下文并发访问产生数据竞争或死锁。

## 技术方案

- 拒 NMI 调用拿锁 kfunc（v3）+ 两处 irqsave 保护 + idle-search scratch nodemask 的 `irqsave` 保护（详见 09-03 003）。本日为复审进展。

## 版本演进与当前进展

- 复审中；强调 NMI 上下文只能调用不拿锁、不睡眠的 kfunc。

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
  - [[sched-20260903-003]] sched_ext NMI kfunc 审计后续修复（拒 NMI 拿锁 kfunc v3 + 两处 irqsave）。
- 相关代码/commit：
  - `kernel/sched/ext.c` NMI/kfunc 调用门禁

---
id: sched-20260904-010
date: '2026-09-04'
subject: 'sched_ext: two more context-safety fixes found in the NMI kfunc audit'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched_ext+two+more+context-safety+fixes+found+in+the+NMI+kfunc+audit
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: null
authors:
- Wanwu Li
- Tejun Heo
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 2
related_articles:
- sched-20260903-003
tags:
- sched_ext
---
