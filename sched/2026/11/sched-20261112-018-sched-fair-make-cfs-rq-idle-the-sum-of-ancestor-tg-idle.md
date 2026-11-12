# sched/fair: Make cfs_rq::idle the sum of ancestor tg::idle

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261106-003：Peter Zijlstra 发 3 补丁系列修 cgroup SCHED_IDLE 任务组抢占，patch 2 把 `cfs_rq::idle` 改为「祖先 tg::idle 之和」；Kayra 指出 patch 2 有任务组创建竞态。
- sched-20261107-005 / 20261109-006 / 20261110-011：patch 2 v2 并入竞态修正，获 Vincent/Kayra/Josh 多方 Reviewed-by。
- sched-20261112-018（今天）：**Peter 把 patch 2 再次 push 出队列**（「看看机器人还能找到什么」），**0-day 机器人随即抓到构建失败**——`idle` 成员只存在于 `CONFIG_FAIR_GROUP_SCHED` 下，导致 `!CONFIG_FAIR_GROUP_SCHED` 编译不过；Kayra 定位并给出修法（把该成员下移到 `CONFIG_FAIR_GROUP_SCHED` 内、`h_load` 附近）。

## 背景与问题

（承接 sched-20261106-003 / 20261107-005 / 20261109-006 / 20261110-011）cgroup SCHED_IDLE 任务组的抢占语义：`cfs_rq::idle` 此前只反映本组自身 idle 状态、未聚合祖先，导致嵌套 idle 判定错误。patch 2 用「`cfs_rq::idle` = 祖先 tg::idle 之和」修复。今日 Peter 再次 push 后，0-day 抓到 `idle` 成员放错了位置——不在 `CONFIG_FAIR_GROUP_SCHED` 保护内，破坏 `!CONFIG_FAIR_GROUP_SCHED` 的构建。

## 技术方案

（承接）patch 2 的 `cfs_rq::idle` 成员本应在 `CONFIG_FAIR_GROUP_SCHED` 保护内。Kayra 分析 0-day 报告（`202611121431.06YgiErz-lkp@intel.com`）后给出修法：把该成员下移到 `CONFIG_FAIR_GROUP_SCHED` 段内（`h_load` 附近）。

## 版本演进与当前进展

*current_version: v2（patch 2，2026-11-07）*。今日：Peter 再次 push patch 2 入队列，被 0-day 抓到 `!CONFIG_FAIR_GROUP_SCHED` 构建失败，修法已由 Kayra 定位，预计下一次 push 修复。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（作者/维护者）**：「Yeah, pushed out again, lets see if the robots find more」——patch 2 已再次进队列，靠 0-day 兜底。
- **Kayra Cizmeci**：接住 0-day 报告并定位——`idle` 只在 `CONFIG_FAIR_GROUP_SCHED` 下，应下移到该保护段内（`h_load` 旁）。
- 无 NAK；patch 2 本身已多方 Reviewed-by，仅剩一个构建配置修复。

## 合入评估

*likelihood=high*。patch 2 已获 Vincent/Kayra/Josh 三方评审并再次进队列，仅剩 `!CONFIG_FAIR_GROUP_SCHED` 构建修复（修法已明确）。*blocking_issues*：`idle` 成员需下移到 `CONFIG_FAIR_GROUP_SCHED` 保护内。*next_action*：Peter 采纳 Kayra 的修法重新 push，即可进 tip。

## 效果评估

无量化性能数据，属抢占语义正确性修复。Vincent 此前确认 patch 2 可避免 `find_matching_se()` 无谓调用（微观优化）。

## 我可以参与的点

- **review**：核对 `idle` 成员下移后，所有访问该成员的代码点是否都在 `CONFIG_FAIR_GROUP_SCHED` 保护内（`!CONFIG_FAIR_GROUP_SCHED` 下 `cfs_rq::idle` 语义应如何退化）。

## 参考链接

- Kayra 对构建失败的定位: https://lore.kernel.org/all/avXFHBcVoMkZY6uL@scheduler.schedules/
- 0-day 构建失败报告: https://lore.kernel.org/oe-kbuild-all/202611121431.06YgiErz-lkp@intel.com/

---
id: sched-20261112-018
date: '2026-11-12'
subject: "sched/fair: Make cfs_rq::idle the sum of ancestor tg::idle"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<avXFHBcVoMkZY6uL@scheduler.schedules>"
lore_url: "https://lore.kernel.org/all/avXFHBcVoMkZY6uL@scheduler.schedules/"
authors: [Peter Zijlstra, Vincent Guittot]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v2
    msgid: "<20261107113639.GK2668200@noisy.programming.kicks-ass.net>"
    date: '2026-11-07'
    summary: "cfs_rq::idle 改为祖先 tg::idle 之和并并入竞态修正"
    review_outcome: "多方 Reviewed-by；再次 push 被 0-day 抓到 !CONFIG_FAIR_GROUP_SCHED 构建失败"
upstream_commit: null
fixes_commit: null
merged_branch: "queue/sched/urgent"
merge_assessment:
  likelihood: high
  blocking_issues: ["idle 成员需下移到 CONFIG_FAIR_GROUP_SCHED 保护内"]
  next_action: "Peter 采纳 Kayra 修法重新 push 后进 tip"
contribution_opportunities:
  - kind: review
    description: "核对 idle 成员下移后所有访问点都在 CONFIG_FAIR_GROUP_SCHED 保护内"
generated_at: "2026-11-13T09:00:00+08:00"
source_email_count: 2
related_articles: [sched-20261106-003, sched-20261107-005, sched-20261109-006, sched-20261110-011]
tags: [cgroup, cfs]
---