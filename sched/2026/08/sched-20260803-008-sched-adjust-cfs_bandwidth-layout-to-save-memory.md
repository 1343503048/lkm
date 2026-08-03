---
id: sched-20260803-008
date: 2026-08-03
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<unknown>"
lore_url: "unknown"
authors: [Hongling Zeng]
maintainers_involved: [Peter Zijlstra, Vincent Guittot]
current_version: v1
patch_series:
  - version: v1
    msgid: "<unknown>"
    date: 2026-08-03
    summary: "重排 cfs_bandwidth 结构成员，把运行期热字段（period_timer、hrtimer_active、throttled_lb 等）聚拢，使 32 位小结构体也落在 4 字节对齐，减少内存占用。附 before/after 结构体布局。"
    review_outcome: "邮件内以 before/after 对比展示布局优化；尚未见 maintainer NAK。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["纯布局优化，需确认对热路径字段偏移无负面 cache-line 影响"]
  next_action: "等待 maintainer 对『聚合热字段 vs 拆分到不同 cache line』权衡的认可；属低优先级清理。"
contribution_opportunities:
  - kind: review
    description: "cfs_bandwidth 成员聚合后热字段是否落到同一 cache line 带来正面效果，可审阅 pahole before/after 确认无 cache-line 撕裂回归。"
generated_at: "2026-08-04T00:20:00"
source_email_count: 1
related_articles: []
tags: [cfs, bandwidth_control]
---
# sched: 重排 cfs_bandwidth 布局以节省内存


## TL;DR
`sched` 重排 `cfs_bandwidth` 结构成员以节省内存并对齐热字段。属低严重度的布局优化，合入可能性 medium，需确认 cache-line 影响。

## 背景与问题
`cfs_bandwidth`（CFS 带宽控制，用于 `cpu.cfs_quota_us`/`cfs_period_us`）结构体内存布局在 32 位平台下因成员对齐产生填充浪费，且不常访问的字段与运行期热字段交错，影响 cache 局部性。作者意图在不改变功能的前提下优化布局。

## 技术方案
把运行期热字段（`period_timer`、`hrtimer_active`、`throttled_lb` 等）聚拢到结构体前部，使结构体在 32 位平台也以 4 字节边界对齐，减少填充。邮件给出 before/after 布局对比，展示节省的字节数。

## 版本演进与当前进展
v1（2026-08-03），作者 Hongling Zeng。附完整 before/after `struct cfs_bandwidth` 布局。

## Maintainer 意见与讨论焦点
尚未见 maintainer 回复（v1 刚发）。潜在关注点：聚合热字段可能把它们推到同一 cache line，也可能因与写频繁字段同 line 引发伪共享——需确认权衡。

## 合入评估
合入可能性 medium。纯清理性质、低优先级，无功能风险，但需 maintainer 确认 cache-line 权衡后才会被接收。

## 效果评估
邮件给出 pahole 风格 before/after 布局对比作为效果证据（节省内存字节）。无运行时 benchmark，属内存 footprint 优化。

## 我可以参与的点
- 可审阅聚合后热字段是否落入同一 cache line 造成伪共享，回帖 pahole/cache-line 分析补强证据。

## 参考链接
- lore thread: 未获取到
