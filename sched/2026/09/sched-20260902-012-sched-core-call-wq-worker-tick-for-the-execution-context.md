# sched/core: Call wq_worker_tick() for the execution context

## TL;DR

Hui Su 的 proxy execution 记账修正：`sched_tick()` 把 `rq->donor` 传给 `wq_worker_tick()`，
而 workqueue 的 CPU 时间记账与 CPU-intensive 判定属于**执行上下文**，应该传 `rq->curr`。
补丁只有 +5/-4，带 `Fixes: af0c8b2bf67b ("sched: Split scheduler and execution contexts")`。
workqueue 维护者 Tejun Heo 在 12 小时内给了 `Acked-by`，并直接把路由问题抛给 Peter Zijlstra：
"Peter, how do you want to route this patch? It can go through either sched or wq."
截至 9/7 调度侧无人接话。这是同一作者 5 封「donor/curr 语义外溢」修正中的一封，
同系列里最长的一条线（numa/cache task tick）已经被 Tim Chen 要求改到上一层去做。

## 背景与问题

proxy execution 把上下文拆成两半之后（`af0c8b2bf67b`），`sched_tick()` 里的分工是：调度侧记账走
`rq->donor`，`sum_exec_runtime` 走 `rq->curr`。作者指出 `wq_worker_tick()` 站错了边——它做的是
「当前真正在跑的 kworker」的 CPU 时间统计和 `WORKER_CPU_INTENSIVE` 检测，与 worker pool 的
并发管理（concurrency management）联动。原文给出的两类错法：

- donor 不是 worker、`curr` 是 worker：kworker 代跑时被跳过 workqueue 记账，作者写的是
  "can delay WORKER_CPU_INTENSIVE handling and pool concurrency management, which can delay
  pending kernel work and userspace operations depending on it."
- donor 是 worker、`curr` 是别的任务：会给一个**已经阻塞**的 kworker 记账。

也就是说这不是纯理论修正：方向上一个是「该限流的 worker 没被限流」，一个是「给不在跑的 worker 记了时间」。

## 技术方案

只改 `kernel/sched/core.c` 的 `sched_tick()`（+5/-4，`base-commit: 89a312991dc6e638a36adc43ccb91dbc25504c04`）：
局部变量 `donor` 旁边加 `curr`，锁内取 `curr = rq->curr`，最后

```c
-	if (donor->flags & PF_WQ_WORKER)
-		wq_worker_tick(donor);
+	if (curr->flags & PF_WQ_WORKER)
+		wq_worker_tick(curr);
```

`psi_account_irqtime(rq, donor, NULL)` 等调度侧记账刻意保留 donor。作者明确写成
"Use rq->curr for the workqueue tick hook while retaining rq->donor for scheduler accounting."
—— 这个「只切消费者、不动拆分本身」的取舍是这类补丁的共同形态。

## 版本演进与当前进展

- 9/2 23:02 v1（UID 74394，msgid 后缀 `-2-`，其 `-1-`（封面或同系列另一封）未进入当天缓存）。
- 9/3 02:21 Tejun Heo：`Acked-by` + 路由问题（UID 74950）。
- 9/3 之后到 9/7：作者本人没有再发同主题版本，Peter Zijlstra 没有回答路由问题。
- 同一作者同期还在推同一条语义线的其它补丁：9/2 19:25 `task_sched_runtime()`（UID 73775，
  `Fixes: 7de9d4f94638`，**到 9/7 零回帖**）、9/3 00:33 `[PATCH 1/2] sched/numa:` +
  `[PATCH 2/2] sched/cache: Use execution context for ... task tick`（UID 74644/74668），
  被 Tim Chen 意见推动后 9/3 12:11 重发为 `[PATCH v2 0/2] sched: Fix execution-context tick
  handling under proxy execution`（UID 75867）。

## Maintainer 意见与讨论焦点

- **Tejun Heo（workqueue 维护者）**：直接给 `Acked-by: Tejun Heo <tj@kernel.org>`，没有要求任何改动；
  他关心的是合入路径而不是内容——"It can go through either sched or wq."。也就是说内容层面此补丁已无对手。
- **Peter Zijlstra / John Stultz（调度侧）**：到 9/7 **沉默**。这正是卡点：补丁改的是 `sched_tick()`，
  而 `sched_tick()` 当天正同时被 PE、`task_h_load()` 重做、core-sched 7/7 系列三路改动触碰。
- 值得引用的对照：Tim Chen 在同作者紧邻的一条线上提出了**本类补丁真正的技术难点**——
  donor 可能是 DL/RT 任务，此时 `task_tick_fair()` 根本不会被调用，所以修正点不该放在
  `task_tick_fair()` 里，而应上移到 `sched_tick()` 判 `rq->curr` 的调度类，并且
  `sched_tick_remote()` 也要补上，否则 nohz_full CPU 会彻底失去这段 tick。作者接受了这个方案并出了 v2。
  这一条对本补丁同样是提醒：`wq_worker_tick()` 现在挂在 `sched_tick()` 主干上，proxy exec 下
  `curr` 的 worker 身份判定与 `!scx_switched_all()` 分支的相对位置需要 sched 侧确认。
- **一个提交规范风险**：v1 只发了 `-2-` 这一封，缓存里没有 `-1-`。同一批邮件里 Peter 对 kcov 作者
  的同类问题说过得很重（见 [[sched-20260902-016]]）："You've send me a partial series; which is the
  same as not sending me anything at all."
- 无 NAK。

## 合入评估

**likelihood: likely**。依据：正确的维护者已 `Acked-by` 且未附加条件；补丁 5 行、有 `Fixes` 标签、
无争议、无行为面扩散（只影响带 `PF_WQ_WORKER` 的任务）。卡点只有一个，而且是流程性的：Tejun 把路由
决定权交给 Peter，Peter 未答，所以它既不在 sched 树也不在 wq 树里悬着。次一级的风险是同作者 4 封
同类修正各占一条线程、没有整体方案，Peter 很可能要求合并成一个「PE 下统一按执行上下文取任务」的系列
再来一次。注意 `Fixes` 指向 `af0c8b2bf67b`，线程里**没有** `Cc: stable`——PE 尚未进已发布内核，
这条本来也不该走 stable。

## 效果评估

线程内**没有任何测试数据**：本补丁正文只有机制推论，作者没有给出 worker CPU 时间偏差量、
`WORKER_CPU_INTENSIVE` 误判次数或 pool 并发变化的数字。同作者的 `task_sched_runtime()`（73775）
反而带了实测描述（RT 与 fair donor 各代理一个 fair mutex owner，修复前 `CPUCLOCK_SCHED` 在确认处于
proxy exec 的窗口里持续读到不变的 runtime，修复后未再观察到陈旧读，非 proxy 对照组不变），
本补丁可以复用同一套测试骨架，目前没人做。也没人报告过线上症状。

## 我可以参与的点

- **回合判断**：这条只对开了 PROXY_EXEC 的内核有意义，OLK-6.6 没有 PE 拆分，**不需要回合**；
  真正要提前建立认知的是「调度上下文 vs 执行上下文」这套双上下文语义，以及哪些 per-task 记账/限流
  消费者会站错边——本线程目前是 workqueue，后续会有更多。
- **回答 Tejun 的路由问题**（以用户/测试者身份）：给一份「开 PE + unbound workqueue + 长 CPU 密集
  worker」的实测，量化修复前后 worker 的 `sum_exec_runtime` 归属与 rescuer/并发管理行为，
  是把这个补丁推过线最省事的方式。
- **提议把 5 封同类修正并成一个系列**：`task_sched_runtime()`（零回帖）、`wq_worker_tick()`、
  `task_tick_numa()`/`task_tick_cache()`（已有 v2）、`sched/rt` RT watchdog（9/3 19:12）、
  `sched/cputime` cgroup 归属（9/3 19:07）。现在的状态是一个一个补丁地补，评审者要反复重建上下文。
- **接手零回帖的那封**：`sched/core: fix task_sched_runtime() for proxy execution`（73775）带着实测却没人回。

## 参考链接

- v1 补丁（UID 74394）：https://lore.kernel.org/all/20260902150208.1209922-2-sh_def@163.com/
- Tejun Heo 的 Acked-by 与路由问题（UID 74950）：https://lore.kernel.org/all/aphpMkGmuOrUByf3@slm.duckdns.org/
- 同日同类修正 `fix task_sched_runtime()`（UID 73775，零回帖）：https://lore.kernel.org/all/20260902112539.879979-1-sh_def@163.com/
- 紧邻同语义线 v1（UID 74644 / 74668）：https://lore.kernel.org/all/20260902163336.1552840-1-sh_def@163.com/
- Tim Chen 的「上移到 sched_tick() + 补 sched_tick_remote()」意见：https://lore.kernel.org/all/c5a2d651a5d647fb29f13fe483301b3b6e292b4d.camel@linux.intel.com/
- 该线 v2 封面（UID 75867）：https://lore.kernel.org/all/20260903041154.2479761-1-sh_def@163.com/
- 相关：[[sched-20260902-001]]（proxy execution 批合入，`af0c8b2bf67b` 的来源）、[[sched-20260902-002]]（同期调度核心清理）

---
id: sched-20260902-012
date: '2026-09-02'
subject: 'sched/core: Call wq_worker_tick() for the execution context'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260902150208.1209922-2-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20260902150208.1209922-2-sh_def@163.com/
upstream_commit: null
fixes_commit: af0c8b2bf67b
merged_branch: null
current_version: v1
generated_at: '2026-09-07'
authors:
- Hui Su
maintainers_involved:
- Tejun Heo
- Tim Chen
patch_series:
- '[PATCH] sched/core: Call wq_worker_tick() for the execution context'
merge_assessment:
  likelihood: high
  blocking_issues:
  - 'Tejun Heo 已 Acked-by 并把路由决定交给 Peter Zijlstra，Peter 截至 9/7 未答（sched 树还是 wq 树未定）'
  - '同作者 4~5 封 donor/curr 语义修正分散在多条线程，Peter 可能要求并成一个系列'
  - 'v1 只发了 msgid -2- 这一封，缓存中未见 -1-，存在 partial series 被退回的风险'
  next_action: '回答 Tejun 的路由问题：给一份 PE + CPU 密集 unbound worker 的实测，并提议把同类修正并为一个系列'
contribution_opportunities:
- '开 PROXY_EXEC 跑 CPU 密集的 unbound workqueue，量化 wq_worker_tick() 改用 rq->curr 前后的 worker CPU 归属与 WORKER_CPU_INTENSIVE 判定'
- '接手当天零回帖的 sched/core: fix task_sched_runtime() for proxy execution（UID 73775），它已带实测却无人回应'
- '把 task_sched_runtime / wq_worker_tick / task_tick_numa / task_tick_cache / RT watchdog 五处 execution-context 修正整理成一个系列提交'
- '确认 wq_worker_tick() 在 sched_tick() 中与 !scx_switched_all() 分支的相对位置在 sched_ext + PE 组合下是否仍正确'
source_email_count: 7
related_articles: []
tags:
- sched/core
---
