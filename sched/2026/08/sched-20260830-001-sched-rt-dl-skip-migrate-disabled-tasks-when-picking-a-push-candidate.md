# sched/rt,dl: Skip migrate-disabled tasks when picking a push candidate

## TL;DR

Seiji Nishikawa（Red Hat）单补丁：`migrate_disable()` 过的 RT/DL 任务**仍留在该 CPU 的 pushable 列表里、且 rq 仍被标为 overloaded**，于是 RT 均衡器反复试图把它推走；推不动时 `push_rt_task()` 会退化成用 per-CPU stopper 去推 `rq->curr`，而这条回退路径的复检（`task != pick_next_pushable_task(rq)`）**必然失败**，形成每 ~17 µs 一轮的死循环。作者给了完整的 ftrace 数据：一个 89 ms 窗口里隔离核有 **37.18 ms 花在什么也没搬的 stopper 上**，wake stopper 5204 次、真正完成的 push 只有 1 次。做法很小：在 `pick_next_pushable_task()`/`pick_next_pushable_dl_task()` 的跳过条件里加 `is_migration_disabled(p)`。证据充分、改动 4 行，当天无人回复。

## 背景与问题

- **场景**：为一个 RT 用途隔离出来的 CPU，上面两个同优先级 `SCHED_FIFO` 任务——taskA 已 `migrate_disable()` 并入队，taskB 是 `rq->curr`。
- **症状与量化数据**（作者用 `sched_switch` + 自行添加的 RT 均衡器 tracepoint 采得）：一个 89 ms 窗口内
  - taskB 只拿到 **51.95 ms** 真实 CPU，`migration/N` .stopper 吃掉 **37.18 ms** 且什么都没搬，taskA **0.00 ms**（一直 runnable 在队、从未被选中），idle 0.01 ms；
  - 计数：本核处理 **7667** 次 push-IPI、`pick_next_pushable_task()` **17481** 次返回仍被钉住的 taskA、`find_lock_lowest_rq()` **5204** 次在复检处放弃、真正完成的 push **1** 次、taskA 的迁移 **0** 次。
- **根因链条**（作者描述，已核对主线代码成立）：
  1. `migrate_disable()` 的任务不能被移动，但它**没有被从 `rq->rt.pushable_tasks` 摘掉**，`rq->rt.overloaded = 1` 也仍在；
  2. 于是别的 CPU 在自身 RT 均衡时不断向该核发 push-IPI，该核上的 `push_rt_task()` 看着队头 taskA 推不动，就回退去推 `rq->curr`（taskB）——该回退由 `a7c81556ec4d`（"sched: Fix migrate_disable() vs rt/dl balancing"）引入，走 per-CPU stopper；
  3. `find_lock_lowest_rq()` 为了取目标 rq 锁会放掉本 rq 锁，回来后复检 `task != pick_next_pushable_task(rq)`；被推的是 taskB，但 `pick` 返回队头 taskA——因为 `set_next_task_rt()` 会把正在运行的任务从 pushable 列表里摘掉，**taskB 永远不可能成为队头**，所以复检**每次都失败**；
  4. 循环无法自止：每轮之后 rq 状态完全不变，下一枚 push-IPI 再做同样的事。作者的采样里它只在 taskB 自己睡着时才结束，随后 taskA 才被本地选中并离开 pushable 列表。
- **已有的半截修复**：自发 IPI 那条路已被 `94894c9c477e`（"sched/rt: Skip currently executing CPU in rto_next_cpu()"）堵住且有效；但 rq 仍被标 overloaded，所以**别的 CPU 会继续把 IPI 打过来**，同一个循环照跑。

## 技术方案

一个"钉住的任务从一开始就不该被当成 push 候选"的判断，与 `e0ca8991b2de`（"sched: Make class_schedulers avoid pushing current, and get rid of proxy_tag_curr()"）为 `task_on_cpu()` 加的跳过同一形状：

```c
 	plist_for_each_entry(i, head, pushable_tasks) {
-		/* make sure task isn't on_cpu (possible with proxy-exec) */
-		if (!task_on_cpu(rq, i)) {
+		/* skip tasks that cannot be migrated */
+		if (!task_on_cpu(rq, i) && !is_migration_disabled(i)) {
```

`kernel/sched/rt.c` 与 `kernel/sched/deadline.c` 各一处（`pick_next_pushable_task()` / `pick_next_pushable_dl_task()`），共 +4/−4。

加上跳过之后的行为：若队头（唯一多出来的可运行任务）被钉住，helper 直接返回 `NULL`，`push_rt_task()`/`push_dl_task()` 提前放弃，不再唤醒 stopper；被钉住的任务在 `curr` 让出后就地运行；如果钉住任务后面还排着一个真能迁移的任务，它现在会被正确挑出并推走。作者并指出：这让"回退去推 `rq->curr`"这条路在队头被钉住时**不可达**，而"没有损失，因为那条路本来就被复检挡死"——采样里它跑了 5204 次、什么都没搬。

`Fixes: a7c81556ec4d`，即把回退推 curr 机制引进来的那个提交。

## 版本演进与当前进展

- 8/30 15:37（北京时间）v1 发出，当日**无任何回复**，无 Acked-by/Reviewed-by。
- 本地主线树（`/home/zq/code/linux`）核对：`pick_next_pushable_task()`/`pick_next_pushable_dl_task()` 当前仍只有 `if (!task_on_cpu(rq, i))`，即该问题在主线尚未修复，`Fixes:` 指向的 `a7c81556ec4d` 已存在。
- 没有 v2 迹象，`Cc: stable` 本邮件也未加。

## Maintainer 意见与讨论焦点

- 本日内没有维护者表态，因此没有已确认的分歧；可以从补丁本身预判的争点有两处：
  1. **只修候选挑选、不修状态**：`rq->rt.overloaded` 与被钉住任务留在 pushable 列表这两件事都没动。修完之后，钉住任务仍会让本核被别的 CPU 持续 push-IPI（只是每轮更早退出、不再唤醒 stopper）。作者自己论证了"pinned task should never have been returned as a push candidate in the first place"，但"是否该在 `migrate_disable()` 时把它摘出列表/清 overloaded"仍是悬着的下一步。
  2. **回退路径的存废**：作者证明了队头被钉住时"推 `rq->curr`"必然被复检拦下，但 `a7c81556ec4d` 引入该回退时是有目的的（`migrate_disable()` vs rt/dl 均衡），跳过条件收紧后那个原始问题是否仍被覆盖，需要 RT 维护者确认。
- 未见任何人质疑数据本身。

## 合入评估

**possible**，且倾向正面：问题被完整量化（tracepoint 级别的因果链，而不只是"我看到变慢了"），修复是 4 行、有明确 `Fixes:`、并复用同文件里已有的 `task_on_cpu()` 跳过模式。RT/DL 侧维护者需要确认上面两点，尤其第 2 点关系到 `a7c81556ec4d` 的原始意图；这类小补丁一旦拿到 RT 维护者的 Reviewed-by 通常会被直接收走。尚未进 tip/stable（未获取到）。

## 效果评估

本条是当天少见的**有数字**的修复：89 ms 窗口内 51.95 ms / 37.18 ms / 0.00 ms 的每任务 CPU 分布、7667 次 push-IPI、17481 次队头命中、5204 次复检放弃、1 次成功 push、0 次 taskA 迁移——即该隔离核约 **42%** 的时间被无效的 push 循环吃掉。需要注意的是：这份数据是"问题现场"的量化，作者**没有给出打补丁后的对照测量**（例如窗口内 stopper 时间是否归零）。

## 我可以参与的点

- **补一个"补丁后"的对照 trace**：作者只证明了问题的存在，没证明修复把开销清零。任何人都可以在同型机器上复现 + 打补丁，回帖给出前后对比，这是本线程最可能被引用的第一份第三方数据。
- **推到 cpuset/isolcpus 交叉场景**：`migrate_disable()` + 隔离核 + 同优先级 FIFO 任务的组合，和 cpuset 独占核、isolcpus/housekeeping 的部署形态直接相关；可以验证在"任务被 cpuset 限死在一个核 + 用户态 `migrate_disable()`"这类真实业务形态下同一循环是否出现（这类负载社区通常没覆盖）。
- **追问第二步**：是否应该在 `migrate_disable()` 时把任务摘出 pushable 列表/或在不满足"存在可推任务"时清 `overloaded`，从而消掉跨核 push-IPI 流量。这需要一个更强的方案，适合以回帖形式先提出来讨论。
- **回合判断**：4 行、低风险、有 `Fixes:`，若 OLK-6.6 带 RT/DL push balance 且线上有隔离核 + `migrate_disable()` 的组合，属于可直接跟进的候选；上游尚未合入，建议等 RT 维护者表态后再动。

## 参考链接

- lore thread（v1，当日唯一邮件）: https://lore.kernel.org/all/20260830073746.2189355-1-snishika@redhat.com/
- 相关已有修复（自发 IPI 侧，`94894c9c477e`）: 邮件正文引用，未获取到独立 lore 链接
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260830-001
date: '2026-08-30'
subject: "sched/rt,dl: Skip migrate-disabled tasks when picking a push candidate"
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: "<20260830073746.2189355-1-snishika@redhat.com>"
lore_url: "https://lore.kernel.org/all/20260830073746.2189355-1-snishika@redhat.com/"
authors: [Seiji Nishikawa]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260830073746.2189355-1-snishika@redhat.com>"
    date: 2026-08-30
    summary: "在 pick_next_pushable_task()/pick_next_pushable_dl_task() 的跳过条件里加 is_migration_disabled()，避免钉住任务引发 push_rt_task() 回退推 curr 的无效循环"
    review_outcome: "v1 刚发出，暂无 review 意见"
upstream_commit: null
fixes_commit: "a7c81556ec4d"
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "RT/DL 维护者尚未表态，需确认收紧跳过条件后 a7c81556ec4d 的原始场景仍被覆盖"
    - "未清理 rq->rt.overloaded 与 pushable 列表本身，跨核 push-IPI 流量仍在"
    - "缺少打补丁后的对照 trace 数据"
  next_action: "等 RT 维护者 review；补前后对照测量，并讨论是否顺带解决 overloaded 状态"
contribution_opportunities:
  - kind: testing
    description: "复现隔离核 + 同优先级 FIFO + migrate_disable() 的循环，并给出打补丁后的 CPU 时间/计数对照数据"
  - kind: review
    description: "验证收紧 push 候选后 a7c81556ec4d 想解决的 migrate_disable() vs rt/dl 均衡场景没有被漏掉"
  - kind: discussion
    description: "追问是否应在 migrate_disable() 时摘出 pushable 列表或清 overloaded，以消除无效的跨核 push-IPI"
generated_at: "2026-09-07T22:06:23"
source_email_count: 1
related_articles: []
tags: [rt, deadline, affinity]
---
