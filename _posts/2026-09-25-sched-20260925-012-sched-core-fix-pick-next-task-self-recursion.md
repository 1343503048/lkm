---
id: sched-20260925-012
date: 2026-09-25
subject: 'sched/core: Fix pick_next_task() self recursion'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260828101659.812011872@infradead.org>
lore_url: https://lore.kernel.org/all/20260828101659.812011872@infradead.org/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: '2026-09-26T01:15:00'
authors:
- Peter Zijlstra
maintainers_involved:
- Peter Zijlstra
patch_series:
- version: v1
  msgid: <20260828101659.812011872@infradead.org>
  date: 2026-08-28
  summary: 保留本地 core_task_seq 用序列号不匹配检测 pick_next_task 的 core-wide 锁 drop 窗口
  review_outcome: 09-03 Aaron Lu 补充 uncookied fast path 的 core_cookie 检查；09-25 Peter
    认可并加入
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: Peter 并入 Aaron 的 core_cookie 检查后发下一版或直接收进 sched/core
contribution_opportunities:
- kind: review
  description: core scheduling 加固系列其余 6 枚尚未被系统 review，可逐枚审读回帖
- kind: testing
  description: 在启用 CONFIG_SCHED_CORE + 多 HT 任务的高频唤醒/入队压力下复现并验证修复
source_email_count: 1
related_articles: []
tags:
- core_sched
title: 'sched/core: Fix pick_next_task() self recursion'
layout: article
---

## TL;DR

Peter Zijlstra 的 core scheduling 加固系列 1/7（修复 `pick_next_task()` 在 core-wide 锁被 drop 后可能被另一 sibling 重入、踩坏 core-wide 任务选择状态甚至 NULL deref 的问题），今天因 Aaron Lu（bytedance）09-03 的一条补充意见被 Peter 接受并表态「Let me add this」而推进。这是一枚确定性正确性修复，合入可能性高。

## 背景与问题

在 core scheduling（超线程隔离）下，`pick_next_task()` 的 `pick_task()` 可能通过 newidle balance 放下 core-wide 的 `rq->lock`。锁被放下的窗口里，另一个 sibling 可能再次进入 `pick_next_task()`，二者会踩坏共享的 core-wide 任务选择状态，极端情况下导致 NULL 解引用。Peter 的修复思路是保留一份本地 `core_task_seq` 拷贝（该值在 {en,de}queue 和 schedule 时递增），用序列号不匹配来检测这个窗口——因为 `RETRY_TASK` 只可能发生在锁 break 期间有更高优先级任务入队时，而这也必然递增 `core_task_seq`，所以序列号不匹配足以覆盖该情形。

## 技术方案

（Peter 的原始修复 + Aaron Lu 的补充）核心机制：`pick_next_task()` 保留本地 `core_task_seq`，锁重新获取后若序列号不匹配则重试。Aaron Lu 指出一个遗漏：**uncookied no-sync fast path** 里，锁重新获取后还要检查 core-wide 是否仍处于 uncookied 状态——因为 `pick_task()` 放下锁的期间，sibling 可能建立了 core-wide cookie，此时 uncookied 快路径不再成立。他给出具体 diff：在 `if (!next->core_cookie)` 分支里加

```c
if (unlikely(rq->core->core_cookie))
    goto restart;
```

并解释为何这里选择检查 `rq->core->core_cookie` 而不是 `core_task_seq`：若 sibling 选中的是 uncookied 任务，本 rq 走快路径依然安全，所以用 cookie 状态判断比序列号更精确。Peter 回复认可：「I had considered adding the seq check here, but didn't see any problem it would solve. Clearly I missed this case. Let me add this.」

## 版本演进与当前进展

- 08-28：Peter 发出系列（msgid `<20260828101659.812011872@infradead.org>`），1/7 即本枚。
- 09-03：Aaron Lu 回帖指出 uncookied no-sync fast path 的遗漏并给 diff（msgid `<20260903111335.GA3594512@bytedance.com>`）。
- 09-25：Peter 认可并表态加入（msgid `<20260925143356.GO4120091@noisy.programming.kicks-ass.net>`）。系列其余 6 枚本日无新进展。

## Maintainer 意见与讨论焦点

无分歧。Aaron Lu（资深社区成员）的补充被 Peter 当场接受；Peter 坦言此前「考虑过加 seq 检查但没想到它能解决的问题」，等于承认这是一个真实缺口。无 NAK。

## 合入评估

*likelihood=high*。维护者已明确「Let me add this」，修复逻辑静态可证，无阻塞项。*next_action*：等 Peter 把 Aaron 的补充并入系列并（可能）发下一版或直接收进 sched/core。

## 效果评估

无 benchmark；这是 core scheduling 下的 NULL deref 防御性修复，正确性由锁窗口分析静态可证。暂无效果数据。

## 我可以参与的点

- `review`：系列其余 6 枚（core scheduling 加固）尚未被系统 review，可逐枚审读并回帖。
- `testing`：在启用 core scheduling（`CONFIG_SCHED_CORE` + 多 HT 任务）的高频唤醒/入队压力下复现并验证修复前后行为。

## 参考链接

- Peter 认可 Aaron 补充: https://lore.kernel.org/all/20260925143356.GO4120091@noisy.programming.kicks-ass.net/
- Aaron Lu 的补充 diff: https://lore.kernel.org/all/20260903111335.GA3594512@bytedance.com/
- 系列 1/7（Peter）: https://lore.kernel.org/all/20260828101659.812011872@infradead.org/
