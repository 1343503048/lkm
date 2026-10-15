---
id: sched-20261015-025
date: 2026-10-15
subject: 'sched_ext: Keep proxy donors with slice left on the local DSQ'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <20261010090621.184717-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20261010090621.184717-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Tejun Heo
current_version: v4
patch_series:
- version: v1
  msgid: null
  date: 2026-10-02
  summary: 有 slice donor 放本地 DSQ 头部 + SCX_RQ_PROXY_PICK_PENDING 区分记账性 put
  review_outcome: Tejun 质疑 IMMED 对 blocked donor 语义
- version: v3
  msgid: null
  date: 2026-10-10
  summary: 双标志方案落地
  review_outcome: Tejun 指出 bypass WARN 与更高优先级类抢占两点
- version: v4
  msgid: <20261010090621.184717-1-arighi@nvidia.com>
  date: 2026-10-10
  summary: 修正 v3 两点；Tejun 今日应用进 for-7.4
  review_outcome: Tejun 应用并补两条 core-sched 边界 review，follow-up 修复中
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.4
merge_assessment:
  likelihood: merged
  blocking_issues:
  - follow-up 边界修复尚未被 Tejun 收取
  next_action: Tejun 审阅并收取 follow-up（sched-20261015-010）
contribution_opportunities:
- kind: testing
  description: 见 sched-20261015-010：多 SMT/多 cookie 拓扑下验证
generated_at: '2026-10-16T01:05:00'
source_email_count: 3
related_articles:
- sched-20261002-008
- sched-20261003-001
- sched-20261007-005
- sched-20261009-011
- sched-20261010-010
tags:
- sched_ext
- proxy_execution
title: 'sched_ext: Keep proxy donors with slice left on the local DSQ'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-008-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.html">sched-20261002-008</a>：Andrea Righi 发 `sched_ext/for-7.4` 单补丁——有 slice 的 proxy donor 放本地 DSQ 头部，用 `SCX_RQ_PROXY_PICK_PENDING` 区分「记账性 put」与「真实 IMMED 抢占」，避免 BPF 无意义 dispatch 往返。
- <a class="article-ref" href="/lkm/2026/10/03/sched-20261003-001-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.html">sched-20261003-001</a>：Tejun 提出根本质疑——IMMED 对 blocked donor 不该起作用；Andrea 认同并当天改。
- <a class="article-ref" href="/lkm/2026/10/07/sched-20261007-005-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.html">sched-20261007-005</a>：Tejun 定下正确方向——IMMED donor 只在「马上要被 pick」的记账性 put 时保持本地。
- <a class="article-ref" href="/lkm/2026/10/09/sched-20261009-011-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.html">sched-20261009-011</a>：Tejun 确认双标志（`SCX_RQ_PROXY_PICK_PENDING` + `SCX_RQ_PROXY_BLOCKING`）方案成立。
- <a class="article-ref" href="/lkm/2026/10/10/sched-20261010-010-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.html">sched-20261010-010</a>：v3 落地，Tejun review 指出 bypass 路径 WARN 与更高优先级类抢占两点，v4 修正。
- <a class="article-ref" href="/lkm/2026/10/15/sched-20261015-025-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.html">sched-20261015-025</a>（今天）：Tejun 给出 Claude 生成式 review 的两条 core-sched 边界问题并**应用 v4 到 `sched_ext/for-7.4`**；Andrea 用 virtme-ng 复现其一、给出原型，随后发 follow-up 修复（见 <a class="article-ref" href="/lkm/2026/10/15/sched-20261015-010-sched-ext-keep-proxy-donors-local-through-core-sched-retries.html">sched-20261015-010</a>）。

## 背景与问题
（承接 20261002-008 → 20261010-010）proxy execution 下 blocked 任务可作为 donor 留在 runqueue；`put_prev_task_scx()` 把保留 donor 交还 BPF 造成无意义 dispatch 往返。经多轮收敛为双标志方案后，v4 落地。今天 Tejun 在 v4 应用后补两条代码级 review（见 follow-up 文章）。

## 技术方案
（承接 v4）v4 恢复 `SCX_RQ_PROXY_PICK_PENDING` 区分记账性 put 与真实 IMMED 抢占；`SCX_ENQ_IMMED` 临时本地插入；blocked donor 允许收 `SCX_ENQ_LAST`；owner 变更时置 `SCX_RQ_PROXY_BLOCKING` 跳过 reenqueue。Tejun 今日 review 指出的两条边界（残留 `SCX_RQ_PROXY_PENDING`、IMMED donor 被误送回 BPF）已在 follow-up（<a class="article-ref" href="/lkm/2026/10/15/sched-20261015-010-sched-ext-keep-proxy-donors-local-through-core-sched-retries.html">sched-20261015-010</a>）修复。

## 版本演进与当前进展
- v1→v4（见 related 文章）→ 今日 Tejun 应用 v4 进 `sched_ext/for-7.4`，并指出两条边界；Andrea 复现并原型化，发 follow-up 修复。

## Maintainer 意见与讨论焦点
Tejun Heo 应用 v4 的同时给出 review：问题 1（abandoned blocked-donor pick 残留 flag 到 core-sched forced idle）代码上可行但未复现；问题 2（IMMED 记账 put 的 reenqueue scan 把队首 donor 误送 BPF）Andrea 在 2000 次 mutex 基线中复现 174 次。双方对修复方向（cookie 匹配 + DSQ 标记）已一致。

## 合入评估
*likelihood=merged*。v4 已应用进 `sched_ext/for-7.4`；剩余两条边界由 follow-up（<a class="article-ref" href="/lkm/2026/10/15/sched-20261015-010-sched-ext-keep-proxy-donors-local-through-core-sched-retries.html">sched-20261015-010</a>）修复。*blocking_issues*：follow-up 尚未被 Tejun 收取。*next_action*：Tejun 审阅并收取 follow-up 修复。

## 效果评估
Andrea 的 follow-up 原型验证：修复后 2000 次 mutex 试验中 blocked IMMED reenqueue 归零（详见 <a class="article-ref" href="/lkm/2026/10/15/sched-20261015-010-sched-ext-keep-proxy-donors-local-through-core-sched-retries.html">sched-20261015-010</a>）。v4 本身无独立基准。

## 我可以参与的点
- *testing*：见 follow-up 文章 <a class="article-ref" href="/lkm/2026/10/15/sched-20261015-010-sched-ext-keep-proxy-donors-local-through-core-sched-retries.html">sched-20261015-010</a>（多 SMT/多 cookie 拓扑下验证）。

## 参考链接
- Tejun 的 review：https://lore.kernel.org/all/1548cc9309a6e0894e358262e0b3d4ee@kernel.org/
- Tejun 应用 v4：https://lore.kernel.org/all/5b3d2c576222c62738b7006d85f96a23@kernel.org/
- Andrea 的复现与原型：https://lore.kernel.org/all/atCQB_nF5di8pgUN@gpd4/
- v4 patch：https://lore.kernel.org/all/20261010090621.184717-1-arighi@nvidia.com/
