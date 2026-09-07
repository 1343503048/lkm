# sched/fair: remove quota/burst write-order dependency

## TL;DR

CFS CPU 带宽的 quota 与 burst 控制当前使内核态写入顺序变得重要：在 quota 无限时配置 burst，会阻止后续有限 quota 安装。目前v2 0/3，本日收到复审。- 关注点：写入顺序不再影响配置成败，cgroup v1/v2 行为需文档化一致。

## 背景与问题

CFS CPU 带宽的 quota 与 burst 控制当前使内核态写入顺序变得重要：在 quota 无限时配置 burst，会阻止后续有限 quota 安装；先增 burst 再增 quota（burst-first）会以 EINVAL 失败。本系列让配置的 burst 值与当前 quota 解耦，在 CFS 补充运行时间时再施加 quota 相对钳制，并加 selftest + 文档。

## 技术方案

- v2 变化：
  - 在 refill（补充运行时间）时施加钳制，而非改变配置的 burst。
  - 保留 `cpu.max.burst` / `cpu.cfs_burst_us` 报告值。
  - 新增两种写入顺序的 selftest，并更新 cgroup v1/v2 文档。

## 版本演进与当前进展

- v2 0/3，本日收到复审。
- 关注点：写入顺序不再影响配置成败，cgroup v1/v2 行为需文档化一致。

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
  - `kernel/sched/fair.c` CFS 带宽 refill 路径
  - cgroup CPU 带宽（`cpu.max` / `cpu.max.burst`）

---
id: sched-20260904-004
date: '2026-09-04'
subject: 'sched/fair: remove quota/burst write-order dependency'
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched/fair+remove+quota/burst+write-order+dependency
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: null
authors:
- Zhe Liu
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
- sched/fair
- cgroup
---
