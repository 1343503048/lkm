# sched_ext: Add lazy preemption support

## TL;DR
增量更新：Andrea Righi 推出 sched_ext/for-7.4 懒抢占系列 v6，落实 Tejun Heo 三条意见（把 slice_expires_lazy 塞进 scx.disallow 旁的 padding 而非让 task_struct 膨胀 8 字节、修正 LAZY_SLICE_EXPIRY 文档、先置 lazy resched 请求再恢复 tick 依赖）。Tejun 以 AI 辅助评审跑通 vng 下全部 selftest，并给出若干待修的小问题（autogen 头顺序、selftest 健壮性），合入可能性高。

## 背景与问题
背景见 sched-20260916-007：fair 类可通过 lazy rescheduling 延迟调度边界，sched_ext 此前只暴露即时抢占给 BPF 调度器。本系列补齐懒抢占能力。

## 技术方案
方案不变：新增 enqueue/kick 抢占标志的 lazy 变体，使运行中的 sched_ext 任务切片到期后可推迟调度边界直到返回用户态或下一次调度 tick；SCX_OPS_LAZY_SLICE_EXPIRY 选择默认懒切片到期，任务级可用 `scx_bpf_task_set_slice_expiry()` 双向覆盖；bypass 仍强制即时重调度；lazy enqueue/kick 请求还会在目标为 NO_HZ_FULL 上的无限切片任务时恢复调度 tick。

## 版本演进与当前进展
- v5（09-16）：上一版。
- v6（09-17，`<20260917070751.3617935-1-arighi@nvidia.com>`）：pack slice_expires_lazy 到 disallow 旁 padding（Tejun）、修正 LAZY_SLICE_EXPIRY 对 PREEMPT_DYNAMIC/bypass 的文档（Tejun）、先置 lazy resched 请求再恢复 tick 依赖（Tejun）。virtme-ng 下 kick（6 PASS）/nohz_tick（1 PASS）均通过。

## Maintainer 意见与讨论焦点
- **Tejun Heo（AI 辅助评审，v6）**：build + vng selftest 通过，kick/tick 路径 trace 正确。剩余待修点：8 字节 task_struct 膨胀（已修）、PREEMPT_DYNAMIC 下 lazy 是运行时模式而非"无懒抢占内核"的表述、bypass 才强制即时重调度、置 TIF 位应先于恢复 tick 依赖、autogen 头须按定义顺序重生成（SCX_KICK_PREEMPT_LAZY 排在 SCX_KICK_WAIT 后）、selftest 多处健壮性问题（observation_valid 对非零切片应跳过、DONE 竞态应轮询、nohz 阶段应先验证 tick 确已停、缺 __resched_curr BTF 时应跳过而非连带失败）。
- 无 NAK；评审是"小修即可"级别。

## 合入评估
*likelihood=high*。面向 for-7.4 的特性系列，测试全绿，评审只剩排版/健壮性小修，作者积极迭代。*blocking_issues*：v7 需落实 Tejun 剩余小修。*next_action*：作者发 v7 落实上述收尾点。

## 效果评估
无性能数据；功能验证：vng 下 kick 6/6、nohz_tick 1/1 通过，lazy/full/none 三模式均过。

## 我可以参与的点
- kind=testing：在真实 PREEMPT_DYNAMIC + NO_HZ_FULL 机器上跑 kick/nohz_tick selftest，验证 lazy 抢占在非 virtme 环境下的行为。
- kind=review：核对 selftest 的 observation_valid 与 DONE 轮询改动是否引入新的时序假设。

## 参考链接
- lore（v6 cover）: https://lore.kernel.org/all/20260917070751.3617935-1-arighi@nvidia.com/

---
id: sched-20260917-010
date: '2026-09-17'
subject: 'sched_ext: Add lazy preemption support'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20260917070751.3617935-1-arighi@nvidia.com>'
lore_url: 'https://lore.kernel.org/all/20260917070751.3617935-1-arighi@nvidia.com/'
authors:
  - 'Andrea Righi'
maintainers_involved:
  - 'Tejun Heo'
current_version: v6
patch_series:
  - version: v5
    msgid: '<20260915194611.2674127-1-arighi@nvidia.com>'
    date: '2026-09-15'
    summary: '懒抢占标志与 selftest'
    review_outcome: 'Tejun AI 评审给出小修'
  - version: v6
    msgid: '<20260917070751.3617935-1-arighi@nvidia.com>'
    date: '2026-09-17'
    summary: 'pack 到 padding、修文档、先置 resched 再恢复 tick 依赖'
    review_outcome: 'Tejun 测试全绿，剩余小修待 v7'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - 'v7 需落实 Tejun 剩余排版/健壮性小修'
  next_action: '作者发 v7 落实收尾点'
contribution_opportunities:
  - kind: testing
    description: '在真实 PREEMPT_DYNAMIC + NO_HZ_FULL 机器上跑 kick/nohz_tick selftest'
  - kind: review
    description: '核对 selftest 的 observation_valid 与 DONE 轮询改动'
generated_at: '2026-09-18T09:00:00'
source_email_count: 5
related_articles:
  - sched-20260916-007
tags:
  - sched_ext
  - preempt
---