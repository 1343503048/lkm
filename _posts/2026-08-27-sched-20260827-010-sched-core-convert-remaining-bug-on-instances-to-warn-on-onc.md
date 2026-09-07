---
id: sched-20260827-010
date: '2026-08-27'
subject: 'sched/core: Convert remaining BUG_ON() instances to WARN_ON_ONCE()'
subsystem: sched
type: fix
status: stalled
severity: low
thread_root_msgid: <20260827-warn_instead_bug-v1-1-b515c0f74b89@gmail.com>
lore_url: https://lore.kernel.org/all/20260827-warn_instead_bug-v1-1-b515c0f74b89@gmail.com/
authors:
- Amin Gattout
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <20260827-warn_instead_bug-v1-1-b515c0f74b89@gmail.com>
  date: 2026-08-27
  summary: 把 09348d75a6ce 漏掉的 core.c 残留 BUG_ON 转为 WARN_ON_ONCE
  review_outcome: Peter Zijlstra NAK：这些失败点必须保持 BUG_ON
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - 领域维护者明确 NAK，且理由适用于全部转换站点
  next_action: 作者撤回或逐点论证个别站点可降级，预期不会发生
contribution_opportunities: []
generated_at: '2026-09-07T22:05:00'
source_email_count: 2
related_articles: []
tags:
- preempt
title: 'sched/core: Convert remaining BUG_ON() instances to WARN_ON_ONCE()'
layout: article
---

## TL;DR
Amin Gattout 想把 core.c 里 `09348d75a6ce`（调度器 BUG_ON 全面转 WARN_ON_ONCE）漏掉的几处残留也转掉，Peter Zijlstra 两分钟内回复明确否决：这些点**就该**是 BUG_ON——初始化/启动路径失败后没有任何继续的意义。条目以 NAK 告终，但把"哪些失败允许带病运行、哪些必须当场停机"的边界说清了。

## 背景与问题
`Documentation/process/deprecated.rst` 不鼓励 BUG_ON（崩溃使报告/调试更困难，消息常来不及落盘）。09348d75a6ce 已转换调度器主体，core.c 仍剩数处：`sched_tick_offload_init()` 的 `alloc_percpu` 失败、`preempt_schedule_irq()` 的调用者合法性检查等（10+/10-，作者对 arm64 + NO_HZ_FULL + SCHED_CLASS_EXT 做了 build test 保证每个站点都被编译）。

## 技术方案
机械转换 BUG_ON→WARN_ON_ONCE。作者引用的通用论据：WARN_ON_ONCE 给用户报告机会，坚持"不可能状态后不可继续"的系统管理员可用 `panic_on_warn`。

## 版本演进与当前进展
v1 即被 NAK（本封 msgid `<20260827-warn_instead_bug-v1-1-b515c0f74b89@gmail.com>`；Peter 回复 `<20260827114229.GK687043@noisy.programming.kicks-ass.net>`）。大概率不会有 v2。

## Maintainer 意见与讨论焦点
Peter 的否决理由值得记录："These all really should be BUG_ON(), there is absolutely no point in trying to complete the boot if they fail."——与转换过的那批（运行期一致性检查，警告后系统还能跑）不同，这批失败点在启动/不可恢复上下文，继续跑只会产生更糟的现场。这是该系列唯一的 review，讨论即终局。

## 合入评估
**unlikely**。领域维护者直接 NAK 且理由覆盖补丁全部站点；无第三方声援。`next_action`：若作者想继续，只能逐点拆分论证某些站点可以活着（预期收益接近零）。

## 效果评估
无数据（此类补丁无需 benchmark）。

## 我可以参与的点
- 硬约束上无参与价值，但结论本身有用：做 OLK 硬化/移植时，区分"调度器运行期不变量（可 WARN_ON_ONCE）"与"启动期分配/入口检查（保留 BUG_ON）"，不要跟着 deprecated 文档一刀切。

## 参考链接
- lore（v1）: https://lore.kernel.org/all/20260827-warn_instead_bug-v1-1-b515c0f74b89@gmail.com/
- Peter 的 NAK: https://lore.kernel.org/all/20260827114229.GK687043@noisy.programming.kicks-ass.net/
- tip-bot commit: 未获取到
- stable backport: 未获取到
