---
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261031170541.710939-1-tj@kernel.org>
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series: []
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 Tejun 收取进 sched_ext/for-7.4-fixes
contribution_opportunities:
- kind: testing
  description: runtime CPU hotplug 下验证 enqueue 不再先于 cpu_online 触发
upstream_commit: null
fixes_commit: null
merged_branch: null
source_email_count: 1
related_articles:
- sched-20261101-003
tags:
- sched_ext
id: sched-20261102-017
subject: 'sched_ext: Fix ops.enqueue/dispatch() calls before ops.cpu_online()'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
title: 'sched_ext: Fix ops.enqueue/dispatch() calls before ops.cpu_online()'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/11/01/sched-20261101-003-sched-ext-fix-ops-enqueue-dispatch-calls-before-ops-cpu-onli.html">sched-20261101-003</a>：修 runtime CPU up 时 sched 域重建令 rq 提前 online、导致 `ops.cpu_online()` 之前调用 `ops.enqueue()/dispatch()`；方案移除 rq_online/rq_offline 钩子、改在 `handle_hotplug()` 统一管 SCX_RQ_ONLINE（两补丁，for-7.4-fixes，Cc stable v6.12+）。
- sched-20261102（今天）：Andrea Righi 回帖 **Reviewed-by 两个补丁**（"look good to me, haven't found any issues"），系列获维护者侧认可，等待收取。

## 背景与问题

（承接）`ops.cpu_online()` 的文档承诺与 SCX_RQ_ONLINE 门控被 sched 域重建顺序破坏，导致 online 之前触发 `ops.enqueue()/dispatch()`。

## 技术方案

（承接）`handle_hotplug()` 单独跟踪 SCX_RQ_ONLINE，放在 `ops.cpu_online()` 之后置位；sched 域重建不再触碰该标志。今日无代码变更，仅新增 review 背书。

## 版本演进与当前进展

两补丁系列，今日拿到 Andrea Righi 双 Reviewed-by。

## Maintainer 意见与讨论焦点

Andrea Righi（sched_ext 核心 reviewer）全篇认可，无遗留问题。

## 合入评估

likelihood=high。维护者侧 reviewer 已 RB，预期进 sched_ext/for-7.4-fixes。

## 效果评估

（承接）正确性修复，无性能数据。

## 我可以参与的点

- testing：在运行时 CPU hotplug 场景验证 `ops.enqueue()` 不再先于 `ops.cpu_online()` 触发。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261031170541.710939-1-tj@kernel.org/
