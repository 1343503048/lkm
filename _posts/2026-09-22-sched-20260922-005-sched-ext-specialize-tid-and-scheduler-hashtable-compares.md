---
id: sched-20260922-005
date: '2026-09-22'
subject: 'sched_ext: Specialize TID and scheduler hashtable compares'
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: <20260921185943.4031480-1-usama.arif@linux.dev>
lore_url: https://lore.kernel.org/all/20260921185943.4031480-1-usama.arif@linux.dev/
authors:
- Usama Arif
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20260921185943.4031480-1-usama.arif@linux.dev>
  date: '2026-09-22'
  summary: 为 scx_tid_hash/scx_sched_hash 提供专用比较，折叠为单次 u64 比较
  review_outcome: Tejun 合入 sched_ext/for-7.4；bpf-ci 建议可选宏重构
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.4
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入；bpf-ci 宏重构建议为可选后续
contribution_opportunities:
- kind: testing
  description: 在 sched_ext 调度器上验证 tid→task 反查与 sub-sched 路径无回退
- kind: discussion
  description: 回应 bpf-ci 关于用生成宏合并两处比较函数的建议
generated_at: '2026-09-23T00:00:00'
source_email_count: 4
related_articles:
- sched-20260922-004
tags:
- sched_ext
- perf
title: 'sched_ext: Specialize TID and scheduler hashtable compares'
layout: article
---

## TL;DR
Usama Arif 为 sched_ext 的 TID 与 scheduler 两张 rhashtable 提供专用比较回调，把 `scx_bpf_tid_to_task()`（热路径，用于 tid→task 反查）和 `scx_find_sub_sched()`（被子调度器 dispatch 与管理 kfunc 调用）上的泛型 `rhashtable_compare()`/`memcmp()` 折叠为编译期单次 u64 比较。这是 DSQ hashtable（见 sched-20260922-004）的跟进。Tejun Heo 已把 1-2 合入 `sched_ext/for-7.4`。bpf-ci 的 AI review 建议两处比较函数可用生成宏合并。

## 背景与问题
`scx_tid_hash` 与 `scx_sched_hash` 都用自然对齐的 u64 key，但没提供 `obj_cmpfn`，导致 rhashtable 在每次查找时回落 `rhashtable_compare()`：`memcmp(ptr + ht->p.key_offset, arg->key, ht->p.key_len)`。虽只比 8 字节，但泛型路径在运行时加载 offset/length 并 emit out-of-line `memcmp()`。`scx_bpf_tid_to_task()` 与 `scx_find_sub_sched()` 都可能出现在调度热路径上。

## 技术方案
第一补丁为 `scx_tid_hash` 加专用比较，把 `scx_bpf_tid_to_task()` 的比较变成对 `scx->tid` 的直接等值测试（也覆盖插入时的重复检查）。第二补丁为 `scx_sched_hash` 加比较，把 `scx_find_sub_sched()` 的比较变成对 `ops.sub_cgroup_id` 的直接比较。两处 const 参数使编译器内联回调、每次对象比较退化为单次 u64 比较；disassembly 确认查找循环不再调 `memcmp()` 或 out-of-line 比较器。`kernel/sched/ext/ext.c` 新增 22 行，无功能变化。

## 版本演进与当前进展
v1（`<20260921185943.4031480-1-usama.arif@linux.dev>`）当日发出。Tejun 回帖已合入 1-2 到 `sched_ext/for-7.4`（把 `scx_tid_cmpfn()` 签名并到一行）。

## Maintainer 意见与讨论焦点
- **Tejun Heo**：合入无异议。
- **bpf-ci AI review**（bot+bpf-ci）：指 `scx_sched_cmpfn()` 与 `scx_tid_cmpfn()` 只差容器类型与字段，问是否用小生成宏合并更清晰，还是两处拼写出来更直白。此为风格建议，未阻塞合入。

## 合入评估
*likelihood=merged*。已合入 `sched_ext/for-7.4`。blocking_issues 无；bpf-ci 的宏建议属可选后续。

## 效果评估
作者在 cover 声明无功能变化（No functional change intended），编译产物确认查找循环不再 call `memcmp()` 或 out-of-line 比较器；未给出独立 benchmark 数字（收益与 DSQ 系列同类，见 sched-20260922-004 的 2.9x 数据）。

## 我可以参与的点
- **testing**：在基于 sched_ext 的调度器上验证 tid→task 反查与 sub-sched 查找路径无功能/性能回退。
- **discussion**：回应 bpf-ci 的宏重构建议（是否值得为两处比较引入生成宏）。

## 参考链接
- lore thread: https://lore.kernel.org/all/20260921185943.4031480-1-usama.arif@linux.dev/
