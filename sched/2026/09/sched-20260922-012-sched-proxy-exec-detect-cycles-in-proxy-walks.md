# sched/proxy_exec: detect cycles in proxy walks

## TL;DR
本文为增量更新，完整背景见 sched-20260915-009 与 sched-20260919-012。Hui Su 的 proxy_exec 环检测 RFC（Online Brent，免持久 walk 状态）当天迎来实质性三方讨论：John Stultz 认可其以极小开销尽早检出小环，并仍建议保留 max-depth 兜底；Peter Zijlstra 强调 proxy 机制「硬依赖 block 图无环」，必须在暴露给用户态前强制检测，且应讨论是否返回 `-EDEADLK` 给用户态。方向从「要不要环检测」转向「环检测如何配合用户态错误返回」。

## 背景与问题
背景见 sched-20260915-009：proxy execution 的 blocked_on 链成环会让 `find_proxy_task()` 持 rq->lock 死循环。Hui Su 的 RFC 用 Brent 环检测在无持久状态、不加 task_struct/rq 字段的情况下探测环。

## 技术方案
方案本身见 sched-20260915-009（Brent checkpoint/power/span 三段状态完全属于单次 `find_proxy_task()` 调用）。当天讨论不涉及新代码，聚焦两个设计问题：环检测的兜底（固定 max-depth 计数器 vs Brent 尽早检出）与错误语义（返回 `-EDEADLK`）。

## 版本演进与当前进展
RFC 仍为 v1（`<20260914165455.2126134-2-sh_def@163.com>`）。当天是维护者/社区三方首次对该 RFC 的实质评审，无新版发出。

## Maintainer 意见与讨论焦点
- **John Stultz**（proxy exec 主作者）：「Thanks for sending this out」，认为配上 Suleiman 的 futex 工作后环检测更关键；认同 Peter 此前提到的 max-depth 计数器仍是好兜底，但 Brent 能以几乎无开销尽早检出小环；他会把固定 `MAX_PROXY_CHAIN_DEPTH` 的简化版留在自己树里，并把这个 RFC 作为潜在优化纳入。
- **K Prateek Nayak**：提出关键设计问题——若最终要给用户态返回 `-EDEADLK`（context 指向 Peter 09-17 邮件），是否在乎环从哪条链开始检测，还是链上任意位置返回即可；并问 Brent 先收敛到链上某点再额外遍历找环起点是否可接受。
- **Peter Zijlstra**：明确「PI futex 和 rt_mutex 都已返回 -EDEADLK，鉴于 proxy 硬依赖 block 图无环，在暴露给用户态前强制检测 + 返回 -EDEADLK 几乎是必须的（rather mandatory）」。

## 合入评估
likelihood=unknown（本 RFC 本身仍待方向决策）。方向获得 John 与 Peter 认可（环检测必要），但尚未确定具体方案是否采纳，且 -EDEADLK 语义引入新的接口设计问题。blocking_issues：方案与「返回 -EDEADLK 到用户态」的结合方式未定；Brent 检出环起点是否满足错误语义未决。next_action：作者回应 K Prateek/ Peter 的 -EDEADLK 问题，明确环检测与用户态错误返回的接口。

## 效果评估
无本日新增数据；RFC 性能对比线索见 sched-20260915-009（正常无环路径 ns/call 在测试深度上与 v5 相当）。

## 我可以参与的点
- **review**：分析 K Prateek 提出的「-EDEADLK 需在链起点返回 vs 链上任意点返回」对 futex/rt_mutex 语义一致性的影响。
- **discussion**：讨论 Brent 环检测如何在满足错误返回位置语义与零持久状态之间取舍。

## 参考链接
- lore（RFC 1/1）: https://lore.kernel.org/all/20260914165455.2126134-2-sh_def@163.com/
- John Stultz 回复: https://lore.kernel.org/all/CANDhNCqZwGk+wqhB4N8Emq0rPmzsrVWzHmayiSj9ptg-vLzo3Q@mail.gmail.com/
- K Prateek 回复: https://lore.kernel.org/all/8669890e-c8a5-448e-b059-d959e3a1d73c@amd.com/
- Peter 回复: https://lore.kernel.org/all/20260922071816.GT4121339@noisy.programming.kicks-ass.net/

---
id: sched-20260922-012
date: '2026-09-22'
subject: 'sched/proxy_exec: detect cycles in proxy walks'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: '<20260914165455.2126134-2-sh_def@163.com>'
lore_url: 'https://lore.kernel.org/all/20260914165455.2126134-2-sh_def@163.com/'
authors:
  - 'Hui Su'
maintainers_involved:
  - 'Peter Zijlstra'
current_version: v1
patch_series:
  - version: RFC 1/1
    msgid: '<20260914165455.2126134-2-sh_def@163.com>'
    date: '2026-09-14'
    summary: 'Brent 环检测，无持久状态（见 sched-20260915-009）'
    review_outcome: 'John/K Prateek/Peter 三方评审，聚焦 -EDEADLK 语义'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - '环检测与返回 -EDEADLK 给用户态的接口语义未定'
  next_action: '作者回应 -EDEADLK 返回位置问题，明确方案与用户态错误返回的结合'
contribution_opportunities:
  - kind: review
    description: '分析 -EDEADLK 在链起点 vs 任意点返回对 futex/rt_mutex 语义一致性的影响'
  - kind: discussion
    description: '讨论 Brent 检测如何在错误返回位置语义与零持久状态间取舍'
generated_at: '2026-09-23T00:00:00'
source_email_count: 3
related_articles:
  - sched-20260915-009
  - sched-20260919-012
tags:
  - proxy_execution
  - deadline
---