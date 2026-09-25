# sched, steal_governor: Introduce preferred CPUs and steal-driven vCPU backoff

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260909-010：v13（13 补丁）发出，封面请求 Peter/Ingo 考虑排入 sched/core、目标 7.4，并把上一轮 Yury Norov 三条评审意见全部收掉（改名 `npc_push_work_pending`、挪到 `steal_*` 旁、加 `CONFIG_PREFERRED_CPU` 守卫）。
- sched-20260925-010（今天）：Peter Zijlstra 首次对 v13 逐枚细读 06/08/09 三枚补丁，提出四点意见——`task_can_sched_on_preferred()` 命名/语义别扭（建议 `task_can_migrate_to_preferred`）、08/13 的 push stopper 写法应与 `__balance_push_cpu_stop()` 对齐并说明多出的 `!is_migration_disabled()` 是否多余、09/13 统计含义需在 changelog 写清、以及输出格式变化需要 bump schedstat 版本。Shrikanth 逐条接受，正在准备 v14。

## 背景与问题

（承接 sched-20260909-010）大规模机器上客户普遍做 vCPU 超配：给 VM 配很多 vCPU、背后是更小的共享 pCPU 池。多个 VM 同时高负载时 pCPU 池被争抢，hypervisor 为公平 preempt 某个 vCPU；若被 preempt 的 vCPU 正持锁或关中断，整体前进能力崩盘——除丢失的 CPU 时间外，还有锁持有者被抢占、TLB/cache miss、host 调度开销。缓解办法是让 guest 主动把负载折叠到更少 vCPU 上，少要一些 pCPU、降低 host 争抢。已有手段（CPU 热插拔/隔离 cpuset）是重量级管理操作、需重建拓扑且破坏用户态亲和性；显式任务亲和性几乎不可维护。于是需要一种快的、协作式的、内核内的退让机制，且不违反用户/任务亲和性契约。建模选择：用 guest 已看到的 steal time 作为争抢程度的量化——它在 paravirt 世界是既有构造，主流架构都支持。

## 技术方案

（承接 sched-20260909-010）分两层，策略与机制切开。**Layer A（调度器机制 preferred CPUs）**：引入 CPU 状态 preferred，表示「这个 vCPU 可安全使用」，经 `cpu_preferred_mask` 暴露并严格维持为 `cpu_active_mask` 子集；三个介入点——唤醒 `is_cpu_allowed()` 检查、tick 侧 stopper 推送非 preferred CPU 上的当前任务、`sched_balance_rq` 把域 span 限制在 `cpu_preferred_mask` 内。硬约束：绝不破坏用户亲和性。**Layer B（策略引擎 `drivers/virt/steal_governor.c`）**：可加载驱动（`CONFIG_STEAL_GOVERNOR`），按 steal 比例低/高阈值（默认 1000ms 周期、200/500）在 vCPU 间折叠/展开。规模 23 files changed, 804 insertions(+), 19 deletions(-)。

## 版本演进与当前进展

今天 Peter 对 v13 的三枚补丁做了逐枚 review（均带具体 diff 建议），Shrikanth 逐条回应并承诺改 v14：

- **06/13 `is_cpu_allowed()`**：Peter 认为 `task_can_sched_on_preferred()` 返回 false 表示「任务在 preferred CPU 上」读起来很别扭，真正的问法是「能否迁移到 preferred CPU」，并建议加注释。Shrikanth 回贴采纳，函数改名为 `task_can_migrate_to_preferred(struct task_struct *p, int cpu)`。
- **08/13 push current task**：Peter 给出重写版 `sched_non_preferred_cpu_push_stop()`，指出其与 `__balance_push_cpu_stop()` 逻辑几乎一样却「visual different for no reason」，并要求回答多出的 `!is_migration_disabled()` 到底是谁多余。Shrikanth 回：会删掉它——理由 (1) 任务若在 stopper 跑前被远程 CPU 拉走，`task_rq` 检查会失败并 bail out；(2) 该策略当前只覆盖 FAIR，FAIR 任务不可能在 stopper 之前抢先运行。
- **09/13 迁移统计**：Peter 对 `nr_migrations_cpu_non_preferred` 的含义只读出「push 迁移次数」、语义不完整；并要求「既然改了输出格式，是否该 bump schedstat 版本，之前那个 perf schedstat 是否也要适配新格式」。Shrikanth 回：会更新 changelog，其余照办。

版本节奏：v10（08-12）→ v11（08-25）→ v12（09-03）→ v13（09-09），v14 在改。截至今日 Peter 尚未对「入队 sched/core、目标 7.4」明确表态，但已进入逐枚细读阶段，是显著的正向信号。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra 今日四条意见全部是命名/结构/changelog/统计版本级别的收尾性意见，没有一条质疑机制设计本身**（preferred CPU + steal governor 的分层、不破坏亲和性的硬约束、FAIR-only 范围都没有被推翻）。这说明设计层面已基本被接受，剩下的是实现细节的打磨。
- 尚未表态的缺口（承接 09-09）：Peter 对「何时入队、是否冲 7.4」仍未拍板；跨子系统的 `kernel/cpu.c`、`drivers/base/cpu.c`、`drivers/virt/`、`arch/s390/`、`fs/proc/uptime.c` 侧仍无对应维护者 ack；x86/s390 量化数据仍是基于 v2 的旧版本。
- Shrikanth 对四条意见的回应都是「接受并照改」，没有争辩，收口速度快。

## 合入评估

*likelihood=medium*，较 v13 发出当日略有上升——从「无人回帖」进入「维护者逐枚细读并只提收尾意见」。*blocking_issues*：Peter 未就入队时机表态；跨子系统 ack 仍空白；非 PowerPC 证据版本过旧。*next_action*：Shrikanth 按今日四条意见改出 v14 重发；Peter 需对入队时点表态；补齐跨子系统 ack 与 x86/s390 当前版本数据。

## 效果评估

今日无新 benchmark 数据；09-09 封面的 PowerPC 三列对照（baseline/disabled/enabled）与 x86/s390 ΔRPS 表见 related_articles（注意 x86/s390 数据基于 v2，已过期）。暂无新增效果数据。

## 我可以参与的点

- `review`：`drivers/virt/` 新目录、`kernel/cpu.c` 与 `drivers/base/cpu.c` 的 preferred CPU sysfs、`arch/s390/hiperdispatch.c`、`fs/proc/uptime.c` 的对应维护者 ack 仍是空白，逐条提请评审比再提代码细节更有价值。
- `testing`：用 v14（即将发出）重跑 x86 KVM 的 pgbench/hackbench/sysbench 三列对照，替换已过期的 v2 数据。
- `discussion`：09/13 引入新的 schedstat 字段后，perf 侧 `schedstat` 解析工具是否需要适配新格式，Peter 自己都存疑（"did we ever merge that perf schedstat thing"），可以帮忙确认并给出适配 patch。
- `new_patch`：回合到自家分支时按 OLK 规范，`Fixes` 需引用自家 commit。

## 参考链接

- v13 封面: https://lore.kernel.org/all/20260909135617.871006-1-sshegde@linux.ibm.com/
- Peter 对 06/13: https://lore.kernel.org/all/20260925074314.GF4121339@noisy.programming.kicks-ass.net/
- Peter 对 08/13: https://lore.kernel.org/all/20260925074953.GG4121339@noisy.programming.kicks-ass.net/
- Peter 对 09/13（changelog）: https://lore.kernel.org/all/20260925075134.GH4121339@noisy.programming.kicks-ass.net/
- Peter 对 09/13（schedstat 版本）: https://lore.kernel.org/all/20260925154540.GO2009045@noisy.programming.kicks-ass.net/
- Shrikanth 对 06/13（改名）: https://lore.kernel.org/all/3a509e01-6d50-47ed-a53e-2613f2aaee8b@linux.ibm.com/
- Shrikanth 对 08/13: https://lore.kernel.org/all/4e2421fe-4b26-4d92-8709-bfa8d3a4114a@linux.ibm.com/
- Shrikanth 对 09/13: https://lore.kernel.org/all/e152585c-aa6c-4e50-b427-7683e28f8584@linux.ibm.com/

---
id: sched-20260925-010
date: 2026-09-25
subject: "sched, steal_governor: Introduce preferred CPUs and steal-driven vCPU backoff"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260909135617.871006-1-sshegde@linux.ibm.com>"
lore_url: "https://lore.kernel.org/all/20260909135617.871006-1-sshegde@linux.ibm.com/"
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v13
generated_at: "2026-09-26T01:15:00"
authors:
  - "Shrikanth Hegde"
maintainers_involved:
  - "Peter Zijlstra"
patch_series:
  - version: v13
    msgid: "<20260909135617.871006-1-sshegde@linux.ibm.com>"
    date: 2026-09-09
    summary: "改名 npc_push_work_pending、加 CONFIG_PREFERRED_CPU 守卫、更新注释；请求排入 sched/core 冲 7.4"
    review_outcome: "09-25 Peter 逐枚细读 06/08/09 三枚，提命名/结构/changelog/schedstat 版本四条意见；Shrikanth 接受并准备 v14"
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "Peter 尚未对入队 sched/core、目标 7.4 明确表态"
    - "跨子系统（drivers/base/cpu.c、kernel/cpu.c、drivers/virt、arch/s390、fs/proc/uptime.c）ack 仍空白"
    - "x86/s390 量化数据基于 v2，已过期"
  next_action: "Shrikanth 按今日四条意见改出 v14 重发；Peter 表态入队时点；补齐跨子系统 ack 与当前版本数据"
contribution_opportunities:
  - kind: review
    description: "drivers/virt 新目录、preferred CPU sysfs、arch/s390/hiperdispatch.c、fs/proc/uptime.c 的对应维护者 ack 仍空白，可逐条提请评审"
  - kind: testing
    description: "用 v14 重跑 x86 KVM 的 pgbench/hackbench/sysbench 三列对照，替换已过期的 v2 数据"
  - kind: discussion
    description: "09/13 新增 schedstat 字段后 perf schedstat 解析工具是否需适配新格式，Peter 自己存疑，可确认并给适配 patch"
  - kind: new_patch
    description: "回合到自家分支时按 OLK 规范，Fixes 需引用自家 commit"
source_email_count: 8
related_articles:
  - "sched-20260909-010"
  - "sched-20260907-011"
  - "sched-20260905-005"
  - "sched-20260903-002"
  - "sched-20260902-014"
tags:
  - load_balance
  - affinity
  - sched_debug
  - arm64
---