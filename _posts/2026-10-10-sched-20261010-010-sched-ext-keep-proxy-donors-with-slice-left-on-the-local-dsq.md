---
id: sched-20261010-010
date: '2026-10-10'
subject: 'sched_ext: Keep proxy donors with slice left on the local DSQ'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261010090621.184717-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20261010090621.184717-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Tejun Heo
current_version: v4
patch_series:
- version: v3
  msgid: <20261009200827.4026499-1-arighi@nvidia.com>
  date: '2026-10-10'
  summary: 落地双标志（PICK_PENDING + PROXY_BLOCKING），blocked donor 收 ENQ_LAST
  review_outcome: Tejun 抓到 bypass WARN 与更高类抢占 reenqueue 两问题
- version: v4
  msgid: <20261010090621.184717-1-arighi@nvidia.com>
  date: '2026-10-10'
  summary: 记账 put 跳过 ENQ_LAST 路径；更高类抢占后本地 reenqueue
  review_outcome: 待 Tejun review
upstream_commit: null
fixes_commit: ee172227d0dc
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - v4 尚无 Tejun 回帖
  next_action: Tejun review v4 后进 sched_ext/for-7.4
contribution_opportunities:
- kind: testing
  description: 按 16 CPU VM + pipe mutex 争用 + scx_qmap -X 复现验证 v4 不再 WARN
- kind: review
  description: 复核更高类抢占后本地 reenqueue 对 enabled/disabling 的覆盖
generated_at: '2026-10-11T09:00:00'
source_email_count: 3
related_articles:
- sched-20261002-008
- sched-20261003-001
- sched-20261007-005
- sched-20261009-011
tags:
- sched_ext
- proxy_execution
title: 'sched_ext: Keep proxy donors with slice left on the local DSQ'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-008-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.html">sched-20261002-008</a>：Andrea Righi（NVIDIA，sched_ext 维护者）发 `sched_ext/for-7.4` 单补丁——commit ee172227d0dc 让 `put_prev_task_scx()` 把保留 proxy donor 以 `SCX_ENQ_BLOCKED` 交还 `ops.enqueue()`，但三类 put 只是 proxy 记账，BPF 被迫反复做无意义 dispatch；补丁改为有 slice 的 donor 放本地 DSQ 头部，并用 `SCX_RQ_PROXY_PICK_PENDING` 区分「记账性 put」与「真实 IMMED 抢占」。
- <a class="article-ref" href="/lkm/2026/10/03/sched-20261003-001-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.html">sched-20261003-001</a>：Tejun 提出根本质疑——IMMED 对 blocked donor 不该起作用（donor 正被 proxy execution 服务中）；Andrea 认同并当天发 v2 全部采纳：删 PICK_PENDING、IMMED 全面豁免。
- <a class="article-ref" href="/lkm/2026/10/07/sched-20261007-005-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.html">sched-20261007-005</a>：Tejun 收回自己 10-03 的方向（「Sorry, I steered this the wrong way」）——全面豁免覆盖了调度器对任务的明确意图；正确条件是「只在其马上要被 pick 时保持本地」，要求回到 v1 的 PICK_PENDING 语义。Andrea 提出双 rq 标志实现。
- <a class="article-ref" href="/lkm/2026/10/09/sched-20261009-011-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.html">sched-20261009-011</a>：Tejun 确认双标志方案成立（「Yeah, that sounds good to me」），进入 v3 待发。
- <a class="article-ref" href="/lkm/2026/10/10/sched-20261010-010-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.html">sched-20261010-010</a>（今天）：**Andrea 当天连发 v3→v4**。v3 落地双标志设计；Tejun review v3 发现 bypass 路径 WARN（bypass 测试跳过 keep、put 落到 ENQ_LAST 分支，无 ENQ_LAST 的 ENQ_BLOCKED 调度器触发 WARN，16 CPU VM 上 pipe mutex 争用复现）与「更高类抢占后 IMMED donor 停在 local DSQ」问题；**v4 当天修复这两处**（代理记账 put 跳过 ENQ_LAST 路径；更高类抢占后调度一次本地 reenqueue）。v4 尚未获 Tejun 回帖。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-008-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.html">sched-20261002-008</a> → 20261003-001 → 20261007-005 → 20261009-011）proxy execution 下 blocked 在 mutex 上的任务可作为 donor 留在 runqueue；ee172227d0dc 后 `put_prev_task_scx()` 把保留 donor 交还 BPF 造成无意义 dispatch 往返。10-07 Tejun 定下正确方向：IMMED donor 只在「马上要被 pick」的记账性 put 时保持本地，真实抢占仍交还 BPF；10-09 Tejun 确认 Andrea 的双标志（`SCX_RQ_PROXY_PICK_PENDING` + `SCX_RQ_PROXY_BLOCKING`）方案成立。今天的问题是 v3 落地的**代码级 bug**——两条 bypass/抢占边界路径没有按新语义收口。

## 技术方案
（承接 v1/v2 框架 + 10-07/10-09 双标志定稿）v3 落地：恢复 `SCX_RQ_PROXY_PICK_PENDING` 区分记账性 put 与真实 IMMED 抢占；用 `SCX_ENQ_IMMED` 做临时本地插入；blocked donor 允许收 `SCX_ENQ_LAST`；所有者变更时置 `SCX_RQ_PROXY_BLOCKING`、跳过 reenqueue。

Tejun review v3（`<61e309273c68312c1c68e3da2ea45394@kernel.org>`）指出两点，v4（`<20261010090621.184717-1-arighi@nvidia.com>`）据此修正：

1. **bypass 路径 WARN**：bypass 测试把一个 proxy_put 也跳过 keep，导致 put 落到以 idle 为 `@next` 的 ENQ_LAST 分支，对无 ENQ_LAST 的 ENQ_BLOCKED 调度器 WARN；每个在 enable/disable 期间被 pick 又经 `proxy_resched_idle()` 放回的 blocked donor 都命中。修复：代理记账 put 跳过 SCX_ENQ_LAST 路径（v4 Changes 第 2 条）。
2. **更高优先级类抢占**：插入时 `rq->next_class` 仍是 ext，`proxy_resched_idle()` 随后把它降为 idle、IMMED donor 停在 local DSQ；更高类醒来走 idle 的 `wakeup_preempt()` 而非 `wakeup_preempt_scx()`，donor 落到新任务后面。修复：更高类抢占后调度一次本地 reenqueue，让被「停靠」的 IMMED donor 回到 BPF（v4 Changes 第 1 条）。

v4 还把 `SCX_ENQ_IMMED`/`SCX_ENQ_BLOCKED` 的文档按新语义改写，并保留「slice 用尽的 donor 走常规 put 路径可收 ENQ_LAST」的语义。

## 版本演进与当前进展
- v1/v2（10-02/10-03）：见 related_articles。
- v3（今天，`<20261009200827.4026499-1-arighi@nvidia.com>`）：落地双标志（PICK_PENDING + PROXY_BLOCKING），恢复 PICK_PENDING 区分记账 put 与真实抢占，blocked donor 收 ENQ_LAST。
- Tejun review v3（today）：bypass WARN + 更高类抢占 reenqueue 两个问题，另指出 `SCX_ENQ_IMMED` 注释仍是 v2、`dispatch_one()`/`dsq_inc_nr()` 等注释与 v3 逻辑脱节的杂项。
- v4（今天，`<20261010090621.184717-1-arighi@nvidia.com>`）：修 bypass WARN（记账 put 跳过 ENQ_LAST）+ 更高类抢占后本地 reenqueue。

## Maintainer 意见与讨论焦点
- **Tejun Heo**（sched_ext 首席维护者）：10-07/10-09 定方向；今天对 v3 做代码级 review，抓到 bypass WARN（自述 16 CPU VM 复现）与更高类抢占导致的 donor 停靠问题，并连带澄清 v3 与注释的一致性。方向仍认可，无 NAK。
- **Andrea Righi**（作者）：当天 v4 全部落点修复两处问题。
- 分歧已从「方向」缩到「v4 的实现是否正确」，无剩余方向性争议。

## 合入评估
*likelihood=high*。设计已获 Tejun 拍板，v3 的两处代码级问题当天被 v4 修复；只差 Tejun 对 v4 的最终 review。*blocking_issues*：v4 尚无 Tejun 回帖。*next_action*：Tejun review v4 后进 `sched_ext/for-7.4`，随 7.4 窗口上行。

## 效果评估
本补丁为语义/正确性修复（消除 BPF 无意义 dispatch 往返 + 假 WARN），无性能数据；Tejun 的 bypass WARN 在 16 CPU VM 上以 pipe mutex 争用 + 循环 `scx_qmap -X` 复现，v4 旨在消除该 WARN。

## 我可以参与的点
- 按 Tejun 的复现步骤（16 CPU VM、pipe mutex 争用 + 循环 `scx_qmap -X`）验证 v4 不再触发 bypass 路径 WARN；
- 复核更高类抢占后「本地 reenqueue」是否覆盖 enabled/disabling 两条路径。

## 参考链接
- v3: https://lore.kernel.org/all/20261009200827.4026499-1-arighi@nvidia.com/
- Tejun review v3: https://lore.kernel.org/all/61e309273c68312c1c68e3da2ea45394@kernel.org/
- v4: https://lore.kernel.org/all/20261010090621.184717-1-arighi@nvidia.com/
