# sched/fair: Update decision matrix and rename pinned-task group state

> **subject**：`sched/fair: Update decision matrix and rename pinned-task group state`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260928-004：Jemmy Wong 的 3 补丁 v1（纯澄清/清理、No functional change）——patch 1 补齐 `sched_balance_find_src_group()` 上方决策矩阵注释表（`smt_balance`/`llc_balance` 两列此前无人更新），patch 2-3 把「cpus_ptr 固定任务导致的均衡失败」状态从 `group_imbalanced`/`sgc->imbalance` 改名。v1 无 review。
- sched-20261002-010（今天）：Tim Chen（Intel）完成实质 review 并当场促成 v2——patch 1 逐格核对后发现一处错误：local=`has_spare`、busiest=`llc_balance` 应为「force」而非「nr_idle」（`prefer_sibling` 且 group 为 LLC 级时 `group_llc_balance` 分支短路 `sibling_imbalance()` 无条件拉取）；patch 2 建议更贴切的 `group_pinned_imb`（保留 pinned 限定词、匹配短名 imb）。Jemmy 当日回复确认并发出 v2：该格改为 force、命名采用 `group_pinned_imb`/`sgc->pinned_imb`/`sg_pinned_imb()`，changelog 同步改写。

## 背景与问题

（承接 sched-20260928-004）`sched_balance_find_src_group()` 上方的 group-type 决策矩阵注释表由 Vincent Guittot（commit 0b0695f2b34a）引入，之后 fee1759e4f04 加 `group_smt_balance`、f38cc2f0d8a3 加 `group_llc_balance` 都没更新表；`group_imbalanced` 名不副实（6263322c5e8f 后是亲和性失败标志而非负载倾斜度量）。今天 Tim 的核对发现 v1 patch 1 的新表仍有一格与代码不符：

```c
if (sds.prefer_sibling && local->group_type == group_has_spare &&
    (busiest->group_type == group_llc_balance ||
     sibling_imbalance(env, &sds, busiest, local) > 1))
        goto force_balance;
```

`group_llc_balance` 分支短路了 `sibling_imbalance()` 测试——`prefer_sibling` 置位时该组合无条件 force。而 `prefer_sibling` 来自 busiest 组的子域 flags：`sd_init()` 对每层都设 SD_PREFER_SIBLING、只有 SD_NUMA 清除——跨 LLC 的组（域层级 span per-LLC）保留该 flag，故「除非子域是 NUMA 域，该格就是 force」。v1 表里写 nr_idle、changelog 却说 force，自相矛盾。

## 技术方案

（承接 v1 框架）v2 三补丁（`<20261002154634.71878-{1..4}-jemmywong512@gmail.com>`，2 文件 +39/−33）：

1. **v2 1/3 Add smt_balance and llc_balance to the decision matrix**：local `has_spare` × busiest `llc_balance` 一格改为 **force**（Tim）；changelog 与 cover 按其实际触发条件改写——SD_PREFER_SIBLING 在 SMT/CLUSTER/MC/PKG 各层都设、仅 SD_NUMA 清除，故除非子域是 NUMA 域，该格强制拉取。
2. **v2 2/3 Rename group_imbalanced to group_pinned_imb**（Tim 建议，v1 为 `group_pinned_task`）：保留「pinned」限定词、匹配既有 `group_misfit_task` 式短名与 `imb` 缩写习惯。
3. **v2 3/3 Rename sgc->imbalance to sgc->pinned_imb**：reader 同步改 `sg_pinned_imb()`。

仍为 No functional change；patch 1 独立于 2-3。

## 版本演进与当前进展

- v1（09-28，`<20260928042018.10618-1-jemmywong512@gmail.com>`）：3 补丁，无 review（sched-20260928-004）。
- 10-02（今天）：
  - 05:34 Tim 对 1/3 的 review（`<57c0b8017ec57818815dd833963b594304d61447.camel@linux.intel.com>`）：逐格核对、指出 force/nr_idle 错格，要求 flip。
  - 05:54 Tim 对 2/3 的 review（`<88f28ac61e238cef9bcf8fda3adb4326c15ba15e.camel@linux.intel.com>`）：建议 `group_pinned_imbalance`/`group_pinned_imb` 更具描述性。
  - 19:02/19:03 Jemmy 两封回复（`<5FA792B9-...>`、`<EFCC9B8D-...>`）：确认短路分析、补充 prefer_sibling 传播路径自查（update_sd_lb_stats 取 busiest 子域 flags），承诺 v2 改 force + group_pinned_imb。
  - 23:46 v2 0/3+1/3+2/3+3/3 发出，changelog 记录两条 Tim 意见的落实。

## Maintainer 意见与讨论焦点

- **Tim Chen**（Intel，评审者）：本轮是高质量的「表格 vs 代码」逐格核对（「I walked the new rows and columns against sched_balance_find_src_group(), and they line up, with one exception」），并给出精确的触发链分析。
- **Jemmy Wong**（作者）：当日完成 review 回应 + v2 重发，响应迅速。
- Vincent Guittot / Peter Zijlstra（fair.c 负责人）：仍未表态——命名类改动最终需其认可。
- 无分歧残留：Tim 的两条意见全部落实。

## 合入评估

*likelihood=medium*。低风险清理系列，经 Tim 实质 review 修正后表格与代码一致性有保证；但决策矩阵注释与负载均衡路径命名最终裁定权在 Vincent/Peter，尚未表态。*blocking_issues*：Vincent/Peter 未 review。*next_action*：等负载均衡维护者对 v2 的收取（无功能变化、注释准确性已经 Tim 背书）。

## 效果评估

无性能数据（No functional change）。质量证据：Tim 逐格核对 + 作者两处修正闭环。

## 我可以参与的点

- `review`：v2 表格里其余格（尤其 `smt_balance` 行与 NUMA 域子域例外）可再做一轮独立核对——Tim 只报了一处错格，交叉验证能进一步降低注释错误的存量。
- `discussion`：向 Vincent/Peter 补一条「为什么值得合入」的说明（注释与代码脱节曾误导过多少 review），帮助系列过门。

## 参考链接

- v2 cover: https://lore.kernel.org/all/20261002154634.71878-1-jemmywong512@gmail.com/
- Tim 对 1/3 的 review: https://lore.kernel.org/all/57c0b8017ec57818815dd833963b594304d61447.camel@linux.intel.com/
- Tim 对 2/3 的 review: https://lore.kernel.org/all/88f28ac61e238cef9bcf8fda3adb4326c15ba15e.camel@linux.intel.com/

---
id: sched-20261002-010
date: '2026-10-02'
subject: 'sched/fair: Update decision matrix and rename pinned-task group state'
subsystem: sched
type: discussion
status: under_review
severity: none
thread_root_msgid: '<20260928042018.10618-1-jemmywong512@gmail.com>'
lore_url: 'https://lore.kernel.org/all/20261002154634.71878-1-jemmywong512@gmail.com/'
authors:
  - 'Jemmy Wong'
maintainers_involved: []
current_version: v2
patch_series:
  - version: v1
    msgid: '<20260928042018.10618-1-jemmywong512@gmail.com>'
    date: '2026-09-28'
    summary: '3 补丁：决策矩阵补列 + pinned-task 命名清理'
    review_outcome: '无 review'
  - version: v2
    msgid: '<20261002154634.71878-1-jemmywong512@gmail.com>'
    date: '2026-10-02'
    summary: 'llc_balance×has_spare 格改 force；命名改 group_pinned_imb/sgc->pinned_imb/sg_pinned_imb()'
    review_outcome: '落实 Tim Chen 两条意见，当日发出'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'Vincent/Peter 未 review'
  next_action: '等负载均衡维护者对 v2 收取'
contribution_opportunities:
  - kind: review
    description: '对其余格（smt_balance 行、NUMA 子域例外）做独立交叉核对'
  - kind: discussion
    description: '向维护者补充合入价值说明'
generated_at: '2026-10-03T01:00:00'
source_email_count: 8
related_articles:
  - sched-20260928-004
tags:
  - load_balance
---
