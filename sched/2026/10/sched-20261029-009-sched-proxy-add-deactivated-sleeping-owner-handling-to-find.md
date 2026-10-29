# sched/proxy: Add deactivated (sleeping) owner handling to find_proxy_task()

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261024-001（v33）：John Stultz 的 proxy execution 第 5 阶段「Sleeping Owner Handling」第 33 版，扩到 7 补丁，聚合多人修复（psi 状态、远程 tick 用 rq->donor、无 owner 激活 blocked donor、proxy 链循环检测等）；Peter Zijlstra、Andrea Righi、Kayra Cizmeci 当日密集 review。
- sched-20261026-006：7/7 核心补丁及 1/3/4 补丁的深度 review。
- sched-20261027-010：Kayra 对 7/7 再提一条——质疑 `find_proxy_task()` 里 deactivated（sleeping）owner 处理是否也需覆盖 delayed 任务，给出 `proxy_enqueue_on_owner()` → `block_task()` → `dequeue_task_fair()` 可能只置 `sched_delayed` 的链路。
- sched-20261029-009（今天）：K Prateek Nayak 回 Juri Lelli（proxy 维护者）：**ACK** `!task_on_migrating(p) && p->is_blocked` 应已覆盖所有 case；顺带指出 `dl_task_offline_migration()` 把被节流任务迁出 offline rq 的方式「很有意思」。此前 Kayra 担心的 delayed 覆盖问题由此基本收敛。

## 背景与问题
（承接 v33）proxy execution 第 5 阶段处理「任务阻塞在 mutex 上而 owner 本身在睡眠」：需在 owner 唤醒时重新激活挂在其上的 waiter 树，waiters 可嵌套、需额外列表规避级联递归。7/7 补丁给 `find_proxy_task()` 加 deactivated（sleeping）owner 的查找处理。此前的开放点是 Kayra 提出的「是否也需覆盖 `sched_delayed`（而非仅 `is_blocked`）任务」——今日 K Prateek 以 `!task_on_migrating(p) && p->is_blocked` 的条件组合认定已覆盖。

## 技术方案
（承接 v33）7/7 补丁内容为在 `find_proxy_task()` 中处理已停用的睡眠 owner。今日无代码变更；K Prateek Nayak 从条件完备性角度确认 `!task_on_migrating(p) && p->is_blocked` 覆盖所有 case，并补充观察：`dl_task_offline_migration()` 迁移被节流任务离开 offline rq 的方式特殊（节流任务在该路径下的迁移语义值得留意，属题外但相关）。

## 版本演进与当前进展
*current_version: v33*（2026-10-23，cover `<20261023220431.1106611-1-jstultz@google.com>`）。7/7 补丁自 20261024 起连续多日被密集 review，今日获 K Prateek Nayak 的条件完备性 ACK，Kayra 的 delayed 覆盖疑虑基本消除。无新补丁版本。

## Maintainer 意见与讨论焦点
- **K Prateek Nayak（AMD，今天）**：向 Juri Lelli（维护者）确认 `!task_on_migrating(p) && p->is_blocked` 覆盖所有 case（Ack）；并指出 `dl_task_offline_migration()` 对被节流任务的处理「interesting」，可能是后续需要单独审视的点。
- **Kayra Cizmeci（20261027）**：质疑 deactivated owner 处理是否覆盖 `sched_delayed` 任务——今日被 K Prateek 的条件组合回应基本解决。
- 未解决焦点：`dl_task_offline_migration()` 迁被节流任务的行为是否隐含 bug，K Prateek 只是提出观察、未下结论，Juri 尚未回应。

## 合入评估
*likelihood=low*。7/7 单补丁的条件完备性获 ACK、趋于收敛，但 proxy execution 整体仍是第 33 版、未合入主线的实验性大系列，单补丁的 ACK 不改变整体节奏。*blocking_issues*：proxy execution 整体仍待主线化（依赖前 4 个阶段的进展）；`dl_task_offline_migration()` 对被节流任务的迁移语义待澄清。*next_action*：Juri Lelli 收取该 ACK 并决定 7/7 是否可纳入系列下一版。

## 效果评估
无性能数据——proxy execution 系列以正确性为主线，今日讨论是条件完备性的确认，无 benchmark。

## 我可以参与的点
- **review**：K Prateek 点名的 `dl_task_offline_migration()` 对被节流任务的迁移语义，可结合 `kernel/sched/deadline.c` 分析其是否隐含问题。
- **testing**：在 proxy execution 分支上构造「owner 睡眠 + waiter 嵌套 + delayed 任务」场景，验证 7/7 对 sleeping/delayed owner 的覆盖是否完整。

## 参考链接
- lore thread（v33 cover）: https://lore.kernel.org/all/20261023220431.1106611-1-jstultz@google.com/
- K Prateek Nayak 今日的 Ack: https://lore.kernel.org/all/faec8c94-0837-430b-ba60-00fa4a8a5eb4@amd.com/

---
id: sched-20261029-009
date: 2026-10-29
subject: "sched/proxy: Add deactivated (sleeping) owner handling to find_proxy_task()"
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: "<20261023220431.1106611-1-jstultz@google.com>"
lore_url: "https://lore.kernel.org/all/20261023220431.1106611-1-jstultz@google.com/"
authors: [John Stultz]
maintainers_involved: []
current_version: v33
patch_series:
  - version: v33
    msgid: "<20261023220431.1106611-1-jstultz@google.com>"
    date: 2026-10-23
    summary: "7 补丁：proxy execution 第 5 阶段 Sleeping Owner Handling；7/7 给 find_proxy_task() 加 deactivated owner 处理"
    review_outcome: "Kayra 质疑 delayed 任务覆盖；今日 K Prateek Nayak 确认 !task_on_migrating && is_blocked 覆盖所有 case"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - "proxy execution 整体仍是未合入的实验性大系列"
    - "dl_task_offline_migration() 对被节流任务的迁移语义待澄清"
  next_action: "Juri Lelli 收取 ACK 并决定 7/7 是否纳入系列下一版"
contribution_opportunities:
  - kind: review
    description: "分析 dl_task_offline_migration() 对被节流任务的迁移是否隐含问题"
  - kind: testing
    description: "构造 owner 睡眠 + waiter 嵌套 + delayed 任务场景验证 7/7 覆盖完整性"
generated_at: "2026-10-30T09:30:00"
source_email_count: 1
related_articles: [sched-20261024-001, sched-20261025-010, sched-20261026-006, sched-20261027-010]
tags: [proxy_execution]
---