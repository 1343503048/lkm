---
id: sched-20260828-004
date: '2026-08-28'
subject: 'sched/cache: Keep nr_pref_llc_running in the runnable domain'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260827135000.735138-1-zhanxusheng@xiaomi.com>
lore_url: https://lore.kernel.org/all/59e2b8265fc650266b93d8f523c366edfa912428.camel@linux.intel.com/
authors:
- Tim Chen
- Zhan Xusheng
maintainers_involved:
- Tim Chen
current_version: v1
patch_series:
- version: v1
  msgid: <59e2b8265fc650266b93d8f523c366edfa912428.camel@linux.intel.com>
  date: '2026-08-28'
  summary: 在 set_delayed()/clear_delayed() 同步 nr_pref_llc_running 使其落在 runnable 域；account_llc_dequeue()
    跳过仍 delayed 的任务避免二次递减；nr_llc_running 与 sd->llc_counts 保持 queued 语义
  review_outcome: Zhan Xusheng 给出 Reviewed-by 并逐条验证四种计数顺序与三个不会重复计数的路径
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 补丁以回帖内嵌形式投递，未走正式 [PATCH]，无法收集标签
  - 无量化影响数据（错判频率/迁移次数）
  - nr_pref_llc_running 的全部读者是否都能接受 runnable 语义未确认
  next_action: 作者以正式 [PATCH] 重发并确认计数器读者集合
contribution_opportunities:
- kind: review
  description: 核对 nr_pref_llc_running 的全部读者，确认是否有隐含 queued 语义的读者会因口径改变而受影响
- kind: testing
  description: 在多 LLC 机器上测量修复前后被 active balance 迁出首选 LLC 的任务数，补上唯一缺失的证据
generated_at: '2026-09-07T22:08:24'
source_email_count: 2
related_articles:
- sched-20260827-018
- sched-20260830-003
tags:
- load_balance
- topology
- cfs
title: 'sched/cache: Keep nr_pref_llc_running in the runnable domain'
layout: article
---

## TL;DR

一个由提问换来的真 bug：cache-aware scheduling 的 `alb_break_llc()` 用 `nr_pref_llc_running == cfs.h_nr_runnable` 判断"源 rq 上跑的任务是不是全都偏好本 LLC"，但**两个计数器覆盖的集合不同**——`nr_pref_llc_running` 跟着 queued 语义走，`h_nr_runnable` 会扣掉 delay-dequeue 的任务。`DELAY_DEQUEUE` 打开时，一个偏好源 LLC 的任务入睡后仍被计入 `nr_pref_llc_running`，等式破裂 → `alb_break_llc()` 返回 false → active balance 可以把任务从它偏好的 LLC 上拽走。Zhan Xusheng（Xiaomi）8/27 提出疑问，Tim Chen（Intel，CAS 主要维护者）8/28 直接在回帖里给出修复补丁，Zhan 当天回 `Reviewed-by` 并逐条验证了计数不重不漏。修的是主线 CAS 的默认行为，属于可关注的小而确定的修复。

## 背景与问题

Cache-aware scheduling 聚合的守门逻辑之一在 `alb_break_llc()`：active load balance 会破坏 LLC 局部性，所以只有当源 rq 上"所有 runnable 的 fair 任务都偏好源 LLC"时才否决这次 active balance。判据写成两个计数相等：

```
env->src_rq->nr_pref_llc_running == env->src_rq->cfs.h_nr_runnable
```

问题在于两者语义不同源：

- `nr_pref_llc_running` 在 `account_llc_enqueue()`/`account_llc_dequeue()` 里更新，紧邻 `cfs_rq->nr_queued`，走的是 **queued** 语义；
- `h_nr_runnable` 在 `set_delayed()`/`clear_delayed()` 里更新，会**剔除** delay-dequeued 的任务。

于是：起初所有 running 任务都偏好源 LLC；某个偏好源 LLC 的任务在 `DELAY_DEQUEUE` 下入睡 → 它仍被算进 `nr_pref_llc_running`，而 `h_nr_runnable` 下降 → 等式不再成立 → `alb_break_llc()` 返回 false。而 active balance 只搬 runnable 任务，并且**这是它唯一会查阅的 LLC 检查**：stopper 一旦跑起来，`LBF_ACTIVE_LB` 会跳过 `can_migrate_task()` 里的逐任务判断。结果就是任务被从自己的首选 LLC 上迁走。

## 技术方案

Tim Chen 的选择是**在计数器一侧修**，而不是给 `alb_break_llc()` 换判据：让 `nr_pref_llc_running` 与 `h_nr_runnable` 一样落在 runnable 域。

- 新增 `account_llc_delayed()` / `account_llc_requeue_delayed()`，在 `set_delayed()` / `clear_delayed()` 里同步增减 `nr_pref_llc_running`。
- 防重复计数是关键难点，作者的处理：任务入睡时 `set_delayed()` 已把它从计数里减掉；之后真正 dequeue 时 `dequeue_entity()` 会先 `account_llc_dequeue()` 再 `clear_delayed()`，若不动就会"减一次、又加回来"。因此 `account_llc_dequeue()` 在 `p->se.sched_delayed` 仍置位时**跳过**递减，并清掉 `p->pref_llc_queued`，让后续 `clear_delayed()` 也不再动这个计数。
- 有意**不动** `nr_llc_running` 与 `sd->llc_counts`，保持它们的 queued 语义。

备选方案（隐含）：把判据改成"所有 queued 任务都偏好源 LLC"（即让 `h_nr_runnable` 换成 queued 口径）。作者没选，因为 active balance 本身只搬 runnable 任务，判据留在 runnable 域才对得上语义。

补丁元数据里有两处值得留意：`Reported-by: Zhan Xusheng`，以及 **`Assisted-By: Claude Opus 4.8 <noreply@anthropic.com>`**——即这份 commit message 与实现有 LLM 协助成分，这是当日线程里没被任何人评论的一个事实，社区对 LLM 标注的处理仍在演化。

## 版本演进与当前进展

- 8/27 21:50 Zhan Xusheng 发帖提问：`sched/fair: which tasks should nr_pref_llc_running be compared against?`
- 8/28 04:57 Tim Chen 回帖承认问题成立并**在回帖正文里 inline 贴出完整补丁**（未单独发 `[PATCH]` 邮件）：
  > "Thank you for your review of this code. You have a valid point that DELAY_DEQUEUE could cause problem with the check in question. ... I think the proper thing to do is to make sure the nr_pref_llc_running accounts correctly the number of running tasks that prefer the source LLC. And exclude those that are delayed dequeued."
- 8/28 10:20 Zhan Xusheng 回 `Reviewed-by`，并补了一份不重不漏的顺序论证（见下节）。
- 注意：截至本日补丁仍是"回帖内嵌"形态，标题未走 `[PATCH]` 前缀，正式提交与 `lore` 上的独立线程要后续版本才有。

## Maintainer 意见与讨论焦点

**Tim Chen（Intel，CAS 侧维护者）**：认可问题、给出方向明确的最小修复，并且判断依据写得很直白——"Active balance only moves runnable tasks, and this is the only LLC check it consults"。他选择修计数器而不是改判据，理由是 `nr_pref_llc_running` 应与它被比较的那个域一致。

**Zhan Xusheng（Xiaomi，报告方）**：他的 `Reviewed-by` 不是走过场，而是把 Tim 那句"needs care to not count a task twice"完整验证了一遍：

- 指出"跳过递减所依赖的顺序在 diff 里看不见"，于是把它写进邮件留档：`dequeue_hierarchy()`（fair.c:8148）经 `dequeue_entity()` 到达 `account_llc_dequeue()`，而 `clear_delayed()` 要到 8164 才跑，所以测试 `se->sched_delayed` 时它仍置位。
- 列出四条序列并逐条平衡：`enqueue, dequeue` → `+1, -1`；`enqueue, sleep, wake, dequeue` → `+1, -1(set_delayed), +1(clear_delayed), -1`；`enqueue, sleep, 真正 dequeue` → `+1, -1, skip, no re-add`；负载均衡搬动 delayed 任务 → 源侧不变、目的侧 `+1`（此时 `sched_delayed` 已清）。
- 补了三个"不会重复计数"的论证：`requeue_delayed_entity()` 只做 `__enqueue_entity()` + `clear_delayed()`，不经过 `account_entity_enqueue()`；`account_mm_sched()` 看不到 delayed 任务，因为 fair.c:12245 的 `task_running_on_cpu()` 要求 `task_on_rq_queued()` 且调用方是 `update_curr()`；`sd->llc_counts` 保持 queued 语义是对的，因为它的两个读者（fair.c:11895、13228）都是拿 `llc_counts` 与另一个 `llc_counts` 比，delayed 任务两边同时偏移。

分歧：**无**。当日线程里没人质疑这条修复的方向，也没人提出 benchmark 需求。

## 合入评估

**likelihood: likely**。

- 有利：CAS 侧维护者本人写的补丁；问题定义清楚、改动局部（+44/-1，单文件 `kernel/sched/fair.c`）；已有一个由报告方给出的 `Reviewed-by`，且报告方本身就是最了解该判据的人；不需要新配置项、不碰 uapi。
- 卡点：补丁目前是**回帖内嵌**而非正式 `[PATCH]` 投递，需要作者重发才能收集 review 标签；邮件里没有量化影响（哪个负载下会看到不该发生的跨 LLC 迁移）；`nr_pref_llc_running` 的读者是否只有 `alb_break_llc()` 一处，尚需确认——若还有其它读者按 queued 语义理解它，改口径会引入新问题。
- `next_action`：Tim Chen 以正式 `[PATCH]` 重发，并确认 `nr_pref_llc_running` 的全部读者都能接受 runnable 语义；等待 Peter Zijlstra/Ingo 侧的取用。

## 效果评估

**无效果数据**。线程里没有任何 benchmark、没有迁移次数统计、没有"错判频率"的测量，两边都是从语义推导出发下结论。唯一可核对的"影响面"论证是定性的：一旦 `alb_break_llc()` 误判返回 false，`LBF_ACTIVE_LB` 会跳过 `can_migrate_task()` 的逐任务 LLC 检查，所以**没有第二道闸门**拦住这次迁移——这也是为什么两人认为值得修。修复的实际收益（减少多少无谓跨 LLC 迁移）目前无人测量。

## 我可以参与的点

- **提供第二读者视角**（这条最实在）：全量核对 `nr_pref_llc_running` 在内核里的读者集合，确认是否只有 `alb_break_llc()` 按 runnable 域理解它；如果发现有读者隐含 queued 语义，这就是上游需要的那条 review。
- **量化收益**：`perf stat -e 'sched:sched_migrate_*'` + `sd->llc_counts`/`nr_pref_llc_running` 的 tracepoint 或 `bpf` 探针，在开 `DELAY_DEQUEUE` 的多 LLC 机器上测修复前后"被 active balance 迁出首选 LLC 的任务数"，直接回帖——这是当前线程唯一缺的证据。
- **`DELAY_DEQUEUE` 交互排查**：如果内部内核同时开了 delay dequeue 和 cache-aware 类聚合逻辑（或自研的 LLC 亲和策略），这是同一类"两个计数器口径不一致"的坑，可以按同样方法自查一遍本地实现的记账点是否都在 `set_delayed()`/`clear_delayed()` 上同步。
- **回合判断**：主线 CAS 落地晚于 6.6，OLK-6.6 无 `nr_pref_llc_running`，本补丁不可直接回合；但其结论（delayed 任务会让"所有任务都偏好 X"这类全称判据失效）适用于任何按 rq 计数器做 LLC/NUMA 亲和判断的自研逻辑。
- 顺带可以观察的一点：补丁带 `Assisted-By: Claude Opus 4.8` 而当天无人对此表态。若社区后续对 LLM 标注提出流程意见，这条会是一个可观察样本。

## 参考链接

- 修复补丁（内嵌于 Tim Chen 回帖）: https://lore.kernel.org/all/59e2b8265fc650266b93d8f523c366edfa912428.camel@linux.intel.com/
- Zhan Xusheng 的提问（线程根）: https://lore.kernel.org/all/20260827135000.735138-1-zhanxusheng@xiaomi.com/
- Zhan Xusheng 的 Reviewed-by 与顺序论证: https://lore.kernel.org/all/20260828022012.936112-1-zhanxusheng1024@gmail.com/
- 相关代码: `kernel/sched/fair.c` `account_llc_enqueue()` / `account_llc_dequeue()` / `set_delayed()` / `clear_delayed()` / `alb_break_llc()` / `dequeue_hierarchy()`
- tip-bot commit: 未获取到
- stable backport: 未获取到
