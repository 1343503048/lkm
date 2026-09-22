# sched/proxy: allow SCHED_PROXY_EXEC with PREEMPT_RT

## TL;DR
本文为增量更新，完整背景见 sched-20260921-003。此前 Quchaosheng 发补丁让 `SCHED_PROXY_EXEC` 可与 `PREEMPT_RT` 同时编译。当天 Peter Zijlstra 明确表示想等「真正准备 drop rt_mutex」时才合并该选项，作者 Quchaosheng 随即公开撤回补丁（withdraw）。系列以 superseded 收尾。

## 背景与问题
背景见 sched-20260921-003：补丁摘掉 Kconfig `depends on !PREEMPT_RT` 让组合可编译，但被指出 RT 下 `blocked_on` 恒为 NULL、新增访问器实为死代码，无实际代理执行语义。

## 技术方案
方案见 sched-20260921-003。当天无新代码。

## 版本演进与当前进展
v2（`<20260921102712.3245860-1-quchaosheng000406@163.com>`）后，当天 Peter 与作者先后回复，作者明确撤回。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**：「I would like to wait with this until such time that we're indeed ready to drop rt_mutex entirely. Having the build option but it being effectively 'broken' just doesn't make much sense to me.」
- **Quchaosheng**（作者）：回应 Peter 与 Sebastian 的共同质疑——承认「没有今天的构建失败、正是没人碰过这个组合、Kconfig 已写明 broken 是循环论证」，补丁是引入该组合而非修复它；Peter 的表述比自己更准确：该特性在 PREEMPT_RT 下实质上 broken，携带这样一个状态的 build 选项毫无意义。作者声明撤回补丁，并指出若 proxy execution 要在 PREEMPT_RT 上真正有意义，得等 RT mutex 维护 `blocked_on`，届时该工作需自证其价值。

## 合入评估
likelihood=rejected（作者主动撤回，维护者明确推迟）。blocking_issues：特性在 RT 下无实际效果，需先让 rt_mutex 维护 `blocked_on`。next_action：无——待未来 RT mutex 支持 blocked_on 后另起炉灶。

## 效果评估
无性能数据。作者自述此前 boot/压力测试真实但测试的是一个本不该存在的组合，作为论证无价值。

## 我可以参与的点
- **new_patch**：真正有价值的工作是让 PREEMPT_RT 的 rt_mutex 维护 `blocked_on`，使 proxy execution 在 RT 下生效——可研究 RT mutex 与 proxy execution 的交互并提交后续补丁。

## 参考链接
- lore thread: https://lore.kernel.org/all/20260921081525.2982361-1-quchaosheng000406@163.com/
- Peter 回复: https://lore.kernel.org/all/20260922064110.GR4121339@noisy.programming.kicks-ass.net/
- 作者撤回: https://lore.kernel.org/all/20260922070618.70119-1-quchaosheng000406@163.com/

---
id: sched-20260922-013
date: '2026-09-22'
subject: 'sched/proxy: allow SCHED_PROXY_EXEC with PREEMPT_RT'
subsystem: sched
type: feature
status: superseded
severity: none
thread_root_msgid: '<20260921081525.2982361-1-quchaosheng000406@163.com>'
lore_url: 'https://lore.kernel.org/all/20260921081525.2982361-1-quchaosheng000406@163.com/'
authors:
  - 'Quchaosheng'
maintainers_involved:
  - 'Peter Zijlstra'
current_version: v2
patch_series:
  - version: v1
    msgid: '<20260921081525.2982361-1-quchaosheng000406@163.com>'
    date: '2026-09-21'
    summary: '统一 blocked_on 辅助函数参数并适配 RT mutex 成员访问（见 sched-20260921-003）'
    review_outcome: 'RT 维护者质疑无实际效果'
  - version: v2
    msgid: '<20260921102712.3245860-1-quchaosheng000406@163.com>'
    date: '2026-09-21'
    summary: '仅修 Cc/注释/措辞，内容同 v1'
    review_outcome: 'Peter 明确推迟，作者撤回'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: rejected
  blocking_issues:
    - '特性在 RT 下无实际效果，需先让 rt_mutex 维护 blocked_on'
  next_action: '无——待未来 RT mutex 支持 blocked_on 后另起'
contribution_opportunities:
  - kind: new_patch
    description: '实现 PREEMPT_RT 下 rt_mutex 维护 blocked_on，使 proxy execution 在 RT 生效'
generated_at: '2026-09-23T00:00:00'
source_email_count: 3
related_articles:
  - sched-20260921-003
tags:
  - proxy_execution
  - preempt
---