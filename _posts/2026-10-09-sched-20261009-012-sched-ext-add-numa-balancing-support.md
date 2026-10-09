---
id: sched-20261009-012
date: '2026-10-09'
subject: 'sched_ext: Add NUMA balancing support'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261004072901.3579967-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/61b9a8607e1f25ffd316f13135432581@kernel.org/
authors:
- Andrea Righi
maintainers_involved:
- Andrea Righi
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20261004072901.3579967-1-arighi@nvidia.com>
  date: '2026-10-04'
  summary: SCX_OPS_NUMA_BALANCING opt-in 扫描 + scx_bpf_task_numa_nid() + selftest
  review_outcome: 10-09 Tejun 建议改为事件式 op（preferred node 变化回调）
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Tejun 的事件 op 替代 flag+轮询建议待作者回应
  - donor→curr 切换依赖 Hui Su 系列时序
  next_action: Andrea 回应 Tejun 接口建议并调整设计
contribution_opportunities:
- kind: discussion
  description: 事件式 op vs flag+轮询的取舍分析
- kind: testing
  description: 多 NUMA 机器验证 preferred node 变化回调频率与开销
generated_at: '2026-10-10T01:30:00'
source_email_count: 1
related_articles:
- sched-20261002-014
- sched-20261004-001
- sched-20261005-008
- sched-20261006-005
tags:
- sched_ext
- numa_balancing
title: 'sched_ext: Add NUMA balancing support'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-014-sched-ext-drive-the-numa-balancing-scan-for-scx-tasks.html">sched-20261002-014</a>：Vladimir Vdovin 的单片 RFC——自动 NUMA balancing 对 sched_ext 任务事实性关闭：SCX 下 `numa_pte_updates/s = 0`（fair 2.4M-3.9M）、跑在 preferred nid 37%（fair 83%）。Andrea Righi 回复 backlog 里有完整方案。
- <a class="article-ref" href="/lkm/2026/10/04/sched-20261004-001-sched-ext-add-numa-balancing-support.html">sched-20261004-001</a>：Andrea 发 5 补丁系列（`SCX_OPS_NUMA_BALANCING` opt-in 扫描 + `scx_bpf_task_numa_nid()` kfunc + selftest，`sched_ext/for-7.4`）。
- <a class="article-ref" href="/lkm/2026/10/05/sched-20261005-008-sched-ext-add-numa-balancing-support.html">sched-20261005-008</a>：Vladimir 对 3/5 提出 proxy execution 语义问题——扫描从 donor 驱动是否 intended？
- <a class="article-ref" href="/lkm/2026/10/06/sched-20261006-005-sched-ext-add-numa-balancing-support.html">sched-20261006-005</a>：Andrea 详尽作答（donor 仅与现行 `task_tick_fair()` 一致；扫描作为 task work 在 p 自身 mm 内跑，绝不错扫；同意最终随 `rq->curr` 切换）。Vladimir 交出回植实测背书（4G 内存 20 秒迁完）。
- <a class="article-ref" href="/lkm/2026/10/09/sched-20261009-012-sched-ext-add-numa-balancing-support.html">sched-20261009-012</a>（今天）：**Tejun Heo 首次 review**——质疑为什么要用一个独立 ops flag 门控，建议改成事件式 op（preferred node 变化时回调，初始 node 在 enable 时上报，实现该 op 才启用 hinting-fault 扫描），让调度器拿到可响应的事件而非可轮询的值。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-014-sched-ext-drive-the-numa-balancing-scan-for-scx-tasks.html">sched-20261002-014</a> → <a class="article-ref" href="/lkm/2026/10/05/sched-20261005-008-sched-ext-add-numa-balancing-support.html">sched-20261005-008</a> → <a class="article-ref" href="/lkm/2026/10/06/sched-20261006-005-sched-ext-add-numa-balancing-support.html">sched-20261006-005</a>）BPF 调度器下的任务对 NUMA balancing 不可见：扫描只从 fair tick 排队，SCX 任务地址空间从不被扫描、preferred node 冻结。Andrea 的 5 补丁系列补齐 opt-in 扫描与 preferred node 暴露；今天 Tejun 首次进场，对 3/5 的门控机制提出更根本的设计质疑。

## 技术方案

（承接）5 补丁：1/5 通用 NUMA 代码开放非 fair 调度类驱动；2/5 任务放置留给 BPF；3/5 `SCX_OPS_NUMA_BALANCING` opt-in + sched_ext tick 驱动扫描；4/5 `scx_bpf_task_numa_nid()`；5/5 selftest。

**Tejun 的替代设计提议**（今天）：

- 质疑「独立 ops flag 门控」的必要性。替代方案：一个在任务 preferred node 变化时被调用的 op（类比 `ops.set_weight()` 从 reweight 路径调用），初始 node 在 enable 时上报（也像 `set_weight`），且**仅当调度器实现了该 op 时才启用 hinting-fault 扫描**。
- 论证：`sched_setnuma()` 是 node 的唯一写者，它本就在 rq 锁下对任务 dequeue/re-enqueue，所以 op 可以从那里调用（正如 `set_weight` 从 reweight 路径调用）。
- 收益：调度器拿到的是「可响应的**事件**」，而不是「要轮询的**值**」。

## 版本演进与当前进展

- 10-02/10-04/10-05/10-06：见 related_articles。
- 10-09（今天）：Tejun 首次 review，建议把「opt-in flag + kfunc 轮询」改为「事件式 op（preferred node 变化回调）+ enable 时上报初始 node」。作者尚未回应。

## Maintainer 意见与讨论焦点

- **Tejun Heo**（sched_ext 顶层维护者，今天首次进场）：核心关切是接口形态——事件回调优于「flag 门控 + 值轮询」；给出与 `ops.set_weight()` 对称的调用路径论证。这是系列合入关口的关键 review。
- **Andrea Righi**（作者）：尚未对 Tejun 的替代设计表态。
- 焦点从「donor vs curr 语义」转向「op 接口形态」，是合入前的最后一道设计关卡。

## 合入评估

*likelihood=medium*。作者/测试员侧的有效性已被 Vladimir 回植实测背书，但 Tejun 首次 review 即提出接口形态改动（flag→事件 op），若采纳需重构 3/5 与 4/5。*blocking_issues*：Tejun 的「事件 op 替代 flag+轮询」建议待作者采纳/反驳；donor→curr 切换仍依赖 Hui Su 系列时序。*next_action*：Andrea 回应 Tejun 的接口建议并调整设计。

## 效果评估

（承接）Vladimir 回植实测：stress-ng 4G worker 从 node0 taskset 到 node1 后 20 秒内约 1M 页整体迁往 node1、`numa_scan_seq` 推进、`numa_preferred_nid` 正确翻转、任务保持在钉住的 CPU。今天无新数据。

## 我可以参与的点

- `discussion`：就「事件式 op（preferred node 变化回调）vs opt-in flag + kfunc 轮询」给出取舍分析——事件回调在「扫描频率 vs 调度器即时反应」上的权衡。
- `testing`：在 4 节点（多 NUMA）机器上验证 preferred node 变化回调路径的触发频率与开销。

## 参考链接

- Tejun 今日回复: https://lore.kernel.org/all/61b9a8607e1f25ffd316f13135432581@kernel.org/
- 系列 cover: https://lore.kernel.org/all/20261004072901.3579967-1-arighi@nvidia.com/
