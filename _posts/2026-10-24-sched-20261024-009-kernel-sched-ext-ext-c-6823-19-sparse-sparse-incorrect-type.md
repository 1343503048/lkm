---
id: sched-20261024-009
date: 2026-10-24
subject: 'kernel/sched/ext/ext.c:6823:19: sparse: sparse: incorrect type in assignment
  (different address spaces)'
subsystem: sched
type: bug
status: rfc
severity: low
thread_root_msgid: <202610240742.zGIUIQt7-lkp@intel.com>
lore_url: https://lore.kernel.org/all/202610240742.zGIUIQt7-lkp@intel.com/
authors:
- kernel test robot
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无 patch、无归因确认
  next_action: sched/ext 维护者清理 rq->curr/rq->donor 相关 __rcu 解引用点
contribution_opportunities:
- kind: review
  description: 核对 rq->donor/rq->curr 解引用点是否确需 rcu_dereference
- kind: new_patch
  description: 提交批量清理补丁，补 rcu_dereference 或修正标注
generated_at: '2026-10-25T01:00:00'
source_email_count: 1
related_articles: []
tags:
- sched_ext
- rt
- deadline
title: 'kernel/sched/ext/ext.c:6823:19: sparse: sparse: incorrect type in assignment
  (different address spaces)'
layout: article
---

## TL;DR
kernel test robot（0day/LKP）的 sparse（W=1，sparc64 randconfig）编译告警报告：proxy execution 使 `rq->curr` / `rq->donor` 带 `__rcu` 标注后，kernel/sched 下大量直接解引用点（rt.c、deadline.c、ext.c、syscalls.c、sched.h）触发「different address spaces」告警，主题指向 ext.c:6823 处对 `__rcu` 指针的 `p->sched_class` 解引用。属构建 lint 噪音、非运行时 bug，无 patch、无维护者回应。

## 背景与问题
0day 机器人在 linus master（head `17bb0e2f6c80`、commit `db87a8f530b6` "sched_ext: Merge branch 'for-7.3-fixes' into for-7.4"）上加跑 sparse（sparc64-randconfig-r2307、clang-20、sparse v0.6.5-rc1）得到一批「incorrect type in assignment/argument/initializer (different address spaces)」告警，核心模式是 `struct task_struct *`（普通地址空间）与 `struct task_struct [noderef] __rcu *`（__rcu 地址空间）混用：多处把 `rq->curr`、`rq->donor`（现为 `__rcu` 标注）直接当普通指针使用。报告的 Fixes 标签指向 `db87a8f530b6`（merge commit，实为 proxy execution 相关 `__rcu` 标注引入的批量告警）。

## 技术方案
非补丁，为 sparse 告警报告。告警遍布：`kernel/sched/rt.c`（1579/1605/1627/1653/2006/2029/2380/2382、1313 等多处 `donor`/`curr`）、`kernel/sched/deadline.c`（3157/3167/3273/2737/2757/1189/1287/1816/2131/2979/2619/2620/2694/2714/3318/3320/3322/3584/3637）、`kernel/sched/ext/ext.c`（454/1547/1751/2559/2573/3477/3824/5018/5019/6823/7601/7605/9161/9207）、`kernel/sched/syscalls.c`（202/1420）、`kernel/sched/sched.h`（2505）。另有大量 kfunc 符号「was not declared. Should it be static?」的既有稀疏噪音。报告给出 config/reproduce 下载地址，并请求若单独修则加 `Reported-by: kernel test robot` 与 `Closes:` 标签。

## 版本演进与当前进展
*current_version: null*。为 kernel test robot 自动报告（`<202610240742.zGIUIQt7-lkp@intel.com>`），当日发出、无回应。

## Maintainer 意见与讨论焦点
无维护者表态。告警多为 `__rcu` 地址空间标注与解引用点的机械不一致，根因是 proxy execution 改动了 `rq->curr`/`rq->donor` 的标注而未同步更新全部解引用点。

## 合入评估
*likelihood=unknown*。属构建期 sparse 噪音报告、非运行时 bug，通常由 sched 维护者随手修正 `__rcu` 解引用（加 `rcu_dereference` 或调整标注）或忽略；无 patch 与回应。*blocking_issues*：无 patch、无归因确认。*next_action*：sched/ext 维护者清理 `rq->curr`/`rq->donor` 相关解引用点或补充 `rcu_dereference`。

## 效果评估
无性能/运行时影响，为纯编译期 sparse 检查告警，无量化数据。

## 我可以参与的点
- *kind: review*：逐点核对 `rq->donor`/`rq->curr` 的解引用是否确需 `rcu_dereference()`，区分真标注缺失与可忽略的 sparse 噪音。
- *kind: new_patch*：提交批量清理补丁，为这些解引用点补 `rcu_dereference` 或修正标注。

## 参考链接
- 报告: https://lore.kernel.org/all/202610240742.zGIUIQt7-lkp@intel.com/
- 复现材料: https://download.01.org/0day-ci/archive/20261024/202610240742.zGIUIQt7-lkp@intel.com/
