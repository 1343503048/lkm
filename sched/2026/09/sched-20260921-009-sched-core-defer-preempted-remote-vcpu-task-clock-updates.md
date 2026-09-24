# sched/core: Defer preempted remote vCPU task clock updates

## TL;DR
增量更新：Dongli Zhang 的"延迟被抢占远程 vCPU 的 task clock 更新" RFC 昨日收到 KVM 维护者 Sean Christopherson 的技术质疑——该方案的关键约束"hypervisor 在清除 preempted 标记前发布最新 stealtime"在旧版 KVM 上无法保证，作者尚未回应。合入前景趋弱。

## 背景与问题
背景见 sched-20260824-008：KVM 客户机里，当 vCPU A 为被抢占的 vCPU B 做远程记账时，host 直到 vCPU B 重新进入才更新 stealtime，导致 vCPU A 把 stolen 区间误计入任务运行时间，任务被施加错误调度惩罚。RFC 提出延迟远程 CPU 对已标记 preempted 的 vCPU 的 `clock_task` 更新。

## 技术方案
本日无新代码。核心约束仍如 RFC 所述：需要 hypervisor 在清除 `preempted` 标记之前发布最新 stealtime。Sean 的质疑正落在这条约束的可实现性上。

## 版本演进与当前进展
- RFC v1（08-24，thread root `<20260824012716.753022-1-dongli.zhang@oracle.com>`）。
- 09-21：Sean Christopherson 在 patch 2/2 下提问，等待作者回应。

## Maintainer 意见与讨论焦点
- **Sean Christopherson（KVM/x86 维护者）**：质疑本方案依赖的约束不可强制——"What happens if the hypervisor doesn't do that? Because it's infeasible to guarantee this will never run on an older version of KVM."（如果 hypervisor 不这么做会怎样？因为无法保证它永远不会在旧版 KVM 上运行。）这直指方案的兼容性缺口：旧版/其他 hypervisor 未必满足"先发布 stealtime 再清 preempted 标记"的时序。

## 合入评估
*likelihood=low*。RFC 方案的核心假设被维护者质疑为不可强制保证（旧版 KVM 不满足时序约束），问题真实但方案依赖无法控制的 hypervisor 行为。*blocking_issues*：需解释在 hypervisor 不满足时序约束时的降级行为，或改用不需要 hypervisor 配合的方案。*next_action*：作者回应 Sean 的问题，说明该约束不满足时的后果与回退策略。

## 效果评估
无性能数据；修复目标（消除 KVM 客户机中被抢占任务的错误调度惩罚）仍停留在机制层面，未见实测验证。

## 我可以参与的点
- **review / discussion**：分析在 hypervisor 不满足 stealtime 时序约束时的失败模式与可能的降级/替代方案（例如是否需要 KVM 特性位或切换到不需要 host 配合的记账方式）。
- **testing**：在 KVM 环境（含旧版 KVM）验证该 RFC 在 hypervisor 行为不符合假设时的实际影响。

## 参考链接
- lore thread: https://lore.kernel.org/all/20260824012716.753022-1-dongli.zhang@oracle.com/

---
id: sched-20260921-009
date: '2026-09-21'
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
    review_outcome: 'Sean Christopherson 质疑 hypervisor 时序约束无法保证（旧版 KVM 不满足）'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - '核心约束（hypervisor 先发布 stealtime 再清 preempted）在旧版 KVM 上无法保证，方案可行性被质疑'
  next_action: '作者回应 Sean 的问题，说明约束不满足时的降级行为或给出替代方案'
contribution_opportunities:
  - kind: discussion
    description: '分析 hyptrvisor 不满足 stealtime 时序约束时的失败模式与替代方案'
  - kind: testing
    description: '在 KVM（含旧版）环境验证 hypervisor 行为不符合假设时的实际影响'
generated_at: '2026-09-22T01:10:00'
source_email_count: 1
related_articles:
  - sched-20260824-008
tags:
  - cfs
  - sched_clock
---