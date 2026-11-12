# sched/fair: Add push task mechanism for fair

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261106-002：Vincent Guittot 的 v3 大系列（20 补丁）改进短 slice 任务调度延迟；dragonboard rb5 上 4 短任务同时醒来平均延迟约 1051us→61us。
- sched-20261107-004：Kayra 评审 patch 02-06，对 03/04/05 给 Reviewed-by。
- sched-20261109-002 / 20261110-010：Peter 评审 08/20（质疑新增列表 + plist）与 02/20，Vincent 逐条收口。
- sched-20261111-009：Peter 建议 08/20 限界（仿 `detach_one_task()`），并称「plist 对 fair/DL 无意义」。
- sched-20261112-015（今天）：**Peter 提议把 `cfs_tasks` 直接做成 RB-tree 或 augmented list（按 `{slice, exec_start}` 排序）**，Vincent 回应「可以用 RB 树、只是最初想复用 exclusive 的 pushable_tasks」并解释要「选一个 meaningful 任务而非随机」；**02/20 的 DEQUEUE_CLASS 问题被 Vincent 确认**——需在 `DEQUEUE_SLEEP`/`DEQUEUE_CLASS` 时更新 `idle_seq`。

## 背景与问题

（承接 sched-20261106-002 … 20261111-009）短 slice 任务在 EEVDF 下因 slice 短、lag 反复累积排不上队，多任务同时醒来堆叠同一 idle CPU。Vincent 的 v3 用「正 lag 衰减 + 选 CPU 考虑 slice + fair 类 push 回调」解决。今日收口在 push 候选列表的数据结构与 `cfs_tasks` 的语义边界。

## 技术方案

今日为设计评审，焦点两个补丁：

- **08/20 `Add push task mechanism for fair`**：Peter 指出 `cfs_tasks` 本身就是 pushable 列表（每个消费者都经 `can_migrate_task()`，`nr_cpus_allowed == 1` 的任务必失败），疑问在于作者要「一次 push 后 drop 任务」的额外语义；提议与其修剪列表长度，不如把 `cfs_tasks` 改成 RB-tree 并施加便利排序（`{se->slice, se->exec_start}`，slice 相等时近似现状、多 slice 长度时短者优先），或 augmented list（按 exec_start 排序、按 slice 增强）。Vincent 回应：可以用 RB 树、但最初只想复用 exclusive 的 pushable_tasks；不想要「随机任务」而只要「meaningful」的那个；愿在下一版加 slice 排序。此外澄清 push 的主场景是「任务被放回 runnable 列表时周期性找另一 CPU」，以及 patch 20 里「多个短任务选中同一 CPU」的情形。
- **02/20 `Reset lag at wakeup when prev CPU has been idle`**：Vincent 确认（回应 K Prateek 上一轮追问）——需要在 `DEQUEUE_SLEEP` 或 `DEQUEUE_CLASS` 时更新 `idle_seq`（补齐换类离开 fair 导致 rq 变 idle 的覆盖）。

## 版本演进与当前进展

*current_version: v3（2026-11-06，`<20261106151947.3991524-1-vincent.guittot@linaro.org>`）*。仍为 v3 评审收口，08/20 的数据结构（RB-tree vs 专用 pushable list）与 02/20 的 idle_seq 更新预计在 v4 落地，尚未发 v4。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（sched 维护者）**：进一步收敛 08/20——`cfs_tasks` 即 pushable 列表，作者的额外语义（一次 push 后 drop）值得商榷；提出 RB-tree / augmented list 两种更干净的数据结构，把「选对任务」放进排序而非「修剪列表长度」。
- **Vincent Guittot（作者/fair 维护者）**：接受可用 RB 树，解释复用 pushable_tasks 只因它 exclusive；强调要选「meaningful 而非随机」的任务（某些场景想 push 多个，如 patch 20），并说明 push 主场景是周期性为回 runnable 列表的任务找 CPU。
- 无 NAK。分歧从「要不要限界」演进到「用哪种数据结构承载 push 候选排序」的实现取舍。

## 合入评估

*likelihood=medium*。作者是 fair 维护者、系列方向无异议，但 08/20 的数据结构方案（RB-tree vs 专用列表）尚未落定，需作者在 v4 体现 Peter 的建议。*blocking_issues*：08/20 的 push 候选数据结构取舍待落定；02/20 的 idle_seq 更新待入 v4。*next_action*：Vincent 按 Peter 建议改 08/20（RB-tree/augmented list 或论证专用列表）、把 02/20 的 idle_seq 更新并入，发 v4。

## 效果评估

无今日新增数据。系列此前数据（承接 20261106-002）：dragonboard rb5 上 4 短任务同时醒来平均延迟约 1051us→61us，hackbench pipe +15-25%。

## 我可以参与的点

- **review**：评估 RB-tree（`{slice, exec_start}` 排序）与 augmented list 哪个更契合「周期性为回 runnable 列表任务找 CPU + patch 20 多短任务堆叠」的场景，以及它能否天然取代「一次 push 后 drop」的额外语义。
- **testing**：在大量短 slice 任务同时唤醒的压力场景验证 08/20 下一版（RB-tree 化）的 push 疏散效果与遍历成本。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261106151947.3991524-1-vincent.guittot@linaro.org/
- Peter 的 RB-tree 提议: https://lore.kernel.org/all/20261112121933.GW1813469@noisy.programming.kicks-ass.net/
- Vincent 对 meaningful 任务的解释: https://lore.kernel.org/all/CAKfTPtBfQd5nD9jNdayGbEW_P2bDMvOm=GZ3Q-gu+O6KkQmKbA@mail.gmail.com/

---
id: sched-20261112-015
date: '2026-11-12'
subject: "sched/fair: Add push task mechanism for fair"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261106151947.3991524-1-vincent.guittot@linaro.org>"
lore_url: "https://lore.kernel.org/all/20261106151947.3991524-1-vincent.guittot@linaro.org/"
authors: [Vincent Guittot]
maintainers_involved: [Peter Zijlstra]
current_version: v3
patch_series:
  - version: v3
    msgid: "<20261106151947.3991524-1-vincent.guittot@linaro.org>"
    date: '2026-11-06'
    summary: "20 补丁改进短 slice 任务延迟：正 lag 衰减、选 CPU 考虑 slice、fair push 回调"
    review_outcome: "Peter 提议 RB-tree/augmented list 承载 push 排序；02/20 idle_seq 更新确认；待 v4"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["08/20 的 push 候选数据结构取舍待落定", "02/20 idle_seq 更新待入 v4"]
  next_action: "Vincent 按 Peter 建议改 08/20、并入 02/20 的 idle_seq 更新后发 v4"
contribution_opportunities:
  - kind: review
    description: "评估 RB-tree vs augmented list 对 push 场景的契合度"
  - kind: testing
    description: "大量短 slice 任务同时唤醒压力下验证 08/20 下一版的疏散效果与成本"
generated_at: "2026-11-13T09:00:00+08:00"
source_email_count: 8
related_articles: [sched-20261106-002, sched-20261107-004, sched-20261109-002, sched-20261110-010, sched-20261111-009]
tags: [eevdf, cfs]
---