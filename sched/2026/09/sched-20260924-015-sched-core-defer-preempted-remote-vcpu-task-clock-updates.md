# sched/core: Defer preempted remote vCPU task clock updates

## TL;DR
- sched-20260921-009：Dongli Zhang 的「延迟被抢占远程 vCPU 的 task clock 更新」RFC 被 KVM 维护者 Sean Christopherson 质疑——方案关键约束「hypervisor 在清除 preempted 标记前发布最新 stealtime」在旧版 KVM 上无法保证，作者尚未回应。
- sched-20260924-015（今天，增量更新）：Dongli Zhang 回应 Sean 的质疑，承认约束确实不成立并详述失败模式——旧版 KVM 会先清 `st->preempted`、后发布 stealtime，导致客户机观察到 `!vcpu_is_preempted()` 却读到旧 stealtime，被抢占区间被错误记到 `rq->clock_task`，且后续更新因 `prev_steal_time_rq` 被推进而永久丢失。作者重申这正是他把该系列标为 RFC、寻求更好方案的原因。

## 背景与问题
- sched-20260921-009（背景见 sched-20260824-008）：KVM 客户机里，当 vCPU A 为被抢占的 vCPU B 做远程记账时，host 直到 vCPU B 重新进入才更新 stealtime，导致 vCPU A 把 stolen 区间误计入任务运行时间。RFC 提出延迟远程 CPU 对已标记 preempted 的 vCPU 的 `clock_task` 更新。
- 本日无新增背景，是作者对「方案约束不可强制」质疑的正面回应。

## 技术方案
- 本日无新代码。作者用具体时序说明了约束失效的机制：
  - 旧版 KVM 可在相应 stealtime 更新**发布之前**先清掉 `st->preempted`；
  - 于是客户机观察到 `!vcpu_is_preempted()` 并消费 deferred clock delta，却仍读到旧 stealtime——被抢占区间被错误记到 `rq->clock_task`；
  - 下一次更新时累积的 stealtime delta 被观测到，但可能大于新的小 `rq->clock` delta 而被截断；而 `prev_steal_time_rq` 仍推进到新 stealtime 值，剩余 stealtime 在后续更新中不再记账。
- 作者明确「这就是我把这个 patchset 标为 RFC 的原因，想征询是否有更好的方案」。

## 版本演进与当前进展
- RFC v1（08-24，`<20260824012716.753022-1-dongli.zhang@oracle.com>`）→ 09-21 Sean 质疑 → 本日（09-24）作者回应失败模式并继续寻求更好方案。无新版补丁。

## Maintainer 意见与讨论焦点
- **Sean Christopherson（KVM/x86 维护者）**（此前）：质疑「先发布 stealtime 再清 preempted」这条约束无法强制（旧版 KVM 不满足）。
- **Dongli Zhang（作者）**（本日）：承认约束不成立，并给出了「先清 preempted、后发布 stealtime」导致的错误记账/永久丢失 stealtime 的完整时序；态度是「求证更好方案」而非坚持原案。
- 无 NAK；核心分歧仍是「方案依赖不可控的 hypervisor 行为」。

## 合入评估
*likelihood=low*。RFC 方案的核心假设已被作者自己确认在旧版 KVM 上不成立（先清标记后发布 stealtime），问题真实但方案需要不依赖 hypervisor 时序的替代设计。*blocking_issues*：原方案依赖的 hypervisor 时序无法保证，失败模式下还会错误记账并丢失 stealtime。*next_action*：作者或社区提出不依赖 hypervisor 时序的替代方案（或 KVM 侧配合的特性）。

## 效果评估
无性能数据；作者本日给出的是失败模式下的正确性论证（错误记账 + stealtime 丢失的时序），未附实测。

## 我可以参与的点
- kind=discussion：分析「延迟远程 task clock 更新」在 hypervisor 时序不满足时的替代设计（如 KVM 特性位、或改用不依赖 host 配合的记账方式）。
- kind=testing：在旧版/新版 KVM 上验证 preempted 标记与 stealtime 发布的实际时序，为方案可行性提供数据。

## 参考链接
- lore thread: https://lore.kernel.org/all/20260824012716.753022-1-dongli.zhang@oracle.com/
- 作者回应: https://lore.kernel.org/all/02e6b16a-67d0-439e-868b-435fe1c38400@oracle.com/

---
id: sched-20260924-015
date: '2026-09-24'
subject: 'sched/core: Defer preempted remote vCPU task clock updates'
subsystem: sched
type: discussion
status: rfc
severity: low
thread_root_msgid: '<20260824012716.753022-1-dongli.zhang@oracle.com>'
lore_url: 'https://lore.kernel.org/all/20260824012716.753022-1-dongli.zhang@oracle.com/'
authors:
  - 'Dongli Zhang'
maintainers_involved:
  - 'Sean Christopherson'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260824012716.753022-1-dongli.zhang@oracle.com>'
    date: '2026-08-24'
    summary: 'RFC：延迟远程 CPU 对已标记 preempted 的 vCPU 的 clock_task 更新'
    review_outcome: '作者确认旧版 KVM 时序约束不成立，寻求更好方案'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - '原方案依赖的 hypervisor 时序无法保证，失败模式会错误记账并丢失 stealtime'
  next_action: '提出不依赖 hypervisor 时序的替代方案或 KVM 侧配合特性'
contribution_opportunities:
  - kind: discussion
    description: '分析不依赖 hypervisor 时序的替代设计'
  - kind: testing
    description: '在旧/新版 KVM 验证 preempted 标记与 stealtime 发布时序'
generated_at: '2026-09-25T09:00:00'
source_email_count: 1
related_articles:
  - sched-20260921-009
  - sched-20260824-008
tags:
  - cfs
  - sched_clock
---