---
id: sched-20260906-003
date: '2026-09-06'
subject: 'selftests/sched_ext: Fail interrupted test runs'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: null
lore_url: null
upstream_commit: null
fixes_commit: 9d851afa4826
merged_branch: null
current_version: v1
generated_at: '2026-09-07T00:10:00'
authors:
- Tianyi Chen
maintainers_involved:
- Tejun Heo
patch_series:
- version: v1
  msgid: null
  date: 2026-09-06
  summary: selftests/sched_ext runner 在收到 SIGINT/SIGTERM 时设置 exit_req 而提前停止，但退出状态只反映失败测试数，导致被中断的运行在已完成测试都未失败时返回成功。改为把
    exit_req 纳入失败判定，使调用方能区分「被中断」与「成功」；结果计数仍只统计实际跑过的测试。
  review_outcome: v1 刚发出，暂无 review 意见
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 Tejun 合入 sched_ext 测试树
contribution_opportunities: []
source_email_count: 1
related_articles:
- sched-20260906-001
tags:
- sched_ext
title: 'selftests/sched_ext: Fail interrupted test runs'
layout: article
---

## TL;DR

Tianyi Chen 修 sched_ext selftest runner：被 SIGINT/SIGTERM 中断的运行若已完成测试都未失败会误报成功。把 exit_req 纳入失败判定即可区分「中断」与「成功」。纯测试树修复，severity 低。

## 背景与问题

SIGINT/SIGTERM 会设置 `exit_req`，使 runner 在跑完剩余测试前停止。但退出状态只反映失败测试数，于是当被中断运行里已完成的测试都没有失败时，整体返回成功——把「被中断」误判成「成功」。

## 技术方案

把 `exit_req` 纳入失败条件，使调用方能区分「被中断的运行」与「成功的运行」；同时保持结果计数只覆盖实际跑过的测试。

## 版本演进与当前进展

v1 首次发出，无 review 意见。作者在 GDB 下对真实 runner 注入信号验证：在首个测试前、以及在某个示例测试通过后分别投递信号，原始 runner 四种情况都返回 0，修复后返回 1；正常 `-h/-l/-t` 示例调用仍返回 0。补丁 `Fixes: 9d851afa4826`，并标注 `Assisted-by: LLM`。

## Maintainer 意见与讨论焦点

v1 刚发出，暂无维护者意见。

## 合入评估

selftest 行为正确性修复，无争议，`likelihood=high`。

## 效果评估

作者给出 GDB 信号注入验证（原返回 0、修复后返回 1），属测试正确性验证，无性能数字。

## 我可以参与的点

当前阶段暂无明显参与空间，可持续观察后续版本（CI 是否采纳该中断判定）。

## 参考链接

- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到
