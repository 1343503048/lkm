# sched: Allow enabling proxy exec with sched_ext

# sched_ext: 在 sched_ext 下启用 proxy execution

## TL;DR
Andrea Righi 的 15-patch 系列把内核主流的 SCHED_PROXY_EXEC（代理执行）机制带到 sched_ext：互斥锁/RT 阻塞的任务可被同调度类或更早调度类的高优先级任务「代理执行」，从而缓解优先级反转。Tejun 评价「Nice.」并指出两处需澄清的语义。属大型 feature，合入可能性高，仍处 review。

## 背景与问题
proxy execution 是缓解 mutex/rt 优先级反转的机制：当一个高优先级任务被低优先级持有者（被 PI 提升）阻塞时，允许让「代理 donor」在持有锁的 CPU 上继续跑，直到锁释放。主线在 CFS/RT 下已有实现，但 sched_ext（BPF 可写调度器）尚未接入——BPF 调度器需要自行决定哪些 donor 可以、哪些不应被代理，且 blocked donor 的生命周期与 SCX 的入队/抢占路径需要正确交织。

## 技术方案
- 把 proxy donor 的准入判定下放给 BPF 调度器：`scx_allow_proxy_exec()` / enqueue path，调度器可声明是否管理 blocked donor（`SCX_OPS_ENQ_BLOCKED`）。
- 修正 `put_prev_task_scx()`：rq lock 自 `scx_allow_proxy_exec()` 起一直持有，需在 put_prev 时正确维护 blocked donor 状态。
- 修正 `wakeup_preempt_scx()`：被 mutex 阻塞的 donor 保持入队用于代理执行，其唤醒不走 `enqueue_task_scx()`，若 BPF 调度器管理 blocked donor 则需显式 `resched_curr()` 让其重新考虑此前拒绝派发的 donor。
- `scx_qmap`（测试调度器）加 proxy 支持：被本地 DSQ 拒绝的 blocked donor 移到 global DSQ，让其他 CPU 加速消费。

## 版本演进与当前进展
v1 于 2026-07-28 由 Andrea Righi 发出（15 patch）。08-04 上 Tejun 对 13/15、14/15 给出 review，要求澄清两处语义；John Stultz（原始 proxy execution 作者）给 Acked-by。当前仍在 review。

## Maintainer 意见与讨论焦点
- Tejun Heo：整体「Nice.」，但要求解释 (1) 14/15 中 blocked donor 拒绝后移 global DSQ 为何必要；(2) 13/15 `wakeup_preempt_scx` 中 `resched_curr()` 的动机与注释是否准确（「若 BPF 调度器管理 blocked donor」语义不清）。
- John Stultz：Acked-by。

属大型基础设施扩展，无方向反对，焦点在实现清晰度。

## 合入评估
合入可能性 high。Tejun 已表态认可，且随 sched_ext/for-7.3 路线推进。剩余仅为 review 澄清，无架构障碍。

## 效果评估
邮件未附 benchmark。属机制扩展，效果以「正确接入 proxy execution + 无优先级反转回归」衡量；需 sched_ext CI 与 scx_qmap 测试覆盖验证。

## 我可以参与的点
- 审阅 13/15 的 `resched_curr()` 动机与 14/15 的 global-DSQ 重派必要性，回帖澄清性 review（Tejun 已发起询问，作者尚未答复）。

## 参考链接
- lore thread: 未获取到

---
subject: "sched: Allow enabling proxy exec with sched_ext"
id: sched-20260804-001
date: 2026-08-04
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260728154332.0000000-1-arighi@nvidia.com>"
lore_url: "unknown"
authors: [Andrea Righi, Tejun Heo, John Stultz]
maintainers_involved: [Tejun Heo, Peter Zijlstra]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260728154332.0000000-1-arighi@nvidia.com>"
    date: 2026-07-28
    summary: "15-patch 系列：在 sched_ext 下启用 SCHED_PROXY_EXEC（mutex/rt 阻塞的任务可被同/他调度类的高优先级任务「代理执行」）。核心是把 proxy donor 的准入判定下放给 BPF 调度器（scx_allow_proxy_exec / enqueue path），并修正 put_prev_task_scx、wakeup_preempt_scx 中与 proxy 交互的语义。讨论 thread 在 08-04 活跃。"
    review_outcome: "Tejun Heo：对整体「Nice.」并给出两处 review（blocked donor 拒绝后移到 global DSQ 的必要性、wakeup_preempt 中 resched_curr 的注释与动机）。John Stultz：Acked-by（其原始 proxy execution 工作被复用）。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["Tejun 的两处 review 仍需作者澄清/补注释（scx_qmap 14/15 与 wakeup_preempt 13/15）"]
  next_action: "等待 Andrea 对 Tejun review 的回复（解释 blocked-donor 重派与 resched_curr 动机），预计随 sched_ext/for-7.3 路线合入。"
contribution_opportunities:
  - kind: review
    description: "可审阅 13/15 wakeup_preempt_scx 中 resched_curr() 的动机与注释是否清晰，以及 14/15 scx_qmap 中 blocked donor 拒绝后移 global DSQ 的必要性，参与 Tejun 发起的澄清讨论。"
generated_at: "2026-08-05T00:25:00"
source_email_count: 4
related_articles: []
tags: [sched_ext, proxy_execution]
---
