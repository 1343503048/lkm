# Improving latency of short slice tasks

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261106-002：Vincent Guittot（sched/fair 维护者）的 v3 大系列（20 补丁）改进短 slice 任务调度延迟：正 lag 衰减、选 CPU 考虑 slice、fair 类新增 push 回调、让 feec() 按 cost+slice 选 CPU、修复多任务同时醒来堆叠同一 idle CPU。dragonboard rb5 上 4 短任务同时醒来平均延迟约 1051us→61us，hackbench pipe +15-25%；cyclictest 99.9 分位略回退。
- sched-20261107-004：Kayra Cizmeci 密集评审 patch 02–06/20，对 03/04/05 给 Reviewed-by，对 02 提 WRITE_ONCE 配对、对 06 提「排除有 RT 任务在跑的 CPU」实质担忧。
- sched-20261109-002（今天）：**Peter Zijlstra 亲自评审**——对 08/20（push task 机制）质疑「为何要新增列表与 plist，rq->cfs_tasks 本身就是 MRU 序」，建议用 `list_for_each_entry_reserve` 复用；对 02/20 判定「无 WRITE_ONCE 逻辑上可行但 KCSAN 会告警」；对 06/20 指出 `READ_ONCE` 应为 `rcu_dereference_all()` 且只选最早一个 slice_cpu 的语义问题。Vincent 逐条回应。

## 背景与问题

（承接 sched-20261106-002 / 20261107-004）短 slice 任务的调度延迟痛点：EEVDF 下短任务因 slice 很短、lag 反复累积，常排不上队；多任务同时醒来会堆叠到同一 idle CPU 而非分散。Vincent 的 v3 20 补丁系列用「正 lag 衰减 + 选 CPU 时考虑 slice + fair 类 push 回调」整体解决，并修复 feec()/EAS 的选核逻辑。今日进入 Peter Zijlstra（sched maintainer）的评审阶段。

## 技术方案

今日评审聚焦三个补丁的设计取舍：

- **08/20 `Add push task mechanism for fair`**：作者为 fair 类新增 push 回调与专门的列表/plist 供 push 遍历。Peter 质疑：与其加新列表，不如在 `rq->cfs_tasks` 上加 `p->nr_cpus_allowed > 1` 条件复用（该列表本就用于迁移，排除 pinned 任务合理）；且 `rq->cfs_tasks` 已由 `set_next_task_fair()` 维护为 MRU 序（current 移到队首），用 `list_for_each_entry_reserve` 跳过 blocked/current 即可得到「最久未运行的任务优先被 push」的语义，无需 plist。
- **02/20 `Reset lag at wakeup when prev CPU has been idle`**：Peter 判定无 `WRITE_ONCE` 时编译器按字节乱序写也无害（因为只做相等比较，任何中间态都不等于任一先前快照），但要么补文档说明、要么直接 `WRITE_ONCE` 让 KCSAN 闭嘴。Vincent 回应：他评估后认为不严格必要，因为 `READ_ONCE` 只用于比较相等、不参与计算。
- **06/20 `Add min slice check when selecting CPU`**：Peter 指出应改用 `rcu_dereference_all()` 而非 `READ_ONCE`；并指出实现只选「第一个」slice_cpu（最早而非最新），而最新一个可能更好（还没变 stale）。Kayra 追问是否每找到一个就覆盖 slice_cpu；Vincent 回应「patch 20 会处理多任务选同一 CPU 的情形」。
- **05/20 `Add per cpu cached min_slice`**：Vincent 自纠——`rq->min_slice = 0` 的初始化本应属于本补丁，误并入 patch 6。

## 版本演进与当前进展

*current_version: v3（2026-11-06 发出，20 补丁）*。今日为评审日，无新版本：Peter 对 02/06/08 给出设计级意见，Vincent 逐条回应（02 坚持不必要 WRITE_ONCE 但接受补文档、05 自纠补丁归属、06 交 patch 20 兜底）。Kayra 的 06 疑问得到解答。预期作者据此出 v4。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**：对 08/20 的 push 机制提出结构性异议——主张复用 `rq->cfs_tasks`（加 `nr_cpus_allowed > 1` 条件）而非新增列表与 plist，这是对方案复杂度的实质质疑，作者需回应或改设计。
- **Vincent Guittot（作者，sched/fair 维护者）**：对 02/20 坚持「WRITE_ONCE 非严格必要」的判断，对 05/20 承认补丁归属笔误，对 06/20 以 patch 20 兜底回应。
- 分歧集中在 08/20 的 push 实现方式，尚未达成一致。

## 合入评估

*likelihood=medium*。系列被维护者（Peter）积极评审且作者是本子系统维护者，但 08/20 的实现方式（新列表 vs 复用 cfs_tasks）尚需作者回应/改版，02/20 的 KCSAN 隐患需文档或 WRITE_ONCE 收尾。*blocking_issues*：① 08/20 push 机制实现方式未定；② 02/20 需处理 KCSAN 告警风险；③ 06/20 的 `rcu_dereference_all` 与 slice_cpu 覆盖语义待改。*next_action*：作者回应 Peter 的 08/20 质疑并出 v4。

## 效果评估

今日无新增性能数据。既有数据（20261106-002）：dragonboard rb5 上 4 短任务同时醒来平均延迟约 1051us→61us，hackbench pipe +15-25%，cyclictest 99.9 分位略回退（正 lag 衰减所致，作者已知）。

## 我可以参与的点

- **review**：就 08/20 push 机制「复用 rq->cfs_tasks 还是新列表」给出自己的实现/复杂度判断（Peter 提出、尚未定论）。
- **testing**：在含 RT 任务的混合负载下验证 06/20 min slice 选 CPU 是否误选「有 RT 任务在跑」的 CPU（Kayra 此前的实质担忧，今日未见直接回应数据）。

## 参考链接

- Peter 对 08/20 的评审: https://lore.kernel.org/all/20261109155418.GL1779021@noisy.programming.kicks-ass.net/
- Peter 对 02/20 的评审: https://lore.kernel.org/all/20261109154536.GK1779021@noisy.programming.kicks-ass.net/

---
id: sched-20261109-002
date: '2026-11-09'
subject: "Improving latency of short slice tasks"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261109155418.GL1779021@noisy.programming.kicks-ass.net>"
lore_url: "https://lore.kernel.org/all/20261109155418.GL1779021@noisy.programming.kicks-ass.net/"
authors: [Vincent Guittot]
maintainers_involved: [Peter Zijlstra]
current_version: v3
patch_series:
  - version: v3
    msgid: "<20261106151947.3991524-9-vincent.guittot@linaro.org>"
    date: '2026-11-06'
    summary: "20 补丁：正 lag 衰减、选 CPU 考虑 slice、fair 类 push 回调、feec() 按 cost+slice 选 CPU、修复多任务堆叠"
    review_outcome: "Peter 评审 02/06/08，对 push 实现方式提结构性异议；Kayra 密集评审 02-06"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "08/20 push 机制实现方式（新列表 vs 复用 rq->cfs_tasks）未定"
    - "02/20 需处理 KCSAN 告警风险"
  next_action: "作者回应 Peter 的 08/20 质疑并出 v4"
contribution_opportunities:
  - kind: review
    description: "就 08/20 push 机制复用 rq->cfs_tasks 还是新列表给出判断"
  - kind: testing
    description: "在含 RT 任务的混合负载下验证 06/20 是否误选有 RT 任务在跑的 CPU"
generated_at: "2026-11-10T09:00:00+08:00"
source_email_count: 9
related_articles: [sched-20261106-002, sched-20261107-004]
tags: [eevdf, load_balance, cfs]
---
