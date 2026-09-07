---
id: sched-20260902-001
date: '2026-09-02'
subject: Sleeping Owner Handling for Proxy Execution (v31)
subsystem: sched
type: feature
status: merged_tip
severity: medium
thread_root_msgid: <20260807035232.1881495-3-jstultz@google.com>
lore_url: https://lore.kernel.org/all/20260807035232.1881495-3-jstultz@google.com/
upstream_commit: null
fixes_commit: 7de9d4f94638
merged_branch: tip/sched/core
current_version: v31
generated_at: '2026-09-07'
authors:
- John Stultz
- Vasily Gorbik
- Christian Loehle
- Peter Zijlstra
- Andrea Righi
maintainers_involved:
- Peter Zijlstra
- K Prateek Nayak
- Juri Lelli
- Tim Chen
- Tejun Heo
patch_series:
- 'sched/deadline: Ignore proxy-exec sched_yield()'
- 'sched/core: Don''t steal a proxy-exec donor'
- 'sched/core: Avoid migrating blocked_on tasks'
- 'sched/core: Don''t proxy-exec unmatched cookie lock owners'
- 'sched: Switch rq->next_class in proxy_reset_donor()'
- 'sched: Break out core of attach_tasks() helper into sched.h'
- 'sched: Migrate whole chain in proxy_migrate_task()'
- 'sched: Add deactivated (sleeping) owner handling to find_proxy_task()'
- 'sched: Distinguish proxy activations from wakeups'
merge_assessment:
  likelihood: likely
  blocking_issues:
  - 8/9 sleeping owner handling 与 9/9 未进树，补丁自陈锁设计 awkward 并公开求 review，全系列零回帖
  - 1/9 需 DL 侧继续背书；9/9 与 Andrea Righi 的 sched_ext/PE 系列存在两行交叉依赖
  - 上下文语义外溢未收口：73775 task_sched_runtime() 到 9/7 仍无人回帖，cgroup 归属（78587/78784）未定
  next_action: 跟 73775 / 74394 / 76822 / 78587 四条后续修正，等 v32 或下一轮 RESEND 看 8/9 是否拿到
    review
contribution_opportunities:
- '回帖接手 73775（sched/core: fix task_sched_runtime() for proxy execution），该补丁至今零回帖且带可复现观察'
- 为 8/9 sleeping owner handling 构造压测：mutex 持有者主动 sleep + waiter 树 + 中间节点唤醒
- 就 78587/78784 的 cgroup CPU 时间归属给出 cpuset/容器视角的结论与测试
- 在 OLK-6.6 一类 backport 上逐点比对 try_steal_cookie()/find_proxy_task()/proxy_reset_donor()
  三处改动
source_email_count: 7
related_articles: []
tags:
- proxy_execution
- sched/core
title: Sleeping Owner Handling for Proxy Execution (v31)
layout: article
---

## TL;DR

09-02 `tip/sched/core` 一次合入 PE v31 的 6 个补丁（2/9~7/9），但**系列标题所指的那一个补丁
——8/9 `Add deactivated (sleeping) owner handling to find_proxy_task()`——并没有进树**，1/9 和 9/9
同样留下。进树的全是作者自己在封面里预判为「easy to queue」的前置修复与 core-scheduling 补丁。
同日 Hui Su 立刻报出 `task_sched_runtime()` 取错上下文（73775），说明 PE 的
「调度上下文 `rq->donor` / 执行上下文 `rq->curr`」分裂已经外溢到 runtime 记账、workqueue、
NUMA/cache tick、cgroup 记账，9/2~9/5 已连续出现 5 条后续修正。

## 背景与问题

Proxy Execution（PE）让 mutex 持有者借用阻塞者的调度上下文运行，`rq->donor` 是调度上下文、
`rq->curr` 是执行上下文。v31 要解决的是链条末端持有者已经睡下去的场景，封面正文写得很直接：
"Since there is nothing we can do to boost the sleeping owner at that point, we instead deactivate
and queue the waiter on a list attached to the owner. Then when the owner wakes up, we will activate
the waiters on the same runqueue, so they can then boost the owner to run."，并指出真正难的是
waiter 会形成树、树中间节点被唤醒时级联 wakeup 必须非递归地处理。

09-02 进树的不是这套逻辑，而是它周围的一圈正确性问题：core scheduling 的 cookie 选择被 proxy
绕过、donor 被跨核偷走、blocked_on 任务被无意义迁移、`proxy_reset_donor()` 漏设 `rq->next_class`、
`attach_tasks()` 需要复用。

## 技术方案

以下每条都有当日 tip-bot2 通知的正文与 diff，Committer 均为 Peter Zijlstra，
CommitterDate Wed 02 Sep 2026 09:37:20/21 +02:00：

- **2/9 `sched/core: Don't steal a proxy-exec donor`**（`3dd95f077371`，Vasily Gorbik，
  `Fixes: 7de9d4f94638`）：`try_steal_cookie()` 的保护条件加一项 `p == src->donor`。
  commit message 讲清后果——donor 被偷走后源 rq 仍把它当 current，CFS 侧 `cfs_rq->curr`
  指向被偷实体，下一次 pick 命中 `put_prev_entity()` 的 WARN_ON_ONCE。
- **3/9 `sched/core: Avoid migrating blocked_on tasks`**（`9be817f991e2`，John Stultz）：
  同一循环里 `task_is_blocked(p)` 直接 `goto next`，理由是 "the proxy logic will just migrate it
  back to the owner's rq"。
- **4/9 `sched/core: Don't proxy-exec unmatched cookie lock owners`**（`09351db90a28`，
  Vasily Gorbik，`Fixes: 7de9d4f94638`，`Reported-by: K Prateek Nayak`）：
  `find_proxy_task()` 末端若最终 owner 与已选中的 core cookie 不匹配
  （`!sched_cpu_cookie_match(rq, owner)`），当前执行上下文已在 blocked 链上就
  `proxy_resched_idle(rq)`，否则 `p = donor; clear_task_blocked_on(p, NULL); goto deactivate;`。
  作者注 `[jstultz: Added tweak to ensure we deactivate donor, not runnable owner]`。
- **5/9 `sched: Switch rq->next_class in proxy_reset_donor()`**（`1f8805138593`，
  `Fixes: f13beb010e4a`）：补一行 `rq->next_class = rq->curr->sched_class;`。
- **6/9 `sched: Break out core of attach_tasks() helper into sched.h`**（`6b73a09e943f`，
  `Suggested-by: K Prateek Nayak`）：链式 enqueue 核心抽成 `__attach_tasks()`
  （fair.c -16/+19，sched.h +19）。
- **7/9 `sched: Migrate whole chain in proxy_migrate_task()`**（`772d9ffbfd26`）：沿
  `blocked_donor` 指针一次迁完整条链，而不是 `find_proxy_task()` 里逐跳迁移。

**未进树**：1/9 `sched/deadline: Ignore proxy-exec sched_yield()`（`From:` Christian Loehle，
`Acked-by:` Juri Lelli，`Fixes: 127b90315ca0`）、8/9（`From:` Peter Zijlstra，Sob 链含 Juri Lelli /
Valentin Schneider / Connor O'Brien）、9/9 `sched: Distinguish proxy activations from wakeups`
（`From:` Andrea Righi，新增 `ENQUEUE_PROXY` 并在 sched_ext 侧抑制 `SCX_ENQ_WAKEUP`）。

## 版本演进与当前进展

v31 本身是一封 RESEND，封面第一句就是 "Didn't get much feedback last round, as a number of folks
were on vacation"。v31 相对上一轮的四点变化（封面逐条）：并入 Christian 的 `yield_task_dl()` 早退；
修 K Prateek 指出的「sleeping owner 与 waiter 入队并发导致 waiter 卡死」竞争；按 Maria Yu /
Tengfei Fan 的复现调整 `do_activate_blocked_waiter()` 修 `rq->nr_iowait` 失衡；并入 Andrea Righi
让 sched_ext 与 sleeping-owner handling 共存的改动。

作者的路线图为 1) prep patches 2) single rq proxying 3) simple donor migration
4) optimized donor migration 5) **sleeping owner handling <- We are here!** 6) chain level balancing
7) proxy rwsems，并预先写明 "Hopefully the earlier patches will be easy to queue, but I suspect
there will be lots of review feedback for me to address in the last two."——当日结果与这句话完全吻合。
整串分支：`proxy-exec-v31-7.2-rc4`。

后续（同一处上下文分裂的外溢）：73775 `fix task_sched_runtime()`（9/2）、
74394 `Call wq_worker_tick() for the execution context`（9/2）、
76822 `sched/rt: Fix RT watchdog accounting for proxy execution`（9/3）、
78587 `[PATCH v2] sched: Account cgroup CPU time to the execution context`（9/4），
以及 [[sched-20260903-001]] / [[sched-20260904-001]] / [[sched-20260905-001]] 记录的 tick 系列 v1->v3。

## Maintainer 意见与讨论焦点

- 调度侧对 v31 的 9 封补丁**零回帖**（整个缓存里 26034~26044 没有任何 reviewer 回复）。
  维护者的态度只体现在合入上：一次 queue 六个，无 NAK、无附带条件，也意味着 8/9 没被任何人接手。
- 讨论热点当天就移到「合入之后」。Hui Su 73775 给出机制与实测：`task_sched_runtime()` 用
  `task_current_donor(rq, p)` 取调度上下文、又用 `p->sched_class->update_curr(rq)`，代理运行时
  被记账对象应是 donor，因此改成 `task_current()` + `rq->donor->sched_class->update_curr(rq)`，
  `Fixes: 7de9d4f94638`。测试描述原文："Tested with both RT and fair donors proxy-executing a fair
  mutex owner. Before the change, CPUCLOCK_SCHED reads repeatedly returned unchanged runtime during
  confirmed proxy-execution windows. After the change, no stale reads were observed. The non-proxy
  control case was unchanged." 该补丁到 9/7 仍无人回帖。
- Tejun Heo 对 74394 已给 `Acked-by` 并主动问路由（见 [[sched-20260902-012]]）；
  sched/cache 侧由 Tim Chen 从 9/3 起接手（75219 / 78148 / 77800 / 80559 / 80942 / 80952），
  Chen Yu（77066 / 80406）与作者（75742 / 81773）一路迭代到 v3；Tejun 在 78784 追问 cgroup 归属。
- 真正未收口的语义问题：donor 与 owner 属于不同 cgroup 时 CPU 时间记到谁头上（78587 系列），
  以及 `task_tick_core()` 是否同样要改用执行上下文（Chen Yu 的追问，暂无回答）。

## 合入评估

**likelihood: likely**（就已合入的 2/9~7/9 六个补丁而言，事实已完成，随 tip/sched/core 进入下一个
合并窗口）。**就 sleeping owner handling 本身（8/9 + 9/9）而言为 unclear。**

卡点：8/9 是 PE 路线上第一个真正改锁语义的大块，补丁正文自带 NOTE："This has been particularly
challenging to get working properly, and some of the locking is particularly awkward. I'd very much
appreciate review and feedback for ways to simplify this." 在全员休假、无人回帖的情况下，Peter
不会单独 queue 它。1/9 需要 DL 侧继续背书（Juri Lelli 已 Acked-by），9/9 与 Andrea Righi 的
sched_ext/PE 系列存在两行交叉依赖，必须协调顺序。

## 效果评估

当日没有任何 benchmark——这六个补丁都是正确性修复，改动量 1~19 行。可用的效果证据是故障面：
2/9 的 commit message 给出可复现后果（`put_prev_entity()` WARN_ON_ONCE），4/9 给出 core scheduling
cookie 被绕过的语义漏洞（源头是 Prateek 的报告 `10282ce9-f4ae-498f-9b57-f4e1e61fffbc@amd.com`），
7/9 是把逐跳迁移换成整链迁移以减少 `find_proxy_task()` 的循环次数。反面证据更值钱：合入不到 4 小时
就有第三方报出 runtime 记账错误（73775），说明 PE 的上下文语义在外围路径上尚未收敛。
8/9 的性能影响没有任何数字。

对回背的参考价值：这批改动点小、`Fixes:` 明确（`7de9d4f94638` / `f13beb010e4a`），若已在 OLK-6.6
一类内核上自行合过 PE backport，`try_steal_cookie()`、`find_proxy_task()`、`proxy_reset_donor()`
三处需逐点比对；`put_prev_entity()` 的 WARN_ON_ONCE 是判断 donor 偷取问题最直接的探针。

## 我可以参与的点

- **73775 至今零回帖**，且带了可复核的 CPUCLOCK_SCHED 观察，回 `Tested-by` 或给反例的成本极低。
- 替 PE 的 sleeping-owner 路径补量化与压测：作者明确欢迎简化建议。现成模板是同仓库线程里
  K Prateek Nayak 给的 `coresched new -t pid -- perf bench sched messaging -p -l 100000 -g 8`
  （出现在 [[sched-20260902-015]] 引用的旧线程中），再加 mutex 持有者主动 sleep 的用例。
- cpuset/cgroup 视角切入：78587 / 78784 那条「cgroup CPU 时间记到执行上下文」的线直接决定容器内
  CPU 用量在 PE 下是否可解释，也是本仓库读者最有发言权的地方。
- 1/9 与 9/9 未进树：同时跑 PE 与 sched_ext 的人需要盯住 Andrea 提到的两行交叉依赖，
  并验证 `ENQUEUE_PROXY` 缺失时 sched_ext 的 wakeup 统计是否偏差。

## 参考链接

- v31 已合入的六个补丁（Message-ID 取自 tip-bot2 通知的 `Link:`）：
  - https://lore.kernel.org/all/20260807035232.1881495-3-jstultz@google.com/ （2/9 Don't steal a proxy-exec donor）
  - https://lore.kernel.org/all/20260807035232.1881495-4-jstultz@google.com/ （3/9 Avoid migrating blocked_on tasks）
  - https://lore.kernel.org/all/20260807035232.1881495-5-jstultz@google.com/ （4/9 Don't proxy-exec unmatched cookie lock owners）
  - https://lore.kernel.org/all/20260807035232.1881495-6-jstultz@google.com/ （5/9 Switch rq->next_class in proxy_reset_donor()）
  - https://lore.kernel.org/all/20260807035232.1881495-7-jstultz@google.com/ （6/9 Break out core of attach_tasks()）
  - https://lore.kernel.org/all/20260807035232.1881495-8-jstultz@google.com/ （7/9 Migrate whole chain in proxy_migrate_task()）
- 4/9 的问题报告（`Link:` 中出现）：https://lore.kernel.org/all/10282ce9-f4ae-498f-9b57-f4e1e61fffbc@amd.com/
- 后续修正：https://lore.kernel.org/all/20260902112539.879979-1-sh_def@163.com/ （task_sched_runtime）
  ；https://lore.kernel.org/all/20260902150208.1209922-2-sh_def@163.com/ （wq_worker_tick）
- v31 封面（`[RESEND][PATCH v31 0/9]`）自身的 Message-ID 未获取到：缓存中该邮件只带占位 msgid。
- 相关：[[sched-20260902-012]]、[[sched-20260902-015]]、[[sched-20260903-001]]、[[sched-20260903-005]]
