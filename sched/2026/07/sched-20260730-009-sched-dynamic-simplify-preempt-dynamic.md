# sched dynamic simplify preempt dynamic

## TL;DR

Mark Rutland 的 5-patch 系列简化 `PREEMPT_DYNAMIC` 配置。Mete Durlu 在 s390 上测试显示 vmlinux 减小约 1MB，bzImage 减小约 32KB，bloat-o-meter 显示净减少约 107KB。无行为变化报告。

## 背景与问题

`PREEMPT_DYNAMIC` 允许运行时切换抢占模式，但当前实现较为复杂。该系列旨在简化配置和实现。

## 技术方案

5-patch 系列，简化 PREEMPT_DYNAMIC 的实现和配置接口。

## 版本演进与当前进展

- 2026-07-03: v1 发出
- 2026-07-30: Mete Durlu 提供 s390 测试结果

## Maintainer 意见与讨论焦点

暂无 maintainer 明确 review 意见。

## 合入评估

- **likelihood**: medium
- 需要更多架构的测试验证

## 效果评估

s390 测试结果（Mete Durlu）：
- vmlinux: 409MB → 408MB（减小约 1MB）
- bzImage: 12.9MB → 12.85MB（减小约 32KB）
- bloat-o-meter: add/remove 67/50, grow/shrink 731/2058, net -106857 bytes
- 行为测试：sniff tests 未发现行为变化

## 我可以参与的点

- **多架构测试**：在 x86/arm64/riscv 上测试并报告 size 和行为变化
- 如果有特定 PREEMPT_DYNAMIC 使用场景，可以验证简化后的功能完整性

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260703133358.698078-1-mark.rutland@arm.com
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
subject: "sched dynamic simplify preempt dynamic"
id: sched-20260730-009
date: 2026-07-30
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260703133358.698078-1-mark.rutland@arm.com>"
lore_url: "https://lore.kernel.org/lkml/20260703133358.698078-1-mark.rutland@arm.com"
authors: [Mark Rutland]
maintainers_involved: [Mark Rutland]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260703133358.698078-1-mark.rutland@arm.com>"
    date: 2026-07-03
    summary: "5-patch series to simplify PREEMPT_DYNAMIC configuration"
    review_outcome: "Mete Durlu provided s390 test results showing ~1MB vmlinux size reduction"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["Need more arch testing and review"]
  next_action: "Gather more arch test results"
contribution_opportunities:
  - kind: testing
    description: "Test on other architectures (x86, arm64, riscv) and report size/behavior changes"
generated_at: "2026-07-31T00:10:00"
source_email_count: 1
related_articles: []
tags: [preempt]
---
