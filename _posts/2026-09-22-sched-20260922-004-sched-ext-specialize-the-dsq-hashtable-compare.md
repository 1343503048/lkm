---
id: sched-20260922-004
date: '2026-09-22'
subject: 'sched_ext: Specialize the DSQ hashtable compare'
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: <20260921171928.1639407-1-usama.arif@linux.dev>
lore_url: https://lore.kernel.org/all/20260921171928.1639407-1-usama.arif@linux.dev/
authors:
- Usama Arif
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20260921171928.1639407-1-usama.arif@linux.dev>
  date: '2026-09-22'
  summary: 为 dsq_hash 提供 obj_cmpfn，编译期折叠为单次 u64 等值比较
  review_outcome: Tejun 合入 sched_ext/for-7.4，并建议 TID/scheduler 同类优化
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.4
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入，无后续动作
contribution_opportunities:
- kind: testing
  description: 在自建 sched_ext 调度器多 DSQ 场景验证性能无回退
- kind: extend
  description: 发现 sched_ext 内其它同构 rhashtable 热点可继续提同类补丁
generated_at: '2026-09-23T00:00:00'
source_email_count: 3
related_articles: []
tags:
- sched_ext
- perf
title: 'sched_ext: Specialize the DSQ hashtable compare'
layout: article
---

## TL;DR
Usama Arif 为 sched_ext 的 DSQ（dispatch queue）哈希表补上 `obj_cmpfn`，把 `find_user_dsq()` 热路径上的泛型 `rhashtable_compare()`（运行时读 offset/length 再 out-of-line `memcmp` 8 字节）折叠成编译期对 `dsq->id` 的单次 u64 比较。作者在 Meta 机群 A/B 实测该查找快 2.9x。Tejun Heo 已合入 `sched_ext/for-7.4`，并建议对 TID/scheduler 哈希表做同样处理（已由作者以 0/2 系列跟进）。

## 背景与问题
`rhashtable` 是泛型容器，不感知 key 形状：`dsq_hash_params` 只声明了 `key_len/key_offset/head_offset`，查找回落到 `rhashtable_compare()`，每次比较都要在运行时把 offset 和 length 从 `ht->p` 读出，对每个遍历元素发出 out-of-line `memcmp()`——两次加载、一次调用、一次长度分发，只为比较 8 字节，解释开销比比较本身还大。`find_user_dsq()` 位于 `__schedule()` 路径，且 `scx_layered` 每次 dispatch 决策都调用 `scx_bpf_dsq_nr_queued()`，在 Meta 机群上该查找有显著成本并出现在全机群 profile 中。

## 技术方案
提供 `obj_cmpfn`：`dsq_hash_params` 是 const 对象、按值传入 `__always_inline __rhashtable_lookup()`，故 `params.obj_cmpfn` 是编译期常量，三元选择被折叠、回调内联，比较退化为对 `dsq->id` 的单次 `cmp`。因结果只被测试是否为零，`memcmp` 附带的全序语义从未被观测，故可安全用等值比较替代。`kernel/sched/ext/ext.c` 新增 11 行。

## 版本演进与当前进展
v1 当日发出，附 A/B 数据。Tejun Heo 回帖已合入 `sched_ext/for-7.4`（仅把 `dsq_cmpfn()` 签名并到一行），并指出 `scx_tid_hash`/`scx_sched_hash` 同为 u64 key、同样回落 `rhashtable_compare()`，且 `scx_bpf_tid_to_task()` 也在热路径，问是否做相同处理——作者回复「Yes, let me send those as follow-ups!」（已由当日另一 0/2 系列跟进）。

## Maintainer 意见与讨论焦点
- **Tejun Heo**：合入无异议，并主动提示 TID/scheduler 两处同类优化点。无争议。

## 合入评估
*likelihood=merged*。已合入 `sched_ext/for-7.4`。blocking_issues 无。

## 效果评估
作者给出实测数据：在 Meta 机群对 `scx_layered` 创建的 DSQ id 做内核内 A/B（两组参数编进同一内核），查找快 **2.9x**；disassembly 确认查找循环不再调用 `memcmp()` 或 out-of-line 比较器。无功能变化（No functional change intended）。

## 我可以参与的点
- **testing**：在自建 sched_ext 调度器（尤其多 DSQ 场景）上验证查找行为与性能无回退。
- **extend**：TID/scheduler 哈希表特化已由作者跟进，若发现 sched_ext 内其它 rhashtable 同构热点可继续提同类补丁。

## 参考链接
- lore thread: https://lore.kernel.org/all/20260921171928.1639407-1-usama.arif@linux.dev/
