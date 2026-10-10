---
id: sched-20261010-012
date: '2026-10-10'
subject: 'sched_ext: Add NUMA balancing support'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261004072901.3579967-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20261004072901.3579967-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20261004072901.3579967-1-arighi@nvidia.com>
  date: '2026-10-04'
  summary: 5 补丁：SCX_OPS_NUMA_BALANCING opt-in 扫描 + scx_bpf_task_numa_nid() kfunc +
    selftest
  review_outcome: Tejun 建议改事件式 op；Andrea 今日接受，v2 待发
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - v2（事件式 op）未发
  - 1/5、2/5 的 NUMA 侧 review 未开始
  next_action: Andrea 发事件式 op 的 v2，等 Tejun/Mel 侧 review
contribution_opportunities:
- kind: testing
  description: 在 2/4 节点宿主机验证 v2 的 hinting-fault 扫描与 preferred node 上报
- kind: review
  description: 复核 set_numa_node 在 enable/扫描路径的调用时序
generated_at: '2026-10-11T09:00:00'
source_email_count: 1
related_articles:
- sched-20261002-014
- sched-20261004-001
- sched-20261005-008
- sched-20261006-005
- sched-20261009-012
tags:
- sched_ext
- numa_balancing
title: 'sched_ext: Add NUMA balancing support'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-014-sched-ext-drive-the-numa-balancing-scan-for-scx-tasks.html">sched-20261002-014</a>：Vladimir Vdovin 单片 RFC——自动 NUMA balancing 对 sched_ext 任务事实性关闭：扫描只从 fair tick 排队，SCX 任务 `numa_pte_updates/s = 0`（fair 2.4M-3.9M）、跑在 preferred nid 37%（fair 83%）；Andrea Righi 回复 backlog 有完整方案，Vladimir 撤 sketch 转测试。
- <a class="article-ref" href="/lkm/2026/10/04/sched-20261004-001-sched-ext-add-numa-balancing-support.html">sched-20261004-001</a>：Andrea 发 5 补丁系列（`SCX_OPS_NUMA_BALANCING` opt-in 扫描 + `scx_bpf_task_numa_nid()` kfunc + selftest，`sched_ext/for-7.4`）。
- <a class="article-ref" href="/lkm/2026/10/05/sched-20261005-008-sched-ext-add-numa-balancing-support.html">sched-20261005-008</a>：Vladimir 对 3/5 提 proxy execution 语义问题——扫描从 donor 驱动是否 intended？
- <a class="article-ref" href="/lkm/2026/10/06/sched-20261006-005-sched-ext-add-numa-balancing-support.html">sched-20261006-005</a>：Andrea 澄清 donor 仅为与现行 `task_tick_fair()` 一致、扫描作为 task work 在 p 自身 mm 内跑绝不错扫、同意最终随 `rq->curr` 切换；Vladimir 交出回植实测背书。
- <a class="article-ref" href="/lkm/2026/10/09/sched-20261009-012-sched-ext-add-numa-balancing-support.html">sched-20261009-012</a>：Tejun 首次 review——质疑为何用独立 ops flag 门控，建议改成事件式 op（preferred node 变化时回调 + enable 时上报初始 node）。
- <a class="article-ref" href="/lkm/2026/10/10/sched-20261010-012-sched-ext-add-numa-balancing-support.html">sched-20261010-012</a>（今天）：**Andrea 接受 Tejun 的接口建议**——放弃独立 ops flag，改为 `void (*set_numa_node)(struct task_struct *p, s32 nid)` 回调，在 `sched_setnuma()` 里、rq 锁下调用，让 BPF 在任务被 reenqueue 前更新放置状态；实现该回调才启用 hinting-fault 扫描。Andrea 将做实验并发新版本。

## 背景与问题
（承接）BPF 调度器下的任务对 NUMA balancing 不可见：扫描只从 fair tick 排队，SCX 任务地址空间从不被扫描 hinting fault、preferred node 冻结——BPF 调度器决定任务放置时拿不到「任务的内存在哪」。Vladimir 的 KVM 宿主机实测：SCX 下 `numa_pte_updates/s = 0`、58% 任务无 preferred_nid、跑在 preferred nid 37% vs fair 83%。Andrea 的 5 补丁系列以 opt-in 补齐扫描与 preferred node 暴露。今天的关键收敛在**接口形态**：Tejun 认为「opt-in flag + kfunc 值轮询」不如「事件回调」，Andrea 接受。

## 技术方案
（承接 5 补丁：1/5 通用 NUMA 代码开放非 fair 调度类驱动；2/5 放置留给 BPF；3/5 opt-in 扫描；4/5 `scx_bpf_task_numa_nid()`；5/5 selftest。）今天确定的接口调整：

- 用 `void (*set_numa_node)(struct task_struct *p, s32 nid)` 事件式回调替代「独立 ops flag 门控 + kfunc 轮询」；
- 在 `sched_setnuma()` 里、rq 锁下调用，简化代码并让 BPF 在任务被 reenqueue 之前更新其放置状态；
- 实现该回调即启用 hinting-fault 扫描（初始 preferred node 在 enable 时上报）。

Andrea 表示会做实验并据此发新版本（v2）。

## 版本演进与当前进展
*current_version: v1*（5 补丁，`<20261004072901.3579967-1-arighi@nvidia.com>`）。今天的增量（Andrea 回帖 `<aslWrnlHYy9b5lEm@gpd4>`）：

- 回应 Tejun 的 ops flag 质疑：「no particular reason to use a separate ops flag… I like the ops callback approach that reports the preferred node and enables the hinting-fault scan when the callback is implemented」；
- 提出 `set_numa_node(p, nid)` 在 `sched_setnuma()` rq 锁下调用；
- 「I'll do some experiments with this approach and send a new version」——v2 待发。

## Maintainer 意见与讨论焦点
- **Tejun Heo**（sched_ext 顶层维护者）：核心关切是接口形态——事件回调优于「flag 门控 + 值轮询」，这是合入前最后的设计关卡。
- **Andrea Righi**（作者、sched_ext 维护者）：今天接受并具体化（`set_numa_node` 在 rq 锁下调用），表示做实验后发新版本。
- 无 NAK；接口形态已收敛为「事件式 op」，剩余是 v2 的实现与 Tejun 对 1/5、2/5 动 `kernel/sched/fair.c` 的把关。

## 合入评估
*likelihood=medium*。作者/测试员侧有效性已有 Vladimir 回植实测背书，接口形态今天由 Tejun 与 Andrea 收敛；但 3/5、4/5 需按事件 op 重构，且 1/5、2/5 动 NUMA 公平侧代码，Tejun 与 NUMA 侧维护者的 review 仍未开始。*blocking_issues*：v2（事件 op 版）未发；1/5、2/5 的 NUMA 侧 review 未开始。*next_action*：Andrea 发事件式 op 的 v2，等 Tejun/Mel 侧 review。

## 效果评估
Vladimir 的回植实测（见 related_articles）：把 1-3/5 回植 6.18.54 + 自家调度器后，4G 内存 20 秒完成迁移——为系列有效性背书。今天的接口讨论无新增数据。

## 我可以参与的点
- 等 v2 事件式 op 落地后，复测 `set_numa_node` 回调在 enable/扫描路径的调用时序；
- 在 2 节点/4 节点宿主机上验证 v2 的 hinting-fault 扫描与 preferred node 上报。

## 参考链接
- 系列 cover: https://lore.kernel.org/all/20261004072901.3579967-1-arighi@nvidia.com/
- Andrea 今日回帖: https://lore.kernel.org/all/aslWrnlHYy9b5lEm@gpd4/
