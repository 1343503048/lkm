# cpufreq: longrun: fix kernel-doc warning

## TL;DR
Manuel Ebner 发往 cpufreq 的 v2 补丁：修复 longrun 驱动的 kernel-doc 告警。当日 cpufreq 维护者 Viresh Kumar 直接「Applied. Thanks.」收取。属 x86 老驱动（Transmeta LongRun）的文档级修复。

## 背景与问题
`cpufreq-longrun` 驱动存在 kernel-doc 告警（此前同驱动已有一处 kernel-doc 拼写修复见 related_articles），本补丁继续清理剩余告警。

## 技术方案
单补丁（v2）：修正 longrun 驱动的 kernel-doc 告警。具体 diff 未完整进入当日缓存。

## 版本演进与当前进展
*current_version: v2*（`<20261020071913.1677196-2-manuelebnerli@mailbox.org>`）。

## Maintainer 意见与讨论焦点
Viresh Kumar（cpufreq 维护者）直接收取，无额外意见。

## 合入评估
*likelihood=merged*。已由 cpufreq 维护者 Viresh Kumar 收取。

## 效果评估
文档级修复，无性能影响。

## 我可以参与的点
无。

## 参考链接
- Viresh 收取回帖：https://lore.kernel.org/all/atg4APgeoSHQWNeI@vireshk-B250M-D3H/

---
id: sched-20261021-019
date: 2026-10-21
subject: "cpufreq: longrun: fix kernel-doc warning"
subsystem: sched
type: fix
status: merged_tip
severity: none
thread_root_msgid: "<20261020071913.1677196-2-manuelebnerli@mailbox.org>"
lore_url: "https://lore.kernel.org/all/20261020071913.1677196-2-manuelebnerli@mailbox.org/"
authors: ["Manuel Ebner"]
maintainers_involved: ["Viresh Kumar"]
current_version: v2
patch_series:
  - version: v2
    msgid: "<20261020071913.1677196-2-manuelebnerli@mailbox.org>"
    date: 2026-10-20
    summary: "修复 longrun 驱动 kernel-doc 告警"
    review_outcome: "Viresh Kumar 收取"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已收取，无需进一步动作"
contribution_opportunities: []
generated_at: "2026-10-22T01:30:00"
source_email_count: 1
related_articles: ["sched-20261019-005"]
tags: [cpufreq]
---