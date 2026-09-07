# sched: irq: cpu-hotplug race vs set_cpus_allowed_ptr()

## TL;DR

Sebastian Andrzej Siewior（linutronix）09-07 16:58 发出 RFC：syzbot 报出的一个 CPU 热插拔与 `set_cpus_allowed_ptr()` 的竞态——IRQ 线程在 `irq_thread_check_affinity()` 里请求迁移到一个「当时在线、但可能马上掉线」的 CPU，`__migrate_task()` 被 `is_cpu_allowed()` 拒掉后返回当前 rq，结果任务所在 CPU 与 `task_struct::cpus_mask` 不再匹配，后续 `migrate_enable()` 会去改亲和性而 `affine_move_task()` 却等不到 `migration_pending`。他给了两种互斥的修法（IRQ 侧持 `cpus_read_lock`；或让 `migration_cpu_stop()` 在迁移失败时把当前 CPU 补进 `cpus_mask`），并称能复现到 v6.8、「大概从 migrate-disable 诞生第一天就在」。本日以 RFC 形式孤零零一封，无人表态。

## 背景与问题

触发链条（作者原文梳理，以下为转述加关键原文引用）：

1. 有人改了某个 IRQ 的亲和性，IRQ-core 置 `IRQTF_AFFINITY` 并唤醒相关中断线程去调整自己的掩码；
2. 线程调 `set_cpus_allowed_ptr()` 更新掩码，据此挑一个应运行的 CPU。作者强调：「It is verified that this CPU is online however there is no guarantee that this CPU remains online while affine_move_task() is moving _this_ task.」由于是当前任务自己请求迁移，会走 stopper/`migration_cpu_stop()`，任务在此期间会暂停一会儿；
3. 若这段时间该 CPU 掉线（不再在 `cpu_online_mask` 里），`__migrate_task()` 因 `is_cpu_allowed()` 拒绝而返回**任务当前所在**的 rq，这个 rq 与它的 `task_struct::cpus_mask` 不一致。

后果（作者标题为 "The aftermath"）：IRQ 线程所在 CPU 与 `cpus_mask` 不匹配。之后一次 `migrate_disable() -> schedule()` 会改 `cpus_ptr`，从而保证随后的 `migrate_enable()` 把任务更新到请求的亲和掩码上；但此时 `affine_move_task()` 期望 `task_struct::migration_pending` 已被置位，而它是 NULL——因为「在 migrate-disable 区间内」根本没人请求过亲和性变更。

值得注意的是主线代码里本来就有一段自认的软肋，与本 RFC 指向同一处（我在 `~/code/linux` 的 `kernel/sched/core.c:2671` 附近读到，非邮件内容）：

```c
/*
 * XXX __migrate_task() can fail, at which point we might end
 * up running on a dodgy CPU, AFAICT this can only happen
 * during CPU hotplug, at which point we'll get pushed out
 * anyway, so it's probably not a big deal.
 */
```

作者这封邮件等于给出了一例「it *is* a big deal」：被推出去的那一步本身依赖 `migration_pending`，而它此刻是空的。

## 技术方案

作者同时实现了两条路，明确说「Both changes are implemented to illustrate, one is enough」：

- **路线 A（genirq 侧收口）**：在 `irq_thread_check_affinity()` 里把 `set_cpus_allowed_ptr(current, mask)` 包进 `scoped_guard(cpus_read_lock)`（新增 `#include <linux/cpuhplock.h>`），保证迁移期间目标 CPU 一直在 `cpu_online_mask` 中；掩码若已失效则直接被拒。他还抛出一个更强的问题：「Maybe we should also check if cpus_read_lock is held during the invocation of set_cpus_allowed_ptr() so we don't get this problem from other callers.」——即把「持 cpu hotplug 锁」变成所有调用者的契约。
- **路线 B（sched 侧兜底）**：在 `migration_cpu_stop()` 里，`__migrate_task()` 返回后若 `rq != cpu_rq(arg->dest_cpu)`，就 `cpumask_set_cpu(rq->cpu, &p->cpus_mask)`，把实际所在 CPU 纳入掩码，从而避免被 `migrate_enable()` push。作者自评这条路的味道：「It might be a bit inconsistent and feels a bit like select_fallback_rq() without the printk.」

改动量：`kernel/irq/manage.c | 6 ++++--`、`kernel/sched/core.c | 2 ++`。

取舍上，A 把责任推给调用者（可能牵出大量其它调用点），B 保持 `set_cpus_allowed_ptr()` 现有语义但让 `cpus_mask` 被事后修正（可能与 `sched_class::set_cpus_allowed` 看到的掩码不一致，作者自己也点了 "did not see this mask"）。

## 版本演进与当前进展

- 09-07 16:58 Sebastian Andrzej Siewior 发出 RFC 单补丁，in-reply-to 的是 syzbot 的原始报告（`<6a9919ac.94649fcc.25487e.0005.GAE@google.com>`，正文 `Closes:` 指向该链接）。
- 本日无 v2、无任何回帖。
- 作者给出的历史定位：「I can reproduce this back on v6.8, therefore I assume we have this since day #1 of migrate-disable.」——即不是新回归，而是长期存在的竞态。

## Maintainer 意见与讨论焦点

未获取到：本日邮件里没有任何维护者回应，也谈不上分歧或共识。目前悬着、需要有人回答的问题有三个（都出自作者本人）：

1. 选 A 还是 B（他明确说两条只留一条）；
2. 是否要把「调用 `set_cpus_allowed_ptr()` 必须持 `cpus_read_lock`」升级成通用检查——这会牵动 genirq 之外的大量调用者，也意味着 `cpus_read_lock` 与 rq 锁的顺序要重新论证；
3. B 方案直接改 `p->cpus_mask` 是否与 `sched_class::set_cpus_allowed()` 看到的掩码/队列状态自洽（作者自己承认 "might be a bit inconsistent"）。

另外邮件未说明该竞态在 syzbot 下最终表现为什么（`WARN`、`migration_pending` 断言失败还是任务卡住），要判定严重度需要去看出现在 `Closes:` 里的原始报告。

## 合入评估

`likelihood=unknown`。这是带两个候选方案的 RFC，作者本人没有倾向性表态，且尚未触及 `kernel/sched/core.c` 中 `affine_move_task()`/`migrate_enable()` 的核心约定；本日无人回帖，既无支持也无反对，因此无法判断走向。可以确定的是它不是「新引入的回归」，所以不会走紧急通道；真正的卡点是**语义选择**：约束调用者（A，扩散面大、易被其它子系统反对）还是让调度器容忍掩码被修正（B，改动小但把不一致状态写进 `cpus_mask`）。若走 A，需要面对「大量非 IRQ 调用者是否已经隐式持锁」的排查；若走 B，需要回答 `migration_pending` 的等待语义是否仍成立。

## 效果评估

无效果数据，也无量化影响：邮件里没有 syzbot 复现脚本、没有触发概率、没有性能数字，作者给的是「可复现到 v6.8」这一时间维度的证据。路线 A 引入的成本（在 `irq_thread_check_affinity()` 外围持 `cpus_read_lock`，与热插拔写锁互斥）没有任何开销或死锁分析——这是后续 review 大概率会问而目前无人回答的点。

## 我可以参与的点

- 讨论（最有价值的一步）：作者公开征求「是否应检查 `set_cpus_allowed_ptr()` 调用时已持 `cpus_read_lock`」。可以用 `git grep set_cpus_allowed_ptr` 梳理自己内核里的调用点，统计有多少确实不持热插拔锁，并检查 `cpus_read_lock()` 与 rq 锁的现有先后顺序，回帖给出可行性判断。这类「影响面清单」目前没人提供。
- 测试：作者说能复现到 v6.8。在有 CPU 热插拔 + 频繁改 IRQ 亲和性的环境（`smp_affinity` 压测与 `echo 0 > online` 并发）里，把 `migrate_disable`/`migrate_enable` 与 `WARN` 插桩打开验证是否可稳定复现，对社区定级为 bug/urgent 有直接帮助。
- 自家分支（new_patch）：我核对了 `~/code/olk-6.6`，同一处两个特征都在——`kernel/irq/manage.c:1171` 的 `set_cpus_allowed_ptr(current, mask)` 外层没有 `cpus_read_lock`，`kernel/sched/core.c:2505` 的 `migration_cpu_stop()` 也没有对 `__migrate_task()` 失败作处理（其下方仍留着那段 `XXX __migrate_task() can fail` 注释）。若我们的 cpuset/中断亲和场景里做过 hotplug，值得独立复现一次；上游方案定了之前不要照着改 `cpus_mask`，两条路线语义差异不小。
- 观察点：该线程一旦有 Peter Zijlstra/Thomas Gleixner/Ingo 任一方表态，会直接影响 `set_cpus_allowed_ptr()` 的契约是否收紧，这对所有依赖它的子系统（含 cpuprt/cpuset、workqueue、drivers）都是要提前知道的变更。

## 参考链接

- RFC 邮件: https://lore.kernel.org/all/20260907085825.f-CZ1Q5y@linutronix.de/
- syzbot 原始报告（正文 `Closes:` 指出的线程根）: https://lore.kernel.org/all/6a9919ac.94649fcc.25487e.0005.GAE@google.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260907-002
date: '2026-09-07'
subject: 'sched: irq: cpu-hotplug race vs set_cpus_allowed_ptr()'
subsystem: sched
type: bug
status: rfc
severity: medium
thread_root_msgid: <20260907085825.f-CZ1Q5y@linutronix.de>
lore_url: https://lore.kernel.org/all/20260907085825.f-CZ1Q5y@linutronix.de/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: '2026-09-07'
authors:
- Sebastian Andrzej Siewior
maintainers_involved: []
patch_series:
- version: v1-rcf
  msgid: <20260907085825.f-CZ1Q5y@linutronix.de>
  date: '2026-09-07'
  summary: RFC 列出两种互斥修法：genirq 侧用 scoped_guard(cpus_read_lock) 包住 irq_thread_check_affinity() 里的 set_cpus_allowed_ptr()（并讨论是否要求所有调用者持该锁）；或 sched 侧在 migration_cpu_stop() 中当 __migrate_task() 未落到 dest_cpu 时把当前 CPU 补进 p->cpus_mask。改动 kernel/irq/manage.c +6/-2、kernel/sched/core.c +2。
  review_outcome: 本日无人回帖，无 Ack 无 NAK，作者也未表示倾向。
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 作者公开征求 A/B 两条路线的选择，社区尚未表态
  - 是否要求所有 set_cpus_allowed_ptr() 调用者持 cpus_read_lock 会牵动其它子系统，影响面未梳理
  - B 方案直接改 p->cpus_mask 与 sched_class::set_cpus_allowed() 的自洽性作者自己存疑
  - 邮件未说明 syzbot 下的最终症状（WARN/挂死），严重度与优先级待定
  next_action: 由调度器与 genirq 维护者定路线；社区可提供调用点清单与稳定复现
contribution_opportunities:
- kind: discussion
  description: 梳理 set_cpus_allowed_ptr() 的调用者中有多少不持 cpus_read_lock，并检查其与 rq 锁的顺序，回应作者「是否应通用检查」的提问
- kind: testing
  description: 在 CPU 热插拔与频繁修改 IRQ 亲和性并发的场景下加桩复现，确认影响版本范围（作者称可复现到 v6.8）
- kind: new_patch
  description: 自家 OLK-6.6 同处缺少保护（kernel/irq/manage.c 的 set_cpus_allowed_ptr 未持 cpus_read_lock、migration_cpu_stop 未处理 __migrate_task 失败），可先独立复现评估，待上游定路线后再决定回合形态
source_email_count: 1
related_articles: []
tags:
- affinity
- preempt
- hang
- syzbot
---
