# sched/proxy: Correct the SCHED_PROXY_EXEC dependency comment

> **subject**：`sched/proxy: Correct the SCHED_PROXY_EXEC dependency comment`

## TL;DR

Quchaosheng 的一枚仅注释类补丁：想修正 `SCHED_PROXY_EXEC` 对 `!PREEMPT_RT` 依赖的注释——指出现有注释「Avoid some build failures w/ PREEMPT_RT until it can be fixed」只描述了依赖移除后的结果而非其存在原因，且「fixed」从未定义；作者给出真正根因（PREEMPT_RT 下 mutex 是 rt_mutex，PI 路径取 `pi_lock`/`rq->lock` 与 `find_proxy_task()` 取 `wait_lock` 形成环）。但在 reviewer 指出原注释对目标读者已足够清晰后，作者于当日**撤回补丁**（「the patch is withdrawn. Sorry for the noise」）。无功能改动。

## 背景与问题

`SCHED_PROXY_EXEC` 在 `!PREEMPT_RT` 下的依赖注释写着「Avoid some build failures w/ PREEMPT_RT until it can be fixed」——作者认为这描述的是「依赖一旦移除后会发生什么」，而非「依赖为何存在」，「fixed」也从未被定义，无法判断何时能移除依赖。作者进一步指出真正的约束：PREEMPT_RT 下 mutex 是 rt_mutex，其 PI 路径在 `wait_lock` 下取 `pi_lock`、在 `pi_lock` 下取 `rq->lock`，而 `find_proxy_task()` 在 `rq->lock` 下取 `mutex->wait_lock`，形成 `wait_lock → pi_lock → rq->lock → wait_lock` 环；该环只因 PREEMPT_RT 下无人设 `blocked_on` 而休眠，且一旦 mutex 不再是 rt_mutex（也正是可移除依赖的条件）即消失。

## 技术方案

原计划是把这个根因写进注释（纯注释改动，无功能变更）。但作者在得到回复后主动撤回，未继续推进。

## 版本演进与当前进展

v1 发出（`<20260930025824.79296-1-quchaosheng000406@163.com>`）后，作者本人（用名 Chaosheng Qu）回帖表示「Dropping it, the patch is withdrawn」，补丁撤回。

## Maintainer 意见与讨论焦点

- 无正式维护者表态。作者在自述中承认原注释「对它所面向的读者读起来是通的」，自己是把它当「开发者笔记（何时能移除依赖）」来读，而那不是注释的本意，遂撤回。

## 合入评估

*likelihood=rejected*。作者已主动撤回补丁，不会进入主线。*blocking_issues*：作者撤回。*next_action*：无需推进；若未来有人需要澄清 `!PREEMPT_RT` 依赖的可移除条件，可重提带根因说明的注释补丁。

## 效果评估

无功能/性能影响（纯注释，且已撤回）。

## 我可以参与的点

- `review`：该系列已撤回，暂无明显参与空间。对 proxy execution 的 `wait_lock/pi_lock/rq->lock` 锁序（及 PREEMPT_RT 下 rt_mutex PI 的 `blocked_on` 行为）感兴趣者，可关注其后续「移除依赖」的实质工作。

## 参考链接

- lore（补丁）: https://lore.kernel.org/all/20260930025824.79296-1-quchaosheng000406@163.com/
- 作者撤回: https://lore.kernel.org/all/6ABCAD0D.07A826.00008@m16.mail.163.com/

---
id: sched-20260930-007
date: '2026-09-30'
subject: 'sched/proxy: Correct the SCHED_PROXY_EXEC dependency comment'
subsystem: sched
type: discussion
status: superseded
severity: none
thread_root_msgid: '<20260930025824.79296-1-quchaosheng000406@163.com>'
lore_url: 'https://lore.kernel.org/all/20260930025824.79296-1-quchaosheng000406@163.com/'
authors:
  - 'Quchaosheng'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260930025824.79296-1-quchaosheng000406@163.com>'
    date: '2026-09-30'
    summary: '修正 SCHED_PROXY_EXEC 的 !PREEMPT_RT 依赖注释（纯注释）'
    review_outcome: '作者撤回补丁'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: rejected
  blocking_issues:
    - '作者已主动撤回补丁'
  next_action: '无需推进；关注 proxy execution 依赖移除的实质工作'
contribution_opportunities:
  - kind: discussion
    description: '关注 proxy execution 在 PREEMPT_RT 下的 rt_mutex PI 锁序与 blocked_on 行为，评估依赖移除条件'
generated_at: '2026-10-01T01:00:00'
source_email_count: 2
related_articles: []
tags:
  - proxy_execution
---