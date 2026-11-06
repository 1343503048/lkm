---
id: sched-20261106-007
date: 2026-11-06
subject: 'sched_ext: Fix partial-SMT core counting in calc_shard_layout()'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: null
lore_url: null
authors:
- Zhang Qiao
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: null
  date: 2026-11-06
  summary: 修复 calc_shard_layout() 的 partial-SMT core 计数。
  review_outcome: 暂无评审；作者仅 checkpatch+编译验证。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无评审
  - 作者未做真机测试
  next_action: 等待 Tejun Heo 评审并在 partial-SMT 真机验证
contribution_opportunities:
- kind: testing
  description: 在 partial-SMT 硬件上验证 calc_shard_layout shard 布局
- kind: review
  description: 核对 partial-SMT core 计数修正逻辑的拓扑角例覆盖
generated_at: '2026-11-07T09:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261105-010
- sched-20261106-006
tags:
- sched_ext
title: 'sched_ext: Fix partial-SMT core counting in calc_shard_layout()'
layout: article
---

## TL;DR

Zhang Qiao 单独提交的 sched_ext for-7.4-fixes 补丁，修复 `calc_shard_layout()` 在 partial-SMT 系统（部分核开 SMT、部分不开）上的 core 计数错误。这是对昨日 Tejun Heo「把修复单独发出来」要求的直接响应——放弃 `scx_cid_init()` 拆解重构后，把其中的真实 bug 修复独立成补丁。基于 for-7.4-fixes tip（`4c2e0751d5e6`），作者本地 commit `90dc81241273`，已过 checkpatch 与编译验证、未做真机测试。

## 背景与问题

`sched_ext` 的 `calc_shard_layout()` 负责把在线 CPU 按 LLC/cluster/core 拓扑切成 shard（用于 SCX 调度器的 CPU 分组）。在 partial-SMT 系统上——例如某些核是 2-way SMT、另一些核 SMT 被关闭——按「core」计数的方式会算错，导致 shard 布局与实际拓扑不符。单核 shard 的硬上限角例（hard-cap）已被另一提交 `651694bc47a1` 覆盖，本补丁专注剩余的 partial-SMT core 计数问题。

## 技术方案

补丁修正 `calc_shard_layout()` 对 partial-SMT 场景的 core 计数逻辑（具体 diff 在邮件附件中，未内嵌正文）。补丁主题前缀已带 `sched_ext/for-7.4-fixes`，基于 for-7.4-fixes tip `4c2e0751d5e6`，作者本地 commit `90dc81241273`。

## 版本演进与当前进展

*current_version: v1（2026-11-06 发出）*。这是「拆解重构被否决后、单独发修复」的第一步。作者自述补丁已过 checkpatch 与编译验证，但未做真机测试；正式提交 LKML 时补丁须内嵌正文（git send-email），本文基于的缓存邮件为作者经 QQ 邮箱发送的清单/附件草稿（含 patch、给 Tejun 的回帖草稿、发送清单三个附件），LKML 内联版本链接未获取到。

## Maintainer 意见与讨论焦点

暂无评审。Tejun Heo 此前在拆解线程（<a class="article-ref" href="/lkm/2026/11/06/sched-20261106-006-sched-ext-decompose-scx-cid-init.html">sched-20261106-006</a>）明确要求「把修复单独发出来」，本补丁正是该要求的落实，方向符合维护者预期。

## 合入评估

*likelihood=unknown*。补丁刚单独发出、尚无评审；它落在维护者明确认可的「单独发修复」路径上，但需通过评审与真机验证。*blocking_issues*：① 无评审；② 作者未做真机测试（checklist 自述）。*next_action*：等待 Tejun Heo 评审，并在 partial-SMT 真机上验证。

## 效果评估

暂无效果数据。作者在发送清单中注明「未做真机测试」（仅 checkpatch 与编译验证），修复效果为主观判断、未见测试数据。

## 我可以参与的点

- **testing**：在 partial-SMT（部分核关 SMT）的硬件上验证 `calc_shard_layout()` 的 shard 布局是否与实际拓扑一致——作者明确缺真机测试，这是最直接的参与点。
- **review**：核对 partial-SMT core 计数的修正逻辑是否覆盖所有拓扑角例。

## 参考链接

- lore 链接未获取到（本日缓存为作者 QQ 邮箱清单/附件草稿，非 LKML 内联补丁；`thread_root_msgid`/`lore_url` 无法取得真实 lore 值，按规则置 null）。
