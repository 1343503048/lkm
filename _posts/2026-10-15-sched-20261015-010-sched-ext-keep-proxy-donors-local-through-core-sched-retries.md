---
id: sched-20261015-010
date: 2026-10-15
subject: 'sched_ext: Keep proxy donors local through core-sched retries'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261015101935.2844323-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20261015101935.2844323-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20261015101935.2844323-1-arighi@nvidia.com>
  date: 2026-10-15
  summary: cookie 匹配才算 proxy put + SCX_TASK_DSQ_PROXY_IDLE 标记 + rq_is_open() 识别
  review_outcome: Andrea 原型验证通过，待 Tejun 收取
upstream_commit: null
fixes_commit: 7ab553756463
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: Tejun 审阅 follow-up 并入 sched_ext/for-7.4
contribution_opportunities:
- kind: testing
  description: 在多 SMT/多 cookie 拓扑下验证 cookie 匹配与 rq_is_open() 识别，覆盖未复现的问题 1 路径
generated_at: '2026-10-16T01:05:00'
source_email_count: 1
related_articles: []
tags:
- sched_ext
- proxy_execution
title: 'sched_ext: Keep proxy donors local through core-sched retries'
layout: article
---

## TL;DR
Andrea Righi（sched_ext 维护者）为 `sched_ext/for-7.4` 发修复：`v4 "Keep proxy donors with slice left"` 落地后，Tejun Heo 的 review 指出两条 core-sched 边界路径会让 `SCX_RQ_PROXY_PENDING` 残留、或把本就该留在本地 DSQ 的 IMMED donor 错误送回 BPF。Andrea 用 virtme-ng 复现了其中一个、给出本地原型，并正式发补丁：要求 donor 的 cookie 匹配才算 proxy put、用 `dsq_flags` 标记被 proxy put 停靠的 donor、并让 `rq_is_open()` 识别该标记。带 `Fixes: 7ab553756463`。

## 背景与问题
Tejun 对 v4 的 review（Claude 生成式审阅）发现两条未被复现的代码级问题，Andrea 后续用 reproducer 逐条跟进：
1. **abandoned blocked-donor pick 残留标志**：blocked donor 被 pick 后 `set_next_task_scx()` 置 `SCX_RQ_PROXY_PENDING`；若 `find_proxy_task()` 因 `blocked_on` 变化或 owner 迁走而返回 NULL、`__schedule()` 回到 pick_again，core-sched 路径上本 rq 由 fair/RT 任务赢得 `pick_task()`，`pick_task_scx()` 不跑、标志不清；随后 cookie 不匹配强制 idle，`put_prev_task_scx()` 把残留标志误当成 proxy 记账 put。Andrea 未复现这条，但代码上可行、标志可能 stale。
2. **IMMED donor 被错误送回 BPF**：有效的 IMMED 记账 put 会调度本地 reenqueue scan；若 SCX 任务在 scan 前被唤醒，`rq->next_class` 恢复为 ext、`rq_is_open()` 判定 CPU closed，scan 把「其实在本地 DSQ 队首、CPU 正要转 idle」的 donor 送回 BPF。这条 Andrea 在基线里 2000 次 mutex 试验中数出 174 次命中。

## 技术方案
单补丁（include/linux/sched/ext.h + kernel/sched/ext/ext.c，+28/−1）：
- 要求 donor 的 cookie 与 CPU 匹配，才把 put 当作 proxy put（cookie 不匹配走普通 forced-idle 路径）。
- 引入 `SCX_TASK_DSQ_PROXY_IDLE`（`dsq_flags` 第 2 位）：proxy put 把 donor 停靠到本地 DSQ 时置位，离开 DSQ 时清零。
- `rq_is_open()` 在 rq donor idle 时，识别本地 DSQ 队首「带该标记且 cookie 匹配」的 donor，从而避免 pending scan 把 donor 送走。作者自嘲「又一个 flag」，但全部自包含在 ext.c。

## 版本演进与当前进展
新补丁（<20261015101935.2844323-1-arighi@nvidia.com>），是对已应用 v4 的 follow-up 修复。Andrea 的原型在 virtme-ng 上通过（2000 次试验、同/跨 CPU owner、开/关 `SCX_OPS_ENQ_BLOCKED`，blocked IMMED reenqueue 归零）。

## Maintainer 意见与讨论焦点
Tejun Heo（发现问题方）此前已把 v4 applied 到 `sched_ext/for-7.4`，同时提出这两条边界。Andrea 认同问题 2 可复现、问题 1 代码上可行但未复现，并给出「cookie 匹配 + 本地 DSQ 标记」自包含修复。分歧点已基本收敛，等待 Tejun 对 follow-up 的收取。

## 合入评估
*likelihood=high*。修复的是维护者自己 review 出的、即将进 7.4 的补丁中的缺陷，作者已复现并带原型验证，属例行 follow-up。*blocking_issues*：无实质阻塞，等 Tejun 收取确认。*next_action*：Tejun 审阅 follow-up 并入 `sched_ext/for-7.4`。

## 效果评估
Andrea 的原型验证：2000 次 mutex 基线中 174 次 blocked IMMED 误送回；修复后所有配置（同/跨 CPU owner、开/关 ENQ_BLOCKED）blocked IMMED reenqueue 归零。未给出最终补丁的独立基准。

## 我可以参与的点
- *testing*：在 core scheduling 更复杂的拓扑（多 SMT、多 cookie）下验证 cookie 匹配逻辑与 `rq_is_open()` 识别，覆盖 Andrea 未复现的问题 1 路径。

## 参考链接
- patch：https://lore.kernel.org/all/20261015101935.2844323-1-arighi@nvidia.com/
- Tejun 的 review（问题出处）：https://lore.kernel.org/all/1548cc9309a6e0894e358262e0b3d4ee@kernel.org/
