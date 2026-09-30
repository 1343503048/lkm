---
id: sched-20260930-006
date: '2026-09-30'
subject: 'sched/core: Fix context analysis errors in non-preferred CPU push'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260929164712.1054883-1-sshegde@linux.ibm.com>
lore_url: https://lore.kernel.org/all/20260929164712.1054883-1-sshegde@linux.ibm.com/
authors:
- Shrikanth Hegde
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260929164712.1054883-1-sshegde@linux.ibm.com>
  date: '2026-09-30'
  summary: 把 context_unsafe_alias(rq) 移到 rq_lock() 之前，修复 clang23 线程安全分析误报
  review_outcome: 'Nathan 给 Tested-by # build'
upstream_commit: null
fixes_commit: 74699f56ebcf
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 尚未见维护者收取
  next_action: 由 sched/core 维护者收取进 tip
contribution_opportunities:
- kind: testing
  description: 用 clang23 + CONFIG_PREFERRED_CPU=y 验证构建通过、=n 配置无回归
- kind: review
  description: 核对该函数其余加锁点是否还有「加锁后再切 rq 别名」的静态分析盲区
generated_at: '2026-10-01T01:00:00'
source_email_count: 2
related_articles: []
tags:
- cfs
title: 'sched/core: Fix context analysis errors in non-preferred CPU push'
layout: article
---

> **subject**：`sched/core: Fix context analysis errors in non-preferred CPU push`

## TL;DR

Shrikanth Hegde 的 sched/core 构建修复：`CONFIG_PREFERRED_CPU=y` 下 clang23 的线程安全分析报错——`context_unsafe_alias(rq)` 被放在 `rq_lock()` 之后，此时已把锁与原始 `rq` 别名关联，后续改 `rq` 别名与 `rq_unlock()` 触发「释放未持有/并非所有路径都持有」的静态告警。补丁把 alias barrier 移到 `rq_lock()` 之前。带 `Fixes: 74699f56ebcf`（"sched/core: Push current task from non preferred CPU"）与 `Reported-by: Nathan Chancellor`；Nathan 已给 `Tested-by # build`。属纯构建正确性修复，无运行时影响。

## 背景与问题

Nathan Chancellor 报告 clang23 在 `CONFIG_PREFERRED_CPU=y` 时构建失败：

```
kernel/sched/core.c:11298:3: error: releasing raw_spinlock 'rq_lockp(rq)' that was not held [-Werror,-Wthread-safety-analysis]
kernel/sched/core.c:11303:1: error: raw_spinlock 'rq_lockp(__this_rq())' is not held on every path through here
```

根因是 commit 74699f56ebcf 引入的 `context_unsafe_alias(rq)` 被放在 `rq_lock()` 之后——此时线程安全分析已把锁与原始 `rq` 别名关联，之后切换 `rq` 别名（改指另一个 rq）再 `rq_unlock(rq, &rf)`，静态分析认为释放的不是当初持有的锁。

## 技术方案

把 `context_unsafe_alias(rq)` barrier 移到 `rq_lock()` 之前，让「rq 别名会变」这一事实在加锁之前就被分析器计入。纯注释/属性层面的挪动，无功能改动。

## 版本演进与当前进展

v1 刚发出（`<20260929164712.1054883-1-sshegde@linux.ibm.com>`）。当日 Nathan Chancellor 回复「Thanks for the quick fix!」并给 `Tested-by: Nathan Chancellor # build`。

## Maintainer 意见与讨论焦点

当日无维护者表态。报告者 Nathan（clang 内核构建维护者之一）已确认修复有效（`Tested-by # build`）。无 NAK。

## 合入评估

*likelihood=high*。单点、纯静态分析标注挪动的构建修复，带 `Fixes:` 与报告者的 `Tested-by`，风险极低。*blocking_issues*：尚未见维护者收取。*next_action*：由 sched/core 维护者（或 Peter）收取进 tip。

## 效果评估

定性：消除 clang23 + `CONFIG_PREFERRED_CPU=y` 下的 `-Wthread-safety-analysis` 构建失败。无性能数据。

## 我可以参与的点

- `testing`：用 clang23（或更早支持 thread-safety 的 clang）+ `CONFIG_PREFERRED_CPU=y` 验证构建通过、并确认 `=n` 配置无回归。
- `review`：核对该函数中 `rq` 别名的其余加锁点是否还存在同类「加锁后再切换别名」的静态分析盲区。

## 参考链接

- lore（补丁）: https://lore.kernel.org/all/20260929164712.1054883-1-sshegde@linux.ibm.com/
- Nathan 的 Tested-by: https://lore.kernel.org/all/20260929202720.GC3237201@ax162/
