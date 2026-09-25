# sched_ext: Place dsq_vtime next to dsq_priq

## TL;DR

Usama Arif 的缓存布局优化：把 `dsq_vtime` 挪到 `dsq_priq` 紧邻之前，让 vtime 有序 DSQ 的红黑树插入（每次下降都要同时读访问任务的 `dsq_vtime` 与 `dsq_priq`）落在同一 64 字节 cache line，减少冷访问任务的多余 cache line 填充。实测 16-vCPU KVM guest 下 enqueue 区间缩短 4~6%。已被 Tejun Heo 应用到 sched_ext/for-7.4。

## 背景与问题

`scx_dispatch_enqueue()` 对 vtime 有序的 DSQ 在持有 `dsq->lock` 时调用 `rb_add()`。红黑树下降的每一层，`scx_dsq_priq_less()` 都要读被访问任务的 `dsq_vtime`，而这个比较又用同一个任务的 `dsq_priq` 决定走左/右子树。改动前，这两个字段在 x86-64 布局里落在**不同的 64 字节 cache line** 上，冷访问任务在依赖下降路径上要多一次 cache line 填充——加长了 `dsq->lock` 的持锁时间、加剧锁竞争。

## 技术方案

把 `dsq_vtime` 紧邻移到 `dsq_priq` 之前，`dsq_seq`/`dsq_flags` 保持在 `dsq_list` 旁。作者检查的两份 x86-64 布局（scx 起始于 task_struct 偏移 776 与 840）中，`dsq_list` 到 `dsq_priq` 的字段落在同一 cache line；具体落位取决于 task_struct 整体布局，不保证所有配置/架构一致。仅字段重排，无调度行为变化。diffstat：include/linux/sched/ext.h 12 insertions(+), 11 deletions(-)。

## 版本演进与当前进展

- v1（2026-09-24，`<20260924161446.3039726-1-usama.arif@linux.dev>`）。
- 09-25：Tejun 回帖「Applied to sched_ext/for-7.4」（msgid `<6ae9d2d1972afdedf0117ec01aba783f@kernel.org>`）。

## Maintainer 意见与讨论焦点

Tejun Heo 直接应用、无异议。无 NAK、无分歧。

## 合入评估

已应用到 sched_ext/for-7.4（*likelihood=merged*），`merged_branch=sched_ext/for-7.4`，随下一合并窗口进入主线。*blocking_issues* 无。

## 效果评估

16-vCPU KVM guest 实测（作者自测）：instrumented enqueue 区间在 scx_lavd 与 scx_layered 下缩短 4~6%；scx_mitosis 与端到端负载时间无一致变化。作者也诚实注明：cache line 落位不保证所有配置/架构都受益，属布局依赖的优化。

## 我可以参与的点

- `testing`：在自家架构（如 arm64 或不同 task_struct 布局的 x86 配置）上复测 enqueue 区间，验证 4~6% 是否具有架构普适性。
- `extend`：`dsq_vtime` 之外的冷热字段（如 `ddsp_vtime`、`dsq_list`）是否还有可合并到同一 cache line 的布局优化空间，可继续排查 pahole。

## 参考链接

- 补丁: https://lore.kernel.org/all/20260924161446.3039726-1-usama.arif@linux.dev/
- Tejun 应用回帖: https://lore.kernel.org/all/6ae9d2d1972afdedf0117ec01aba783f@kernel.org/

---
id: sched-20260925-020
date: 2026-09-25
subject: "sched_ext: Place dsq_vtime next to dsq_priq"
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: "<20260924161446.3039726-1-usama.arif@linux.dev>"
lore_url: "https://lore.kernel.org/all/20260924161446.3039726-1-usama.arif@linux.dev/"
upstream_commit: null
fixes_commit: null
merged_branch: "sched_ext/for-7.4"
current_version: v1
generated_at: "2026-09-26T01:15:00"
authors:
  - "Usama Arif"
maintainers_involved:
  - "Tejun Heo"
patch_series:
  - version: v1
    msgid: "<20260924161446.3039726-1-usama.arif@linux.dev>"
    date: 2026-09-24
    summary: "dsq_vtime 紧邻 dsq_priq，减少 vtime 插入的 cache line 填充"
    review_outcome: "09-25 Tejun 应用到 sched_ext/for-7.4"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已应用到 sched_ext/for-7.4，随合并窗口进主线"
contribution_opportunities:
  - kind: testing
    description: "在 arm64 或不同 task_struct 布局的 x86 配置复测 enqueue 区间，验证 4~6% 的架构普适性"
  - kind: extend
    description: "用 pahole 排查 dsq_vtime 之外（ddsp_vtime、dsq_list）是否还有可合并到同一 cache line 的布局优化"
source_email_count: 2
related_articles: []
tags:
  - sched_ext
---