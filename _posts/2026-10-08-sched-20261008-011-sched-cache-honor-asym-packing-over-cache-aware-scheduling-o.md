---
id: sched-20261008-011
subject: 'sched/cache: Honor asym packing over cache aware scheduling on hybrid systems'
date: '2026-10-08'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <b29badede27bb6bfb4a759e06754cb19657f0778.1791308631.git.tim.c.chen@linux.intel.com>
lore_url: https://lore.kernel.org/all/b29badede27bb6bfb4a759e06754cb19657f0778.1791308631.git.tim.c.chen@linux.intel.com/
authors:
- Tim Chen
maintainers_involved: []
current_version: v3
patch_series:
- version: v1
  msgid: <221f8b0345328c4b26b65daff4d3eec56a32b06d.1790617047.git.tim.c.chen@linux.intel.com>
  date: '2026-09-29'
  summary: can_migrate_llc_task()/llc_balance() 让 asym packing 优先于 cache-aware
  review_outcome: Kayra 指出注释/实现语义不一致并给边界反例
- version: v2
  msgid: null
  date: null
  summary: 空窗期（无日报）内发出，msgid 见 v3 的 Link v2
  review_outcome: null
- version: v3
  msgid: <b29badede27bb6bfb4a759e06754cb19657f0778.1791308631.git.tim.c.chen@linux.intel.com>
  date: '2026-10-08'
  summary: 移除冗余 SD_ASYM_PACKING 检查改用 group_asym_packing；收齐三 Tested-by + Reviewed-by
  review_outcome: 待维护者收取进 sched/urgent
upstream_commit: null
fixes_commit: 23b2b5ccc45c
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 尚无 Peter/Ingo 收取或 tip 合入通告
  next_action: 等维护者收取进 sched/urgent，随后回合 stable 7.2.x
contribution_opportunities:
- kind: review
  description: 复核 group_asym_packing 替代后是否覆盖 Kayra 的边界反例
- kind: testing
  description: big/little + cache-aware 平台验证编译回归消失且无新 LLC 抖动
generated_at: '2026-10-09T01:00:00'
source_email_count: 1
related_articles:
- sched-20260929-003
tags:
- load_balance
- x86
- regression
title: 'sched/cache: Honor asym packing over cache aware scheduling on hybrid systems'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-003-sched-cache-honor-asym-packing-over-cache-aware-scheduling-o.html">sched-20260929-003</a>：Tim Chen 针对 cache-aware 调度在 AMD big/little 平台的性能回退发修复——asym packing 想放任务到最高优先级 CPU、cache-aware 想共置同进程任务到同一 LLC，二者相反；补丁让 asym packing 在「迁往优先级更高的空核」时优先于 cache-aware。带 `Fixes:` + 双 `Tested-by` + `Cc: stable # 7.2.x`。
- <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-011-sched-cache-honor-asym-packing-over-cache-aware-scheduling-o.html">sched-20261008-011</a>（今天）：v3 发出——按 Kayra 意见移除 `llc_balance()` 里冗余的 `SD_ASYM_PACKING` 检查、改用 `sgs->group_asym_packing`，并把 `need_active_balance()` 里的 asym 判断提前；新增 Chen Yu 的 `Tested-by` 与 Kayra 的 `Reviewed-by`。至此三位测试者背书、仍等 Peter 收取进 sched/urgent。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-003-sched-cache-honor-asym-packing-over-cache-aware-scheduling-o.html">sched-20260929-003</a>）回归场景：AMD Ryzen AI HX 370 上跑 cache 密集的 Clang full-LTO 链接，小核频率低得多（3.3 vs 5.1 GHz）、L3 只有一半（8 vs 16 MB），cache-aware 调度把任务钉到小核 LLC 双重受损、构建显著变慢。冲突根源是 asym packing（要最高优先级 CPU）与 cache-aware（要共置到同一 LLC、不论优先级）表达相反策略。今天背景无新增，仍是收口这处回归。

## 技术方案

（承接 + 今日 v3）`kernel/sched/fair.c` 三处让 asym packing 在 hybrid 上优先于 cache-aware：

- `can_migrate_llc_task()`：在进入「too many threads / exceed LLC capacity」检查前，先判 `env->idle && sched_asym(env->sd, dst_cpu, src_cpu)`，若 dst 相对 src 优先级更高则直接 `mig_unrestricted`。
- `llc_balance()`：asym packing 域上若目的 CPU 优先级高于源组所有 CPU（`sgs->group_asym_packing`），直接 `return false` 优先走 asym packing。v3 按 Kayra 意见移除了 v1/v2 里冗余的 `SD_ASYM_PACKING` 检查，改用 `group_asym_packing`。
- `need_active_balance()`：把 `asym_active_balance()` 的判断提到 `alb_break_llc()` 之前。

v3 相对 v2（v2 在补跑空窗期内、无独立文章）的改动：移除冗余 `SD_ASYM_PACKING` 检查（Kayra Cizmeci 指出），并新增 `Tested-by: Chen Yu`、`Reviewed-by: Kayra Cizmeci`。仍带 `Fixes: 23b2b5ccc45c`、`Reported-by: Klaus Kusche`、`Cc: stable # 7.2.x`。

## 版本演进与当前进展

- v1（09-29，见 related 文章）：Kayra 指出注释与实现语义不一致并给边界反例，Tim 表示将发 cleaned-up 版进 sched/urgent。
- v2（10-05 前后，空窗期无文章，msgid 见 v3 的 Link v2）。
- v3（今日，`<b29badede27bb6bfb4a759e06754cb19657f0778.1791308631.git.tim.c.chen@linux.intel.com>`）：移除冗余检查 + 收齐三个 `Tested-by`（Klaus Kusche、Ricardo Neri、Chen Yu）与 Kayra 的 `Reviewed-by`。

## Maintainer 意见与讨论焦点

- **Kayra Cizmeci**（reviewer，非维护者）：v1 时的边界反例（`sched_asym()` 在「dst 优先级更高但非空闲」时是否放行）与注释/实现语义不一致，已在 v3 通过移除冗余检查与改用 `group_asym_packing` 部分回应；并给出 `Reviewed-by`。
- **Klaus Kusche / Ricardo Neri / Chen Yu**：三位 `Tested-by` 背书。
- 本日仍无 Peter Zijlstra 或 Ingo 的收取/合入表态；上一阶段作者已明示会投 `sched/urgent`。

## 合入评估

*likelihood=high*。修复方向有回归场景背书、`Fixes:` + `Cc: stable # 7.2.x`、三位测试者 + 一位 reviewer 全部到位、v3 已消化 review 意见；只差维护者收取。*blocking_issues*：尚无 Peter/Ingo 的收取或 tip 合入通告。*next_action*：等维护者收取进 sched/urgent（作者已表态投递），随后回合 stable 7.2.x。

## 效果评估

本日无新增 benchmark 数字。效果证据沿用 related 文章：Klaus 复测「looks good」、两个编译任务 wallclock 优于所有 cache-aware 版本且不差于关 cache-aware 基线；今日新增三位 `Tested-by` 是复测通过的定性背书，非量化数据。

## 我可以参与的点

- `review`：复核 v3 用 `group_asym_packing` 替代显式 `SD_ASYM_PACKING` 检查后，是否仍正确覆盖 Kayra v1 提出的边界反例。
- `testing`：在 big/little + cache-aware 平台验证该补丁的编译负载回归消失、且无新的 LLC 抖动或跨核反复迁移。

## 参考链接

- v3 补丁: https://lore.kernel.org/all/b29badede27bb6bfb4a759e06754cb19657f0778.1791308631.git.tim.c.chen@linux.intel.com/
- v1 补丁: https://lore.kernel.org/all/221f8b0345328c4b26b65daff4d3eec56a32b06d.1790617047.git.tim.c.chen@linux.intel.com/
