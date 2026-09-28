# sched/fair: Update decision matrix and rename pinned-task group state

## TL;DR

Jemmy Wong 发的 3 补丁系列，纯代码澄清/清理、明确标注「No functional change」：patch 1 把 `sched_balance_find_src_group()` 上方的 group-type 决策矩阵注释表补齐（此前新增 `smt_balance`、`llc_balance` 两类组时没人更新这张表）；patch 2-3 把「因 cpus_ptr 固定任务导致的负载均衡失败」状态从 `group_imbalanced`/`sgc->imbalance` 改名为 `group_pinned_task`/`sgc->pinned_task`，消除与 `env->imbalance`、`imbalance_pct` 的命名冲突。v1 刚发出，暂无 review。

## 背景与问题

（代码质量改进类）决策矩阵注释表由 Vincent Guittot 在 commit 0b0695f2b34a（"sched/fair: Rework load_balance()"）引入。之后 commit fee1759e4f04 加了 `group_smt_balance`、commit f38cc2f0d8a3 加了 `group_llc_balance`，两个作者都没更新这张矩阵表。另一处：`group_imbalanced` 这个名字来自早年的 group_imb 启发式（确实曾检测 per-CPU 负载倾斜），但 commit 6263322c5e8f 把它改成了「亲和性失败标志」却沿用旧名——如今 `group_classify()` 对它的判定、`calculate_imbalance()` 对它的处理（只搬一个任务、imbalance=1）、以及 `sgc->imbalance` 与 `env->imbalance`/`imbalance_pct` 的冲突，都让这个名字名不副实。

## 技术方案

- patch 1：更新决策矩阵注释表，把 busiest 的 `smt_balance` 与 `llc_balance` 两列补上（两列均为 N/A，因为二者只在非本地组被标记；作为 busiest 都走 nr_idle 检查而非无条件 force，并与更忙的本地组对比）。patch 1 独立于 2-3，可单独应用。
- patch 2：`group_imbalanced` → `group_pinned_task`（紧跟 `group_misfit_task` 的 adjective_noun 命名），枚举是 fair.c 本地符号，无 tracepoint/schedstat 可见面变化。
- patch 3：`sgc->imbalance` → `sgc->pinned_task`，reader 由 `sg_imbalanced()` 改名为 `sg_pinned_task()`。

## 版本演进与当前进展

*current_version: v1*，28 日发出（4 封：封面 + 3 补丁），暂无任何 review 回复。

## Maintainer 意见与讨论焦点

无维护者或社区回应。系列定位是低风险的澄清/清理补丁，但负载均衡路径的维护者（Vincent Guittot、Peter Zijlstra 等）尚未表态。

## 合入评估

*likelihood=unknown*。v1 刚发出、无人回复，无法判断维护者是否认可这批命名与矩阵表的改法。*blocking_issues*：无评审反馈；「No functional change」需维护者确认命名与注释确实只改表象不改语义。*next_action*：等待负载均衡维护者对 patch 1 矩阵表与 patch 2-3 命名的 review。

## 效果评估

无性能数据——作者在封面明确「No functional change」，改动旨在纠正注释与命名、降低后续维护的认知负担。

## 我可以参与的点

- `review`：核对 patch 1 的决策矩阵表是否准确反映 `group_smt_balance`/`group_llc_balance` 的实际判定路径（尤其 smt_vs_nonsmt_groups、prefer_sibling 的边界），以及 patch 2-3 重命名是否漏改任何 `sgc->imbalance`/`group_imbalanced` 引用。
- `discussion`：这类「为历史遗留命名正名」的重命名是否值得做、是否有更贴切的命名，可参与讨论。

## 参考链接

- 系列封面: https://lore.kernel.org/all/20260928042018.10618-1-jemmywong512@gmail.com/

---
id: sched-20260928-004
date: '2026-09-28'
subject: 'sched/fair: Update decision matrix and rename pinned-task group state'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20260928042018.10618-1-jemmywong512@gmail.com>'
lore_url: 'https://lore.kernel.org/all/20260928042018.10618-1-jemmywong512@gmail.com/'
authors:
  - 'Jemmy Wong'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260928042018.10618-1-jemmywong512@gmail.com>'
    date: '2026-09-28'
    summary: '决策矩阵注释表补 smt/llc 两列；group_imbalanced/sgc->imbalance 改名 pinned_task'
    review_outcome: '暂无 review'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - '无评审反馈，需负载均衡维护者确认命名与矩阵表只改表象不改语义'
  next_action: '等待负载均衡维护者 review'
contribution_opportunities:
  - kind: review
    description: '核对矩阵注释表与 smt/llc 判定路径、重命名是否漏改引用'
  - kind: discussion
    description: '评估历史遗留命名正名的改名是否贴切'
generated_at: '2026-09-29T01:00:00'
source_email_count: 4
related_articles: []
tags:
  - load_balance
  - cfs
---