# sched/fair: Add smt_balance and llc_balance to the decision matrix

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260928-004：Jemmy Wong 的 3 补丁 v1（纯澄清/清理、No functional change）——patch 1 补齐 `sched_balance_find_src_group()` 上方决策矩阵注释表（`smt_balance`/`llc_balance` 两列此前无人更新），patch 2-3 把「cpus_ptr 固定任务导致的均衡失败」状态改名。
- sched-20261002-010：Tim Chen（Intel）完成实质 review 并促成 v2——发现 v1 新表 local=`has_spare` × busiest=`llc_balance` 一格应为「force」而非「nr_idle」（`group_llc_balance` 分支短路 `sibling_imbalance()` 无条件拉取）；patch 2 命名改 `group_pinned_imb`。Jemmy 当日发 v2 落实。
- sched-20261003-006（今天）：Tim Chen 对 v2 1/3 给出 **Reviewed-by**——该补丁（决策矩阵表补齐）正式获得发现错误的原 reviewer 认可。

## 背景与问题

（承接 sched-20261002-010）`sched_balance_find_src_group()` 上方的 group-type 决策矩阵注释表由 Vincent Guittot（commit 0b0695f2b34a）引入，之后 fee1759e4f04 加 `group_smt_balance`、f38cc2f0d8a3 加 `group_llc_balance` 都没更新表。v2 1/3 把 local=`has_spare` × busiest=`llc_balance` 格改为 force（SD_PREFER_SIBLING 各层都设、仅 SD_NUMA 清除，跨 LLC 组无条件拉取），changelog 按实际触发条件改写。

## 技术方案

（承接 v2）三补丁（`<20261002154634.71878-{1..4}-jemmywong512@gmail.com>`，2 文件 +39/−33）：

1. **1/3 Add smt_balance and llc_balance to the decision matrix**：补齐两列、修正 force 格；今日获 Tim Chen `Reviewed-by`。
2. **2/3 Rename group_imbalanced to group_pinned_imb**。
3. **3/3 Rename sgc->imbalance to sgc->pinned_imb**。

仍为 No functional change；patch 1 独立于 2-3。

## 版本演进与当前进展

- v1（09-28）：无 review。
- v2（10-02，`<20261002154634.71878-1-jemmywong512@gmail.com>`）：按 Tim 意见修正 force 格与命名。
- 10-03：Tim Chen 对 v2 1/3 `Reviewed-by`（`<b71a4c1c1ea96f786672f1c18f39a85252f4baa3.camel@linux.intel.com>`）。2/3、3/3 尚无 review。

## Maintainer 意见与讨论焦点

- **Tim Chen**：v1 逐格核对发现错误 → v2 采纳 → 10-03 对 1/3 给 Reviewed-by。review 闭环完整。
- Vincent Guittot（决策矩阵引入者、fair.c 事实 maintainer）尚未表态——系列改的是他引入的注释表与命名，其认可通常是收取前提。

## 合入评估

*likelihood=medium*。1/3 已有发现者本人的 R-b、内容为纯注释澄清（风险极低）；但系列还含 2/3+3/3 的标识符改名（跨 fair.c 多处使用点），且 Vincent 未表态。*blocking_issues*：2/3、3/3 无 review；Vincent Guittot 未认领。*next_action*：等 Vincent 回复；若其只想要 1/3，系列可拆分收取（patch 1 本就独立）。

## 效果评估

无功能变化（No functional change），无性能数据。价值在文档正确性：决策矩阵表与代码行为一致，降低后续 LB 修改者的误读风险（Tim 核对发现的 force 格错误正是误读实例）。

## 我可以参与的点

- `review`：快速核对 2/3+3/3 改名是否覆盖 `group_imbalanced`/`sgc->imbalance` 的全部使用点（grep 级检查即可），补一条 review 回帖帮系列凑齐两片的 review。

## 参考链接

- lore（v2 1/3）: https://lore.kernel.org/all/20261002154634.71878-2-jemmywong512@gmail.com/
- lore（Tim Chen Reviewed-by）: https://lore.kernel.org/all/b71a4c1c1ea96f786672f1c18f39a85252f4baa3.camel@linux.intel.com/

---
id: sched-20261003-006
date: '2026-10-03'
subject: 'sched/fair: Add smt_balance and llc_balance to the decision matrix'
subsystem: sched
type: discussion
status: under_review
severity: none
thread_root_msgid: '<20261002154634.71878-1-jemmywong512@gmail.com>'
lore_url: 'https://lore.kernel.org/all/20261002154634.71878-2-jemmywong512@gmail.com/'
authors:
  - 'Jemmy Wong'
maintainers_involved:
  - 'Tim Chen'
current_version: v2
patch_series:
  - version: v1
    msgid: '<20260928042018.10618-1-jemmywong512@gmail.com>'
    date: '2026-09-28'
    summary: '决策矩阵注释表补齐 + group_imbalanced 改名（3 补丁）'
    review_outcome: '无 review'
  - version: v2
    msgid: '<20261002154634.71878-1-jemmywong512@gmail.com>'
    date: '2026-10-02'
    summary: 'force 格修正 + group_pinned_imb/sgc->pinned_imb 命名'
    review_outcome: '10-03 Tim Chen 对 1/3 给 Reviewed-by；2/3+3/3 待 review'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - '2/3、3/3 无 review'
    - 'Vincent Guittot 未表态'
  next_action: '等 Vincent 回复；patch 1 可独立收取'
contribution_opportunities:
  - kind: review
    description: '核对 2/3+3/3 改名覆盖全部使用点并回帖，帮系列凑齐 review'
generated_at: '2026-10-04T01:00:00'
source_email_count: 1
related_articles:
  - sched-20260928-004
  - sched-20261002-010
tags:
  - load_balance
  - fair
---
