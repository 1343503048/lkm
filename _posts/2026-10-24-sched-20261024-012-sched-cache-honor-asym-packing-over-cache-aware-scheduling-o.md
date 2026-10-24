---
id: sched-20261024-012
date: 2026-10-24
subject: 'sched/cache: Honor asym packing over cache aware scheduling on hybrid systems'
subsystem: sched
type: fix
status: merged_tip
severity: high
thread_root_msgid: <b29badede27bb6bfb4a759e06754cb19657f0778.1791308631.git.tim.c.chen@linux.intel.com>
lore_url: https://lore.kernel.org/all/b29badede27bb6bfb4a759e06754cb19657f0778.1791308631.git.tim.c.chen@linux.intel.com/
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
  review_outcome: Kayra Reviewed-by + 多位 Tested-by；Peter 收取进 sched/urgent
upstream_commit: ee92b7ef4c1e271b3c1ea2a8b13034bdc62422a7
fixes_commit: 23b2b5ccc45c
merged_branch: tip/sched/urgent
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: stable 7.2.x 回合
contribution_opportunities:
- kind: testing
  description: 真实 hybrid 平台复测 cache 密集构建负载，确认收益与无回归
generated_at: '2026-10-25T01:00:00'
source_email_count: 1
related_articles:
- sched-20261023-013
tags:
- cfs
- load_balance
- regression
title: 'sched/cache: Honor asym packing over cache aware scheduling on hybrid systems'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/06/sched-20261006-002-sched-cache-honor-asym-packing-over-cache-aware-scheduling-o.html">sched-20261006-002</a> / <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-011-sched-cache-honor-asym-packing-over-cache-aware-scheduling-o.html">sched-20261008-011</a>：Tim Chen 针对「cache-aware 调度在 AMD big/little 混合平台性能回退」的修复——让 asym packing 在迁向更高优先级空核时优先于 cache-aware；v3 移除冗余 `SD_ASYM_PACKING` 检查、改用 `group_asym_packing`，已获 Kayra Reviewed-by 与 Chen Yu/Klaus Kusche/Ricardo Neri Tested-by。
- <a class="article-ref" href="/lkm/2026/10/24/sched-20261024-012-sched-cache-honor-asym-packing-over-cache-aware-scheduling-o.html">sched-20261024-012</a>（今天）：Peter Zijlstra 将补丁合入 **tip/sched/urgent**（commit `ee92b7ef4c1e27...`），附 Kayra `Suggested-by`、Klaus `Reported-by` 与多位 Tested-by/Reviewed-by，并 `Cc: stable # 7.2.x`。系列正式合入。

## 背景与问题
（承接 20260929-003 → 20261006-002 → 20261008-011）回归场景：AMD Ryzen AI HX 370 上 cache 密集的 Clang full-LTO 链接，小核频率低（3.3 vs 5.1 GHz）、L3 只有一半（8 vs 16 MB），cache-aware 调度把任务钉到小核 LLC 双重受损、构建显著变慢。冲突根源是 asym packing（要最高优先级 CPU）与 cache-aware（要共置同一 LLC、不论优先级）表达相反策略。今日无新背景，为合入确认。

## 技术方案
（承接 v3 + 今日合入）`kernel/sched/fair.c` 三处让 asym packing 在 hybrid 上优先于 cache-aware：`can_migrate_llc_task()` 在进入「too many threads / exceed LLC capacity」检查前先判 `env->idle && sched_asym(...)`；`llc_balance()` 上 asym packing 域优先返回；`need_active_balance()` 把 `asym_active_balance()` 判断提前。已合入版本 diff（+17/-3）与 v3 方案一致。

## 版本演进与当前进展
*current_version: v3*。今日进展：合入 tip/sched/urgent（commit `ee92b7ef4c1e271b3c1ea2a8b13034bdc62422a7`）。

## Maintainer 意见与讨论焦点
Peter Zijlstra 今日将补丁合入 sched/urgent（committer 落款 Peter），提交消息记录：`Reported-by: Klaus Kusche`、`Suggested-by: Kayra Cizmeci`、`Reviewed-by: Kayra Cizmeci`、`Tested-by: Klaus Kusche / Ricardo Neri / Chen Yu`，并 `Cc: stable@vger.kernel.org # 7.2.x`。无分歧。

## 合入评估
*likelihood=merged*。已合入 tip sched/urgent（`Fixes: 23b2b5ccc45c`，`Closes:` 指向回报链接），待回合 stable 7.2.x。*blocking_issues*：无。*next_action*：stable 7.2.x 回合（已带 `Cc: stable # 7.2.x`）。

## 效果评估
既有数据延续（Chen Yu，AMD Ryzen 9 8945HX 仿真 hybrid）：补丁前 cache-aware ON 使吞吐 **-56.6%**，补丁后回到与 OFF 持平（**+1.5%**，噪声内）。Klaus 在真实 Ryzen AI HX 370 上验证了回归修复。今日无新数据。

## 我可以参与的点
- *kind: testing*：在真实 AMD/Intel hybrid 平台复测 cache 密集构建负载，确认修复收益与无明显回归。

## 参考链接
- tip 提交: https://git.kernel.org/tip/ee92b7ef4c1e271b3c1ea2a8b13034bdc62422a7
- 前文: <a class="article-ref" href="/lkm/2026/10/23/sched-20261023-013-sched-cache-honor-asym-packing-over-cache-aware-scheduling-o.html">sched-20261023-013</a> / <a class="article-ref" href="/lkm/2026/10/06/sched-20261006-002-sched-cache-honor-asym-packing-over-cache-aware-scheduling-o.html">sched-20261006-002</a> / <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-011-sched-cache-honor-asym-packing-over-cache-aware-scheduling-o.html">sched-20261008-011</a>
