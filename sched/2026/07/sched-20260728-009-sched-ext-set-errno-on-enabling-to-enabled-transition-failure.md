# sched ext set errno on enabling to enabled transition failure

## TL;DR

sched_ext 启用流程中一个极小的错误处理缺陷：当 SCX_ENABLING → SCX_ENABLED 的 cmpxchg 竞态失败时，函数跳转到 err_disable 但 ret 仍为 0，导致内核日志打印 "scx_root_enable() failed (0)" 这样无意义的信息。单行修复，设置 ret = -EBUSY。

## 背景与问题

`scx_root_enable_workfn()` 负责将 sched_ext 从 ENABLING 状态切换到 ENABLED。函数末尾通过 cmpxchg 原子操作完成状态转换。如果在此期间有其他路径改变了状态（竞态），cmpxchg 失败，函数跳转到 `err_disable` 标签进行回退。

问题在于：此时 `ret` 变量仍保留着上一次成功调用 `__scx_init_task()` 的返回值 0。回退路径打印的错误信息为 `scx_root_enable() failed (0)`，errno 为 0 完全没有诊断价值。

影响范围：仅在极端竞态条件下触发（多个启用请求并发），对功能无影响（回退逻辑本身正确），仅影响错误日志的可读性。

## 技术方案

在 cmpxchg 失败后、跳转 err_disable 前，添加一行 `ret = -EBUSY`。

选择 -EBUSY 的理由：与函数顶部其他启用状态守卫（检查 SCX_ENABLING/SCX_ENABLED 状态）使用的错误码一致，语义上表示"调度器正忙/状态已被占用"。

修改量：`kernel/sched/ext/ext.c` 增加 1 行。

## 版本演进与当前进展

- **v1**（2026-07-28 发出）：首次提交，单 patch 单行修复。

v1 刚发出，暂无 review 意见。

## Maintainer 意见与讨论焦点

暂无 maintainer 回复。sched_ext 的 maintainer 为 Tejun Heo 和 David Vernet。

此修复极为直接，预期不会有争议。

## 合入评估

合入可能性高。理由：
- 修改量极小（1 行），风险几乎为零
- 修复的是明确的代码缺陷（错误路径未设置返回值）
- 与函数内其他错误路径的处理方式一致
- 不涉及任何行为变更，仅改善错误日志

唯一可能的延迟因素是 maintainer 的 review 周期。

## 效果评估

暂无效果数据。修复前后唯一可观察差异是竞态失败时内核日志从 "failed (0)" 变为 "failed (-16)"（-EBUSY）。

## 我可以参与的点

- 审查 `scx_root_enable_workfn()` 中其他错误路径，确认是否有类似的 ret 未初始化/未更新问题
- 当前阶段参与空间有限，可持续观察是否有 maintainer 提出修改意见

## 参考链接

- lore thread: 未获取到
- 修改文件: kernel/sched/ext/ext.c

---
subject: "sched ext set errno on enabling to enabled transition failure"
id: sched-20260728-009
date: 2026-07-28
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: null
lore_url: null
authors: [Liang Luo]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: null
    date: 2026-07-28
    summary: "scx_root_enable_workfn() 中 ENABLING->ENABLED cmpxchg 失败时未设置 ret，导致错误日志打印无意义的 errno 0"
    review_outcome: "v1 刚发出，暂无 review 意见"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待 sched_ext maintainer (Tejun Heo) review"
contribution_opportunities:
  - kind: review
    description: "确认同一函数中其他错误路径是否也存在类似的 ret 未设置问题"
generated_at: "2026-07-30T10:00:00"
source_email_count: 1
related_articles: [sched-20260728-001]
tags: [sched_ext]
---
