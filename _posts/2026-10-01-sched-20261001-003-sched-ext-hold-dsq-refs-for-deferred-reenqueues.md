---
id: sched-20261001-003
date: '2026-10-01'
subject: 'sched_ext: Hold DSQ refs for deferred reenqueues'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20260930101722.2468434-1-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20260930101722.2468434-1-sh_def@163.com/
authors:
- Hui Su
maintainers_involved:
- Tejun Heo
- Andrea Righi
current_version: v1
patch_series:
- version: v1
  msgid: <20260930101722.2468434-1-sh_def@163.com>
  date: '2026-09-30'
  summary: 在 detach 节点前先取 DSQ 引用，回调与 deferred 路径各自释放，防 deferred reenqueue 的 UAF
  review_outcome: Andrea 认可 race 并建议引用管理优化；10-01 Tejun 要求改为无 refcnt 方案
upstream_commit: null
fixes_commit: 84b1a0ea0b7c
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - Tejun 要求的无 refcnt 方案尚未实现，当前 v1 机制需重做
  - 复现测试/步骤尚未附上（Andrea 请求）
  next_action: 按无引用计数思路重构并附复现测试后发 v2
contribution_opportunities:
- kind: review
  description: 参与无 refcnt 的 deferred reenqueue 生命周期设计讨论（销毁路径 full 检测与等待）
- kind: testing
  description: 帮助构造用户 DSQ + dsq_reenq 竞态复现测试供社区验证
generated_at: '2026-10-09T01:00:00'
source_email_count: 1
related_articles:
- sched-20260930-002
tags:
- sched_ext
title: 'sched_ext: Hold DSQ refs for deferred reenqueues'
layout: article
---

> **subject**：`sched_ext: Hold DSQ refs for deferred reenqueues`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-002-sched-ext-hold-dsq-refs-for-deferred-reenqueues.html">sched-20260930-002</a>：Hui Su 的 sched_ext use-after-free 修复——`scx_bpf_dsq_reenq()` 的 deferred reenqueue 路径上，被 deferral 的用户 DSQ 节点可能在 RCU 回调 `exit_dsq()` 到达前被 detach，deferred 路径随后继续用裸 DSQ 指针，回调可能先释放 DSQ，导致 KASAN 报 slab-use-after-free（`run_deferred` 中）。补丁在 `deferred_reenq_lock` 下 detach 节点前先取引用、两侧各自释放，带 `Fixes: 84b1a0ea0b7c` 与 `Cc: stable # v7.1+`；Andrea Righi 认可 race 属实，但建议避免反复排队 RCU 回调地持引用，作者尚未回应。
- <a class="article-ref" href="/lkm/2026/10/01/sched-20261001-003-sched-ext-hold-dsq-refs-for-deferred-reenqueues.html">sched-20261001-003</a>（今天）：Tejun Heo（sched_ext 顶层维护者）直接回复，请作者尝试**完全不用引用计数**的实现——「DSQ destructions are rare events and we can reliably detect whether the DSQ is full or not. I'd much rather make the destruction path expensive than adding refcnt to hot paths.」即宁可让销毁路径变贵，也不往热路径加 refcnt。当前补丁的核心机制被维护者质疑，需要重做。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-002-sched-ext-hold-dsq-refs-for-deferred-reenqueues.html">sched-20260930-002</a>）用户 DSQ 的 deferred reenqueue 机制（`scx_bpf_dsq_reenq()`，引入于 84b1a0ea0b7c）下，被 defer 的用户 DSQ 节点可在 RCU 回调到达 `exit_dsq()` 之前就被 `process_deferred_reenq_users()` detach 走；一旦 detach，`exit_dsq()` 找不到该节点，而 deferred 路径在放弃 `deferred_reenq_lock` 之后仍使用裸 DSQ 指针（检查其 ID、调用 `reenq_user()`），回调可能先释放 DSQ。KASAN 回归测试在 pre-fix 内核上报 `BUG: KASAN: slab-use-after-free in run_deferred+0x1312/0x1710`。今天背景无新增，进展是顶层维护者对修复**方式**给出明确架构偏好。

## 技术方案

（承接）v1 补丁：在 `deferred_reenq_lock` 保护下、detach 节点之前先取 DSQ 引用；RCU 回调在 `exit_dsq()` 之后放弃基础引用，deferred 路径在最后一次访问 DSQ 之后放弃自己的引用，保证对象存活到所有 detach 后的 reenqueue 完成；补丁内核跑同一回归测试无 KASAN 报告。

今天 Tejun 的替代方向（未附代码）：DSQ 销毁是罕见事件、且能可靠检测 DSQ 是否已满（full），把开销移到销毁路径（如销毁时同步等待/重试）而非在热路径维护引用计数。具体实现待作者探索。

## 版本演进与当前进展

- v1（09-30，`<20260930101722.2468434-1-sh_def@163.com>`）：detach 前取引用、两侧各释放；Andrea 认可 race、建议引用管理优化并请提供复现测试。
- 10-01：Tejun 回复（`<ar1DqN6Ek2VwYLwO@slm.duckdns.org>`），要求探索无 refcnt 方案。作者尚无回应。

## Maintainer 意见与讨论焦点

- **Tejun Heo**（sched_ext 顶层维护者）：「Can you try to do it without refcnts? DSQ destructions are rare events and we can reliably detect whether the DSQ is full or not. I'd much rather make the destruction path expensive than adding refcnt to hot paths.」——对当前 refcnt 设计的架构性否定，倾向「销毁路径昂贵化 + full 检测」。
- **Andrea Righi**（sched_ext 维护者，09-30）：认可 race 属实；建议避免「detached reenqueue 持引用期间反复排队 RCU 回调」，提议首个回调即放弃基础引用、由最后释放引用的一侧安排 free。
- 两位维护者的共同点：认可 bug、反对当前引用管理粒度；分歧细节（Andrea 仍是「改进 refcnt 生命周期」、Tejun 干脆「去掉 refcnt」）需要作者提出统一方案。
- 无 NAK，但当前 v1 机制按 Tejun 意见需重做。

## 合入评估

*likelihood=low*。UAF 是真实的 memory-safety bug（KASAN 复现、带 `Fixes:`/`Cc: stable`），修复必然会以某种形态落地；但顶层维护者明确反对往热路径加引用计数，当前 v1 的核心机制需要按「无 refcnt、销毁路径昂贵化」重做，本版难以直接合入。*blocking_issues*：Tejun 的无 refcnt 方案尚未实现；Andrea 09-30 的两个请求（复现测试、引用管理优化）也仍待回应。*next_action*：作者按无引用计数思路重构（销毁路径同步化/DSQ full 检测）、附复现测试后发 v2，再请 Tejun/Andrea 复审。

## 效果评估

本日无新数据。既有证据（09-30）：pre-fix 内核 KASAN 报 `slab-use-after-free in run_deferred`（`swapper/3/0` 读取 8 字节于 `ffff8880087009b0`，经 `run_deferred → ttwu_do_activate → try_to_wake_up`）；修复后同一测试无 KASAN 报告。Tejun 建议的「销毁路径昂贵化」尚无性能权衡数据（销毁是罕见事件，预期开销可忽略，但未见测量）。

## 我可以参与的点

- `review`：设计层面参与「无 refcnt 的 deferred reenqueue 生命周期」讨论——销毁路径如何可靠检测「DSQ full（还有 in-flight reenqueue）」并安全等待，是否有比 Tejun 设想更简单的同步原语。
- `testing`：按 Andrea 的请求帮助构造可复现测试（用户 DSQ + `scx_bpf_dsq_reenq()` 的竞态场景），供社区验证两个方案。

## 参考链接

- Tejun 的回复: https://lore.kernel.org/all/ar1DqN6Ek2VwYLwO@slm.duckdns.org/
- v1 补丁: https://lore.kernel.org/all/20260930101722.2468434-1-sh_def@163.com/
- Andrea 的回复: https://lore.kernel.org/all/ar0qLeKls0oBUEKO@gpd4/
