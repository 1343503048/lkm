# sched_ext: Don't report a forced-idle CPU as open for IMMED tasks

## TL;DR
Andrea Righi 发往 `sched_ext/for-7.3-fixes` 的单补丁修复：core scheduling 可在更高优先级类任务 runnable 时强制某 CPU idle（未打 tag 的 core-wide max 下，不兼容 pick 直接换成 idle 而不去找兼容任务），此时 `rq->next_class` 为 idle，`rq_is_open()` 误报该 CPU「开放」，导致插进其本地 DSQ 的 `SCX_ENQ_IMMED` 任务被 parked 在更高类任务后面，而不是返回 BPF 调度器。当日新发，暂无回帖。

## 背景与问题
core scheduling 能强制一个 CPU idle、而一个更高类任务仍在其上 runnable：在一个未打 tag 的 core-wide max 下，不兼容的 pick 被替换成 idle，且不尝试寻找兼容任务。此时 `rq->next_class` 是 idle，`rq_is_open()` 于是把该 CPU 报告为开放，`SCX_ENQ_IMMED` 任务被插入其本地 DSQ、parked 在更高类任务之后，而不是立即回到 BPF 调度器另找 CPU。复现（作者）：SMT 对的两兄弟都设 ext server runtime 为 0，一个未打 tag 的 SCHED_FIFO 任务在一个兄弟上自旋、强制另一个兄弟 idle，而那里正好有一个打 tag 的 SCHED_FIFO 任务 runnable；插入 forced-idle 兄弟本地 DSQ 的 IMMED 任务从未被 reenqueue，整个测试窗口内一直 parked。开启 ext server 后任务最终会跑，但要等 server 介入，远非「immediate」。

## 技术方案
单补丁（`kernel/sched/ext/ext.c`，+23）：新增 `higher_class_runnable()` 辅助函数（依次检查 stop/dl/rt/fair 是否有 runnable 任务；dl 分支上把 ext server 的 `rb_node` 从 `dl.root` 树中排除，因为 ext server 会选择 SCX 任务优先于 RT/fair）。在 `rq_is_open()` 中增加判断：当 `rq->donor == rq->idle`、不在 dispatch 中（无 `SCX_RQ_IN_DISPATCH`）且 `higher_class_runnable(rq)` 时，返回 false（报告 CPU 忙）。在 dispatch 期间则保持原判断——因为那意味着更高类当时无事可跑。修复后 IMMED 任务被立刻 reenqueue、由 BPF 调度器放到其他 CPU 上运行。带 `Fixes: 98d709cba319`（"sched_ext: Implement SCX_ENQ_IMMED"）。

## 版本演进与当前进展
v1 首版（`<20261017124749.3608468-1-arighi@nvidia.com>`），当日新发，暂无 review 意见。

## Maintainer 意见与讨论焦点
当日无回帖。作者即 sched_ext 维护者、直发 `for-7.3-fixes`，带真实复现场景与 `Fixes:` 标签。潜在评审点（无人提出）：`higher_class_runnable()` 对 ext server 在 dl 树中节点的排除逻辑是否与 `rq_is_open()` 其他路径的语义一致，以及 forced-idle 判定与 core-sched cookie 的交互。

## 合入评估
*likelihood=high*（预期）。维护者直发目标 fixes 分支、带 `Fixes:`、有明确复现路径，属 sched_ext 例行 fix。*blocking_issues*：Tejun 的收取未发生。*next_action*：等 Tejun applied 到 sched_ext/for-7.3-fixes。

## 效果评估
作者描述复现与修复效果：修复前 IMMED 任务在 forced-idle CPU 上整窗 parked 不被 reenqueue；修复后 IMMED 任务被立即 reenqueue、由 BPF 调度器放到其他 CPU 运行。未给出量化 benchmark 数字。

## 我可以参与的点
- *testing*：在 core scheduling 拓扑（SMT 对 + 未打 tag 的 RT/fair 负载 + ext server runtime=0）复现 IMMED 任务 parked，验证修复后立即 reenqueue。
- *review*：复核 `higher_class_runnable()` 中 ext server 节点的排除逻辑与 `rq_is_open()` 其余路径的语义一致性。

## 参考链接
- patch：https://lore.kernel.org/all/20261017124749.3608468-1-arighi@nvidia.com/

---
id: sched-20261017-003
subject: "sched_ext: Don't report a forced-idle CPU as open for IMMED tasks"
date: 2026-10-17
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261017124749.3608468-1-arighi@nvidia.com>"
lore_url: "https://lore.kernel.org/all/20261017124749.3608468-1-arighi@nvidia.com/"
authors: ["Andrea Righi"]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261017124749.3608468-1-arighi@nvidia.com>"
    date: 2026-10-17
    summary: "rq_is_open() 在 donor idle 且有更高类 runnable（且非 dispatch 中）时报告忙，避免 IMMED 任务误 park"
    review_outcome: "当日新发，暂无回帖"
upstream_commit: null
fixes_commit: 98d709cba319
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["Tejun 的收取未发生"]
  next_action: "等 Tejun applied 到 sched_ext/for-7.3-fixes"
contribution_opportunities:
  - kind: testing
    description: "在 core scheduling 拓扑复现 forced-idle CPU 上 IMMED 任务 parked，验证修复后立即 reenqueue"
  - kind: review
    description: "复核 higher_class_runnable() 中 ext server 节点排除逻辑与 rq_is_open() 其余路径语义一致性"
generated_at: "2026-10-18T01:14:00"
source_email_count: 1
related_articles: []
tags: [sched_ext, core_sched]
---