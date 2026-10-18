---
id: sched-20261018-010
date: 2026-10-18
subject: 'x86, sched, mm: Speed up CPU hotplug on large systems'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261015153331.1872641-1-pasha.tatashin@soleen.com>
lore_url: https://lore.kernel.org/all/20261015153331.1872641-1-pasha.tatashin@soleen.com/
authors:
- Pasha Tatashin
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261015153331.1872641-1-pasha.tatashin@soleen.com>
  date: 2026-10-15
  summary: 八补丁：x86/sched/mm 消除顺序热插拔瓶颈，调度侧 5/8（sgc 缓存+惰性分配）、6/8（dl_server O(N^2)→O(N)）
  review_outcome: Tony Luck 实测确认、Prateek 提重构、Tim Chen 提锁与不变量意见
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - v2 未发出
  - 调度侧 5/8、6/8 尚未见 maintainer 正式 review
  next_action: Pasha 发 v2，等待 x86/sched/mm 维护者逐补丁审阅
contribution_opportunities:
- kind: testing
  description: 在更多高核数 x86（EPYC/多 socket）上独立复测顺序热插拔耗时，提供第三方数据
- kind: review
  description: 优先复核 6/8 的 dl_clear_root_domain() O(N^2)→O(N) 记账与 !CONFIG_CPUSETS 缺失实现
generated_at: '2026-10-19T09:00:00'
source_email_count: 3
related_articles:
- sched-20261015-002
- sched-20261016-014
tags:
- topology
- deadline
- dl_server
- x86
title: 'x86, sched, mm: Speed up CPU hotplug on large systems'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/15/sched-20261015-002-x86-sched-mm-speed-up-cpu-hotplug-on-large-systems.html">sched-20261015-002</a>：Pasha Tatashin 发 v1 八补丁系列（x86+sched+mm）加速大规模 x86 服务器顺序热插拔，调度侧为 5/8（sgc 缓存 + 惰性分配）与 6/8（dl_server O(N^2)→O(N) 记账）；480 核 Intel 热插拔总耗时 106.23s→5.07s（21x）。
- <a class="article-ref" href="/lkm/2026/10/16/sched-20261016-014-x86-sched-mm-speed-up-cpu-hotplug-on-large-systems.html">sched-20261016-014</a>：首批 review 到来——Tony Luck 实测离线 4.833s→3.17s、在线 6.157s→3.796s（36 核 Icelake），提示反向离线可再省；Prateek 对 5/8 提 `find_group_balance_cpu()` 重构建议；Tim Chen 指出 7/8 的 free 不受 `sched_domains_mutex` 保护、要求补 `lockdep_assert_cpus_held()` 与惰性分配不变量注释。
- <a class="article-ref" href="/lkm/2026/10/18/sched-20261018-010-x86-sched-mm-speed-up-cpu-hotplug-on-large-systems.html">sched-20261018-010</a>（今天）：Pasha 逐条回应三位 reviewer 并确认折入 v2——采纳 Tony 的「顺序」观点、说明终极目标是并行化（live update 黑out 相关）；采纳 Prateek 的 `find_group_balance_cpu()` 重构；采纳 Tim Chen 的 7/8 changelog 与 `lockdep_assert_cpus_held()`/`WARN_ON_ONCE()` 检查。v2 在望。

## 背景与问题

（承接 20261015-002 → 20261016-014）live update 要求快速 CPU online/offline；系列消除大规模 x86 服务器顺序热插拔在 arch/x86、调度拓扑构建器、deadline 带宽记账、vmstat 四层的瓶颈。今天进入 review 收敛阶段，作者对三位 reviewer 的意见逐条回应并确认折入 v2。

## 技术方案

（承接 20261015-002）今日无新补丁，为 v2 前的 review 回应：

- **回应 Tony Luck（0/8 顺序与并行化）**：认可 Tony 的「反向 offline（从高到低 CPU 号）可避免孤儿 CMCI bank」顺序观点；但指出单线程性能达标后，作者的终极目标是**并行化**操作，使 CPU 数量不再显著影响移除/加回调度器的总时长——这对 live update 至关重要（把 CPU 转给 Caretaker 属 brownout 的一部分，某些配置下构成 live update 的 blackout）。
- **回应 Prateek（5/8 `find_group_balance_cpu()`）**：接受「抽象成独立 `find_group_balance_cpu()` 辅助函数」的重构，并补充三点确认（sgc 按需惰性分配下走到慢路径即首次初始化；`find_group_balance_cpu()` 已校验 `sg_span == sched_domain_span(sibling->child)`），「I will fold this into v2」。
- **回应 Tim Chen（7/8 惰性分配不变量）**：确认更新 changelog 说明 `__sdt_free_percpu()` 由 CPU hotplug 锁与 domain rebuild 串行化，并在 `__sdt_free_percpu()` 加 `lockdep_assert_cpus_held()`；在 `__sdt_alloc()` 与 `__sds_alloc()` 都加注释与 `WARN_ON_ONCE()` 检查，一并进 v2。

## 版本演进与当前进展

*current_version: v1*（v2 筹备中）。

- v1（20261015-002）：八补丁。
- v2（预期）：折入 Tony/Prateek/Tim Chen 的意见——`find_group_balance_cpu()` 重构、7/8 的 changelog 修正 + `lockdep_assert_cpus_held()` + `WARN_ON_ONCE()` 惰性分配不变量检查。

## Maintainer 意见与讨论焦点

本日无维护者（调度子系统 maintainer）表态，均为资深 reviewer 的意见收敛：Tony Luck（Intel，实测数据 + 顺序/并行化方向）、Prateek Nayak（AMD，代码重构）、Tim Chen（Intel，7/8 的锁与不变量）。作者已全部接纳并承诺折入 v2，无分歧遗留。

## 合入评估

*likelihood=medium*。系列有实测数据支撑（作者 21x/2.5x，Tony 独立 36 核实测大幅缩短）、review 顺利收敛，但 v2 尚未发出、跨子系统（x86/sched/mm）仍需各 maintainer（含调度侧 Peter Zijlstra / Vincent Guittot）逐补丁 review，且「并行化」这一更大目标被作者点明为后续方向。*blocking_issues*：v2 未发出；调度侧 5/8、6/8 尚未见 maintainer 正式 review。*next_action*：Pasha 发 v2，等待调度/x86/mm 维护者逐补丁审阅。

## 效果评估

作者基准（480 核 Intel 106.23s→5.07s，21x；512 核 AMD 8.41s→3.38s，2.5x）；Tony Luck 独立验证（36 核 Icelake：offline 4.833s→3.17s、online 6.157s→3.796s）。今日无新数字。

## 我可以参与的点

- `testing`：在更多高核数 x86（尤其 EPYC/多 socket）上独立复测顺序热插拔耗时，验证 5/8、6/8 调度侧改动在 v2 下的收益与无回归；这是社区缺失的独立第三方数据。
- `review`：6/8 的 `dl_clear_root_domain()` O(N^2)→O(N) 记账与 `!CONFIG_CPUSETS` 缺失实现是调度侧最关键、最易出错的改动，可优先复核。

## 参考链接

- 系列封面信：https://lore.kernel.org/all/20261015153331.1872641-1-pasha.tatashin@soleen.com/
- 回应 0/8（Tony Luck 顺序/并行化）：https://lore.kernel.org/all/atTQgM72TWSFZ0AX@google.com/
- 回应 5/8（Prateek 重构）：https://lore.kernel.org/all/atTZJ6Q3vTjvDjgG@google.com/
- 回应 7/8（Tim Chen 锁与不变量）：https://lore.kernel.org/all/atTbn7WhHtK52vCi@google.com/
