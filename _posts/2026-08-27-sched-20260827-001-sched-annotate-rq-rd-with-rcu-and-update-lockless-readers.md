---
id: sched-20260827-001
date: '2026-08-27'
subject: 'sched: Annotate rq->rd with __rcu and update lockless readers'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260826224238.936456-1-atomlin@atomlin.com>
lore_url: https://lore.kernel.org/all/20260826224238.936456-2-atomlin@atomlin.com/
authors:
- Aaron Tomlin
maintainers_involved:
- Peter Zijlstra
- Vincent Guittot
current_version: v7
patch_series:
- version: v7
  msgid: <20260826224238.936456-1-atomlin@atomlin.com>
  date: 2026-08-26
  summary: rq->rd 加 __rcu 注解并规范无锁读者；修复 debug 路径 4 处无锁访问；新增 per-CPU debugfs 文件
  review_outcome: Peter 否定 rq->lock 作为更新锁的保护写法，要求复用 rcu_dereference_sched_domain()
    或别名；Vincent 要求恢复被误删注释；无 NAK
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - v7 的 rcu_dereference_protected(rq->rd, lockdep_is_held(&rq->__lock)) 写法被 Peter
    三条否定，需按 sched_domains_mutex/rcu_dereference_sched_domain 共识重做
  - set_rq_online() 上方注释误删需恢复
  next_action: 作者发出 v8：统一持锁解引用 helper 并恢复注释
contribution_opportunities:
- kind: testing
  description: 在大核数机器上验证 per-CPU debugfs 文件（Patch 6/6）并回帖数据
- kind: review
  description: 在 6.6/OLK-6.6 基线上试转该系列，验证回合成本后跟进社区
generated_at: '2026-09-07T22:05:00'
source_email_count: 8
related_articles: []
tags:
- topology
- sched_debug
- deadline
- cfs
- rt
title: 'sched: Annotate rq->rd with __rcu and update lockless readers'
layout: article
---

## TL;DR
Aaron Tomlin 发出 v7（6 补丁）：给 `struct rq::rd` 补上 `__rcu` 注解，并把 kernel/sched/ 各处无锁直读 `rq->rd` 的路径改为规范的 RCU 解引用。v7 当天就得到 Peter Zijlstra 的实质 review 并当场收敛了实现细节（改用现有 `rcu_dereference_sched_domain()` 或别名），方向无争议，离合入只差一次机械性重发，值得跟踪。

## 背景与问题
`rq->rd`（root_domain 指针）由 `rq_attach_root()` 通过 RCU 更新并用 `call_rcu()` 延迟回收，但字段本身缺少 `__rcu` 编译期注解，且调度器内多处无锁读者（online/offline 路径、debugfs 打印、deadline/rt/fair 遍历）直接裸读该指针。后果有三：编译器/DEC 架构缺少数据依赖屏障保证、Sparse 静态检查无法验证 RCU 读侧契约、锁归属只能靠人肉约定。v7 还捎带修复了 debug 路径上另外几处同类问题：`print_dl_rq()` 无锁读 `rq->rd`、`print_cpu()` 无锁读 `rq->curr`、`sched_show_numa()` 读 `p->mm`、`print_cfs_stats()` 遍历。

## 技术方案
- Patch 1/6：`sched.h` 给 `rd` 加 `__rcu`，按上下文把无锁读者改为 `rcu_dereference()` / `rcu_dereference_sched()` / `rcu_access_pointer()`，持锁处用 `rcu_dereference_protected()`。
- Patch 2–5：分别修 `print_dl_rq()`、`print_cpu()`、`sched_show_numa()`、`print_cfs_stats()` 四处 debug 面的无锁访问。
- Patch 6/6：顺带引入 per-CPU debugfs 文件 `/sys/kernel/debug/sched/cpu/cpu<N>/debug`，只打印单个 CPU 的 runqueue（离线返回 -ENODEV），排查单机延迟异常时不必再拉全量 `/sched/debug`。

关键取舍在第 1 补丁的持锁解引用写法，见下节。

## 版本演进与当前进展
- v7：2026-08-26 晚发出（cover `<20260826224238.936456-1-atomlin@atomlin.com>`），当天未收到意见。
- 08-27：Vincent Guittot 指出 `set_rq_online()` 上方注释被无理由删除，作者承认是改用 `rcu_dereference_sched()` 时误删；Peter Zijlstra 对 `rcu_dereference_protected(rq->rd, lockdep_is_held(&rq->__lock))` 写法提出三条反对（见下节）。更早版本（v1–v6）演进细节不在缓存中，未获取到。当日未出现 v8。

## Maintainer 意见与讨论焦点
Peter Zijlstra 的三点反对（msgid `<20260827073036.GC4121339@noisy.programming.kicks-ass.net>`）：
1. `rcu_dereference_protected()` 只该用于更新侧，且 `rq->lock` 根本不是拓扑/根域的更新锁——更新锁是 `sched_domains_mutex`（`partition_sched_domains()` 持有）；
2. 直接引用 `&rq->__lock` 破坏 rq 锁抽象；
3. 每个调用点重复这套样板"far too verbose"。

作者提议新增 `rcu_dereference_root_domain(p)`（内部 `rcu_dereference_all_check((p), lockdep_is_held(&sched_domains_mutex))`）。Peter 反驳：root domain 本来就是 sched domain 的一部分，直接复用现成的 `rcu_dereference_sched_domain()` 即可；作者退让但希望保留别名以维持 `rq->rd`/`rq->sd` 的对称与可 grep 性；Peter 最终放行："*shrug*, either will do I suppose. You can create an alias if you think it helps."——分歧已收敛，无 NAK。

## 合入评估
**likely**。这是纯注解/正确性工作，Peter 认可方向且已给出明确写法（复用 `rcu_dereference_sched_domain()` 或别名），Vincent 的意见也只是恢复一行注释；`blocking_issues` 仅剩 v8 需要按共识重做持锁解引用辅助函数并恢复注释。`next_action`：作者发 v8。该改动无功能行为变化、影响面是 RCU 注解，维护者接受门槛低。

## 效果评估
暂无效果数据——邮件中没有 benchmark，这类注解补丁的收益是 Sparse 干净化与读侧契约文档化，属于机制正确性而非性能。per-CPU debugfs 文件的收益（定向查看单 CPU runqueue）为主观判断，未见数据。

## 我可以参与的点
- 若在 OLK-6.6 上有同源需求（rq->rd 无锁读、debugfs 全量打印排查困难），此系列结构清晰、无算法争议，是低风险回合候选；可先在 6.6 基线上试转 v7 打点验证。
- Patch 6/6 的 per-CPU debugfs 接口可以顺手回帖测试意见（大核数机器上 `/sched/debug` 全量读取的耗时对比是有价值的数据点）。

## 参考链接
- 系列 cover: https://lore.kernel.org/all/20260826224238.936456-1-atomlin@atomlin.com/
- Patch 1/6: https://lore.kernel.org/all/20260826224238.936456-2-atomlin@atomlin.com/
- Peter 的三点反对: https://lore.kernel.org/all/20260827073036.GC4121339@noisy.programming.kicks-ass.net/
- Peter 的收尾（alias 放行）: https://lore.kernel.org/all/20260827105021.GJ687043@noisy.programming.kicks-ass.net/
- tip-bot commit: 未获取到
- stable backport: 未获取到
