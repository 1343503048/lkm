---
id: sched-20261023-013
date: 2026-10-23
subject: 'sched/cache: Honor asym packing over cache aware scheduling on hybrid systems'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <221f8b0345328c4b26b65daff4d3eec56a32b06d.1790617047.git.tim.c.chen@linux.intel.com>
lore_url: https://lore.kernel.org/all/221f8b0345328c4b26b65daff4d3eec56a32b06d.1790617047.git.tim.c.chen@linux.intel.com/
authors:
- Tim Chen
maintainers_involved:
- Peter Zijlstra
- Kayra Cizmeci
current_version: v3
patch_series:
- version: v3
  msgid: <b29badede27bb6bfb4a759e06754cb19657f0778.1791308631.git.tim.c.chen@linux.intel.com>
  date: 2026-10-08
  summary: 移除冗余 SD_ASYM_PACKING 检查，用 group_asym_packing；asym 判断提前
  review_outcome: Kayra Reviewed-by + Chen Yu Tested-by；等 Peter 收取
upstream_commit: null
fixes_commit: 23b2b5ccc45c
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - Peter 尚未对 v3 明确表态可收取
  next_action: 等 Peter 收取进 sched/urgent 或 tip
contribution_opportunities:
- kind: testing
  description: 在真实 hybrid 平台复测 cache 密集构建负载，确认修复收益
generated_at: '2026-10-24T09:12:00'
source_email_count: 1
related_articles:
- sched-20261006-002
- sched-20261008-011
tags:
- topology
- load_balance
- regression
- x86
title: 'sched/cache: Honor asym packing over cache aware scheduling on hybrid systems'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/10/06/sched-20261006-002-sched-cache-honor-asym-packing-over-cache-aware-scheduling-o.html">sched-20261006-002</a>：Tim Chen 针对「cache-aware 调度在 AMD big/little 混合平台性能回退」的修复——让 asym packing 在「要把任务迁到更高优先级空核」时优先于 cache-aware；v2 把 `can_migrate_llc_task()` 的放行条件落成 `env->idle && sched_asym(...)`，并在 `llc_balance()` 加 `SD_ASYM_PACKING + group_asym_packing` 检查。当日 Kayra `Reviewed-by`（顺带指出显式 `SD_ASYM_PACKING` 检查冗余）、Chen Yu 用 AMD Ryzen 9 8945HX 仿真出 hybrid 实测——补丁前 cache-aware ON 吞吐 -56.6%、补丁后与 OFF 持平（+1.5%）。
- <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-011-sched-cache-honor-asym-packing-over-cache-aware-scheduling-o.html">sched-20261008-011</a>：v3 发出——按 Kayra 意见移除冗余 `SD_ASYM_PACKING` 检查、改用 `sgs->group_asym_packing`，并把 `need_active_balance()` 的 asym 判断提前；新增 Chen Yu `Tested-by` 与 Kayra `Reviewed-by`。此时三位测试者背书、仍等 Peter 收取进 sched/urgent。
- <a class="article-ref" href="/lkm/2026/10/23/sched-20261023-013-sched-cache-honor-asym-packing-over-cache-aware-scheduling-o.html">sched-20261023-013</a>（今天）：Tim Chen 向 Peter 发 ping——「A quick ping on this patch. Do you think it is ready to be applied?」。无新代码，进度仍在等 Peter 给出可收取的明确表态。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-003-sched-cache-honor-asym-packing-over-cache-aware-scheduling-o.html">sched-20260929-003</a> → <a class="article-ref" href="/lkm/2026/10/06/sched-20261006-002-sched-cache-honor-asym-packing-over-cache-aware-scheduling-o.html">sched-20261006-002</a> → <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-011-sched-cache-honor-asym-packing-over-cache-aware-scheduling-o.html">sched-20261008-011</a>）回归场景：AMD Ryzen AI HX 370 上跑 cache 密集的 Clang full-LTO 链接，小核频率低得多（3.3 vs 5.1 GHz）、L3 只有一半（8 vs 16 MB），cache-aware 调度把任务钉到小核 LLC 双重受损、构建显著变慢。冲突根源是 asym packing（要最高优先级 CPU）与 cache-aware（要共置到同一 LLC、不论优先级）表达相反策略。今天无新背景，属收口等待。

## 技术方案
（承接 + 今日无代码）`kernel/sched/fair.c` 三处让 asym packing 在 hybrid 上优先于 cache-aware：`can_migrate_llc_task()` 在进入「too many threads / exceed LLC capacity」检查前先判 `env->idle && sched_asym(...)`；`llc_balance()` 上 asym packing 域若目的 CPU 优先级高于源组（`sgs->group_asym_packing`）则 `return false`；`need_active_balance()` 把 `asym_active_balance()` 判断提到 `alb_break_llc()` 之前。v3 已移除冗余 `SD_ASYM_PACKING` 检查。今日无改动，仅维护者 ping。

## 版本演进与当前进展
*current_version: v3*（v3 patch `<b29badede27bb6bfb4a759e06754cb19657f0778.1791308631.git.tim.c.chen@linux.intel.com>`）。当日无新版本，作者向 Peter 发 ping 催问是否可收取。

## Maintainer 意见与讨论焦点
Tim Chen 今日向 Peter Zijlstra 明确 ping：「Do you think it is ready to be applied?」——暗示 review 侧（Kayra Reviewed-by、Chen Yu/Klaus Kusche Tested-by）已无遗留问题，卡点只剩维护者 Peter 的最终收取动作。截止当日缓存未见 Peter 的回应。此前 Kayra 曾对其余细节（`llc_balance()` 冗余检查）提过意见并已在 v3 落实。

## 合入评估
*likelihood=high*。回归修复、带 `Fixes: 23b2b5ccc45c` + `Reported-by` + `Cc: stable #7.2.x`，三位测试者背书、Kayra Reviewed-by，v3 已收敛完所有 review 意见。*blocking_issues*：Peter 尚未对 v3 给出「可收取」的明确表态。*next_action*：等 Peter 收取进 sched/urgent（或 tip），必要时作者再次 ping 或补 `stable` 收尾。

## 效果评估
既有数据延续（Chen Yu，AMD Ryzen 9 8945HX 仿真 hybrid）：补丁前 cache-aware ON 使吞吐 **-56.6%**（8 线程中 6 个困在 LLC1），补丁后回到与 cache-aware OFF 持平（**+1.5%**，噪声内）。今日无新数据。

## 我可以参与的点
- *kind: testing*：在真实 AMD/Intel hybrid 平台（而非仿真）复测 cache 密集构建负载，确认修复收益与无明显回归。

## 参考链接
- Tim Chen ping: https://lore.kernel.org/all/93c4de9a3c86e0d00808fd7045b385a5a7069e4d.camel@linux.intel.com/
- v3 patch: https://lore.kernel.org/all/b29badede27bb6bfb4a759e06754cb19657f0778.1791308631.git.tim.c.chen@linux.intel.com/
- 前文: <a class="article-ref" href="/lkm/2026/10/06/sched-20261006-002-sched-cache-honor-asym-packing-over-cache-aware-scheduling-o.html">sched-20261006-002</a> / <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-011-sched-cache-honor-asym-packing-over-cache-aware-scheduling-o.html">sched-20261008-011</a>
