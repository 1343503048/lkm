---
id: sched-20260924-005
date: '2026-09-24'
subject: 'sched_ext: Update scx_dispatch_dequeue() comments'
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: <20260923213418.3197834-1-usama.arif@linux.dev>
lore_url: https://lore.kernel.org/all/20260924130503.853919-1-usama.arif@linux.dev/
authors:
- Usama Arif
maintainers_involved:
- Tejun Heo
- Andrea Righi
current_version: v2
patch_series:
- version: v1
  msgid: <20260923213418.3197834-1-usama.arif@linux.dev>
  date: '2026-09-24'
  summary: 更新两段注释描述转移路径与 race 语义
  review_outcome: Tejun 要求点名函数、补 holding_cpu 语义、80 列重排
- version: v2
  msgid: <20260924130503.853919-1-usama.arif@linux.dev>
  date: '2026-09-24'
  summary: 落实 Tejun 三点意见
  review_outcome: Andrea Righi Reviewed-by
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: Tejun 收取 v2 进 sched_ext/for-7.4
contribution_opportunities: []
generated_at: '2026-09-25T09:00:00'
source_email_count: 3
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Update scx_dispatch_dequeue() comments'
layout: article
---

## TL;DR
Usama Arif 的纯注释修正（v2）：`scx_dispatch_dequeue()` 的两段注释描述的是过时的转移路径与竞争对象——`!dsq` 分支如今也因「远端消费」而带上 `holding_cpu`，`dsq` 分支的竞争对方其实是 `unlink_dsq_and_switch_rq_lock()` 而非 `dispatch_to_local_dsq()`。v2 按 Tejun Heo 意见改写了这两段注释并重排为 80 列，已获 Andrea Righi 的 Reviewed-by。无功能变化。

## 背景与问题
`scx_dispatch_dequeue()` 里两段注释已与实际代码路径脱节：

- `!dsq` 分支注释只提「从 BPF 调度器直接 dispatch 到本地 DSQ」是 `holding_cpu` 的来源，但如今 `dispatch_to_local_dsq()` 与「远端消费（remote consumption）」都会走到这里并带 `holding_cpu`。
- `dsq` 分支注释说「正与 `dispatch_to_local_dsq()` 竞争」，实际竞争对方是 `unlink_dsq_and_switch_rq_lock()`。

不更新会导致读者对竞争关系与 `holding_cpu` 语义产生误读（原注释还把一个描述正确但放错了分支的句子挂在另一处）。

## 技术方案
纯注释改动（8 insertions / 8 deletions，kernel/sched/ext/ext.c）：

- `!dsq` 分支注释改为「`dispatch_to_local_dsq()` 或远端消费把任务移到本地 DSQ 时，任务不关联任何 DSQ 但可能带 `holding_cpu`；清除 `holding_cpu` 是在告诉 `dispatch_to_local_dsq()` 它输给了这次 dequeue」。
- `dsq` 分支注释改为「正与 `unlink_dsq_and_switch_rq_lock()` 竞争，对方已把任务从 `@dsq` 移除并设置了 `holding_cpu`；清除 `holding_cpu` 告知对方输了竞争」。

v1→v2（按 Tejun 意见）：注释与 commit message 中显式点名 `dispatch_to_local_dsq()`；补充「清除 `holding_cpu` 让 `dispatch_to_local_dsq()` 知道它输了」这一句；两段注释重排为 80 列。

## 版本演进与当前进展
- v1（`<20260923213418.3197834-1-usama.arif@linux.dev>`）：Tejun Heo 指出应点名 `dispatch_to_local_dsq()`、补一句 `holding_cpu` 清除语义、并按 80 列重排。
- **v2**（本日，`<20260924130503.853919-1-usama.arif@linux.dev>`）：落实上述三点。Andrea Righi 回帖 `Reviewed-by`。

## Maintainer 意见与讨论焦点
- **Tejun Heo（sched_ext 维护者）**：v1 时给出三处具体改写要求（点名函数、补 `holding_cpu` 清除语义、80 列重排），方向为「让注释如实描述当前 transfer 路径与 race 语义」。
- **Andrea Righi**：v2 给出 `Reviewed-by: Andrea Righi <arighi@nvidia.com>`。
- 无争议、无 NAK。

## 合入评估
*likelihood=high*。纯注释修正、零风险，已按维护者意见改版并拿到第二维护者 Reviewed-by。*blocking_issues*：无明确项，仅待 Tejun 最终收取 v2。*next_action*：Tejun 收取 v2 进 `sched_ext/for-7.4`。

## 效果评估
无功能/性能变化；价值在于修正误导性注释，降低后续开发者误读 `holding_cpu` 与 race 语义的风险。

## 我可以参与的点
当前阶段暂无明显参与空间——纯注释修正且已获 Reviewed-by，可持续观察是否收取。

## 参考链接
- lore thread (v2): https://lore.kernel.org/all/20260924130503.853919-1-usama.arif@linux.dev/
- lore (v1): https://lore.kernel.org/all/20260923213418.3197834-1-usama.arif@linux.dev/
- Tejun v1 意见: https://lore.kernel.org/all/7d8f411e5153472c11bf158c4d948816@kernel.org/
