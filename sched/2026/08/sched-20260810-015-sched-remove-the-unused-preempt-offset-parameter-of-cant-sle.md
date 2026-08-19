# sched: Remove the unused preempt_offset parameter of __cant_sleep()

## TL;DR
Boqun Feng 的 3 个抢占/锁相关清理 commit 已由 tip-bot 合入 `tip/locking/core`（2026-08-10 报告）：移除未使用的 `preempt_offset` 参数、避免有符号比较、arm64 启用 `HAS_SEPARATE_PREEMPT_RESCHED_BITS`。merged_tip。

## 背景与问题
抢占计数与 `__cant_sleep()` 等接口存在冗余参数与风格问题；sched 中一处比较本应无符号；arm64 尚未启用独立的 PREEMPT_RESCHED 位（影响重调度延迟粒度）。

## 技术方案
- commit1：`__cant_sleep()` 的 `preempt_offset` 在所有调用点恒为 0，移除之，并把 `preempt_count() > preempt_offset` 简化为 `preempt_count()`。
- commit2：修正 sched 中一处有符号比较为无符号，避免符号扩展隐患。
- commit3：arm64 启用 `HAS_SEPARATE_PREEMPT_RESCHED_BITS`，使重调度位独立于抢占计数，改善重调度延迟粒度。具体实现以 tip 树为准。

## 版本演进与当前进展
已由 tip 机器人合入 `tip/locking/core`，3 个 commit 同日报告。无后续版本。

## Maintainer 意见与讨论焦点
tip-bot 自动合入，代表已进入 tip 维护流。

## 合入评估
已合入 tip 树（merged_tip），随合并窗口进入主线。

## 效果评估
属清理/微优化；arm64 的 PREEMPT_RESCHED 位分离预期改善重调度延迟粒度（无邮件内具体数据）。

## 我可以参与的点
- 在 arm64 PREEMPT 内核上做重调度延迟基准对比；
- 跟踪合并窗口进入主线。

## 参考链接
- tip 分支: tip/locking/core
- commit1: ac4231a77973fc20808ed84c4af343eca2342d4b

---
subject: "sched: Remove the unused preempt_offset parameter of __cant_sleep()"
id: sched-20260810-015
date: 2026-08-10
subsystem: sched
type: cleanup
status: merged_tip
severity: low
thread_root_msgid: "<tip.1754823xxxx.locking@bot>"
lore_url: "未获取到"
authors: [Boqun Feng]
maintainers_involved: [Peter Zijlstra, Ingo Molnar, Mark Rutland, Catalin Marinas]
current_version: merged
patch_series:
  - version: merged
    msgid: "<tip.1754823xxxx.locking@bot>"
    date: 2026-08-10
    summary: "tip-bot 报告 3 个已合入 tip/locking/core 的 commit：(1) 移除 __cant_sleep() 未使用的 preempt_offset 参数；(2) 避免 sched 中一处有符号比较；(3) arm64 启用 HAS_SEPARATE_PREEMPT_RESCHED_BITS。"
    review_outcome: "已由 tip 机器人合入 locking/core，无需额外 review。"
upstream_commit: "ac4231a77973fc20808ed84c4af343eca2342d4b (commit 1)"
fixes_commit: null
merged_branch: "tip/locking/core"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已进入 tip 树，等待下一个合并窗口进入主线。"
contribution_opportunities:
  - kind: testing
    description: "在 arm64 PREEMPT 配置下验证 HAS_SEPARATE_PREEMPT_RESCHED_BITS 启用无回归。"
generated_at: "2026-08-11T00:15:00"
source_email_count: 3
related_articles: ["sched-20260809-004"]
tags: [sched/core, preempt, arm64]
---
