---
id: sched-20261009-011
date: '2026-10-09'
subject: 'sched_ext: Keep proxy donors with slice left on the local DSQ'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261002221559.3090900-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/b064c79615e33deb06e9483e4ddf23c4@kernel.org/
authors:
- Andrea Righi
maintainers_involved:
- Tejun Heo
current_version: v2
patch_series:
- version: v1
  msgid: <20261001191216.2391359-1-arighi@nvidia.com>
  date: '2026-10-02'
  summary: 本地 DSQ 头部 + PICK_PENDING 区分记账性 put
  review_outcome: Tejun 提出 IMMED 全面豁免，催生 v2
- version: v2
  msgid: <20261002221559.3090900-1-arighi@nvidia.com>
  date: '2026-10-02'
  summary: 删 PICK_PENDING；IMMED 全面豁免；折进普通 enqueue 路径
  review_outcome: 10-07 Tejun 收回方向；10-09 确认 Andrea 双标志方案，v3 待发
upstream_commit: null
fixes_commit: ee172227d0dc
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - v3 未发出
  next_action: Andrea 发 v3（双标志版）并过审
contribution_opportunities:
- kind: review
  description: 复核 PROXY_BLOCKING 标志是否覆盖 proxy_reset_donor 全部路径
- kind: testing
  description: IMMED donor 被更高类抢占场景对比 v3 重放置时延
generated_at: '2026-10-10T01:30:00'
source_email_count: 1
related_articles:
- sched-20261002-008
- sched-20261003-001
- sched-20261007-005
tags:
- sched_ext
- proxy_execution
title: 'sched_ext: Keep proxy donors with slice left on the local DSQ'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-008-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.html">sched-20261002-008</a>：Andrea Righi（NVIDIA，sched_ext 维护者）发往 `sched_ext/for-7.4` 的单补丁修复——commit ee172227d0dc 让 `put_prev_task_scx()` 把保留的 proxy donor 以 `SCX_ENQ_BLOCKED` 交还 `ops.enqueue()`，但三类 put 只是 proxy 记账，BPF 被迫反复做无意义 dispatch；补丁改为有 slice 剩余的 donor 放本地 DSQ 头部，并用新 `SCX_RQ_PROXY_PICK_PENDING` rq 标志区分「记账性 put」与「真实 IMMED 抢占」。
- <a class="article-ref" href="/lkm/2026/10/03/sched-20261003-001-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.html">sched-20261003-001</a>：Tejun Heo 提出根本性质疑——IMMED 对 blocked donor 不该起作用；若成立，有 slice 的 donor 无论 IMMED 与否都留本地 DSQ，`SCX_RQ_PROXY_PICK_PENDING` 整个不需要。Andrea 认同并当天发 v2 全部采纳。
- <a class="article-ref" href="/lkm/2026/10/07/sched-20261007-005-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.html">sched-20261007-005</a>：**Tejun 收回自己 10-03 的方向**（"Sorry, I steered this the wrong way"）——对 donor 全面豁免 IMMED 等于覆盖调度器对该任务的明确意图。正确条件是「只在其马上要被 pick 时保持本地」，要求回到 v1 的 PICK_PENDING 语义。Andrea 提出双 rq 标志（`SCX_RQ_PROXY_PICK_PENDING` + `SCX_RQ_PROXY_BLOCKING`）实现，反问方案是否成立。
- <a class="article-ref" href="/lkm/2026/10/09/sched-20261009-011-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.html">sched-20261009-011</a>（今天）：**Tejun 确认方案成立**（"Yeah, that sounds good to me."）。设计定案，进入 v3 待发阶段。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-008-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.html">sched-20261002-008</a> → <a class="article-ref" href="/lkm/2026/10/03/sched-20261003-001-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.html">sched-20261003-001</a> → <a class="article-ref" href="/lkm/2026/10/07/sched-20261007-005-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.html">sched-20261007-005</a>）proxy execution 下 blocked 在 mutex 上的任务可作为 donor 留在 runqueue；ee172227d0dc 后 `put_prev_task_scx()` 把保留 donor 交还 BPF 造成无意义 dispatch 往返。v1 用「本地 DSQ 头部 + PICK_PENDING 区分记账性 put」解决；v2 按 Tejun 意见改为「IMMED 对 blocked donor 全面豁免」。10-07 Tejun 认定 v2 的全面豁免伤到了「IMMED 表达调度器放置意图」这一层，要求回到 v1 的 PICK_PENDING 语义（细化版），并连带简化（删 blocked 豁免与 wakeup 重查、补 caps 映射注释、ENQ_LAST 不排除 donor）。今天的关键推进：Tejun 对 Andrea 的双标志实现方案表态「sounds good」。

## 技术方案

（承接）10-07 Tejun 定下目标条件 + Andrea 的双标志实现回应；今天 Tejun 对该实现拍板：

1. **回到 PICK_PENDING 语义**：IMMED donor 只在「马上要被 pick」时保持本地（`proxy_resched_idle()` 的记账性 put）；真实抢占则像任何 IMMED 任务一样交还 BPF 经 `ops.enqueue()` 重新放置。
2. **连锁简化**：deferred 扫描不再需要 blocked 豁免；`wakeup_preempt_scx()` 的重查也不需要。
3. **Andrea 的两标志实现**：重新引入 `SCX_RQ_PROXY_PICK_PENDING` + 新增 `SCX_RQ_PROXY_BLOCKING`，两个标志定义在 `sched.h`、逻辑全在 `ext.c`，**不动 `sched/core.c`**。
4. **今天 Tejun 确认**：对 Andrea 上述方案（含 `sched_proxy_block_task()` 里 reset 顺序消 WARN 的思路）回复「Yeah, that sounds good to me.」。

## 版本演进与当前进展

- v1（10-02）：本地 DSQ 头部 + PICK_PENDING（<a class="article-ref" href="/lkm/2026/10/02/sched-20261002-008-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.html">sched-20261002-008</a>）。
- v2（10-03）：删 PICK_PENDING、IMMED 全面豁免（<a class="article-ref" href="/lkm/2026/10/03/sched-20261003-001-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.html">sched-20261003-001</a>）。
- 10-07：Tejun 收回 v2 方向、要求回到 PICK_PENDING（细化版）；Andrea 提出双标志实现。
- 10-09（今天）：Tejun 确认双标志方案成立。**v3 待发**（Andrea 落地双标志实现）。
- 未进任何分支；`Fixes: ee172227d0dc`、base 为 `sched_ext/for-7.4`。

## Maintainer 意见与讨论焦点

- **Tejun Heo**（sched_ext 首席维护者）：10-07 主动纠错并定下 PICK_PENDING 语义；今天对 Andrea 的双标志实现拍板「sounds good」。方向性争议已消除。
- **Andrea Righi**（作者，NVIDIA）：提出的双标志方案（关键卖点是不改 `sched/core.c`）获 Tejun 认可。
- 分歧已从「方向」收敛到「v3 落地细节」，无剩余方向性争议。

## 合入评估

*likelihood=high*。设计已获 Tejun 明确认可，方向定案；唯一剩余动作是 Andrea 落地双标志 v3。*blocking_issues*：v3 尚未发出。*next_action*：Andrea 发 v3（PICK_PENDING + PROXY_BLOCKING 双标志版）并过审。

## 效果评估

无性能数据（记账/时序正确性修复）。核心收益是消除「把保留 donor 反复交还 BPF 的无意义 dispatch 往返」这一 proxy-exec 下的开销。

## 我可以参与的点

- `review`：v3 落地后复核 `SCX_RQ_PROXY_BLOCKING` 是否覆盖 `proxy_reset_donor()` 的全部调用路径。
- `testing`：IMMED donor 被更高调度类抢占场景下对比 v3 的重放置时延。

## 参考链接

- Tejun 今日确认: https://lore.kernel.org/all/b064c79615e33deb06e9483e4ddf23c4@kernel.org/
- v2 封面: https://lore.kernel.org/all/20261002221559.3090900-1-arighi@nvidia.com/
