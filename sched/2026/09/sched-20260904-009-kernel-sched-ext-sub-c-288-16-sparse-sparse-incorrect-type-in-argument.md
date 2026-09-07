# kernel/sched/ext/sub.c:288:16: sparse: sparse: incorrect type in argument 1 (different address spaces)

## TL;DR

day/LKP 在 torvalds master（head 940de590b839）上报告 sparse 告警：kernel/sched/ext/sub.c:288 参数 1 地址空间不一致（different address spaces）。目前静态分析/CI（0day）报告，sparc-randconfig W=1 复现（GCC 16.1.0 / sparse 0.6.5-rc1）。

## 背景与问题

0day/LKP 在 torvalds `master`（head `940de590b839`）上报告 sparse 告警：`kernel/sched/ext/sub.c:288` 参数 1 地址空间不一致（different address spaces）。该告警针对已合入提交 `bb70e4fb626b` "sched_ext: Eject the top rescue consumer on overload"（约 4 周前）。

## 技术方案

- 需修正 `sub.c:288` 的 sparse 地址空间标注（`__rcu` / `__user` 等），对该提交单独修复并加 `Fixes:` 标签。

## 版本演进与当前进展

- 静态分析/CI（0day）报告，sparc-randconfig `W=1` 复现（GCC 16.1.0 / sparse 0.6.5-rc1）。
- 需作者发后续补丁修复；属低级清理，不影响功能但影响构建洁净度。

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
  - `bb70e4fb626b` "sched_ext: Eject the top rescue consumer on overload"
  - `kernel/sched/ext/sub.c:288`

---
id: sched-20260904-009
date: '2026-09-04'
subject: 'kernel/sched/ext/sub.c:288:16: sparse: sparse: incorrect type in argument 1 (different address spaces)'
subsystem: sched
type: bug
status: under_review
severity: low
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sparse+sub.c+288+different+address+spaces
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: null
authors:
- kernel test robot
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
- sched_ext
---
