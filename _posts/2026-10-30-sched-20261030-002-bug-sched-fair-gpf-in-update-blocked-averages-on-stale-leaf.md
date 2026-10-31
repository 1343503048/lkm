---
id: sched-20261030-002
date: 2026-10-30
subject: '[BUG] sched/fair: GPF in update_blocked_averages() on stale leaf cfs_rq
  of freed task_group (6.1.159)'
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: <20261030062237.849668-1-ajay.kaher@broadcom.com>
lore_url: https://lore.kernel.org/all/20261030062237.849668-1-ajay.kaher@broadcom.com/
authors:
- Ajay Kaher
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无 vmcore 与 reproducer，根因未定位
  - 未确认是否影响主线（报告基于 6.1.159 vendor 内核）
  next_action: 补充完整 oops/上下文，社区协助定位 list_add_leaf_cfs_rq 的 re-add 路径
contribution_opportunities:
- kind: discussion
  description: 审计 list_add_leaf_cfs_rq() 调用点，排查 teardown 后 re-add 濒死 group cfs_rq
    的路径
- kind: review
  description: 对照 6.1.159 与主线 unregister/free_fair_sched_group 差异，判断是否旧 bug 或 vendor
    改动
generated_at: '2026-10-31T09:00:00'
source_email_count: 1
related_articles: []
tags:
- cfs
- crash
title: '[BUG] sched/fair: GPF in update_blocked_averages() on stale leaf cfs_rq of
  freed task_group (6.1.159)'
layout: article
---

## TL;DR
Ajay Kaher（Broadcom）报告 6.1.159（Photon OS 5.0）内核在 `update_blocked_averages()` 里触发 general protection fault（疑似 use-after-free）：一个已被释放的 task_group 的 cfs_rq 仍挂在 `rq->leaf_cfs_rq_list` 上，`for_each_leaf_cfs_rq_safe()` 遍历到它时解引用 `cfs_rq->tg->se[cpu]` 拿到垃圾指针导致崩溃。无 vmcore、无复现脚本。作者怀疑存在一条「在 `unregister_fair_sched_group()` 之后又把濒死 group 的 cfs_rq 重新加回 leaf list」的路径。

## 背景与问题
崩溃栈（VMware 虚拟平台，swapper/7，非 tainted 6.1.159-9.ph5）：

```
RIP: 0010:update_blocked_averages+0x1b9/0x770
Call Trace: run_rebalance_domains -> handle_softirqs -> ... -> do_idle
Kernel panic - not syncing: Fatal exception in interrupt
```

反汇编定位到 `__update_blocked_fair()`（内联）：`mov rax,[rbx+0x150]` 取 `cfs_rq->tg`，`mov rax,[rax+0xc8]` 取 `tg->se`，`mov rsi,[rax+r14]`（R14=0x38=CPU7*8）取 `tg->se[cpu]`，随后 `cmp qword [rsi+0xe0],0`（`se->avg.load_avg`）时 RSI 已是垃圾值 `054a403b28017da0`。即：

```c
se = cfs_rq->tg->se[cpu];
if (se && !skip_blocked_update(se)) ...
```

`cfs_rq`（0xffff9e82b3d92e00）仍挂在 CPU7 的 leaf list，其 `cfs_rq->tg`/`tg->se` 看起来仍是合法内核地址，但 `tg->se[7]` 已指向被 `free_fair_sched_group()` 释放并复用的内存。

## 技术方案
（本文为 bug 报告，无补丁。）作者对既有 teardown 顺序 `sched_release_group() -> RCU -> unregister_fair_sched_group() -> RCU -> free_fair_sched_group()` 做了推演：该顺序本身应是安全的，除非有什么东西在 `unregister_fair_sched_group()` 之后又把濒死 group 的 cfs_rq 重新 `list_add_leaf_cfs_rq()` 加回 leaf list。`unregister_fair_sched_group()` 里的注释声称「只有空 group 才会被销毁，所以 `on_list` 可投机检查而无 re-add 风险」，实际移除在 rq->lock 下经 `list_del_leaf_cfs_rq()` 完成。作者怀疑存在绕开该假设的路径，正文因邮件被截断未给出完整嫌疑人，也未提出修复。

## 版本演进与当前进展
*current_version: 无*。当日首发 bug 报告，尚无任何维护者/社区回复，无修复补丁，无 vmcore 与 reproducer。

## Maintainer 意见与讨论焦点
当日无维护者表态。核心待澄清点：是否存在一条在 teardown 的 RCU 窗口内重新把 cfs_rq 加回 leaf list 的路径；以及该问题是否为 6.1 专属（vendor backport）还是同样影响主线。

## 合入评估
*likelihood=unknown*。无补丁、无复现、无维护者介入，无法判断合入走向。*blocking_issues*：无 vmcore 与 reproducer，根因未定位，甚至未确认是否影响主线。*next_action*：作者提供更完整 oops/更多上下文，或社区协助定位 re-add 路径；先确认主线是否可复现。

## 效果评估
暂无效果数据。崩溃为 `Fatal exception in interrupt` 导致内核 panic，严重度高，但仅单个报告、无复现。

## 我可以参与的点
- **discussion**：结合主线代码（`/home/zq/code/linux`）审计 `list_add_leaf_cfs_rq()` 的所有调用点，排查是否存在「teardown 之后仍可能 re-add 濒死 group cfs_rq」的路径。
- **review**：对照 6.1.159 与主线 `unregister_fair_sched_group()`/`free_fair_sched_group()` 的差异，判断是否为已修复的旧 bug 或 vendor 特有改动引入。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261030062237.849668-1-ajay.kaher@broadcom.com/
