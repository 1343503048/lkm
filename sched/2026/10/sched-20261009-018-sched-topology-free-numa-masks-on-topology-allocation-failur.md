# sched/topology: Free NUMA masks on topology allocation failure

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260731-003：Fengyu Wang（海光）修 `sched_init_numa()` 中 topology 数组分配失败时的内存泄漏——masks 已 RCU 发布但失败路径未释放。带 `Fixes: cb83b629bae0`，v1 无 review。
- sched-20261009-018（今天）：作者对 v2 发 gentle ping，并转引 Valentin Schneider（8 月 14 日）的 **Reviewed-by** 与 Tim Chen 的 review，询问是否还有进一步意见。v2 已集齐两位评审者的正面意见，处于等维护者应用状态。

## 背景与问题

（承接 sched-20260731-003）`sched_init_numa()` 在分配 topology 数组之前就已通过 RCU 发布 `sched_domains_numa_masks`。当后续 topology 数组 `kzalloc()` 失败时函数直接 return：masks 已发布但 `sched_domains_numa_levels` 仍为零，无代码能解引用它们、也无代码能释放它们。经典的「发布后分配失败」内存泄漏。

## 技术方案

（承接）在 `kzalloc()` 失败路径补清理：`rcu_assign_pointer(sched_domains_numa_masks, NULL)` 撤销 RCU 发布 → `synchronize_rcu()` 等待 reader → 遍历释放 `masks[i][j]`/`masks[i]`/`masks` 本身。`kernel/sched/topology.c` +10/-1。v2 经 Valentin Schneider 审阅并给出 Reviewed-by；Valentin 的评语：「sched_init_numa() 仍无返回值，scheduler topology 代码里分配失败基本总是伴随一片混乱，但这个补丁至少能帮一个坏内核在启动过程里走得更远。」Tim Chen 亦参与 review。今天作者 ping 等应用。

## 版本演进与当前进展

*current_version: v2*（`<20260812062206.82410-1-wangfengyu@hygon.cn>`）。今天作者对 v2 发 gentle ping（`<dfb0cb72eb1a483791dd72fc0f14116d@hygon.cn>`），转引 Valentin 的 Reviewed-by 与 Tim 的 review，请求是否还有进一步意见。

## Maintainer 意见与讨论焦点

- **Valentin Schneider（sched 维护者之一）**：给出 Reviewed-by（8 月 14 日），认为补丁在「坏内核启动走得更远」上有价值，虽自嘲「topology 分配失败几乎总是伴随 dumpster fire」。
- **Tim Chen（Intel）**：参与 review（作者致谢）。
- 无 NAK、无未解决分歧；当前仅是「集齐评审、待应用」的 ping 阶段。

## 合入评估

*likelihood=high*。错误路径内存泄漏的干净小修复，已获 Valentin Schneider 的 Reviewed-by 与 Tim Chen review，无反对意见；缺的只是某位维护者（Peter/Ingo）顺手应用。*blocking_issues*：暂无硬阻塞，等维护者应用。*next_action*：等 tip/sched 维护者应用该补丁。

## 效果评估

无 benchmark；属错误路径内存泄漏修复，效果以「无泄漏」衡量。作者在 v1 曾硬编码 `tl = NULL` 强制触发失败路径，确认 masks 正确释放且机器正常启动。

## 我可以参与的点

- `review`：可审计 sched domain 构建失败回滚路径是否还有其它未释放的 per-node 分配（此前 Hongling Zeng 的同类补丁 19062 也在讨论 topology 失败清理），回帖补充、帮助一并收敛。

## 参考链接

- 作者今日 ping: https://lore.kernel.org/all/dfb0cb72eb1a483791dd72fc0f14116d@hygon.cn/
- v2 补丁: https://lore.kernel.org/all/20260812062206.82410-1-wangfengyu@hygon.cn/

---
id: sched-20261009-018
date: '2026-10-09'
subject: 'sched/topology: Free NUMA masks on topology allocation failure'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20260812062206.82410-1-wangfengyu@hygon.cn>'
lore_url: 'https://lore.kernel.org/all/dfb0cb72eb1a483791dd72fc0f14116d@hygon.cn/'
authors:
  - 'Fengyu Wang'
maintainers_involved:
  - 'Valentin Schneider'
  - 'Tim Chen'
current_version: v2
patch_series:
  - version: v1
    msgid: '<20260731081413.5505-1-wangfengyu@hygon.cn>'
    date: '2026-07-31'
    summary: 'sched_init_numa 分配失败时撤销并释放已发布 numa_masks'
    review_outcome: 'v1 无 review'
  - version: v2
    msgid: '<20260812062206.82410-1-wangfengyu@hygon.cn>'
    date: '2026-08-12'
    summary: '失败路径清理（v1 基础上按 review 调整）'
    review_outcome: 'Valentin Schneider Reviewed-by + Tim Chen review；今日作者 ping 等应用'
upstream_commit: null
fixes_commit: 'cb83b629bae0'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: '等 tip/sched 维护者应用'
contribution_opportunities:
  - kind: review
    description: '审计 sched domain 构建失败回滚的其它未释放分配'
generated_at: '2026-10-10T01:30:00'
source_email_count: 1
related_articles:
  - sched-20260731-003
tags:
  - topology
  - numa_balancing
---