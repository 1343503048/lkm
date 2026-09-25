---
id: sched-20260925-022
date: 2026-09-25
subject: 'sched_ext: Test scx_has_subs() inline before calling sub-sched hooks'
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: <186976febe6753fa0105d144d8d7e59b@kernel.org>
lore_url: https://lore.kernel.org/all/186976febe6753fa0105d144d8d7e59b@kernel.org/
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.4
current_version: v1
generated_at: '2026-09-26T01:15:00'
authors:
- Usama Arif
maintainers_involved:
- Tejun Heo
patch_series:
- version: v1
  msgid: <20260924202711.4042339-1-usama.arif@linux.dev>
  date: 2026-09-24
  summary: 调用 sub-sched hooks 前 inline 测试 scx_has_subs()
  review_outcome: 09-25 Tejun 应用到 sched_ext/for-7.4
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已应用到 sched_ext/for-7.4，随合并窗口进主线
contribution_opportunities:
- kind: testing
  description: 在无子调度器的纯 sched_ext 负载下测量短路优化的开销差异
- kind: review
  description: 确认 scx_has_subs inline 化是否引入 include 依赖或 ABI 问题
source_email_count: 1
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Test scx_has_subs() inline before calling sub-sched hooks'
layout: article
---

## TL;DR

Usama Arif 的 sched_ext 小优化补丁：在调用 sub-scheduler（子调度器）hooks 之前先 inline 地测试 `scx_has_subs()`，无子调度器时省掉后续判断/调用开销。已被 Tejun Heo 应用到 sched_ext/for-7.4。补丁正文不在当日缓存中，细节未获取到。

## 背景与问题

sched_ext 支持 sub-scheduler（子调度器）机制。当没有配置任何子调度器时，sub-sched hooks 相关的判断与路径本可被更快短路。该补丁的意图是把 `scx_has_subs()` 的测试提前 inline，避免无子调度器场景下的多余开销。（因补丁正文未在当日邮件缓存中，背景细节以 subject 推断，具体触发路径未获取到。）

## 技术方案

调用 sub-sched hooks 之前 inline 测试 `scx_has_subs()`。具体改动点与 diffstat 未获取到（补丁正文不在当日缓存）。

## 版本演进与当前进展

- v1（2026-09-24，`<20260924202711.4042339-1-usama.arif@linux.dev>`）：首发。
- 09-25：Tejun 回帖「Applied to sched_ext/for-7.4」（msgid `<186976febe6753fa0105d144d8d7e59b@kernel.org>`）。

## Maintainer 意见与讨论焦点

Tejun Heo 直接应用、无异议。无详细 review 记录（当日缓存仅含应用回帖）。

## 合入评估

已应用到 sched_ext/for-7.4（*likelihood=merged*），`merged_branch=sched_ext/for-7.4`。*blocking_issues* 无。

## 效果评估

暂无效果数据（补丁正文未在当日缓存，未获取到 benchmark 数字）。

## 我可以参与的点

- `testing`：在无子调度器的纯 sched_ext 负载下测量该短路优化的实际开销差异（若可复现）。
- `review`：确认 `scx_has_subs()` inline 化是否引入任何 include 依赖或 ABI 问题。

## 参考链接

- Tejun 应用回帖: https://lore.kernel.org/all/186976febe6753fa0105d144d8d7e59b@kernel.org/
- 补丁（未在当日缓存，msgid 供追溯）: 20260924202711.4042339-1-usama.arif@linux.dev
