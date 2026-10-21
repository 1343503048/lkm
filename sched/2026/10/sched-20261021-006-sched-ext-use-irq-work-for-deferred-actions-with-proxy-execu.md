# sched_ext: Use irq_work for deferred actions with proxy execution

## TL;DR
Andrea Righi 发往 sched_ext 的补丁（其 3 补丁系列之 2/3）：proxy execution 下 deferred actions 改用 `irq_work` 而非直接依赖 balance callback 机制。当日 Tejun Heo 已将其收取到 `sched_ext/for-7.4-fixes`，并备注「未来或可进一步优化，但更应改进 balance_callback 机制本身、而不是从 ext 侧绕开」。

## 背景与问题
proxy execution 引入后，deferred actions（延迟动作）与 balance callback 的交互出现适配问题。本补丁把 deferred actions 改为经 `irq_work` 触发，规避直接 balance callback 机制的耦合。

## 技术方案
单补丁：deferred actions 改用 `irq_work` 承载。具体实现细节未完整展开在当日缓存中，但方向是「用 irq_work 承载 proxy execution 下的延迟动作」。

## 版本演进与当前进展
*current_version: v1*。作为系列 2/3 发出（`<20261020084400.845842-3-arighi@nvidia.com>`），当日即被 Tejun 收取。

## Maintainer 意见与讨论焦点
Tejun Heo（sched_ext 维护者）直接收取，并给出方向性备注：「也许未来还能再优化，但我们更该改进 balance_callback 机制，而不是在 ext 侧绕开它」。无分歧。

## 合入评估
*likelihood=merged*。已由 Tejun 收取到 `sched_ext/for-7.4-fixes`。

## 效果评估
未提供性能基准，属 proxy execution 正确性适配。

## 我可以参与的点
Tejun 提到的「改进 balance_callback 机制本身」是可扩展方向，但超出本补丁范围；当前无即时参与点。

## 参考链接
- 补丁 2/3：https://lore.kernel.org/all/20261020084400.845842-3-arighi@nvidia.com/
- Tejun 收取回帖：https://lore.kernel.org/all/6ac645ace4ab4023b24e8aace406a072@kernel.org/

---
id: sched-20261021-006
date: 2026-10-21
subject: "sched_ext: Use irq_work for deferred actions with proxy execution"
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: "<20261020084400.845842-3-arighi@nvidia.com>"
lore_url: "https://lore.kernel.org/all/20261020084400.845842-3-arighi@nvidia.com/"
authors: ["Andrea Righi"]
maintainers_involved: ["Tejun Heo"]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261020084400.845842-3-arighi@nvidia.com>"
    date: 2026-10-20
    summary: "proxy execution 下 deferred actions 改用 irq_work"
    review_outcome: "Tejun 收取到 sched_ext/for-7.4-fixes，建议未来改进 balance_callback 机制"
upstream_commit: null
fixes_commit: null
merged_branch: "sched_ext/for-7.4-fixes"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已收取，无需进一步动作"
contribution_opportunities: []
generated_at: "2026-10-22T01:30:00"
source_email_count: 1
related_articles: []
tags: [sched_ext, proxy_execution]
---