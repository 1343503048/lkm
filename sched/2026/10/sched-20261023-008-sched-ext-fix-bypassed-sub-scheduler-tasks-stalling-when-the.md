# sched_ext: Fix bypassed sub-scheduler tasks stalling when the host lacks caps

## TL;DR
Tejun Heo 发往 sched_ext/for-7.4 的大型修复系列，当日连发 v1（14 patches）与 v2（15 patches）：一个 bypassing 子调度器的任务经其 host（最近的非 bypassing 祖先）的 per-cpu bypass DSQ 运行，而 caps 是 per-cpu 的、某 CPU 的 dispatch 只在 host 持有 `SCX_CAP_BASE` 时才会下钻到该调度器——bypass 放置与 bypass 负载均衡此前忽略这一点，导致 bypassed 任务可能被排队或搬到「host 无 BASE」的 CPU 上坐等（乃至 host 有 BASE 但无 ENQ 时在 bypass DSQ 与 reject drain 之间无限循环）。修复把 `SCX_CAP_BASE` 定为 bypassed 任务所需唯一 cap、并让受援（rescue）路径与 bypass 负载均衡都变得 cap 感知。v2 按 sashiko 的 review 修订。系列在 Tejun 自有树上，无外部 review 意见回流前属高确信合入。

## 背景与问题
sched_ext 的子调度器（sub-scheduler）可 bypass 到 host 运行：bypassing 调度器的任务走 host 的 per-cpu bypass DSQ。caps 是 per-CPU 授予的，某 CPU 的 dispatch 只对持有 `SCX_CAP_BASE` 的调度器下钻，因此在「host 无 BASE」的 CPU 上、某个 bypass DSQ 永远不会被消费。此前的 bypass 放置与 bypass 负载均衡未意识到这点，后果：bypassed 任务可能被排到或被搬到这样的 CPU 上原地卡住，直到 host 重新获得 cap 或 bypass 窗口结束；而「host 有 BASE 但无 ENQ」时，bypassed 任务会在其 bypass DSQ 与 reject drain 之间来回循环而非运行。同时，被 bypass 任务更依赖 rescue slice 运行，放大了 rescue 路径的既有缺陷（CPU 可能带着 runnable rescuee 空转、kernel 自己的 slice 写入在 bypass 下把 grant 一个 tick 一个 tick 地喂给 rescue、调度器可把 grant 扩展到超过 rescue 带宽）。

## 技术方案
v2 共 15 patches（`kernel/sched/ext/*` + tools autogen，8 files +489/-190），按 cover 的分组：

- **0001-0002 准备**：把 `scx_ent_flags` 的多 bit 字段打包到顶部使单 bit 标志连续；在 claim 被确认处清 `holding_cpu`。
- **0003**：用 `SCX_ENQ_IMMED` 消费 bypass DSQ，使「有 BASE 无 ENQ」的 host 直接运行其 bypassed 任务而非循环。
- **0004-0008 修 rescue slice**：ops.stopping() 后恢复余量、避免 CPU 带着 runnable rescuee 空转、把 grant 标记为 kernel-owned slice（kernel 的 slice 写入不碰它、调度器只能缩短不能延长）。
- **0009**：put_prev_task_scx() 把任务排到 local DSQ 后（plain insert 路径）也重新调度该 CPU。
- **0010**：在 dispatch_one() 里对 bypassing prev 的 slice 于 keep 测试前做过期处理，从而 bypassed rescuee 能在其 kernel slice 上保住 CPU、post-dispatch 测试不会再保住被拒绝的 prev。
- **0011**：host 在其 CPU 上无 BASE 时把 bypassed 任务送 rescue。
- **0012-0015 使 bypass 负载均衡 cap 感知**：capacity/donee 只来自 BASE CPU、抽出「donor DSQ 未持锁插入」的 `bypass_lb_move()`、可搬 home 在其他 CPU 的任务、以及在 host 于某 CPU 失去 BASE 时把该 CPU 的 bypass DSQ 排空到仍能运行的 CPU 或送回重放。

v2 相对 v1 的改动（回应 sashiko）：新增 patch 0010（expire prev slice，替代原 bypass 测试）、补充 patch 0006 的 keep-last 注释与描述、订正 patch 0011/0015 的 refusal 原因列表。测试覆盖三层层级循环 bypass + pinned spinner、fork 与 context-switch 风暴、queued 任务下撤销 caps，并对 holding_cpu 握手、cap 撤销放置、rescue keep 做了小 CPU 数的 model check。基于 sched_ext/for-7.4（`1f5dde349ac2`），分支 `bypass-caps-v2`。

## 版本演进与当前进展
*current_version: v2*。v1（`<20261022213836.2259069-1-tj@kernel.org>`，14 patches）当日深夜发出后，sashiko 给了 review；v2（`<20261023052452.2889061-1-tj@kernel.org>`，15 patches）按 sashiko 意见增至 15 补丁并修订三处描述/注释（见技术方案）。

## Maintainer 意见与讨论焦点
sashiko（系列内以 `#10/#6/#11/#15` 引用其意见）在 v1 上提出：bypassed rescuee 在 dispatch_one() 里的 keep 测试处理、keep-last 通过时的注释/描述、以及 patch 0011/0015 的 refusal 原因清单需修正。v2 全部落实。Tejun Heo 为 sched_ext 维护者、系列在其自有树迭代；当日缓存内未见其他外部 reviewer 上线表态，但 Tejun 的 v2 changelog 表明 review 意见已被吸收。

## 合入评估
*likelihood=high*。属 sched_ext/for-7.4 维护者自有树的正向修复（bypass/子调度器 stall），v2 已回应 review 意见、带 model check 与多层压力测试；sched_ext 树由 Tejun 直管，此类修复通常随之进下一窗口。*blocking_issues*：当日缓存未见第二 reviewer 确认。*next_action*：等 Tejun 定稿并合入 for-7.4（可能待 sashiko 最终确认 v2）。

## 效果评估
无量化性能数据。作者描述了功能级验证：三层层级循环 bypass 下 pinned spinner、fork / context-switch 风暴、queued 任务下撤销 caps；bypass 负载均衡的 remote move 与 drain 均被exercised；holding_cpu 握手、cap 撤销放置、rescue keep 做了小 CPU 数 model check。目标是消除 stall，未提供吞吐/延迟对比数字。

## 我可以参与的点
- *kind: testing*：在多层子调度器 + 快速 cap 授予/撤销的真实 sched_ext 负载上回归，重点验证「host 失 BASE 时 bypass DSQ 排空」与「host 有 BASE 无 ENQ」两条路径不再 stall。
- *kind: review*：复核 v2 新增 0010（expire prev slice）与 0007（kernel slice 只可缩短不可延长）对 slice 记账不变量的一致性。

## 参考链接
- v2 cover: https://lore.kernel.org/all/20261023052452.2889061-1-tj@kernel.org/
- v1 cover: https://lore.kernel.org/all/20261022213836.2259069-1-tj@kernel.org/

---
id: sched-20261023-008
date: 2026-10-23
subject: "sched_ext: Fix bypassed sub-scheduler tasks stalling when the host lacks caps"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261023052452.2889061-1-tj@kernel.org>"
lore_url: "https://lore.kernel.org/all/20261023052452.2889061-1-tj@kernel.org/"
authors: ["Tejun Heo"]
maintainers_involved: ["Tejun Heo"]
current_version: v2
patch_series:
  - version: v1
    msgid: "<20261022213836.2259069-1-tj@kernel.org>"
    date: 2026-10-22
    summary: "14 patches：SCX_CAP_BASE 定为 bypass 唯一 cap，rescue slice 修复 + cap 感知 bypass 负载均衡"
    review_outcome: "sashiko 提出 keep 测试/注释/refusal 清单三处需修"
  - version: v2
    msgid: "<20261023052452.2889061-1-tj@kernel.org>"
    date: 2026-10-23
    summary: "15 patches：新增 expire prev slice、补 keep-last 注释、订正 refusal 原因"
    review_outcome: "回应 sashiko 意见；未见其他 reviewer 上线"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["当日缓存未见第二 reviewer 确认"]
  next_action: "等 Tejun 定稿并合入 for-7.4"
contribution_opportunities:
  - kind: testing
    description: "在多层子调度器 + 快速 cap 撤销场景回归，验证两条 stall 路径已修复"
  - kind: review
    description: "复核 0010 expire prev slice 与 0007 kernel slice 只可缩短的 slice 记账不变量"
generated_at: "2026-10-24T09:07:00"
source_email_count: 31
related_articles: []
tags: [sched_ext]
---