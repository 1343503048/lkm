# sched_ext: sub-scheduler kfuncs use struct scx_sched beyond the RCU read side under sleepable ops

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261024-008：Guikun Yang 报告的潜在 RCU use-after-free——四个子调度器 kfunc（`scx_bpf_sub_grant/sub_revoke/sub_caps/sub_kill_bstr`）经 `scx_find_sub_sched()` 拿到 `struct scx_sched *` 后，只持 `guard(irqsave)`、不持 RCU read lock 就全程解引用。
- sched-20261027-012（今天）：sched_ext 维护者 Tejun Heo 详细回应「**这里没有 use-after-free**」，指出报告的误读点（`rhashtable_lookup()` vs `_fast` 变体、irq-disabled 区域自 v5.0 起即属 RCU read-side），报告关闭。

## 背景与问题
（承接 20261024-008）报告者担心四个 kfunc 在 sleepable struct_ops 的 teardown 窗口内使用已释放的 `struct scx_sched`。核心误读：报告认为 `scx_find_sub_sched()` 是 `rhashtable_lookup()` 的 `_fast` 变体（自取自释 RCU lock），并据此推断调用者必须自己处在 RCU read-side 临界区。

## 技术方案
非补丁。Tejun Heo 逐一澄清：`rhashtable_lookup()`（非 `_fast`）要求调用者处于 RCU read-side 临界区，而 `scx_bpf_sub_grant/sub_revoke/sub_caps` 在 lookup 前都持 `guard(irqsave)`、lookup 与对 child 的全部使用都在 irq-disabled 区域内——自 v5.0 起「irq 关闭区域就是 RCU read-side 临界区」，`synchronize_rcu()`/`call_rcu()` 都会等待它；`scx_bpf_sub_kill_bstr()` 则显式持 `guard(rcu)`。`scx_unlink_sched()` 在最后引用释放前已把 sched 从哈希移除，`scx_kobj_release()` 经 `queue_rcu_work()` 释放，grace period 先于 free。故无 UAF。

## 版本演进与当前进展
*current_version: 无*（bug 报告，无补丁）。维护者已定性为非问题，线程实质关闭。

## Maintainer 意见与讨论焦点
Tejun Heo（sched_ext 维护者）明确「There's no use-after-free here」，并从 RCU 语义层面给出完整论证。无争议残留。

## 合入评估
*likelihood=unknown*（非补丁，无合入对象）。*blocking_issues*：无。*next_action*：无须动作，报告已由维护者释疑关闭。

## 效果评估
无。属误报澄清。

## 我可以参与的点
当前阶段暂无明显参与空间（误报已澄清）。可留意：若报告者后续找到真正的 teardown 竞态，可再跟进。

## 参考链接
- 线程: https://lore.kernel.org/all/tencent_572AA31E5369BE41464E9DDA4CEDA2DA7C09@qq.com/

---
id: sched-20261027-012
date: 2026-10-27
subject: 'sched_ext: sub-scheduler kfuncs use struct scx_sched beyond the RCU read side under sleepable ops'
subsystem: sched
type: discussion
status: under_review
severity: none
thread_root_msgid: '<tencent_572AA31E5369BE41464E9DDA4CEDA2DA7C09@qq.com>'
lore_url: 'https://lore.kernel.org/all/tencent_572AA31E5369BE41464E9DDA4CEDA2DA7C09@qq.com/'
authors:
  - 'Guikun Yang'
maintainers_involved:
  - 'Tejun Heo'
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: '无须动作，误报已由维护者释疑关闭'
contribution_opportunities: []
generated_at: '2026-10-28T09:00:00'
source_email_count: 1
related_articles:
  - sched-20261024-008
tags:
  - sched_ext
---