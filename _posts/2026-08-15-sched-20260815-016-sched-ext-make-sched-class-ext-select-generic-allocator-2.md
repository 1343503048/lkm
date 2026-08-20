---
id: sched-20260815-016
date: 2026-08-15
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <uid-40822@qq-imap>
lore_url: 未获取到
authors:
- Xu Xuefei
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <uid-40822@qq-imap>
  date: 2026-08-15
  summary: 修正 scx_ddsp selftest 中 'failure tests' 偶发失败：flaky 源于任务退出与断言时序竞争。
  review_outcome: v1 刚发出，等待 Tejun review。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 需确认修复不掩盖真实失败路径
  next_action: 等待 Tejun review/apply。
contribution_opportunities:
- kind: testing
  description: 在 CI 中反复运行 scx_ddsp failure tests 验证 flaky 复现率下降。
generated_at: '2026-08-16T00:10:00'
source_email_count: 1
related_articles: []
tags:
- sched_ext
- selftests
title: 'selftests/sched_ext: Fix flaky ddsp failure tests on busy systems'
layout: article
---

## TL;DR
Xu Xuefei 修复 `sched_ext` selftest `scx_ddsp` 中"failure tests"的偶发（flaky）失败：根因是任务退出与断言检查时序竞争。v1 刚发出，等待 Tejun review。

## 背景与问题
`scx_ddsp`（default-select CPU 调度器）selftest 的失败用例在某些 CI 运行中偶发失败，并非真实功能缺陷，而是测试本身时序竞争：断言读取调度器状态/失败计数时，被测试任务可能尚未完成退出，导致断言误判为失败。

## 技术方案
调整 `scx_ddsp` failure tests 的同步/等待逻辑：在断言前确保被测试任务已完全退出，或在断言中容忍退出中间态，消除 flaky。改动仅限 selftest 代码，不影响内核。

## 版本演进与当前进展
v1（40822）2026-08-15 由 Xu Xuefei 发出。暂无 Tejun review 意见。

## Maintainer 意见与讨论焦点
v1 刚发出，等待 Tejun review。注意点：修复不能掩盖真实失败路径（即不能把真实错误也"容忍"掉）。

## 合入评估
合入可能性高（纯 selftest 稳定性修复）。需确认不弱化失败检测。

## 效果评估
降低 CI 中 `scx_ddsp` failure tests 的偶发失败，提升 CI 信号可信度；无内核影响。

## 我可以参与的点
- 在 CI 中反复运行 scx_ddsp failure tests 验证 flaky 复现率下降。

## 参考链接
- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到
