---
id: sched-20261006-005
date: '2026-10-06'
subject: 'sched_ext: Add NUMA balancing support'
subsystem: sched_ext
type: feature
status: under_review
severity: none
thread_root_msgid: <20261004072901.3579967-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/asQYmmrL2SyhZ4sb@gpd4/
authors:
- Andrea Righi
maintainers_involved:
- Andrea Righi
current_version: v1
patch_series:
- version: v1
  msgid: <20261004072901.3579967-1-arighi@nvidia.com>
  date: '2026-10-04'
  summary: SCX_OPS_NUMA_BALANCING opt-in 扫描 + scx_bpf_task_numa_nid() + selftest
  review_outcome: 10-06 作者澄清 donor/curr 语义（时序-only、随 fair 切换）；Vladimir 回植实测背书
related_articles:
- sched-20261002-014
- sched-20261004-001
- sched-20261005-008
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: Tejun 与 NUMA 侧维护者 review 未开始；donor→curr 切换依赖 Hui Su 系列时序
  next_action: Tejun review；Vladimir 交 4 节点测试
generated_at: '2026-10-07T01:00:00'
title: 'sched_ext: Add NUMA balancing support'
layout: article
---

> **subject**：`sched_ext: Add NUMA balancing support`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-014-sched-ext-drive-the-numa-balancing-scan-for-scx-tasks.html">sched-20261002-014</a>：Vladimir Vdovin 的单片 RFC——自动 NUMA balancing 对 sched_ext 任务事实性关闭：SCX 下 `numa_pte_updates/s = 0`（fair 2.4M-3.9M）、跑在 preferred nid 37%（fair 83%）。Andrea Righi 回复 backlog 里有完整方案，Vladimir 撤 sketch 转做测试员。
- <a class="article-ref" href="/lkm/2026/10/04/sched-20261004-001-sched-ext-add-numa-balancing-support.html">sched-20261004-001</a>：Andrea 兑现承诺发 5 补丁系列（`SCX_OPS_NUMA_BALANCING` opt-in 扫描 + `scx_bpf_task_numa_nid()` kfunc + selftest，`sched_ext/for-7.4`）。
- <a class="article-ref" href="/lkm/2026/10/05/sched-20261005-008-sched-ext-add-numa-balancing-support.html">sched-20261005-008</a>：Vladimir 对 3/5 提出 proxy execution 语义问题——扫描从 donor 驱动，而 Hui Su 的 fair tick 系列把 fair NUMA tick 移到执行上下文；donor 是否 intended？
- <a class="article-ref" href="/lkm/2026/10/06/sched-20261006-005-sched-ext-add-numa-balancing-support.html">sched-20261006-005</a>（今天）：**Andrea 详尽作答**——donor 仅为与现行 `task_tick_fair()` 实现一致；澄清记账语义：proxy exec 下 slice 记 donor（`update_curr_scx()`），而 `p->se.sum_exec_runtime` 记 `rq->curr`（`update_se()`）——`task_tick_numa()` 按 sum_exec_runtime 配速，传 donor 意味着其扫描在阻塞期不推进（无害），owner 的扫描等它自己拿到 tick 才推进；**绝不扫错 mm**：`task_tick_numa(rq, p)` 到期时把扫描作为 task work 排队、在 p 自身上下文与自身 mm 里跑——「The owner never scans the donor's memory or the other way around」，传 donor 的唯一效果是**时序**。Andrea 同意扫描最终应随 `rq->curr`（Hui Su 系列给出 hook），但暂不偏离 fair、等 fair 一起切换。**Vladimir 交出首份实测**：把 1-3/5 回移植 6.18.54 + 自家调度器（去 opt-in、随 `sched_numa_balancing` static key、传 curr）——stress-ng 4G worker 从 node0 taskset 到 node1 后 20 秒内 4G（约 1M 页）整体迁往 node1、`numa_scan_seq` 推进、`numa_preferred_nid` 正确翻转、任务保持在钉住的 CPU；同宿主机 vCPU 线程 30 秒内 `task_numa_work()` 零调用（无补丁）vs 现在有调用。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-014-sched-ext-drive-the-numa-balancing-scan-for-scx-tasks.html">sched-20261002-014</a> → <a class="article-ref" href="/lkm/2026/10/05/sched-20261005-008-sched-ext-add-numa-balancing-support.html">sched-20261005-008</a>）BPF 调度器下的任务对 NUMA balancing 不可见：扫描只从 fair tick 排队，SCX 任务地址空间从不被扫描、preferred node 冻结。Andrea 的 5 补丁系列补齐 opt-in 扫描与 preferred node 暴露；Vladimir 质疑 3/5 从 donor 驱动扫描与 fair 侧「NUMA tick 移到执行上下文」的方向矛盾。今天的焦点是**proxy execution 语义澄清**与**系列有效性实证**。

## 技术方案

（承接）5 补丁：1/5 通用 NUMA 代码开放非 fair 调度类驱动；2/5 任务放置留给 BPF；3/5 `SCX_OPS_NUMA_BALANCING` opt-in + sched_ext tick 驱动扫描；4/5 `scx_bpf_task_numa_nid()`；5/5 selftest。

**Andrea 的 donor/curr 澄清**（`<asQYmmrL2SyhZ4sb@gpd4>`）：

- 记账分野：proxy exec 下 `update_curr_scx()` 扣 donor->scx.slice（slice 归 donor），`update_se()` 把 `p->se.sum_exec_runtime` 记到 `rq->curr`（runtime 归执行者）。
- `task_tick_numa()` 用 sum_exec_runtime 配速 → 传 donor 时其扫描在阻塞期不推进（donor 没跑就没 runtime），owner 的扫描等 owner 自己被调度才推进——**正确性不受影响**：到期扫描作为 task work 排队，稍后在 p 自身上下文、自身 mm 内执行；owner 不会扫 donor 的内存、反之亦然。
- 结论：传 donor 的唯一效果是时序（proxy 窗口内 donor 的扫描可能被排队而 owner 的扫描等待）。同意最终应随 `rq->curr`（Hui Su 系列 hook 正确），但「rather not diverge from fair」——保持与 fair 同步切换。

**Vladimir 的回植实测**（`<DLXU0LDPUUSG.2JN9ZOB6YMU07@verdict.gg>`）：6.18.54 + 自家 in-house 调度器，为不改调度器去掉 `SCX_OPS_NUMA_BALANCING`（所有 SCX 任务在 `sched_numa_balancing` static key 下扫描）、传 curr（6.18 无 donor 概念）；fair.c 部分与原系列一致。

## 版本演进与当前进展

- 10-02/10-04/10-05：见 related_articles。
- 10-06（今天）：Andrea 回答 donor 问题（时序-only、随 fair 切换的策略）；Vladimir 交出 1-3/5 回植实测（非原样：去 opt-in + 传 curr）。Tejun 仍未 review。

## Maintainer 意见与讨论焦点

- **Andrea Righi**（作者）：把 Vladimir 的质疑完整闭环——正确性论证（task work 机制保证 mm 归属）+ 设计决策（与 fair 同步切换 donor→curr）。
- **Vladimir Vdovin**（测试员）：用生产宿主机与自家调度器背书系列有效性（4G 内存 20 秒迁移完成）。
- **Tejun Heo**（sched_ext 顶层维护者）：仍未现——合入关口的 review 未开始。
- 焦点：donor vs curr 已由作者澄清并给出演进路径；剩余开放项是 Tejun 对 3/5 改动 `task_tick_numa()` 调用路径的把关。

## 合入评估

*likelihood=medium*（上调）。作者澄清了唯一的设计质疑、外部实测背书到位；但 Tejun/Mel review 未开始，且 donor→curr 的切换承诺依赖 Hui Su 系列落地时序。*blocking_issues*：Tejun 与 NUMA 侧维护者 review 未开始；`SCHED_PROXY_EXEC` 与 SCX 互斥期内的 donor 选择虽无现实 bug、合入后仍是技术债。*next_action*：Tejun review；Vladimir 的 2/4 节点完整测试矩阵待交。

## 效果评估

Vladimir 回植实测（6.18.54、in-house 调度器、stress-ng --vm 4G）：

- 无补丁：`mm->numa_scan_seq` 恒 0、`numa_preferred_nid` 恒 -1、`numa_pte_updates` 不动、4G 全留 node0；
- 有补丁：`numa_scan_seq` 2 分钟推进 7-12；taskset 迁到 node1 后约 20 秒 `numa_preferred_nid` 翻转为 1、整个 4G（约 1M 页）迁到 node1；任务保持钉在原 CPU；
- 宿主机层面：无补丁时 vCPU 线程 30 秒 `task_numa_work()` 零调用（kprobe），有补丁后有调用。

既有基线（10-02，未打补丁的 6.18.5）：SCX `numa_pte_updates/s = 0` vs fair 2.4M-3.9M。

## 我可以参与的点

- `review`：Tejun review 前预核对 3/5 在 BPF 侧的 static key 门控（`sched_numa_balancing` 与 `SCX_OPS_NUMA_BALANCING` 的叠加语义）——Vladimir 回植时去掉 opt-in 也有效，说明两层门可能冗余，可作为 review 输入。
- `testing`：按 Vladimir 的方法在 4 节点机器复测（其 2/4 节点承诺尚有一半未交），重点看跨 2 跳迁移的 preferred_nid 收敛速度。

## 参考链接

- Andrea 的 donor/curr 澄清: https://lore.kernel.org/all/asQYmmrL2SyhZ4sb@gpd4/
- Vladimir 回植实测: https://lore.kernel.org/all/DLXU0LDPUUSG.2JN9ZOB6YMU07@verdict.gg/
- 系列封面: https://lore.kernel.org/all/20261004072901.3579967-1-arighi@nvidia.com/
- Hui Su fair NUMA tick 系列: https://lore.kernel.org/r/20260909092901.2989564-3-sh_def@163.com
