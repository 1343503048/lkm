# sched: core-sched fixes and balancing

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261107-001：Peter Zijlstra 的 v2 系列（12 补丁）发出，核心是 rq_clock/rq_lock 语义整体重做——cover 明说「主差异是 rq_clock 的重做，因为 TJ（Tejun Heo）指出上一版把它彻底搞错了」。新增 `rq_drop_lock()`、分解 `update_rq_clock()`、引入 `RQCF_NOP_MASK` 让已 UPDATED 的 rq 跳过重复更新，取代 v1 靠 `core_clock_updated` 布尔量猜时钟的绕路逻辑。
- sched-20261108-005：Kayra Cizmeci 评审 patch 02/12（`Introduce rq_drop_lock()`）并给 Reviewed-by（仅一处拼写 nit）。
- sched-20261109-007：Kayra 评审 patch 05/12（`Abstract/fix rq_clock_start_loop_update()`）并发现类型 bug——`rq_clock_freeze()` 返回 `unsigned int` 而 `rq_clock_thaw()` 形参是 `bool`，导致 `flags & RQCF_FREEZE` 恒 false；`double_rq_clock_clear_update()` 会误清 RQCF_FREEZE。
- sched-20261111-005（今天）：**Tejun Heo 密集评审并发现多个 bug**——01/12 的 RETRY_TASK 对 sched_ext 不成立、core_cookie 快速路径在 SMT>2 上可 oops；04/12「清 UPDATED 位」被 raw lock 持有者继承导致 clock 静默跳过；12/12 移掉 `sched_class::balance()` 后暴露出 DL `rq->next_class` 未被 dl_server 路径提升的问题。Peter 逐条采纳并现场给 01/12、12/12 的修复 diff，但 Kayra 又指出 12/12 的修复让「waking DL 任务在 FAIR 任务运行时不抢占」——`wakeup_preempt_dl()` 因 `next_class` 被提前置成 DL 而直接早退。Peter 承认「这行不通，我再试」；Tejun 在 cover 层面提出把 clock 状态机简化成「跳过下一跳 bit + per-rq 深度计数」两点，Peter 表示「让我按这个方向玩一玩」。

## 背景与问题

（承接 sched-20261107-001 / 20261108-005 / 20261109-007）Peter 处理 core scheduling 三类问题的 v2 系列（12 补丁）：`pick_next_task()` 自重入、core-sched 下 newidle balance 被整条关掉、`sched_class::balance()` 与 `pick_task()` 职责重叠。v2 的核心变化是 rq_clock/rq_lock 语义整体重做（Tejun 指出 v1 的 rq_clock 方向错了）。今日评审进入深水区：clock 状态机的生命周期（谁清 UPDATED、freeze/drop 期间能否保时钟不动）和 balance() 移除后 DL 侧 `rq->next_class` 的维护责任。

## 技术方案

今日为评审密集期，Peter 现场给出两处修复 diff：

- **01/12 `Fix pick_next_task() self recursion`**：Tejun 指出两处问题——(a) 当 `ops.dispatch()` 只往远端 CPU 的 local DSQ 塞任务（本核无 enqueue/dequeue）时 sched_ext 返回 RETRY_TASK，`WARN_ON_ONCE(p == RETRY_TASK)` 会误报；(b) 快速路径看 `core_cookie == 0` 判定「未 commit」，但 3+ sibling（如 POWER/SMT4）上仍可能有 in-flight 的 core 选择，10/12 使 `pick_task_fair()` 在 newidle 掉锁却不返回 RETRY_TASK 后，可在 SMT4 VM 上于 `__schedule()` 可靠 oops。Peter 采纳：改判 `seq != rq->core->core_task_seq`、去掉 WARN（「Nice find，我一直觉得这个判断跟下面不一致」）。
- **04/12 `Make __update_rq_clock() skip updates on UPDATED`**：Tejun 指出 `RQCF_UPDATED` 只被 `rq_pin_lock()`/`double_rq_clock_clear_update()` 清，`raw_spin_rq_lock()` 的持有者会继承上一持有者的位、`update_rq_clock()` 被静默跳过；追问「你之前说 unlock 时清，为何不这么做」。Peter 解释：对 core-sched 单靠「unlock 时清」不够——SMT0/SMT1 交错会乱掉，patch 6 里就有这幅图（clear-on-unlock 在 patch 6 里是注释状态的）。
- **12/12 `Remove sched_class::balance()`**：Tejun 指出移除后暴露 DL 侧底层问题——`rq->next_class` 只被 `wakeup_preempt()` 提升，但 `dl_server_start()`/`dl_task_timer()`/`dl_server_timer()` 直接 `resched_curr()` 不经过它，`pick_task_dl()` 返回 NULL 后 `balance_rt()` 掉锁期间入队的 DL entity 无人注意。Peter 给出 fix：`enqueue_dl_entity()` 成功时置 `rq->next_class = &dl_sched_class`，并注明「类似的论点也适用于 FAIR vs EXT」。但 Kayra 反驳：正常 wakeup 路径里 `enqueue_dl_entity()` 早把 `next_class` 置成 DL，`wakeup_preempt()` 见 `p->sched_class == next_class` 就调 `wakeup_preempt_dl()`，而它直接早退——于是 FAIR 任务继续跑、新唤醒的 DL 任务干等。Kayra 实测 latency：hackery 12us→200ms、idle 12us→3s。Peter 承认「你说得对，这行不通，我再试」。

此外 K Prateek Nayak 在 05/12 上用 `coresched + perf bench sched messaging` 复现 `!(rq->clock_update_flags & RQCF_UPDATED)` 告警，给出把 `double_rq_clock_clear_update()` 换成 `__rq_clock_clear()` 的验证 diff；Tejun 在 cover（00/12）提出彻底简化：clock 只需两点——「下次更新视为已更新」的 1 bit（`__schedule()` 末尾清掉）+「rq-锁掉锁段内时钟冻结」的 per-rq 深度计数（pin/unpin 增减、drop/repin 不动），去掉 save/restore 语义。

## 版本演进与当前进展

*current_version: v2（2026-11-07，`<20261107115913.261163891@infradead.org>`）*。仍在 v2 上以「现场 diff + 讨论」的方式迭代，尚未发 v3——Tejun 已提议把 clock 状态机整体简化为两点，Peter 明确「Yeah, let me play around with all that」，v3 预计会按此重构。

## Maintainer 意见与讨论焦点

- **Tejun Heo（sched_ext 维护者）**：本轮最密集评审，逐 patch 挑出 sched_ext 与 SMT>2 的边角问题，并在 cover 层面质疑 clock 管理「too subtle」（Kayra 也早已点出 save/restore 在处理跨锁段时行不通），给出两点简化模型。
- **Peter Zijlstra（sched 维护者/作者）**：对 Tejun 的意见整体采纳，现场给 fix diff，但对 04/12「clear on unlock」坚持「core-sched 下不够」的既有结论。
- **Kayra Cizmeci**：在 Peter 的 12/12 fix 上再发现致命缺陷（DL 抢占失效），配了 12us→200ms/3s 的实测数据。
- **K Prateek Nayak**：05/12 复现 clock 告警，给出验证 diff。
- 无 NAK，但 12/12 的 fix 目前是坏的、clock 状态机面临重构，系列仍需一轮 v3。

## 合入评估

*likelihood=medium*。作者与维护者协作密切、方向一致，但今日暴露出 12/12 修复包含一个会破坏 DL 抢占的反直觉 bug，且 Tejun 建议对 clock 状态机做减法重构，v3 前不具合入条件。*blocking_issues*：12/12 的 `next_class` 置位时机错误（Kayra 已实测）；clock 状态机是否需要按 Tejun 两点模型重做。*next_action*：Peter 按两点模型重构 clock 管理、修正 `enqueue_dl_entity` 置 `next_class` 的时机（放在 `wakeup_preempt()` 之后或改判定），出 v3。

## 效果评估

Kayra 给出 12/12 缺陷实测：hackery 场景 DL 唤醒延迟 12us→200ms、idle 场景 12us→3s（bug 引发，非收益）。Tejun 描述 01/12 的 core_cookie 竞态可「在 SMT4 VM 上于 `__schedule()` 可靠 oops」。均为正确性证据，无性能收益数据。

## 我可以参与的点

- **testing**：在 SMT>2（如 POWER、SMT4 x86）和带 BPF 调度器的环境上对 v3 跑 `coresched` + sched 压力，重点验证 Tejun 描述的 core_cookie 竞态与 DL 抢占是否回归。
- **review**：复核 Tejun「两点 clock 模型」与 Peter 现有 `rq_{pin,drop,repin,unpin}_lock()` 语义的映射是否完备（尤其 `double_rq_clock_clear_update()` 是否可安全删除）。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261107115913.261163891@infradead.org/
- Tejun 对 00/12 的 clock 简化建议: https://lore.kernel.org/all/3461bfecf6bc383facc218d56863d6c4@kernel.org/
- Kayra 对 12/12 的反驳: https://lore.kernel.org/all/avRzGYNT-_p3KP9R@scheduler.schedules/

---
id: sched-20261111-005
date: '2026-11-11'
subject: "sched: core-sched fixes and balancing"
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: "<20261107115913.261163891@infradead.org>"
lore_url: "https://lore.kernel.org/all/20261107115913.261163891@infradead.org/"
authors: [Peter Zijlstra]
maintainers_involved: [Peter Zijlstra, Tejun Heo]
current_version: v2
patch_series:
  - version: v2
    msgid: "<20261107115913.261163891@infradead.org>"
    date: '2026-11-07'
    summary: "整体重做 rq_clock/rq_lock 语义；修 pick_next_task 自重入与 core-sched balance"
    review_outcome: "Tejun 发现 sched_ext/SMT>2 多个 bug，提议两点 clock 模型；Kayra 发现 12/12 的 DL 抢占缺陷"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["12/12 的 next_class 置位时机错误（Kayra 实测 DL 抢占失效）", "clock 状态机可能需按 Tejun 两点模型重构"]
  next_action: "Peter 按两点模型重构 clock 并修正 enqueue_dl_entity 置 next_class 的时机后发 v3"
contribution_opportunities:
  - kind: testing
    description: "在 SMT>2 与 BPF 调度器环境上验证 core_cookie 竞态与 DL 抢占回归"
  - kind: review
    description: "复核两点 clock 模型与 pin/drop/repin/unpin 语义映射、double_rq_clock_clear_update 可否删除"
generated_at: "2026-11-12T09:00:00+08:00"
source_email_count: 18
related_articles: [sched-20261107-001, sched-20261108-005, sched-20261109-007]
tags: [core_sched, cfs, deadline, rt]
---