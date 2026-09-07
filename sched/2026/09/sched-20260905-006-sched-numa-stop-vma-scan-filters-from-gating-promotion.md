# sched/numa: stop VMA scan filters from gating promotion

## TL;DR

task_numa_work() 在标记 VMA 以触发 hint fault 前会施加一系列 VMA 级过滤器。目前/2 新系列，本日收到复审（Re：80843 1/2、80869 2/2）。- 关注点：内存分层下 hint fault 作为提升机制，扫描过滤器不应成为提升的永久闸门。

## 背景与问题

`task_numa_work()` 在标记 VMA 以触发 hint fault 前会施加一系列 VMA 级过滤器。这些过滤器是当初 hint fault 作为「socket 驻留信号」时写的——跳过 VMA 只损失一些分辨率。但在内存分层（memory tiering）下，hint fault 不是信号而是机制：慢层 folio 之所以被考虑提升，正是因为扫描标记了它且随后被访问。被扫描排除的 VMA 会被永久排除在提升之外，因为过滤器输入来自扫描自身产生的 fault。

## 技术方案

- Patch 1：覆盖 per-VMA PID 过滤器（自引用问题：VMA 需要 hint fault 才能进入扫描，又需要扫描才能产生 hint fault）。
- Patch 2：覆盖只读文件映射排除（其前提在分层场景下不再成立）。

## 版本演进与当前进展

- 0/2 新系列，本日收到复审（Re：80843 1/2、80869 2/2）。
- 关注点：内存分层下 hint fault 作为提升机制，扫描过滤器不应成为提升的永久闸门。

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
  - `kernel/sched/fair.c` `task_numa_work()`
  - 内存分层（memory tiering）NUMA 自动提升

---
id: sched-20260905-006
date: '2026-09-05'
subject: 'sched/numa: stop VMA scan filters from gating promotion'
subsystem: sched
type: feature
status: under_review
severity: medium
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched/numa+stop+VMA+scan+filters+from+gating+promotion
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: null
authors:
- Gregory Price
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 1
related_articles: []
tags:
- numa_balancing
---
