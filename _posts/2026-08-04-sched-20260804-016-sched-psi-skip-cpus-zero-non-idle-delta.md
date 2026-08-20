---
subject: sched psi skip cpus zero non idle delta
id: sched-20260804-016
date: 2026-08-04
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: <unknown>
lore_url: unknown
authors:
- Dmitry Pletnev
maintainers_involved:
- Johannes Weiner
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <unknown>
  date: 2026-08-04
  summary: PSI 轮询（pressure stall info）在统计各 CPU 的非 idle 时间增量时，对增量为 0 的 CPU 仍走完整更新路径；跳过这些
    CPU 以减少无谓的开销（尤其在大量 idle CPU 的系统上）。
  review_outcome: v1 刚发，邮件未显示 NAK。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 需确认跳过 0 增量 CPU 不会丢失边界情况（如刚退出 idle 的 CPU）
  next_action: 等待 Johannes Weiner / PeterZ 对开销收益与正确性的认可。
contribution_opportunities:
- kind: review
  description: 可审阅跳过 0 增量 CPU 是否在刚退出 idle 的边界条件下仍正确（避免丢失瞬时非 idle 增量），回帖边界分析。
generated_at: '2026-08-05T00:25:00'
source_email_count: 1
related_articles: []
tags:
- psi
- idle
- sched_debug
title: sched psi skip cpus zero non idle delta
layout: article
---

# sched/psi: 跳过非 idle 增量为 0 的 CPU

## TL;DR
PSI 统计中对非 idle 时间增量为 0 的 CPU 仍走完整更新路径，Dmitry Pletnev 改为跳过以减开销（大量 idle CPU 的系统受益明显）。低严重度优化，合入可能性 medium，需确认边界正确性。

## 背景与问题
PSI（pressure stall information）周期性统计每个 CPU 的非 idle 时间增量以计算压力。对增量为 0 的 CPU（持续 idle）仍执行完整更新路径，在拥有大量 idle CPU 的大系统上累积成可观的无谓开销。

## 技术方案
在 PSI 更新循环中，对非 idle 增量（non-idle delta）为 0 的 CPU 直接跳过，避免对其做 group/cpu 状态的冗余更新。改动集中在 `psi_group_cpu` 的增量处理。

## 版本演进与当前进展
v1（2026-08-04），作者 Dmitry Pletnev。

## Maintainer 意见与讨论焦点
尚未见 maintainer 回复。焦点在正确性：需确认「跳过」不会丢失刚退出 idle 的 CPU 的瞬时增量（边界条件）。

## 合入评估
合入可能性 medium。开销优化，无功能风险但需边界正确性确认。

## 效果评估
邮件未附 benchmark。属开销优化，效果以「大系统 PSI 更新开销下降」衡量，需实测验证。

## 我可以参与的点
- 审阅跳过 0 增量 CPU 是否在刚退出 idle 的边界条件下仍正确，回帖边界分析（最直接 review 参与点）。

## 参考链接
- lore thread: 未获取到
