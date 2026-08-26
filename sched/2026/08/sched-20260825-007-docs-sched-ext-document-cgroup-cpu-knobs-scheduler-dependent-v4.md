# docs/sched_ext: document that cgroup CPU knobs are scheduler-dependent

## TL;DR

sched_ext cgroup CPU 接口文档 patch 推进到 v4，Tejun Heo 已将其 apply 到 `sched_ext/for-7.3-fixes` 分支。该文档澄清 sched_ext 下 cgroup CPU 接口（`cpu.weight`、`cpu.idle` 等）的行为取决于 BPF 调度器的实现，而非核心调度器的固定语义。

## 背景与问题

sched_ext 将调度策略完全交给 BPF 调度器，因此 cgroup CPU 接口（如 `cpu.weight`）的语义不再由核心调度器固定定义，而是取决于当前加载的 BPF 调度器如何使用这些参数。用户空间工具和管理员需要理解这一点，避免对 cgroup 接口的行为做出错误假设。

## 技术方案

在 sched_ext 文档中添加说明：cgroup CPU knobs 的行为是 scheduler-dependent 的。

## 版本演进与当前进展

v4 已获 Tejun Heo 确认并 apply 到 `sched_ext/for-7.3-fixes`：
> "Applied to sched_ext/for-7.3-fixes. Thanks."

## Maintainer 意见与讨论焦点

Tejun Heo 已 apply，无争议。

## 合入评估

- **likelihood: merged** — 已 apply 到 sched_ext/for-7.3-fixes 分支
- **blocking_issues**: 无
- **next_action**: 等待 7.3 merge window 合入主线

## 效果评估

暂无效果数据（纯文档）。

## 我可以参与的点

当前阶段已合入，暂无参与空间。

## 参考链接

- lore thread: 未获取到
- tip-bot commit: 未获取到（已 apply 到 sched_ext/for-7.3-fixes）

---
id: sched-20260825-007
date: 2026-08-25
subsystem: sched
type: fix
status: merged_tip
severity: none
thread_root_msgid: "unknown"
lore_url: "unknown"
authors: [Tejun Heo]
maintainers_involved: [Tejun Heo]
current_version: v4
patch_series:
  - version: v4
    msgid: "unknown"
    date: 2026-08-25
    summary: "文档化 sched_ext 下 cgroup CPU knobs 的行为取决于 BPF 调度器"
    review_outcome: "Tejun Heo apply 到 sched_ext/for-7.3-fixes"
upstream_commit: null
fixes_commit: null
merged_branch: "sched_ext/for-7.3-fixes"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已合入 sched_ext/for-7.3-fixes，等待 7.3 merge window"
contribution_opportunities: []
generated_at: "2026-08-27T10:00:00"
source_email_count: 1
related_articles: []
tags: [sched_ext, cgroup]
---
