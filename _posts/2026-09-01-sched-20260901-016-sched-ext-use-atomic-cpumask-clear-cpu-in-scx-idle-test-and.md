---
id: sched-20260901-016
subject: 'sched_ext: Use atomic cpumask_clear_cpu in scx_idle_test_and_clear_cpu()'
date: '2026-09-01'
subsystem: sched
type: fix
status: stalled
severity: low
thread_root_msgid: <20260901152212.1691696-1-michalblk@google.com>
lore_url: https://lore.kernel.org/all/20260901152212.1691696-1-michalblk@google.com/
authors:
- Michal Blaszczyk
maintainers_involved:
- Andrea Righi
current_version: v1
patch_series:
- version: v1
  msgid: <20260901152212.1691696-1-michalblk@google.com>
  date: '2026-09-01'
  summary: 'scx_idle_test_and_clear_cpu() 中 __cpumask_clear_cpu -> cpumask_clear_cpu；Fixes:
    48849271e661；1 文件 +1/-1'
  review_outcome: 09-01 当日无回帖；09-02 Andrea Righi 指出 cpumask_andnot/cpumask_or 同样非原子且该掩码设计上是
    racy/self-correcting，要求改写为 best-effort 并给数据；作者 09-02 撤回，无 v2
upstream_commit: null
fixes_commit: 48849271e661
merged_branch: null
merge_assessment:
  likelihood: rejected
  blocking_issues:
  - 仅原子化单个清位，未覆盖同一掩码上的 cpumask_andnot()/cpumask_or() 批量非原子写，竞态窗口未真正关闭
  - 该 idle SMT 跟踪本身按 racy and self-correcting 设计，作者无法给出可观测收益或工作负载数据
  - 作者 09-02 主动 drop，无 v2
  next_action: 无需跟进；如重开须整份 idle_smts 写点统一原子化并附 KCSAN 报告与快路径开销数据
contribution_opportunities:
- kind: review
  description: 把本案作为自家 KCSAN/Sashiko 告警 triage 清单样本：先确认数据结构并发契约，再核对同一对象全部写点
- kind: extend
  description: 在带 48849271e661 的自家分支上 grep idle_smts 写点，确认是否只有已知的三处非原子写
source_email_count: 3
related_articles:
- sched-20260901-013
- sched-20260901-017
tags:
- sched_ext
- idle
generated_at: '2026-09-07'
title: 'sched_ext: Use atomic cpumask_clear_cpu in scx_idle_test_and_clear_cpu()'
layout: article
---

## TL;DR

Michal Blaszczyk（Google）把 `kernel/sched/ext/idle.c` 里对共享 `idle_smts` 掩码的一次 `__cpumask_clear_cpu()` 换成原子的 `cpumask_clear_cpu()`，理由是 `__cpumask_*` 是非原子 RMW，同字（word）内的并发清位会丢更新。补丁只改 1 行，带 `Fixes: 48849271e661`。**09-01 当日无人回帖**；后续（09-02）Andrea Righi 指出同一函数里 `cpumask_andnot()` 与 `update_builtin_idle()` 里的 `cpumask_or()` 同样是非原子的、且这份 idle SMT 跟踪本来就按「racy and self-correcting」设计，作者随即**主动撤回**了这个补丁。真正的价值不在这个 diff，而在于它给出了一个「Sashiko 类静态分析报出来的并发缺陷，如何被维护者以设计契约驳回」的完整样本。

## 背景与问题

`scx_idle_test_and_clear_cpu()` 是 sched_ext built-in idle 跟踪的快路径：先从 node 级 SMT 掩码里取该 CPU 所属 SMT 组，再清 `idle_smts`，最后清 `idle_cpus`。`idle_smts` 被多个 CPU 无锁并发修改——函数名里没有 `_locked`，外层也没有 rq/`scx_builtin_idle` 之类的锁保护，作者正是抓这一点：

> In scx_idle_test_and_clear_cpu(), the shared idle_smts mask is modified locklessly by concurrent CPUs. Currently, the code uses __cpumask_clear_cpu() to clear a CPU from the mask.

> Because this is a non-atomic read-modify-write operation, concurrent modifications to different bits within the same memory word can lead to data races and lost updates.

这在语义上成立：`__cpumask_clear_cpu()` 走的是非原子的 clear_bit，即对目标字做一次 load / `&= ~BIT(...)` / store。两个 CPU 各自清同一个 `unsigned long` 里的不同位时，只要这两步交错，后写的那次 store 就会把前一次清掉的位重新写回 1——典型的 lost update。

## 技术方案

单点替换，1 文件 +1/-1：

```
-			__cpumask_clear_cpu(cpu, idle_smts);
+			cpumask_clear_cpu(cpu, idle_smts);
```

`cpumask_clear_cpu()` 用 `clear_bit()`，是架构提供的原子位操作，代价是一条带锁前缀/LL/SC 的原子指令（arm64 上 `clrex`/`stxr` 重试）。作者在 commit message 里**没有**给出触发场景、观测到的错误调度行为或任何性能数据，`Fixes:` 指向 `48849271e661 ("sched_ext: idle: Per-node idle cpumasks")`。

被指出的不完整之处（Andrea Righi，09-02）：同一函数上分支 `cpumask_andnot(idle_smts, idle_smts, smt)` 与 `update_builtin_idle()` 里的 `cpumask_or()` 是对同一掩码的**批量非原子写**，只原子化单个清位并不能关闭竞态窗口；且该处非原子是**有意为之**——"this non-atomic handling was intentional to avoid lock overhead on the fast path"（作者 09-02 读码后的结论）。

## 版本演进与当前进展

- **v1（09-01 23:22，`<20260901152212.1691696-1-michalblk@google.com>`）**：`__cpumask_clear_cpu` → `cpumask_clear_cpu`，`Fixes: 48849271e661`。当日线程内无任何回帖，也未进任何分支。
- 09-02 00:20 Andrea Righi（`<apb7OapVwIDZV3D4@gpd4>`）：认可原子化本身合理，但「does not fully address the race」，并指出该跟踪一直是 documented as racy and self-correcting，要求把 commit message 改成「best-effort improvement」并询问是否有工作负载收益数据。
- 09-02 16:07 作者（`<CAD=VTGdfHkt6QfEOOYWBkGaP5dM-eTCFtFA6z-ECyqm+UbXB=A@mail.gmail.com>`）：说明来源是 Sashiko 自动化静态分析报告，自己误判成孤立疏漏；结论是撤回——"Making just this one operation atomic while the rest of the mask is manipulated non-atomically would just be inconsistent and add unnecessary overhead."
- 无 v2。

## Maintainer 意见与讨论焦点

- **Andrea Righi（NVIDIA）**：没有 NAK 措辞，但用两条论据实质上否掉了「这是个需要修的逻辑 bug」的定性：(1) 竞态不完整覆盖（`cpumask_andnot`/`cpumask_or` 同源非原子）；(2) 该子系统契约本身就是「racy and self-correcting」，丢一次更新的后果是下次 idle 事件被自我纠正，而不是永久错位。他还追问「Did you notice any improvements/benefits with some workloads with this patch applied?」——把举证责任交回作者。
- **Tejun Heo**：09-01 未回帖，未表态。
- 焦点最终不在技术细节，而在**定级**：是 concurrency bug（→ `Fixes:` → stable）还是 best-effort 微优化（→ 需 benchmark 支撑，且要么全做要么不做）。作者承认前者是自己误判，遂撤。

## 合入评估

`likelihood = rejected`（作者自行 drop，无人合入）。卡点很明确：改动不能关闭完整竞态窗口，而完整关闭要在 `idle_smts` 的所有写点（单点清位 + `cpumask_andnot` + `cpumask_or`）统一改成原子操作，这恰恰与该快路径避免锁开销的设计相反。若将来真要重开，正确的补丁形态应是「把整份 `idle_smts` 的写全部原子化并附 KCSAN 报告 + 快路径开销数据」，而不是这一行。`Fixes: 48849271e661` 也就没有生效，stable 分支不会收到任何东西。

## 效果评估

**无任何实测数据**——这正是它站不住的地方。作者自述动机是消除静态分析告警，而非可观测的调度异常：没有复现步骤、没有 hang/wrong-idle 统计、没有 hackbench/schbench 之类前后对比，被 Andrea 直接问到有没有收益数据后也没有补。因此「修好了什么」只能停在理论层面：消除一处 lost update 的可能，代价是每次清位从普通 `&=` 变原子指令。

## 我可以参与的点

- **把这条教训用在自家静态告警的 triage 上**：这是「工具报的并发缺陷 ≠ 需修的 bug」的典型样本。自家若在用 KCSAN / Sashiko 类工具扫 sched 代码，回帖前必须先确认该数据结构的**并发契约**（这里是 documented as racy and self-correcting），并检查同一对象的**全部**写点是否同源非原子，否则很容易提一个像本补丁一样被一轮问掉的补丁。
- **可做的一次自查**（不需要等上游）：在自家带 `kernel/sched/ext/idle.c` per-node idle cpumask（`48849271e661` 之后）的分支上，grep `idle_smts` 的所有写点，确认是否只有这三处；如果自家还有额外改动引入第四处非原子写，那才是值得提补丁的地方。
- **不建议**跟着做「单点原子化」：一致性比这半颗药更值钱，本线程里作者已经替我们验证过这个结论。

## 参考链接

- lore thread (v1): https://lore.kernel.org/all/20260901152212.1691696-1-michalblk@google.com/
- Andrea Righi 09-02 质疑: https://lore.kernel.org/all/apb7OapVwIDZV3D4@gpd4/
- 作者 09-02 撤回: https://lore.kernel.org/all/CAD=VTGdfHkt6QfEOOYWBkGaP5dM-eTCFtFA6z-ECyqm+UbXB=A@mail.gmail.com/
- tip-bot commit: 未获取到（补丁已被作者撤回）
- stable backport: 未获取到
