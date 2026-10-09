---
id: sched-20261002-019
date: '2026-10-02'
subject: 'sched/core: Fix context analysis errors in non-preferred CPU push'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <20260929164712.1054883-1-sshegde@linux.ibm.com>
lore_url: https://lore.kernel.org/all/20260929164712.1054883-1-sshegde@linux.ibm.com/
authors:
- Shrikanth Hegde
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <20260929164712.1054883-1-sshegde@linux.ibm.com>
  date: '2026-09-29'
  summary: context_unsafe_alias(rq) 移到 rq_lock() 之前
  review_outcome: 'Nathan Tested-by # build；10-01 合入 tip/sched/core'
upstream_commit: 4b1f75be23c4fb0016a102d1cb108ba355c4c00d
fixes_commit: 74699f56ebcf
merged_branch: tip/sched/core
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 无
contribution_opportunities: []
generated_at: '2026-10-03T01:00:00'
source_email_count: 1
related_articles:
- sched-20260930-006
tags:
- build
- core
title: 'sched/core: Fix context analysis errors in non-preferred CPU push'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-006-sched-core-fix-context-analysis-errors-in-non-preferred-cpu.html">sched-20260930-006</a>：Shrikanth Hegde 发出构建修复——`CONFIG_PREFERRED_CPU=y` 下 clang23 线程安全分析报错，根因是 commit 74699f56ebcf 把 `context_unsafe_alias(rq)` 放在 `rq_lock()` 之后，静态分析此时已把锁与原始 `rq` 别名关联，后续换别名再 `rq_unlock()` 触发「释放未持有锁」告警。补丁把 alias barrier 移到 `rq_lock()` 之前；Nathan Chancellor 已给 `Tested-by # build`。
- <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-019-sched-core-fix-context-analysis-errors-in-non-preferred-cpu.html">sched-20261002-019</a>（今天）：**该补丁已被 Peter Zijlstra 合入 tip/sched/core**（commit `4b1f75be23c4fb0016a102d1cb108ba355c4c00d`，CommitterDate 2026-10-01，tip-bot 于 10-02 回帖公告）。合入版带 `Closes:` Nathan 的报告链接与 `Tested-by: Nathan Chancellor # build`。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-006-sched-core-fix-context-analysis-errors-in-non-preferred-cpu.html">sched-20260930-006</a>）Nathan Chancellor 报告 clang23 在 `CONFIG_PREFERRED_CPU=y` 时构建失败：

```
kernel/sched/core.c:11298:3: error: releasing raw_spinlock 'rq_lockp(rq)' that was not held [-Werror,-Wthread-safety-analysis]
kernel/sched/core.c:11303:1: error: raw_spinlock 'rq_lockp(__this_rq())' is not held on every path through here
```

根因：commit 74699f56ebcf（"sched/core: Push current task from non preferred CPU"）引入的 `context_unsafe_alias(rq)` 被放在 `rq_lock()` 之后——线程安全分析已把锁与原始 `rq` 别名关联，之后切换 `rq` 别名（改指另一个 rq）再 `rq_unlock(rq, &rf)`，静态分析认为释放的不是当初持有的锁。

## 技术方案

（承接）把 `context_unsafe_alias(rq)` barrier 移到 `rq_lock()` 之前（`kernel/sched/core.c` +1/−1），让「rq 别名会变」这一事实在加锁之前就被分析器计入。`sched_non_preferred_cpu_push_stop()` 中具体是从 `update_rq_clock()` 之后挪到 `select_fallback_rq()` 之后、`rq_lock()` 之前。纯分析器层面的挪动，无功能改动。

## 版本演进与当前进展

- v1（09-29，`<20260929164712.1054883-1-sshegde@linux.ibm.com>`）：单补丁 +1/−1，带 `Fixes: 74699f56ebcf`、`Closes: https://lore.kernel.org/all/20260929121838.GA1814129@ax162/`、`Reported-by`/`Tested-by: Nathan Chancellor # build`。
- 10-01 合入 tip/sched/core（commit `4b1f75be23c4fb0016a102d1cb108ba355c4c00d`），10-02 tip-bot 公告。

## Maintainer 意见与讨论焦点

- 无 NAK，无额外讨论：补丁发出两天即被 Peter Zijlstra 收取。Nathan Chancellor 的构建测试报告（Reported-by + Tested-by）是唯一外部输入。

## 合入评估

*likelihood=merged*。已合入 `tip/sched/core`（commit `4b1f75be23c4fb0016a102d1cb108ba355c4c00d`）。纯构建正确性修复，无运行时影响；带 `Fixes:` 标签，若 74699f56ebcf 已随本周期进主线，回合 stable 时应带上本修复。*blocking_issues*：无。*next_action*：无。

## 效果评估

修复后 clang23 `CONFIG_PREFERRED_CPU=y` 构建通过（Nathan `Tested-by # build`）。无运行时行为变化，无性能数据。

## 我可以参与的点

- （无——单行修复已合入，无后续参与空间。）

## 参考链接

- lore（补丁）: https://lore.kernel.org/all/20260929164712.1054883-1-sshegde@linux.ibm.com/
- lore（Nathan 报告）: https://lore.kernel.org/all/20260929121838.GA1814129@ax162/
- tip commit: https://git.kernel.org/tip/4b1f75be23c4fb0016a102d1cb108ba355c4c00d
