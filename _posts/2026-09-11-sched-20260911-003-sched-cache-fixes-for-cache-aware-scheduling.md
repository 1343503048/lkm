---
id: sched-20260911-003
subject: 'sched/cache: Fixes for cache aware scheduling'
date: '2026-09-11'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <cover.1789061845.git.tim.c.chen@linux.intel.com>
lore_url: https://lore.kernel.org/all/cover.1789061845.git.tim.c.chen@linux.intel.com/
authors:
- Tim Chen
- Chen Yu
- Lu Wang
maintainers_involved:
- Peter Zijlstra
- Tim Chen
- Chen Yu
current_version: v1
patch_series:
- version: v1
  msgid: <cover.1789061845.git.tim.c.chen@linux.intel.com>
  date: 2026-09-11
  summary: 4 补丁修复系列：1 收敛 nr_pref_llc_running 到 runnable 域（修 DELAY_DEQUEUE 下计数口径错位），2
    收编 Lu Wang v4（LBF_ACTIVE_LB_LLC 保语义），3 把 sched_cache_stat 抽成 refcount 的 sched_cache_group，4
    task 持引用修 UAF。基于 sched/urgent。
  review_outcome: PeterZ 强烈批评 4/4 实现风格（要求函数化、指 rcu_dereference_protected(true) 错误）；Kayra
    质疑 1/4 计数维护点，Tim 以 set_delayed() 顺序约束与 per-rq/per-cfs_rq 作用域差异自辩；Tim 承诺清理后发 v2。
upstream_commit: null
fixes_commit: df0d98475954
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - patch 4/4 被 PeterZ 打回，需函数抽象重写并撤掉 rcu_dereference_protected(true)
  - patch 3/4 承诺打包合入，合入互相绑定
  - patch 1 的计数维护点设计 Kayra 尚未认同（Tim 已答复但无回音）
  next_action: 等 v2 重写后 PeterZ 复核；跟踪 prctl RFC 讨论对分组抽象的影响
contribution_opportunities:
- kind: review
  description: v2 发出后核对 4/4 是否落实 PeterZ 两条批评、引用转移顺序是否正确
- kind: testing
  description: DELAY_DEQUEUE + active balance 压力下验证 patch 1 计数修复的边界行为
- kind: discussion
  description: 对 cover 点名的 donor 上下文误传与 CAS 干扰 ITMT 两个开放问题提供复现/数据
generated_at: '2026-09-14T11:35:00'
source_email_count: 10
related_articles:
- sched-20260903-011
- sched-20260910-011
tags:
- cfs
- load_balance
title: 'sched/cache: Fixes for cache aware scheduling'
layout: article
---

## TL;DR
Tim Chen 与 Chen Yu 把 cache aware scheduling（CAS，v7.2 合入）合入后发现的问题收拢成一个 4 补丁修复系列：两个修任务被搁置/拽离首选 LLC，两个修一处 KASAN 抓到的 use-after-free。当日 Peter Zijlstra 对 patch 4/4 的实现风格发火（"This is horrific crap"），Tim 承诺清理后发新版——UAF 修复方向无争议，但 4/4 需要重写。

## 背景与问题
CAS 在 v7.2 进主线后陆续暴露问题，作者收拢为系列便于跟踪（基于 sched/urgent 分支）：

- patch 1（Zhan Xusheng 报告）：DELAY_DEQUEUE 下 alb_break_llc() 的计数口径错位——nr_pref_llc_running 跟随 queued 任务、cfs.h_nr_runnable 不含 delay-dequeued 任务，两者相等这一前提失效，active balance 会把任务从首选 LLC 上拉走；
- patch 2（Lu Wang，v4 独立投递过的线程）：active balance 的 stopper 现场重建 lb_env 不继承 migration_type，can_migrate_task() 可能把任务迁出首选 LLC；
- patch 3/4（Hyunwoo Kim 用 KASAN 抓到）：account_mm_sched() 经 p->mm->sc_stat 访问统计，任务在另一 CPU 切换 mm 时旧 mm 及其中统计可被释放，构成 use-after-free。

## 技术方案
- patch 1：把 nr_pref_llc_running 的口径收进 runnable 域——新增 task_pref_llc_runnable()（pref_llc_queued && !sched_delayed）作为唯一判据，由 pref_llc_running_inc/dec() 在 account_llc_enqueue()/account_llc_dequeue()/set_delayed()/clear_delayed() 四个改动点统一维护，防止双计/欠计；nr_llc_running 与 sd->llc_counts 保持 queued 语义不动；
- patch 2：不做 rq 上加字段继承 migration_type 的方案 (a)，选 (b)——新增 LBF_ACTIVE_LB_LLC flag 并在 kick 时选定 stopper 回调，跨异步边界保留 migrate_llc_task 语义，避免把 migration_type 传经 stopper 影响延迟出队任务的语义；
- patch 3：把 sched_cache_stat 从 mm_struct 抽出，改名为 sched_cache_group（refcount + RCU free），mm 只持指针——纯代码搬移，作者明确「不用在 mm 释放路径上锁 rq」这种交换；顺带在 account_mm_sched() 跳过 kthread；新文件 kernel/sched/cache_sched.c 承载 helper；
- patch 4：task_struct 增加 __rcu 的 sched_cache_grp 指针，任务在 copy_mm()/exec_mmap() 取自身引用、exit_mm() 释放，调度器热路径直接经 task 访问 group 而不再穿过 mm——这同时让分组未来可挂到用户自定义分组、cgroup、numa_group 等（cover 明言这两个补丁就是 prctl 分组 RFC 的前两个补丁，提前发以免修复被该讨论拖住）。

cover 同时点名两个尚在讨论、未进本系列的问题：donor 上下文传给 task_tick_cache() 不正确（20260909092901.2989564-1-sh_def@163.com）、CAS 干扰 ITMT（yu.c.chen@intel.com 两封）。

## 版本演进与当前进展
current_version: v1（当日首发，cover msgid `<cover.1789061845.git.tim.c.chen@linux.intel.com>`，09-11 01:46 起入缓存，共 5 封补丁 + 5 封讨论）。

- patch 2 为 Lu Wang v4 独立线程（20260903020656.3793626-1）的收编，带 Tim Chen 与 Chen Yu 双 Reviewed-by（见 sched-20260903-011）；
- 本日无新版本发出，v2 待发（Tim："Will clean it up and send an update"）。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra（对 patch 4/4，强烈负面）**："Guys no! This is horrific crap. This is not how we do things"——批评点有二：fs/exec.c/exit.c 里成片内联的 group get/put 代码应抽象成函数（"Have you heard of this new fangled thing called a function?"，建议改成 `sched_cache_exec_mmap(tsk, mm);` 一类）；以及 `rcu_dereference_protected(..., .condition = true)` 的用法（"that's just wrong"）。结论 "Please, try again."
- **Tim Chen**："Sorry for the warts in this version. Will clean it up and send an update."——接受全部批评，v2 待发。
- **Kayra Cizmeci（对 patch 1）**：质疑为何不在 h_nr_runnable 的更新点顺带维护 nr_pref_llc_running（既然它是子集），可省掉独立判据与四处调用；
- **Tim Chen（答复）**：解释了不能合并的顺序约束——set_delayed() 中 pref_llc_running_dec() 必须在 `se->sched_delayed = 1` 之前执行（此时判据还成立），而 h_nr_runnable 在标志置位后才递减，紧跟其后做会漏减导致计数偏高；且 h_nr_runnable 是 per-cfs_rq 逐层级更新、nr_pref_llc_running 是 per-rq 单值，作用域不同。保持单一判据 + 显式 inc/dec 是设计选择。
- 分歧未闭合处：patch 1 的实现路线 Tim 已自辩，Kayra 未再回；patch 4 的重写幅度（抽象到什么程度）待 v2 验证。

## 合入评估
likelihood=medium：修复需求真实（UAF 是 KASAN 实锤、stranding 有明确机理），patch 2 已有双 R-b，patch 1 口径论证完整；但 patch 4/4 被 PeterZ 打回、整体必须出 v2。blocking_issues：4/4 按批评重写（函数抽象 + 撤掉 rcu_dereference_protected(true)）；PeterZ 情绪强烈，v2 需要他点头；patch 3/4 打包合入的承诺（"they want to go in together"）使两个补丁的合入互相绑定。next_action：等 v2 重写后 PeterZ 的复核；关注 prctl RFC 讨论（分组抽象的动机）是否反过来影响 3/4 的形态。

## 效果评估
本系列为修复向，无 benchmark 数字。patch 1/2 的效果是消除「任务被拽离首选 LLC」的具体场景（Zhan Xusheng 报告、Lu Wang 的 p1/p2 场景推演），UAF 由 KASAN 报告并带 Hyunwoo 的 Tested-by（3/4 补丁标签）；均无量化性能数据，属作者/reviewer 场景级证据。

## 我可以参与的点
- kind=review：v2 发出后核对 4/4 是否落实 PeterZ 的两条批评（exec/exit 路径函数化、rcu_dereference_protected 用法），并检查 exec_mmap() 中 get 在 publish 前、put 在后的引用转移顺序是否保持。
- kind=testing：在开 DELAY_DEQUEUE 的机器上用 active balance 压力场景验证 patch 1 的计数修复（pref_llc_running 偏高/偏低的边界：sleep、wake、dequeue 交错）。
- kind=discussion：cover 点名的两个未收编问题（donor 上下文误传 task_tick_cache()、CAS 干扰 ITMT）尚在讨论，可提供复现或数据。

## 参考链接
- cover letter：https://lore.kernel.org/all/cover.1789061845.git.tim.c.chen@linux.intel.com/
- patch 1/4：https://lore.kernel.org/all/82736e1329bf8ed195bbbc4990486c87094e6789.1789061845.git.tim.c.chen@linux.intel.com/
- patch 2/4：https://lore.kernel.org/all/4c921888d81e4a7eefa14322bf04058a1a30f4e9.1789061845.git.tim.c.chen@linux.intel.com/
- patch 3/4：https://lore.kernel.org/all/cb678eddae708e2865ec69a04edf999119c2168a.1789061845.git.tim.c.chen@linux.intel.com/
- patch 4/4：https://lore.kernel.org/all/4532ec4fd5beb829bccb85822a19360fa4191fe6.1789061845.git.tim.c.chen@linux.intel.com/
- UAF 原始报告（Hyunwoo Kim）：https://lore.kernel.org/lkml/apPb-Dr4nPYuHQOK@v4bel/
- patch 1 报告（Zhan Xusheng）：https://lore.kernel.org/lkml/20260827135000.735138-1-zhanxusheng@xiaomi.com/
- patch 2 前身 v4：https://lore.kernel.org/lkml/20260903020656.3793626-1-wanglu.priv@gmail.com/
