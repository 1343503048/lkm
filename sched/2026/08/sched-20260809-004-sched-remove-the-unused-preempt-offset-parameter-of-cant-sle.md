# sched: Remove the unused preempt_offset parameter of __cant_sleep()

## TL;DR
Boqun Feng 的 3 个抢占相关清理/修复已由 tip-bot 合入 `tip/locking/core`（2026-08-09 报告），属已合入主线前的 tip 阶段。无需额外 review。

## 背景与问题
抢占计数（`preempt_count`）与抢占检查路径在 sched/core 与 locking 子系统间存在语义不一致或冗余调用点，需要统一以降低 proxy execution / 抢占逻辑的理解与维护成本。

## 技术方案
tip-bot 报告了 3 个 commit，统一 sched 侧抢占相关调用点的语义，调整 preempt 计数与抢占检查路径。具体实现细节以 tip 树 commit 为准（邮件为 tip-bot 自动通知，正文为 commit 摘要）。

## 版本演进与当前进展
已由 tip 机器人合入 `tip/locking/core`，3 个 commit 同日报告（28657/28659/28661）。无后续版本。

## Maintainer 意见与讨论焦点
tip-bot 自动合入，代表已进入 tip 维护流；无人工 review 争议记录。

## 合入评估
已合入 tip 树（merged_tip），下一步随合并窗口进入主线。无阻塞项。

## 效果评估
暂无独立效果数据；属维护清理类改动。

## 我可以参与的点
- 在 PREEMPT_RT / 全抢占内核上做回归验证，确认抢占路径无行为变化；
- 持续跟踪下一次合并窗口是否进入主线。

## 参考链接
- tip-bot commit: 未获取到完整 hash
- tip 分支: tip/locking/core

---
subject: "sched: Remove the unused preempt_offset parameter of __cant_sleep()"
id: sched-20260809-004
date: 2026-08-09
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: "<tip.1754732xxxx.locking@bot>"
lore_url: "未获取到"
authors: [Boqun Feng]
maintainers_involved: [Peter Zijlstra, Ingo Molnar, Thomas Gleixner]
current_version: merged
patch_series:
  - version: merged
    msgid: "<tip.1754732xxxx.locking@bot>"
    date: 2026-08-09
    summary: "tip-bot 自动报告 3 个已合入 tip/locking/core 的 commit，均为 sched 侧的抢占相关清理/修复：调整 preempt 计数与抢占检查路径，统一若干调用点语义。"
    review_outcome: "已由 tip 机器人合入 tip/locking/core，无需额外 review。"
upstream_commit: "未获取到完整 hash（tip-bot 多 commit）"
fixes_commit: null
merged_branch: "tip/locking/core"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已进入 tip 树，等待下一个合并窗口进入主线。"
contribution_opportunities:
  - kind: testing
    description: "在 PREEMPT_RT/全抢占配置下验证抢占计数相关路径无回归。"
generated_at: "2026-08-10T00:15:00"
source_email_count: 3
related_articles: []
tags: [sched/core, preempt, proxy_execution]
---
