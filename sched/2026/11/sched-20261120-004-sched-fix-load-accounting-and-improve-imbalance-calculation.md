# sched: Fix load accounting and improve imbalance calculation

## TL;DR

Srikar Dronamraju（IBM）发 3 补丁系列：patch 1 把 delayed-dequeued 任务从 `sum_nr_running` 剔除（修正调度组负载统计高估），patch 2 对「组内 core 数不同」的域改用可运行任务分布计算 imbalance，patch 3 清理 `cache_nice_tries` 初始化。Peter Zijlstra 对 patch 1 指出 `h_nr_runnable` 已排除 delayed、含 delayed 的是 `h_nr_queued`。刚发出，处于澄清阶段。

## 背景与问题

delayed-dequeued 任务在 `rq->nr_running` 中仍可见（尽管已不可运行），导致 `update_sg_lb_stats()` 的 `sum_nr_running` 高估可运行负载、负载均衡统计失真。此外，含「core 数不同」的组的调度域里，仅看 idle CPU 数会误导——较大的组天然有更多 idle CPU，即便它相对更忙；应改按可运行任务分布计算不平衡。第 3 个补丁是 `cache_nice_tries` 初始化的纯清理（结果不变）。

## 技术方案

- **patch 1/3** `sched/fair: Exclude delayed-dequeued tasks from sum_nr_running`：从 `update_sg_lb_stats()` 的 `sum_nr_running` 里排除 delayed-dequeued 任务。
- **patch 2/3** `sched/fair: Use runnable task imbalance for asymmetric groups`：对组规模不等的域，用可运行任务分布替代 idle CPU 计数做 imbalance 计算。
- **patch 3/3** `sched/topology: Simplify cache_nice_tries initialization`：简化初始化、结果不变。

Peter 对 patch 1 的第一条评论：`h_nr_runnable already excludes delayed; its is h_nr_queued that includes it.`——即作者所用的记账口径可能不准确（`sum_nr_running` 与 `h_nr_*` 的关系待澄清）。

## 版本演进与当前进展

*current_version: v1（2026-11-20，`<20261120014946.1355234-5-srikar@linux.ibm.com>`，3 补丁）*。首版（0/3 封面当日 00:35 与 01:49 各发一次，后者为补丁配套）。今日即有 Peter 对 patch 1 的澄清性评论。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（sched maintainer）**：对 patch 1 提示 `sum_nr_running` 与 `h_nr_runnable`/`h_nr_queued` 的延迟任务口径关系，点出作者引用的记账口径可能不准。
- 无 NAK；首条评论属澄清性，尚未展开后续讨论。

## 合入评估

*likelihood=unknown*。系列刚发出，Peter 仅对 patch 1 提出记账口径疑问，方向（修正负载高估、改进不对称组 imbalance）合理但证据尚不足以判断。*blocking_issues*：patch 1 的 `sum_nr_running` 口径需与 Peter 澄清。*next_action*：作者回应 Peter 的口径质疑，随后继续评审。

## 效果评估

作者未给出具体性能/统计数据，仅说明 patch 1 修正 `sum_nr_running` 高估、patch 2 改进不对称组 imbalance 计算的正确性；属正确性修复，效果为「主观判断，未见数据」。

## 我可以参与的点

- **discussion**：就 `sum_nr_running` 与 `h_nr_runnable`/`h_nr_queued` 在 delayed-dequeued 任务上的口径差异提供分析，助作者解答 Peter 的疑问。
- **testing**：在不含大小核/异构拓扑的对称机上验证 patch 1/2 无负载均衡回归，在与 asymmetric（如 Power）机型上复测 patch 2。

## 参考链接

- lore thread（0/3 cover）: https://lore.kernel.org/all/20261120014946.1355234-5-srikar@linux.ibm.com/

---
id: sched-20261120-004
date: '2026-11-20'
subject: "sched: Fix load accounting and improve imbalance calculation"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261120014946.1355234-5-srikar@linux.ibm.com>"
lore_url: "https://lore.kernel.org/all/20261120014946.1355234-5-srikar@linux.ibm.com/"
authors: [Srikar Dronamraju]
maintainers_involved: [Peter Zijlstra]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261120014946.1355234-5-srikar@linux.ibm.com>"
    date: '2026-11-20'
    summary: "3 补丁：排除 delayed-dequeued 任务出 sum_nr_running、不对称组改用 runnable imbalance、清理 cache_nice_tries 初始化"
    review_outcome: "Peter 对 patch 1 提出 h_nr_runnable/h_nr_queued 口径疑问"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["patch 1 的 sum_nr_running 口径需与 Peter 澄清"]
  next_action: "作者回应 Peter 口径质疑后继续评审"
contribution_opportunities:
  - kind: discussion
    description: "分析 sum_nr_running 与 h_nr_runnable/h_nr_queued 在 delayed-dequeued 任务上的口径差异"
  - kind: testing
    description: "在对称机与 asymmetric（Power 等）机型上分别复测 patch 1/2 无负载均衡回归"
generated_at: "2026-11-21T09:00:00+08:00"
source_email_count: 216
related_articles: []
tags: [cfs, load_balance]
---