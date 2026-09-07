# sched/debug: Validate writes to the scan_size_mb debugfs knob

## TL;DR

scan_size_mb 在 task_scan_max() 中作为除数使用，而 debugfs_create_u32() 对写入值不做校验。目前v2 RESEND，作者重发以推进审阅。- 严重度 high：普通 debugfs 写入即可触发内核 panic，影响可测试性/稳定性。

## 背景与问题

`scan_size_mb` 在 `task_scan_max()` 中作为除数使用，而 `debugfs_create_u32()` 对写入值不做校验。向 `/sys/kernel/debug/sched/numa_balancing/scan_size_mb` 写入 0（或某些值）会在 `task_scan_max+0x30` 触发 "divide error" Oops，调用链 `init_numa_balancing → __sched_fork → sched_fork`，导致内核 panic。本补丁（v2 RESEND）对写入做合法性校验。

## 技术方案

- 在 `scan_size_mb` 的 debugfs 写回调中校验取值，拒绝会导致除零或越界的写入（保持在合理范围，如 [1, MAX_SCAN_WINDOW/scan_size]）。

## 版本演进与当前进展

- v2 RESEND，作者重发以推进审阅。
- 严重度 high：普通 debugfs 写入即可触发内核 panic，影响可测试性/稳定性。

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
  - `kernel/sched/debug.c` / `kernel/sched/fair.c` `task_scan_max()`
  - NUMA 平衡调试接口 `scan_size_mb`

---
id: sched-20260905-002
date: '2026-09-05'
subject: 'sched/debug: Validate writes to the scan_size_mb debugfs knob'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched/debug+Validate+writes+to+the+scan_size_mb+debugfs+knob
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: null
authors:
- Zhan Xusheng
- Chen Yu
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 4
related_articles: []
tags:
- sched_debug
- numa_balancing
---
