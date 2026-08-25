---
id: sched-20260822-006
date: 2026-08-22
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: "未获取到"
lore_url: "未获取到"
authors: ["unknown"]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "未获取到"
    date: 2026-08-22
    summary: "同步 sched_ext tools headers + cgroup v2 文档更新"
    review_outcome: "已合入 sched_ext/for-7.3-fixes"
upstream_commit: null
fixes_commit: null
merged_branch: "sched_ext/for-7.3-fixes"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已合入"
contribution_opportunities: []
generated_at: "2026-08-22T10:00:00"
source_email_count: 2
related_articles: []
tags: ["sched_ext", "documentation"]
---

## TL;DR

两个 sched_ext 补丁被合入 `sched_ext/for-7.3-fixes`：1) 同步 tools headers 与 scx 仓库保持一致；2) cgroup v2 文档增加 BPF 调度器回调（cpu.max/cpu.idle）说明。

## 背景与问题

sched_ext 工具的 headers 需要与 scx 上游仓库保持同步，否则可能导致编译或运行时不兼容。同时 cgroup v2 文档缺少对 BPF 调度器回调的说明。

## 技术方案

- Headers 同步：更新 sched_ext tools 目录下的头文件
- 文档更新：在 cgroup-v2 文档中记录 BPF 调度器对 cpu.max 和 cpu.idle 的回调行为

## 版本演进与当前进展

两个补丁均已合入 `sched_ext/for-7.3-fixes`。

## Maintainer 意见与讨论焦点

已合入，无争议。

## 合入评估

- **likelihood**: merged
- 已合入 `sched_ext/for-7.3-fixes`

## 效果评估

改善工具兼容性和文档完整性。

## 我可以参与的点

当前阶段暂无明显参与空间。

## 参考链接

- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到
