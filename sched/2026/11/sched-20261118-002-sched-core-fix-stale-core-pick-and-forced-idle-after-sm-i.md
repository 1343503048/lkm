# sched/core: Fix stale core_pick and forced idle after SM_IDLE fast path

## TL;DR

Ibrahim Elshahed（Amazon）发两补丁系列修复 core scheduling 的 SM_IDLE fast path 问题：当 idle 任务经 fast path 重新入队/被选中后，`rq->core_pick` 与 forced-idle 状态可能残留过期值，导致 core-wide 选择误判。Peter Zijlstra 评审时质疑 patch 2 的 `rq->core_pick` 条件冗余（`!rq->nr_running` 已蕴含无 core_pick），并建议把系列补进自测。刚发出，尚未收敛。

## 背景与问题

core scheduling（SMT 隔离）下，core-wide 的 pick 流程有一个 SM_IDLE fast path：当 CPU 进入 idle 后再次调度时，走快路径直接取 idle，绕过了完整的 core-wide pick 逻辑。作者发现该 fast path 之后 `rq->core_pick`（core 层选择结果）与 forced-idle 相关的记账没有正确复位，可能把过期状态带入下一次 core-wide 选择，破坏 SMT sibling 间的隔离/选择正确性。属 core scheduling 正确性缺陷。

## 技术方案

两补丁（作者 2026-11-17 发出，今日缓存仅含 Peter 的回复，补丁正文未在当日缓存）：

- patch 1/2：修复 SM_IDLE fast path 之后残留的 `core_pick` 状态。
- patch 2/2 `Don't skip a pending core-wide pick on idle re-entry`：避免 idle 重新入队时跳过待处理的 core-wide pick。

Peter 对 patch 2 指出：`rq->core_pick` 条件疑似冗余——既然已有 `!rq->nr_running` 判断，而 `core_pick` 存在时 `nr_running` 必然非零，两个条件重叠，逻辑上可简化。

## 版本演进与当前进展

*current_version: v1（2026-11-17 发出，`<20261117142704.6878-1-lshahed@amazon.de>`，2 补丁）*。今日为评审日：Peter 对 0/2 问「是否值得塞进 selftests」，对 2/2 质疑条件冗余。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（sched maintainer）**：对 2/2 的 `rq->core_pick` 条件提出疑问——`!rq->nr_running` 已存在时，`rq->core_pick` 必然为空，条件重叠；建议把系列补进 selftests 以固化回归测试。
- 无 NAK；属澄清性/结构性意见，尚未涉及方案否定。

## 合入评估

*likelihood=medium*。core scheduling 由 Peter 直接评审、方向（修 fast path 状态残留）明确，但补丁逻辑有待作者回应条件冗余的质疑，且补丁正文未被当日缓存、无法核实细节。*blocking_issues*：① patch 2 的 `rq->core_pick` 条件需作者澄清或简化；② 建议补 selftests。*next_action*：作者回应 Peter 的条件质疑并考虑补自测。

## 效果评估

无性能数据；属 core scheduling 正确性修复，作者未在当日缓存披露复现数据（补丁正文不在此前拉取窗口）。

## 我可以参与的点

- **review**：核对 patch 2 `!rq->nr_running` 与 `rq->core_pick` 条件是否确实冗余，以及 fast path 之后还有哪些 core-sched 字段可能残留过期值。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261117142704.6878-1-lshahed@amazon.de/
- Peter 对 2/2 的评审: https://lore.kernel.org/all/20261118144027.GZ1779021@noisy.programming.kicks-ass.net/

---
id: sched-20261118-002
date: '2026-11-18'
subject: "sched/core: Fix stale core_pick and forced idle after SM_IDLE fast path"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261117142704.6878-1-lshahed@amazon.de>"
lore_url: "https://lore.kernel.org/all/20261117142704.6878-1-lshahed@amazon.de/"
authors: [Ibrahim Elshahed]
maintainers_involved: [Peter Zijlstra]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261117142704.6878-1-lshahed@amazon.de>"
    date: '2026-11-17'
    summary: "两补丁修 SM_IDLE fast path 后的 core_pick/forced-idle 状态残留"
    review_outcome: "Peter 质疑 patch 2 条件冗余，建议补 selftests"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["patch 2 的 rq->core_pick 条件冗余待澄清", "建议补 selftests"]
  next_action: "作者回应 Peter 的条件质疑并考虑补自测"
contribution_opportunities:
  - kind: review
    description: "核对 !rq->nr_running 与 rq->core_pick 条件的冗余性，排查其它残留状态字段"
generated_at: "2026-11-19T09:00:00+08:00"
source_email_count: 2
related_articles: []
tags: [core_sched, hyperthreading]
---
