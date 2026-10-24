# sched_ext: Fix bypassed sub-scheduler tasks stalling when the host lacks caps

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261023-008（v2）：Tejun Heo 发往 sched_ext/for-7.4 的 bypass stall 修复系列（当日 v1→v2，15 patches）：bypassing 子调度器任务走 host 的 per-cpu bypass DSQ，而某 CPU 的 dispatch 只在 host 持有 `SCX_CAP_BASE` 时才下钻，此前 bypass 放置与 bypass 负载均衡忽略这点，导致任务被排到「host 无 BASE」的 CPU 上卡死或循环。修复把 `SCX_CAP_BASE` 定为唯一 cap、让 rescue 与 bypass 负载均衡 cap 感知。v2 按 sashiko review 修订。
- sched-20261024-002（今天，v3）：扩到 17 patches + 3 个跟进补丁（18/17、19/17、20/17），全部 `Reported-by: Sashiko`。v3 新增「bypass 先于 reenqueue 计数测试」「rescue served time 从 charged runtime 计」等，并修正 host 失 BASE 时 migration-disabled 任务的放置。仍无外部 reviewer 上线，属高确信合入。

## 背景与问题
（承接 v2）sched_ext 子调度器可 bypass 到 host 运行：bypassing 调度器的任务走 host 的 per-cpu bypass DSQ；caps 是 per-CPU 授予的，某 CPU 的 dispatch 只对持有 `SCX_CAP_BASE` 的调度器下钻，因此在「host 无 BASE」的 CPU 上 bypass DSQ 永远不会被消费。此前 bypass 放置与 bypass 负载均衡忽略这点：任务可能被排到或搬到这样的 CPU 上原地卡住；「host 有 BASE 无 ENQ」时任务在其 bypass DSQ 与 reject drain 间循环。被 bypass 任务更依赖 rescue slice 运行，放大了 rescue 路径既有缺陷（CPU 带 runnable rescuee 空转、kernel slice 写入把 grant 一个 tick 一个 tick 喂给 rescue、调度器可把 grant 扩展到超带宽）。今日无新背景，为 v3 收口。

## 技术方案
（承接 v2 + 今日 v3）v3 共 17 patches（`kernel/sched/ext/*` + tools autogen）。相对 v3 的关键改动：

- **0003**：在 `scx_do_enqueue_task()` 里先把 bypass 测试提到 reenqueue 计数之前——bypassing 调度器的 reenqueue 是 kernel 的 placement，计数它会 stranded 一个 bypassed 任务并 deadlock disable（sashiko）。
- **0006**：rescue served time 改为从 charged runtime 计。在 proxy execution 下 rescuee 的 `sum_exec_runtime` 跟随 mutex owner 而 slice 跟随 donor，二者双向不一致；`scx_rescue_keep()` 现在在 restore 被拒时 WARN 并结束 rescue（sashiko）。
- **0013**：rescue 被禁用时，把 migration-disabled / migration-pending 任务接纳到 host 失 BASE 的 CPU 的 local DSQ，而不是留在不消费的 bypass DSQ 上。
- **描述修订**：#4/#7/#9/#10/#11/#16/#17 的 rescue-off 与 zero-interval 场景描述更新。

三个跟进补丁（`Reported-by: Sashiko`）：**18/17** 修 NONE rescuee 离开 sched_ext 的 use-after-free（`switched_from_scx()` 对 NONE 任务 `scx_task_slice_ended()` 结束 slice，避免 `rq->scx.rescue.curr` 悬垂）；**19/17** 修 stall watchdog 把 stuck 任务怪到正在退出的 bypassing owner 上（`Fixes: 2c91169377f4`，改为怪 host）；**20/17** 修 lone IMMED 任务在 kept prev 之后等待（`Fixes: 98d709cba319`，dispatch 保 prev 且 local DSQ 有 IMMED 任务时调度 reenqueue）。

## 版本演进与当前进展
*current_version: v3*。v1（`<20261022213836.2259069-1-tj@kernel.org>`，14 patches，10-22）→ v2（`<20261023052452.2889061-1-tj@kernel.org>`，15 patches，10-23）→ v3（`<20261023175608.4120910-1-tj@kernel.org>`，17 patches，10-24）。v3 之后 Tejun 又补发 18/17、19/17、20/17 三个跟进（均 sashiko 报告的问题）。基于 sched_ext/for-7.4（`1f5dde349ac2`）。

## Maintainer 意见与讨论焦点
sashiko（bot，系列内以 `#3/#6/#13` 等引用）在 v2 上继续报告：rescue served time 与 slice 在 proxy execution 下不一致、bypass reenqueue 计数会 stranded 任务并 deadlock disable、host 失 BASE 时 migration-disabled 任务的放置等。v3 全部落实，并补三个新报告（NONE rescuee UAF、watchdog 误责、lone IMMED 等待）。Tejun Heo 为 sched_ext 维护者，系列在其自有树迭代；当日缓存内仍未见到 Tejun 之外的外部 reviewer 上线表态。

## 合入评估
*likelihood=high*。属 sched_ext/for-7.4 维护者自有树的正向修复，v3 已回应 sashiko 全部意见、带 model check 与多层压力测试；sched_ext 树由 Tejun 直管，此类修复通常随之进下一窗口。*blocking_issues*：当日缓存未见第二 reviewer 确认。*next_action*：等 Tejun 定稿合入 for-7.4。

## 效果评估
无量化性能数据。作者描述了功能级验证：三层层级循环 bypass 下 pinned spinner、fork / context-switch 风暴、queued 任务下撤销 caps；bypass 负载均衡的 remote move 与 drain 均被 exercised；holding_cpu 握手、cap 撤销放置、rescue keep 做了小 CPU 数的 model check。目标是消除 stall，未提供吞吐/延迟对比数字。

## 我可以参与的点
- *kind: testing*：在多层子调度器 + 快速 cap 授予/撤销的真实 sched_ext 负载上回归，重点验证「host 失 BASE 时 bypass DSQ 排空」「host 有 BASE 无 ENQ」两条路径不再 stall，以及 v3 新增的 18/17（NONE rescuee 退出）不再 UAF。
- *kind: review*：复核 v3 新增 0006（rescue served time 从 charged runtime 计）与 0003（bypass 先于 reenqueue 计数）对 slice/救援记账不变量的一致性。

## 参考链接
- v3 cover: https://lore.kernel.org/all/20261023175608.4120910-1-tj@kernel.org/
- v2 cover: https://lore.kernel.org/all/20261023052452.2889061-1-tj@kernel.org/
- 前文: sched-20261023-008

---
id: sched-20261024-002
date: 2026-10-24
subject: 'sched_ext: Fix bypassed sub-scheduler tasks stalling when the host lacks caps'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20261023175608.4120910-1-tj@kernel.org>'
lore_url: 'https://lore.kernel.org/all/20261023175608.4120910-1-tj@kernel.org/'
authors:
  - 'Tejun Heo'
maintainers_involved:
  - 'Tejun Heo'
current_version: v3
patch_series:
  - version: v1
    msgid: '<20261022213836.2259069-1-tj@kernel.org>'
    date: 2026-10-22
    summary: '14 patches：SCX_CAP_BASE 定为 bypass 唯一 cap，rescue slice 修复 + cap 感知 bypass 负载均衡'
    review_outcome: 'sashiko 提出 keep 测试/注释/refusal 清单需修'
  - version: v2
    msgid: '<20261023052452.2889061-1-tj@kernel.org>'
    date: 2026-10-23
    summary: '15 patches：新增 expire prev slice、补 keep-last 注释、订正 refusal 原因'
    review_outcome: '回应 sashiko 意见'
  - version: v3
    msgid: '<20261023175608.4120910-1-tj@kernel.org>'
    date: 2026-10-24
    summary: '17 patches + 18/17~20/17：bypass 先于 reenqueue 计数、rescue served time 从 charged runtime 计、失 BASE 时接纳 migration 任务；修 NONE rescuee UAF/watchdog 误责/lone IMMED'
    review_outcome: '回应 sashiko 三组新报告；未见第二 reviewer'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - '当日缓存未见第二 reviewer 确认'
  next_action: '等 Tejun 定稿合入 for-7.4'
contribution_opportunities:
  - kind: testing
    description: '多层子调度器 + 快速 cap 撤销场景回归，验证两条 stall 路径与 NONE rescuee 退出无 UAF'
  - kind: review
    description: '复核 0006 charged-runtime 救援记账与 0003 bypass 先于计数的不变量一致性'
generated_at: '2026-10-25T01:00:00'
source_email_count: 21
related_articles:
  - sched-20261023-008
tags:
  - sched_ext
---