---
id: sched-20261120-014
date: '2026-11-20'
subject: 'sched: Tell rq_online() and rq_offline() whether the CPU changes state'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261118-bug-sched-fair-offline-active-v2-0-b6ede596c6a6@linux.dev>
lore_url: https://lore.kernel.org/all/20261120015130.41615-1-qiliang.yuan@linux.dev/
authors:
- Qiliang Yuan
maintainers_involved: []
current_version: v2
patch_series:
- version: v2
  msgid: <20261118-bug-sched-fair-offline-active-v2-0-b6ede596c6a6@linux.dev>
  date: '2026-11-18'
  summary: 3 补丁：给 rq_online/rq_offline 传 hotplug 布尔，fair 类在根域变化时跳过不必要工作
  review_outcome: 作者宣布 v3 改走独立回调（Prateek 方案）
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 系列正文未捕获
  - v3 尚未发出
  next_action: 作者出 v3（独立回调方案）后交维护者评审
contribution_opportunities:
- kind: review
  description: 核对独立回调方案是否避免 rt/dl 空接参数及 fair 状态与 root domain 无关性
- kind: discussion
  description: 就传 bool 与独立回调两方案取舍补充判断
generated_at: '2026-11-21T09:00:00+08:00'
source_email_count: 216
related_articles: []
tags:
- topology
- cfs
title: 'sched: Tell rq_online() and rq_offline() whether the CPU changes state'
layout: article
---

## TL;DR

Qiliang Yuan 的 v2 3 补丁系列：给 `rq_online()`/`rq_offline()` 传入「CPU 是否改变状态（hotplug）」标志，让 fair 类在根域改变（而非 hotplug）时跳过不必要工作。当日缓存仅含两条回复：作者 Qiliang 解释设计并宣布 v3 将按 Prateek Nayak 的思路改为「root domain 变化用独立回调」；Li kunyu 表示期待 v3。补丁/cover 正文未在当日缓存。

## 背景与问题

`rq_online()`/`rq_offline()` 在两种情形被调用：CPU hotplug（状态真正改变）与 sched domain 重建（CPU 仍 active）。fair 类的 `rq_online_fair()`/`rq_offline_fair()` 处理 task group 的 throttling 与「bandwidth switch」，这些只依赖 hotplug、不依赖 root domain，故在纯 root domain 变化时可跳过。rt/dl 类的回调处理的是 rto_mask/cpupri/dlo_mask/cpudl 等 root domain 内状态，两类情形都要做。系列目标是让两类回调各按需行事。

## 技术方案

v2（`linux.dev` 分支 `bug-sched-fair-offline-active`）给回调加 `hotplug` 布尔参数：fair 的 `rq_offline_fair()` 在 `!hotplug` 时提前返回、`rq_online_fair()` 仅在 hotplug 时 `update_runtime_enabled()`；rt/dl 回调因共享 `sched_class` 回调类型而被迫接收该参数却不使用。

Qiliang 在回复中宣布：既然只有 fair 需要区分，v3 将沿 Prateek Nayak 的思路重构——为 root domain 变化提供独立回调（仅 rt/dl 实现），`rq_online()`/`rq_offline()` 留给 hotplug、无需参数。Peter 的 v1 建议是「传 bool」，Prateek 的备选是「独立回调」，作者最终选后者。

## 版本演进与当前进展

*current_version: v2（2026-11-18，`<20261118-bug-sched-fair-offline-active-v2-0-b6ede596c6a6@linux.dev>`，3 补丁）*。今日为讨论日：作者宣布 v3 重构方向。

## Maintainer 意见与讨论焦点

- **Qiliang Yuan（作者）**：给出各回调在 hotplug/root domain 变化下具体工作的对照表，宣布 v3 改走 Prateek 的「独立回调」路线。
- **Li kunyu（社区评审，非维护者）**：确认已在 patch 2/3 找到相关调用，期待 v3。
- 此前 Peter（v1）建议传 bool；Prateek（v1，AMD）提议独立回调。无 NAK。

## 合入评估

*likelihood=unknown*。重构方向明确（v3 走独立回调），但补丁/cover 正文未捕获、且尚未见维护者对 v2 的合入表态，不足以判断。*blocking_issues*：系列正文未捕获；v3 尚未发出。*next_action*：作者出 v3（独立回调方案）后交维护者评审。

## 效果评估

无数据（补丁正文未获取到，仅见重构方向讨论）。

## 我可以参与的点

- **review**：核对「独立回调」方案是否真能避免 rt/dl 空接参数，以及 fair 的 throttling/bandwidth switch 状态是否确与 root domain 无关。
- **discussion**：就 v2 传 bool 与 Prateek 独立回调两方案的取舍补充判断。

## 参考链接

- lore thread（作者 v2 回复）: https://lore.kernel.org/all/20261120015130.41615-1-qiliang.yuan@linux.dev/
- v2 cover（未获取到正文，msgid）: https://lore.kernel.org/all/20261118-bug-sched-fair-offline-active-v2-0-b6ede596c6a6@linux.dev/
