---
id: sched-20260922-001
date: '2026-09-22'
subject: 'sched/cache: Fixes for cache aware scheduling'
subsystem: sched
type: fix
status: merged_tip
severity: high
thread_root_msgid: <cover.1790035273.git.tim.c.chen@linux.intel.com>
lore_url: https://lore.kernel.org/all/cover.1790035273.git.tim.c.chen@linux.intel.com/
authors:
- Tim Chen
- Lu Wang
- Chen Yu
- Davi Chaves Azevedo
maintainers_involved:
- Peter Zijlstra
current_version: v2
patch_series:
- version: v1
  msgid: null
  date: '2026-09-21'
  summary: 六补丁初始版：计数口径、ALB 迁移语义、内核线程过滤
  review_outcome: 未获取到 v1 原帖，仅从 v2 changelog 得知 v1->v2 改动
- version: v2
  msgid: <cover.1790035273.git.tim.c.chen@linux.intel.com>
  date: '2026-09-22'
  summary: 新增 UAF 修复(patch 3-4)与 hotplug 容量修复(patch 6)，其余小改
  review_outcome: Peter 合入 tip/sched/urgent（6 commits）
upstream_commit: 0d6526f82c3cdefcca47f73f5fc08dc6f335eac6
fixes_commit: null
merged_branch: tip/sched/urgent
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 系列外的 donor 上下文错误与 ITMT 干扰问题需单独跟进
contribution_opportunities:
- kind: testing
  description: 复测 UAF 修复并补 Tested-by（作者 cover 中邀请 Hyunwoo/Zhenhui）
- kind: discussion
  description: 跟进 task_tick_cache() donor 上下文错误与 CAS/ITMT 干扰两个未决问题
generated_at: '2026-09-23T00:00:00'
source_email_count: 14
related_articles: []
tags:
- load_balance
- cfs
title: 'sched/cache: Fixes for cache aware scheduling'
layout: article
---

## TL;DR
Tim Chen 汇总 cache-aware scheduling（CAS，7.2 合入）遗留问题，发出 v2 六补丁修复系列：DELAY_DEQUEUE 下 `nr_pref_llc_running` 计数口径不一致导致主动负载均衡把任务拉离首选 LLC、active load balance 丢失 `migrate_llc_task` 语义、任务 mm 切换时 `account_mm_sched()` 访问已释放 mm 的 UAF、内核线程借用用户线程缓存统计、CPU 热插拔时 LLC 容量被低估。六补丁当天已被 Peter Zijlstra 全部合入 `tip/sched/urgent`（6 个 commit），属已合入的修复系列。

## 背景与问题
CAS（cache-aware scheduling）在 v7.2 合入后，社区陆续报出若干正确性问题，Tim Chen 将其集中在一个系列里便于跟踪。问题来源多样：

1. **计数口径不一致**（patch 1，Reported-by Zhan Xusheng）：`alb_break_llc()` 用 `nr_pref_llc_running == cfs.h_nr_runnable` 判断是否打破 LLC 偏好，但两个计数器覆盖不同集合——前者跟随 queued 任务，后者在 DELAY_DEQUEUE 时会丢弃 delay-dequeued 任务。睡眠的任务仍被计入 `nr_pref_llc_running`，等式被打破，主动负载均衡得以把可运行任务拉离其首选 LLC。
2. **ALB 丢失迁移语义**（patch 2，Lu Wang）：stopper 重建的 `lb_env` 不继承 `migration_type`，`can_migrate_task()` 可能把一个任务移出首选 LLC。
3. **UAF**（patch 3-4，KASAN 报，Hyunwoo Kim 与 Zehnghui Yu 独立发现）：`account_mm_sched()` 经 `p->mm->sc_stat` 取调度统计，任务在一核切换 mm 时另一核可能正在 `account_mm_sched()`，mm 及其内含的统计被释放，造成 use-after-free。
4. **内核线程污染**（patch 5，Chen Yu）：内核线程借用用户线程的缓存统计。
5. **LLC 容量低估**（patch 6，Davi Chaves）：CPU 热插拔拆机时调度域先于 `cacheinfo_cpu_pre_down()` 重建，沿用旧 sharing weight 导致 LLC 字节数被低估。

## 技术方案
六补丁分别处理：

- **patch 1** 修计数侧：让任务恰好在其「排队且位于首选 LLC」期间被计入 `nr_pref_llc_running`。
- **patch 2** 新增 `LBF_ACTIVE_LB_LLC` 标志并在 kick 时选定 stopper 回调，保留迁移意图；放弃「穿过 stopper 传 `migration_type`」的方案（会污染 delayed dequeue）。
- **patch 3** 把 `sched_cache_stat` 从 `mm_struct` 抽出，改名为 refcount 管理的 `sched_cache_group`，独立于 mm 生命周期（纯移动代码）；**patch 4** 才是真正修复：每个任务在 `copy_mm()`/`exec_mmap()` 各自持有引用、`exit_mm()` 释放，配合 `call_rcu()` 让 group 活得比任何 mm 切换更久。附带好处：group 不再跟随地址空间，未来用户组/cgroup/numa_group 可以拥有它（这几条正是 PRCL 分组 RFC 的前两补丁，提前发以免阻塞修复）。
- **patch 5** 在 `account_mm_sched()` 里显式过滤 `PF_KTHREAD`，与 `task_tick_cache()` 配对。
- **patch 6** 传入 CPU down 的容量校验，避免下线 SMT 兄弟后剩余 CPU 的 `llc_bytes` 被 `floor(16MiB*11/12)` 低估（正确应为 16MiB）。

## 版本演进与当前进展
- v1（此前发出）：六补丁基础版。
- v2（2026-09-22，cover `<cover.1790035273.git.tim.c.chen@linux.intel.com>`）：v1 后新增 patch 3-4（UAF）与 patch 6（hotplug 容量）两个修复；patch 1 在 `set_delayed()` 做了小幅代码重排；patch 5 按 Peter 建议从原 patch 3 拆出；fork/exec/exit 的引用管理封装成 `sched_cache_fork()` 等专职函数，格式整理。
- 当天全部六补丁以 `tip/sched/urgent` 分支合入 tip（分别对应 commit `0d6526f82c3c`、`d6013e2465d9`、`28f9c0e0a0b9`、`b636fef85bda`、`65efcccddc83`、`3cb0243767fd`）。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**：对 patch 1 指出其中一段判断在 Linus 树（补丁应用目标）上是死代码，建议随后在 sched/core 移除；对 patch 2 表示每次读 `CAS` 都联想到 Compare-And-Swap。最终六补丁全部合入 `queue.git/sched/urgent`。
- **Chen Yu**（patch 5 作者）回复 Peter，确认 patch 1 当前写法是为了让修复可回迁（CAS 在 flat task-pickup 之前合入）；并应 Peter 要求，把措辞统一为 Cache-Aware-Scheduling。
- **争议点/未解决**：系列之外还有两个独立问题在讨论中未纳入——(1) `task_tick_cache()` 传入错误的 donor 上下文（<https://lore.kernel.org/lkml/20260909092901.2989564-1-sh_def@163.com/>）；(2) CAS 与 ITMT 的干扰（<https://lore.kernel.org/lkml/20260810033742.1688718-1-yu.c.chen@intel.com/>）。

## 合入评估
likelihood=merged。六补丁已全部合入 `tip/sched/urgent`，UAF 修复（patch 3-4）尤其关键，作者还在 cover 中邀请 Hyunwoo/Zhenhui 补 Tested-by。blocking_issues 无（已合入）；系列之外的 donor 上下文与 ITMT 问题需后续单独推进。

## 效果评估
本系列为正确性修复，未附 benchmark。patch 6 给出具体复现数：Ryzen 5 7535U（12 逻辑 CPU 共享 16MiB LLC）下线一个 SMT 兄弟后，剩余 CPU 的 `llc_bytes` 被错算为 `floor(16777216*11/12)=15379114`，正确值应为 16777216，低估会让 `exceed_llc_capacity()` 错误拒绝本该放得下的进程聚合。

## 我可以参与的点
- **testing**：UAF 修复（patch 3-4）的作者在 cover 中明确邀请 Hyunwoo Kim、Zhenhui Yu 复测并补 `Tested-by`；可基于 KASAN/内存毒化复现原崩溃路径验证修复。
- **discussion**：cover 中提到的两个悬而未决问题是清晰切入点——`task_tick_cache()` 的 donor 上下文错误、CAS 与 ITMT 的干扰，均可回帖参与分析。

## 参考链接
- lore thread: https://lore.kernel.org/all/cover.1790035273.git.tim.c.chen@linux.intel.com/
- tip commit 1: https://git.kernel.org/tip/0d6526f82c3cdefcca47f73f5fc08dc6f335eac6
- tip commit 2: https://git.kernel.org/tip/d6013e2465d98d524b030a81c1223882a1bb7e4c
- tip commit 3: https://git.kernel.org/tip/28f9c0e0a0b94c5d3e1b634db545f6e1f94858c5
- tip commit 4: https://git.kernel.org/tip/b636fef85bda7d1bab9c0a45067ab1508d79d946
- tip commit 5: https://git.kernel.org/tip/65efcccddc83d6a19e8a2e2a6117811e39e589bf
- tip commit 6: https://git.kernel.org/tip/3cb0243767fd033bdce95f4f1b5882172a2f8119
