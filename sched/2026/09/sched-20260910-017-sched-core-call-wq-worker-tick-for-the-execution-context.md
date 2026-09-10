# sched/core: Call wq_worker_tick() for the execution context

## TL;DR
本文为增量更新，完整背景与补丁内容见 related_articles 中的 sched-20260902-012。09-10 的进展是**流程卡点被打通**：Peter Zijlstra 回答了 Tejun Heo 七天前（09-03）提出的路由问题——"Sorry, seems this got lost in the email deluge :/ I can take it through sched/urgent."。也就是说这枚 +5/-4 的修复将由 sched 树、且走 urgent 分支收取。我对照本地内核树（与 Linux 7.2-rc6 逐字节一致，`git diff 075b74841bd0` 对该文件为空）确认 `kernel/sched/core.c:5803-5804` 仍是 `if (donor->flags & PF_WQ_WORKER) wq_worker_tick(donor);`，修复尚未落地，Peter 的表态是「愿意收」而非「已收」，缓存内无 tip-bot 回帖。

## 背景与问题
（增量文章，完整背景见 sched-20260902-012，此处只保留判断本日进展所需的部分。）

proxy execution 把上下文拆成调度上下文 `rq->donor` 与执行上下文 `rq->curr`（上游 commit `af0c8b2bf67b` "sched: Split scheduler and execution contexts"，2024-10 进入主线）。`sched_tick()` 里调度侧记账走 donor，`sum_exec_runtime` 走 curr，但 `wq_worker_tick()` 挂错了边——它做的是「当前真正在跑的 kworker」的 CPU 时间统计与 `WORKER_CPU_INTENSIVE` 判定，属于执行上下文。

两种错法（作者原文）：donor 不是 worker 而 curr 是 worker 时，kworker 代跑期间的 workqueue 记账被跳过，"can delay WORKER_CPU_INTENSIVE handling and pool concurrency management, which can delay pending kernel work and userspace operations depending on it"；donor 是 worker 而 curr 是别的任务时，会给一个**已经阻塞**的 kworker 记时间。

触发前提需要说清楚：`CONFIG_SCHED_PROXY_EXEC` 在 `init/Kconfig:936` 依赖 `EXPERT`、且 `depends on !PREEMPT_RT`、`depends on !SCHED_CLASS_EXT`，默认不开启；未开启时 donor 恒等于 curr，本补丁无可观测影响。这也解释了为什么线程里没有 `Cc: stable`。

## 技术方案
方案本日无变化（详见 sched-20260902-012）：只改 `kernel/sched/core.c` 的 `sched_tick()`，+5/-4，在局部变量 `donor` 旁增取 `curr = rq->curr`，然后

```c
-	if (donor->flags & PF_WQ_WORKER)
-		wq_worker_tick(donor);
+	if (curr->flags & PF_WQ_WORKER)
+		wq_worker_tick(curr);
```

`psi_account_irqtime(rq, donor, NULL)` 等调度侧记账刻意保留 donor——「只切消费者、不动拆分本身」是这一批 donor/curr 修正的共同形态。

本日新增的不是代码而是**验证性事实**：本地内核树（`make kernelversion` 为 7.2.0-rc6；已用 `git diff 075b74841bd0 -- kernel/sched/core.c` 确认该文件与 Linux 7.2-rc6 完全一致）的 `kernel/sched/core.c` 中，`sched_tick()` 尾部仍为

```c
	if (donor->flags & PF_WQ_WORKER)
		wq_worker_tick(donor);
```

即缺陷在当前主线依然存在、修复尚未合入；`Fixes:` 指向的 `af0c8b2bf67b` 也已确认为真实上游 commit（2024-10-09）。

## 版本演进与当前进展
- 09-02 23:02 v1（`<20260902150208.1209922-2-sh_def@163.com>`），单补丁，`base-commit: 89a312991dc6e638a36adc43ccb91dbc25504c04`。
- 09-03 02:21 Tejun Heo（workqueue 维护者）给出无条件 `Acked-by`，并把路由问题抛给 Peter："Peter, how do you want to route this patch? It can go through either sched or wq."
- 09-03 → 09-10：调度侧沉默七天，补丁悬在两棵树之间。
- **09-10 16:15（本日）**：Peter 回复 Tejun 那封 ack 邮件，道歉并承诺 "I can take it through sched/urgent."。
- 仍是 v1，无 v2、无 tip-bot 回帖、无 stable 回帖。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra（sched 维护者）**：本日唯一的、也是决定性的一条意见——路由归 sched，且走 `sched/urgent`。urgent 分支意味着按「当前周期的修复」处理，而非压到下个合并窗口。他没有对补丁内容提任何修改要求，也没有要求作者把这批 donor/curr 修正合并成一个系列——**sched-20260902-012 中预判的「Peter 可能要求并为一个系列再来一次」的风险没有发生**。
- **Tejun Heo**：09-03 的 `Acked-by` 无附加条件，内容层面此补丁自始无对手；他的关注点只在合入路径，本日已被回答。
- **"email deluge" 不是客套话**：同日 Peter 在做的事情包括——对 PE + sched_ext v13 的 18 补丁系列逐条给出正式评审（见 sched-20260910-002）、把 Andrea 的 SMT 优先级系列 v5 从收取队列撤下（见 sched-20260910-007，"Andrea is a wee bit fast with re-posting. I'll drop this"）。对照之下可以看到他的收取标准：小、正确、有 `Fixes:`、已被对口维护者 ack 的修复走 urgent 快通道；而有争议或重复投递的系列会被直接 drop。
- **一个当日无人提出的重叠风险**：本补丁与同作者正在评审中的 v4 五补丁 tick 系列（见 sched-20260910-003）改的是同一片代码——后者重构 `sched_tick()`/`task_tick()` 的上下文归属（含把 watchdog 记给 `rq->curr`、引入 sched_class 生命周期回调）。本补丁先经 urgent 落地后，v4 系列必然需要 rebase；反之若 v4 先进，本补丁的 `curr` 取值位置可能已被改写。两条线同作者、同函数、同语义主题，但分散在两条线程里推进，没人协调顺序。
- Tim Chen 在相邻线程提的「修正点应上移到 `sched_tick()` 而非 `task_tick_fair()`」意见对本补丁不适用——`wq_worker_tick()` 本来就挂在 `sched_tick()` 主干上。

## 合入评估
likelihood: high。

依据：对口维护者（Tejun，workqueue）无条件 `Acked-by`；sched 维护者（Peter）明确承诺收取且指定 urgent 分支；补丁 5 行、带真实 `Fixes:` 标签、无技术争议；我已确认缺陷在当前主线仍存在，修复有实际意义而非纸上清理。

blocking_issues：
- 尚未实际落入 tip——缓存内无 tip-bot 回帖，`merged_branch` 仍为空；Peter 的措辞是 "I can take it"，不是 "applied"。
- 与同作者 v4 tick 系列（sched-20260910-003）改同一片 `sched_tick()` 代码，先后顺序无人协调，存在 rebase/冲突成本。
- `sched_tick()` 是当前最热的改动点之一（PE + sched_ext v13 也在触碰），urgent 分支落地前可能需要重打基线。

next_action：等 tip-bot 回帖确认进入 `tip/sched/urgent`；作者宜主动在 v4 tick 系列封面里说明与本补丁的先后关系，避免两条线互相踩。

## 效果评估
线程内**没有任何测试数据**，本日也无新增：作者未给出 worker CPU 时间偏差量、`WORKER_CPU_INTENSIVE` 误判次数或 pool 并发管理延迟的数字，也没人报告过线上症状。

可核实的证据只有代码层面两条（我的审阅结论，非测试结果）：其一，Linux 7.2-rc6 的 `kernel/sched/core.c:5803-5804` 仍为 `if (donor->flags & PF_WQ_WORKER) wq_worker_tick(donor);`，缺陷未修；其二，`CONFIG_SCHED_PROXY_EXEC` 依赖 `EXPERT` 且与 `SCHED_CLASS_EXT`、`PREEMPT_RT` 互斥，默认关闭，因此该缺陷的实际影响面限于显式开启 PE 的调试/专用内核，这与「无 `Cc: stable`」的处理一致。

同作者的 `sched/core: fix task_sched_runtime() for proxy execution`（`<20260902112539.879979-1-sh_def@163.com>`）反而带了实测描述，本补丁可复用同一套测试骨架，至今无人做。

## 我可以参与的点
- **补实测把 urgent 落地后的行为钉住（testing）**：Peter 已承诺走 urgent，意味着这枚补丁会较快进主线，但线程里零数据。开 `CONFIG_SCHED_PROXY_EXEC`（需同时关掉 sched_ext 与 PREEMPT_RT）跑「高优先级任务阻塞在 CPU 密集 kworker 持有的 mutex 上」的场景，量化改前/改后 worker 的 CPU 时间归属、`WORKER_CPU_INTENSIVE` 判定时刻与 pool 并发数变化，回帖到线程——这是把一个「已 ack 但未验证」的修复变成「已验证」的最省事方式。
- **协调与 v4 tick 系列的顺序（discussion）**：两条线同作者、同函数。可在 v4 系列线程里指出本补丁即将经 `sched/urgent` 落地，请作者明确 v4 是否已基于它、以及 `task_tick()` 侧重构会不会改写 `curr` 的取值位置；这类顺序问题维护者通常乐意有人代为指出。
- **接手仍零回帖的相邻补丁（review）**：`sched/core: fix task_sched_runtime() for proxy execution` 带着实测却自 09-02 起无人回应，本补丁被收取说明这条语义线整体是被认可的，去给那封做评审的性价比现在更高。
- **回合判断**：仅对开启 `SCHED_PROXY_EXEC` 的内核有意义。OLK-6.6 未开启该选项（且它与 sched_ext 互斥），**不需要回合**；真正要提前建立的认知仍是「调度上下文 vs 执行上下文」双语义下哪些 per-task 记账/限流消费者会站错边。

## 参考链接
- Peter Zijlstra 承诺经 sched/urgent 收取（本日邮件）: https://lore.kernel.org/all/20260910081526.GD4120091@noisy.programming.kicks-ass.net/
- 被回复的 Tejun Heo ack + 路由问题: https://lore.kernel.org/all/aphpMkGmuOrUByf3@slm.duckdns.org/
- v1 补丁（线程根）: https://lore.kernel.org/all/20260902150208.1209922-2-sh_def@163.com/
- 同作者零回帖的相邻补丁: https://lore.kernel.org/all/20260902112539.879979-1-sh_def@163.com/
- tip-bot commit: 未获取到（Peter 表态当日尚无 tip-bot 回帖）
- stable backport: 不适用（线程内无 Cc: stable，PE 为 EXPERT 选项且默认关闭）

---
id: sched-20260910-017
date: 2026-09-10
subject: "sched/core: Call wq_worker_tick() for the execution context"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20260902150208.1209922-2-sh_def@163.com>"
lore_url: "https://lore.kernel.org/all/20260910081526.GD4120091@noisy.programming.kicks-ass.net/"
upstream_commit: null
fixes_commit: af0c8b2bf67b
merged_branch: null
current_version: v1
generated_at: "2026-09-11T01:35:00"
authors:
  - "Hui Su"
maintainers_involved:
  - "Peter Zijlstra"
  - "Tejun Heo"
patch_series:
  - version: v1
    msgid: "<20260902150208.1209922-2-sh_def@163.com>"
    date: "2026-09-02"
    summary: "sched_tick() 中把 wq_worker_tick() 的入参从 rq->donor 改为 rq->curr，使 workqueue 的 CPU 时间记账与 WORKER_CPU_INTENSIVE 判定跟随执行上下文；psi_account_irqtime() 等调度侧记账保留 donor；kernel/sched/core.c +5/-4。"
    review_outcome: "09-03 Tejun Heo 无条件 Acked-by 并询问 Peter 走 sched 还是 wq 树；调度侧沉默七天后，09-10 16:15 Peter Zijlstra 回复「Sorry, seems this got lost in the email deluge」并承诺 I can take it through sched/urgent，未要求任何改动、未要求与同作者其他 donor/curr 修正合并成系列。"
merge_assessment:
  likelihood: high
  blocking_issues:
    - "尚未实际落入 tip：缓存内无 tip-bot 回帖，Peter 的措辞是 I can take it 而非 applied"
    - "与同作者 v4 五补丁 tick 系列（sched-20260910-003）改同一片 sched_tick() 代码，先后顺序无人协调"
    - "sched_tick() 同时被 PE + sched_ext v13 触碰，落地前可能需要重打基线"
  next_action: "等 tip-bot 确认进入 tip/sched/urgent；作者宜在 v4 tick 系列封面说明与本补丁的先后关系"
contribution_opportunities:
  - kind: testing
    description: "开 CONFIG_SCHED_PROXY_EXEC（需关闭 sched_ext 与 PREEMPT_RT）构造高优先级任务阻塞在 CPU 密集 kworker 所持 mutex 上的场景，量化改前改后 worker CPU 时间归属、WORKER_CPU_INTENSIVE 判定时刻与 pool 并发变化并回帖——该补丁已获承诺收取但线程内零测试数据"
  - kind: discussion
    description: "在同作者 v4 tick 系列线程指出本补丁即将经 sched/urgent 落地，请其明确 v4 是否已基于它、task_tick() 重构是否会改写 curr 的取值位置"
  - kind: review
    description: "接手 sched/core: fix task_sched_runtime() for proxy execution（自 09-02 零回帖、已带实测），本补丁被收取说明该语义线整体获认可"
source_email_count: 1
related_articles:
  - "sched-20260902-012"
  - "sched-20260910-003"
  - "sched-20260910-016"
tags:
  - proxy_execution
  - preempt
---
