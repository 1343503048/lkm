# sched/eevdf: Fix sched idle task group preemption

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261106-003：Peter Zijlstra 发 3 补丁系列修 cgroup SCHED_IDLE 任务组抢占；patch 3（RFC）携带 Vincent 的 `sched/eevdf: Fix sched idle task group preemption`。
- sched-20261107-005 / 20261109-006 / 20261110-011：patch 1/2 获 Vincent/Kayra/Josh 多方 Reviewed-by，patch 3 被 Josh 质疑 `se_is_idle()` 语义。
- sched-20261111-010：Josh 为「检查任何 idle 祖先」的层级相对语义正名。
- sched-20261112-016（今天）：**Peter 把 patch 1/2 推到 queue/sched/urgent**（「它们解决了最糟的部分」），但对 patch 3 仍不买账——「idle 的意思是『无所谓，有空就跑』，为一个 idle 任务去抢占另一个 idle 任务毫无意义」；并提出「idle（任务或 cgroup 属性）应像暗示极低权重一样暗示超长 slice」。

## 背景与问题

（承接 sched-20261106-003 … 20261111-010）cgroup SCHED_IDLE 任务组的抢占语义：`cfs_rq::idle` 此前只反映本组自身 idle 状态、未聚合祖先。patch 1/2 修了核心判定，patch 3 是 EEVDF 层的「idle 组之间不互相抢占」优化。今日 Peter 对 patch 3 的根本必要性提出质疑。

## 技术方案

（承接）今日无新代码：patch 1/2（guard 清理 + `cfs_rq::idle` = 祖先 tg::idle 之和）被 Peter 推入 queue/sched/urgent。patch 3 的 `se_is_idle()` 抢占判定被 Peter 从语义层面质疑——「我们不应为调度另一个『无所谓』的任务而抢占一个『无所谓』的任务」；并给出替代思路：让 idle 属性（任务或 cgroup）暗示一个超长 slice 长度（正如它已暗示极低权重），从而用 EEVDF 的 slice 机制自然实现「idle 任务不急于抢占」，而非在抢占路径上特判。

## 版本演进与当前进展

*current_version: v2（patch 1/2 已入 queue/sched/urgent，patch 3 仍 RFC）*。今日：patch 1/2 被收取进 Peter 的 sched/urgent 队列；patch 3 仍待定，Peter 提出「idle 暗示超长 slice」的替代方向。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（维护者/作者）**：patch 1/2 已推到 queue/sched/urgent；对 patch 3 明确「仍不确信我们需要它」——idle 语义上不应抢占，且质疑「层级位置不同」是否构成抢占理由；给出「idle → 超长 slice」的替代设计。
- 无 NAK（对 patch 1/2）；patch 3 从「语义是否正确」转为「是否值得做、用什么机制做」的取舍。

## 合入评估

*likelihood=medium*。patch 1/2 已入 queue/sched/urgent（即将进 tip），patch 3 仍 RFC 且 Peter 倾向用「超长 slice」替代机制。*blocking_issues*：patch 3 的必要性与实现机制未定（Peter 提出 idle→超长 slice 的替代方向）。*next_action*：Peter 就「idle 暗示超长 slice」是否取代 patch 3 的抢占特判与 Vincent 对齐，再决定 patch 3 的去留。

## 效果评估

无量化性能数据。patch 1/2 为抢占语义正确性修复；patch 3 为「idle 组间不互相抢占」的优化，Peter 认为其收益尚未被证明必要。

## 我可以参与的点

- **discussion**：评估 Peter「idle 属性暗示超长 slice」方案与 patch 3 现有 `se_is_idle()` 特判的等价性与边界差异（超长 slice 是否会影响 idle 任务在真正有普通任务到来时的响应性）——这决定 patch 3 的最终形态。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261105165525.011876858@infradead.org/
- Peter 对 patch 3 的质疑: https://lore.kernel.org/all/20261112123119.GX1813469@noisy.programming.kicks-ass.net/
- Peter 的「idle→超长 slice」想法: https://lore.kernel.org/all/20261112123852.GE1922751@noisy.programming.kicks-ass.net/

---
id: sched-20261112-016
date: '2026-11-12'
subject: "sched/eevdf: Fix sched idle task group preemption"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261105165525.011876858@infradead.org>"
lore_url: "https://lore.kernel.org/all/20261105165525.011876858@infradead.org/"
authors: [Peter Zijlstra, Vincent Guittot]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v2
    msgid: "<20261105165525.011876858@infradead.org>"
    date: '2026-11-05'
    summary: "cfs_rq::idle 改为祖先 tg::idle 之和；patch 3 RFC 携带 EEVDF idle 组抢占修复"
    review_outcome: "patch 1/2 入 queue/sched/urgent；patch 3 被 Peter 质疑必要性并提出超长 slice 替代"
upstream_commit: null
fixes_commit: null
merged_branch: "queue/sched/urgent"
merge_assessment:
  likelihood: medium
  blocking_issues: ["patch 3 必要性与实现机制未定（idle→超长 slice 替代方向待对齐）"]
  next_action: "Peter 与 Vincent 对齐 patch 3 去留后决定"
contribution_opportunities:
  - kind: discussion
    description: "评估 idle 暗示超长 slice 与 se_is_idle 特判的等价性与边界差异"
generated_at: "2026-11-13T09:00:00+08:00"
source_email_count: 2
related_articles: [sched-20261106-003, sched-20261107-005, sched-20261109-006, sched-20261110-011, sched-20261111-010]
tags: [cgroup, cfs, eevdf]
---