# sched/debug: Validate writes to the scan_size_mb debugfs knob

## TL;DR
Zhan Xusheng 提交 v2「sched/debug: Validate writes to scan_size_mb」。该值被写成 0 会在 NUMA 平衡扫描逻辑中触发 divide error panic（由 Chen Yu 指出）。v2 增加写入校验与 sysctl 文档。属 high 严重度崩溃修复，合入可能性高。

## 背景与问题
`scan_size_mb` 控制 NUMA 平衡 task 的扫描窗口大小（pages）。该值经 debugfs/sysctl 可写，但未做下限校验；写成 0 后在 `scan_delay` 等除法相关路径触发 divide error（#DE），导致内核 panic。Chen Yu 在 v1 邮件中明确复现并指出根因。

## 技术方案
- v1：对 debugfs 写入做基本校验，拒绝 0。
- v2：扩展校验并补充 `kernel.sysctl.scan_size_mb` 的 Documentation/admin-guide/sysctl/kernel.rst 文档，说明取值范围与语义，并修正一处相关除零潜在 Oops。设计取舍：在写入路径（而非读取/使用路径）集中校验，保持运行时零开销。

## 版本演进与当前进展
当前 v2。v1 由 Chen Yu 反馈 0 值 panic；v2 加入文档并收紧校验。8/10 发出。

## Maintainer 意见与讨论焦点
Chen Yu、Libo 等讨论校验边界。焦点：是否应完全拒绝 0，还是允许极小值；文档措辞。

## 合入评估
合入可能性 high。崩溃修复，风险低，已有测试反馈。

## 效果评估
无 benchmark；修复 divide-by-zero panic，明确的安全收益。

## 我可以参与的点
- 复现并验证写入 0 不再 panic；
- 评审校验边界是否覆盖所有写入口（sysctl + debugfs）。

## 参考链接
- lore: 未获取到
- 关联: NUMA balancing scan_size_mb

---
subject: "sched/debug: Validate writes to the scan_size_mb debugfs knob"
id: sched-20260810-003
date: 2026-08-10
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: "<20260809144911.xxxxxx-zhan@kernel.org>"
lore_url: "未获取到"
authors: [Zhan Xusheng]
maintainers_involved: [Peter Zijlstra, Mel Gorman, Ingo Molnar, Chen Yu]
current_version: v2
patch_series:
  - version: v1
    msgid: "<20260809144911.xxxxxx-zhan@kernel.org>"
    date: 2026-08-09
    summary: "首次提出对 debugfs 写入 scan_size_mb 做校验，防止被写成 0。"
    review_outcome: "Chen Yu 在 v1 指出 0 值会触发 divide error panic。"
  - version: v2
    msgid: "<20260810025820.xxxxxx-zhan@kernel.org>"
    date: 2026-08-10
    summary: "v2 增加 sysctl 文档说明与更严格的写入校验（拒绝 <=0 的 scan_size_mb），并修正一个除零相关的潜在 Oops。"
    review_outcome: "v2 发出，Chen Yu 与 Libo 继续讨论校验边界。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待维护者确认校验边界（是否允许 0 / 极小值）及文档措辞。"
contribution_opportunities:
  - kind: review
    description: "评审 scan_size_mb 写入校验边界（除零/极小值的拒绝策略）。"
  - kind: testing
    description: "向 /sys/.../scan_size_mb 写入 0 或其它非法值验证不再 panic。"
generated_at: "2026-08-11T00:15:00"
source_email_count: 3
related_articles: []
tags: [sched_debug, crash]
---
