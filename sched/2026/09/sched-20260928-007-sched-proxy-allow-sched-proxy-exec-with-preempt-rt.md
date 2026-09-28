# sched/proxy: allow SCHED_PROXY_EXEC with PREEMPT_RT

## TL;DR

本文为增量更新，完整脉络见 sched-20260922-013。作者 Quchaosheng 此前发补丁让 `SCHED_PROXY_EXEC` 可与 `PREEMPT_RT` 同时编译，被 Peter Zijlstra 与 Sebastian 指出该组合「effectively broken」后已撤回。28 日作者发帖做最终澄清：系列正式撤回，v2 只让组合能 build + boot、并未让 proxy execution 在 RT 下真正可用；构建失败本身是真实存在且仍在树上的，因此 Kconfig `depends on !PREEMPT_RT` 现状正确。

## 背景与问题

- sched-20260922-013：补丁摘掉 Kconfig `depends on !PREEMPT_RT` 让组合可编译，但被指出 RT 下 `blocked_on` 恒为 NULL、新增访问器实为死代码，无实际代理执行语义，作者当日撤回。
- sched-20260928-007（今天）：作者补充关键事实——`blocked_on` 只由 native mutex 慢路径设置，而该路径在 `PREEMPT_RT` 下被编译掉，故该选项会产出「`task_is_blocked()` 恒 false、`find_proxy_task()` 永远到不了」的内核，正是 Peter 所说的「effectively broken 的构建选项」。

## 技术方案

无新代码。作者的结论是：让 `SCHED_PROXY_EXEC` 在 PREEMPT_RT 下真正有意义，需要教 RT mutex 实现去维护 `blocked_on`——这是另一块独立工作，不在本系列范围内。

## 版本演进与当前进展

*status=superseded*：系列已正式撤回（v2 后 Peter 与 Sebastian 质疑、作者撤回）。28 日为作者对当前状态的公开定调，避免他人再花时间：该组合的构建失败（`kernel/sched/core.c` 两者同开）真实存在，但 `depends on !PREEMPT_RT` 的 Kconfig 现状是正确取舍。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**（维护者，前一轮）：不愿携带一个「effectively broken」的 build 选项；作者引用其表述并确认自己的表述不如 Peter 准确。
- **Sebastian**（RT 维护者，前一轮）：同样质疑组合无实际效果。
- 作者接受全部质疑并撤回，无争议残留。

## 合入评估

*likelihood=rejected*（作者主动撤回，方向被 delay/否）。*blocking_issues*：特性在 RT 下无实际效果，需先让 rt_mutex 维护 `blocked_on`。*next_action*：无——待未来 RT mutex 支持 `blocked_on` 后另起炉灶。

## 效果评估

无性能数据。作者明确：此前 boot/压力测试真实，但测的是一个本不该存在的组合，作为论证无价值。

## 我可以参与的点

- `new_patch`：真正有价值的工作是让 PREEMPT_RT 的 rt_mutex 维护 `blocked_on`，使 proxy execution 在 RT 下生效——可研究 RT mutex 与 proxy execution 的交互并提交后续补丁。

## 参考链接

- 作者最终澄清: https://lore.kernel.org/all/20260928093246.1994257-1-quchaosheng000406@163.com/
- Peter 前一轮回复: https://lore.kernel.org/all/20260922064110.GR4121339@noisy.programming.kicks-ass.net/

---
id: sched-20260928-007
date: '2026-09-28'
subject: 'sched/proxy: allow SCHED_PROXY_EXEC with PREEMPT_RT'
subsystem: sched
type: discussion
status: superseded
severity: none
thread_root_msgid: '<20260928093246.1994257-1-quchaosheng000406@163.com>'
lore_url: 'https://lore.kernel.org/all/20260928093246.1994257-1-quchaosheng000406@163.com/'
authors:
  - 'Quchaosheng'
maintainers_involved:
  - 'Peter Zijlstra'
current_version: v2
patch_series:
  - version: v2
    msgid: '<20260921102712.3245860-1-quchaosheng000406@163.com>'
    date: '2026-09-21'
    summary: '仅修 Cc/注释/措辞，内容同 v1'
    review_outcome: 'Peter/Sebastian 质疑无实际效果，作者撤回；09-28 作者最终澄清'
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
generated_at: '2026-09-29T01:00:00'
source_email_count: 1
related_articles:
  - sched-20260922-013
  - sched-20260921-003
tags:
  - proxy_execution
  - preempt
---