---
id: sched-20260915-004
date: '2026-09-15'
subject: 'sched/cache: Introduce infrastructure for cache-aware load balancing'
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: <cover.1775065312.git.tim.c.chen@linux.intel.com>
lore_url: https://lore.kernel.org/all/343a7e07-7fad-4979-9c9b-82ec038c293c@linux.dev/
authors:
- Tim Chen
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: df0d98475954
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - Zenghui 内联修复未经评审
  - Tim 未确认其 4 补丁系列是否覆盖远端 CPU 跨写路径
  next_action: Zenghui 与 Tim 对齐修复路径（内联修 vs 采用 4 补丁系列）并确认覆盖远端记账场景
contribution_opportunities:
- kind: review
  description: 核对 p != current 修复是否遗漏其它远端解引用 rq->curr->mm 的调用点
- kind: testing
  description: 在 SLUB_DEBUG 下跑 exec/exit 压力负载，验证内联修复或 Tim 4 补丁系列能否消除 Poison overwritten
generated_at: '2026-09-16T01:05:00'
source_email_count: 2
related_articles:
- sched-20260902-003
- sched-20260901-001
- sched-20260914-004
tags:
- load_balance
- crash
title: 'sched/cache: Introduce infrastructure for cache-aware load balancing'
layout: article
---

## TL;DR
本文为增量更新（完整背景见 related_articles）。09-15 Zenghui Yu（Huawei）在跑 mm-new 时命中 SLUB「Poison overwritten」——4 字节 0xffffffff 覆写，定位到 `account_mm_sched()` 在远端 CPU 上解引用 `rq->curr->mm` 并写 `mm->sc_stat.cpu = -1` 的 use-after-free，附上「只在 `p == current` 时才记账」的内联修复（Fixes: df0d98475954）。Tim Chen 回复称这是同一 UAF 问题，指路其 4 补丁系列的综合修复。修复本身尚无评审。

## 背景与问题
`account_mm_sched()` 对 `rq->curr` 记账并解引用其 `->mm`：更新 per-cpu 块 `mm->sc_stat.pcpu_sched`，还可能写 `mm->sc_stat.cpu = -1`。采样 `rq->curr` 并调用它的 `update_se()` 不只来自本地上下文（tick、context switch），还通过 `update_curr()` 来自 enqueue/dequeue 路径——这些常在远端 CPU 上运行、持着本 rq 的锁（跨 CPU 的 `try_to_wake_up()`、负载均衡）。rq 锁只能保证 `rq->curr` 身份不变，管不住其 `->mm` 的生命周期：该任务无需 rq 锁即可 execve/exit，在 `task_lock()`/`mmput()` 下换掉并释放 `->mm`。远端 CPU 因此可能在 `->mm` 被释放前采样到有效指针、释放后才写入，破坏已释放的 mm_struct（以及更早被 `mm_destroy_sched()` 释放的 pcpu_sched per-cpu 块）。观察手段为 `CONFIG_SLUB_DEBUG=y` 下偶发的 mm_struct 缓存「Poison overwritten」报告，覆写字节落在 `&mm->sc_stat.cpu`（offset 51432-50752=680，`0xffffffff` 即 -1）。

## 技术方案
Zenghui 内联补丁（kernel/sched/fair.c，+3 行）：在 `account_mm_sched()` 入口加 `if (p != current) return;`——只对物理上正在运行的任务记账，其 `->mm` 在执行期间不会消失。本地 tick、context switch、`sched_ttwu_pending()` 路径不受影响；远端上下文跳过的更新只造成 sc_stat runtime 启发式的轻微少计。Fixes: `df0d98475954 ("sched/cache: Introduce infrastructure for cache-aware load balancing")`。

Tim Chen 的回应指向其 4 补丁系列（cover `cover.1789061845`），称「最后两个补丁以更全面的方式解决该 use-after-free 问题」（此前曾在一个线程里讨论过，见 `apPb-Dr4nPYuHQOK@v4bel`）。

## 版本演进与当前进展
本日为对 Tim Chen v4 22 补丁基础设施系列（cover `cover.1775065312`）的 bug 报告与修复提议。Zenghui 的修复是首次针对「远端 CPU 跨写」这一具体失效路径的内联方案；Tim 未直接评审该补丁，而是引导到其更全面的 4 补丁修复系列。尚无新版或 Ack。

## Maintainer 意见与讨论焦点
- **Zenghui Yu (Huawei)**：报告 SLUB Poison overwritten 并给出 `p != current` 内联修复，标注 `Assisted-by: GLM-5.3 OpenCode`。
- **Tim Chen (Intel)**：认为命中的是同一 UAF，建议改试其 4 补丁系列的综合修复。
- 潜在分歧/未决点：Zenghui 的最小化「只记账当前任务」方案 vs Tim 的「引用计数 + call_rcu 的 sched_cache_group」综合方案（见 related_articles），两者未在当日直接交锋。

## 合入评估
likelihood=unknown。修复方向未收敛（内联最小修 vs 综合 refcount 重构），当日无人 Ack。blocking_issues：Zenghui 内联修复未经评审；Tim 未确认其 4 补丁系列是否覆盖「远端 CPU 跨写」路径。next_action：Zenghui 与 Tim 对齐修复路径（内联修 vs 采用/补齐 4 补丁系列），并确认覆盖远端记账场景。

## 效果评估
Zenghui 报告的具体现象：`[Poison overwritten] 0xffff8001076ec8e8... First byte 0xff instead of 0x6b`，`BUG mm_struct (Tainted: G N): Object corrupt`，allocated in `copy_process`、freed in `__mmdrop`，覆写恒为 4 字节 `0xffffffff`（-1），四周 poison 完好。这是明确的 memory corruption 证据，非性能数据。

## 我可以参与的点
- kind=review：核对 Zenghui 的 `p != current` 修复是否遗漏其它远端解引用 `rq->curr->mm` 的调用点（如负载均衡谓词读取远端任务 `p->mm` 的路径）。
- kind=testing：在 `CONFIG_SLUB_DEBUG=y` 下跑 exec/exit 压力负载，验证内联修复或 Tim 4 补丁系列能否消除 Poison overwritten。

## 参考链接
- Zenghui 报告与内联修复：https://lore.kernel.org/all/343a7e07-7fad-4979-9c9b-82ec038c293c@linux.dev/
- Tim Chen 回复：https://lore.kernel.org/all/eb77a9a6b27940f1ae9acc0b87f75f3b46f28a13.camel@linux.intel.com/
- Tim Chen 4 补丁系列 cover：https://lore.kernel.org/all/cover.1789061845.git.tim.c.chen@linux.intel.com/
