# 2026-09 LKML 调度子系统：特性与性能优化分析

> 数据来源：本仓库 `sched/2026/09/` 下 09-01 ~ 09-10 共 138 篇日报（去重后约 45 个逻辑系列）。
> 本文只梳理**特性（feature）与性能优化**类内容；纯正确性修复、文档/排版清理仅在附录总表中列出。
> 每个系列标注对应日报文章 ID（如 `sched-20260909-010`），细节与 lore 链接见该文。

## 一、总览

9 月的调度器讨论集中在四条主线上：

| 主线 | 核心问题 | 代表系列 |
|---|---|---|
| Proxy Execution 落地 | `rq->donor`（调度上下文）与 `rq->curr`（执行上下文）拆分后的语义收口 | PE v31、PE+sched_ext v13、tick 系列 v4/v5、cgroup 记账、wq_worker_tick |
| 虚拟化超配退让 | CPU 超配下 vCPU 被抢占的隐性代价，guest 主动折叠负载 | steal_governor / preferred CPUs v13 |
| Cache-aware scheduling 扩展 | 聚合域从单 LLC 扩展到 NUMA/LLC 两级 | Jianyong Wu 23 片 RFC、misfit 修复、per-task prctl RFC |
| NUMA balancing 修正 | 分层内存下扫描过滤器挡住提升、per-process 开关缺失 | Gregory Price 2 补丁、Li Zhe prctl、fault locality 修复 |

整体状态（按去重系列计，含非本文重点的修复类）：约 1/4 已进 tip 或 sched_ext 分支，1/2 处于评审中，其余为 RFC/停滞/被拒。

一个贯穿性的观察：**9 月的特性几乎全部由具体平台驱动**——NVIDIA Olympus（SMT 优先级）、IBM PowerVM/s390（steal 治理）、Hygon 多节点 NUMA、Meta 的 DRAM+CXL 分层、Snapdragon X2 的 >4.19GHz boost、低 HZ 嵌入式平台（LB_PROMOTE）。厂商带着复现数据进场是本月的普遍形态，但约半数系列仍然只有单一平台数据、无第三方复现。

---

## 二、Proxy Execution：核心机制落地与外围语义收口

Proxy Execution（PE）让 mutex 持有者借用阻塞者的调度上下文运行。9 月是该特性从「核心机制」走向「语义完备」的一个月：核心补丁部分进树，同时「donor vs curr 该看谁」的二义性在外围路径上集中暴露。

### 2.1 Sleeping Owner Handling for Proxy Execution（v31，RESEND）

> **系列**：`[RESEND][PATCH v31 0/9]`（9 补丁）· **作者**：John Stultz（Google）· **测试分支**：`proxy-exec-v31-7.2-rc4`
> **状态**：2/9~7/9 六个前置补丁已合入 tip/sched/core（Committer Peter Zijlstra，2026-09-02）；1/9、8/9（系列本体）、9/9 未进树
> **日报**：`sched-20260902-001`

#### 背景与问题

Proxy Execution（PE）让 mutex 持有者借用阻塞者的调度上下文运行：`rq->donor` 是调度上下文，`rq->curr` 是执行上下文。v31 要解决的是链条末端的持有者**已经睡下去**的场景，封面原文：

> "Since there is nothing we can do to boost the sleeping owner at that point, we instead deactivate and queue the waiter on a list attached to the owner. Then when the owner wakes up, we will activate the waiters on the same runqueue, so they can then boost the owner to run."

真正难的部分是 waiter 会形成树、树中间节点被唤醒时的级联 wakeup 必须非递归处理。作者给出的路线图是：prep patches → single rq proxying → simple donor migration → optimized donor migration → **sleeping owner handling（当前位置）** → chain level balancing → proxy rwsem——后面还有两块大项。

#### 技术方案

09-02 合入的六个补丁是 sleeping owner 周围的正确性前置（均有 tip-bot2 通知与完整 diff）：

| # | Subject | 关键改动 |
|---|---|---|
| 2/9 | `sched/core: Don't steal a proxy-exec donor`（`3dd95f077371`，Vasily Gorbik，`Fixes: 7de9d4f94638`） | `try_steal_cookie()` 的保护条件加一项 `p == src->donor`——donor 被偷走后源 rq 仍把它当 current，CFS 侧 `cfs_rq->curr` 指向被偷实体，下一次 pick 命中 `put_prev_entity()` 的 WARN_ON_ONCE |
| 3/9 | `sched/core: Avoid migrating blocked_on tasks`（`9be817f991e2`） | 同一循环里 `task_is_blocked(p)` 直接 `goto next`："the proxy logic will just migrate it back to the owner's rq" |
| 4/9 | `sched/core: Don't proxy-exec unmatched cookie lock owners`（`09351db90a28`，`Fixes: 7de9d4f94638`） | `find_proxy_task()` 末端最终 owner 与已选 core cookie 不匹配（`!sched_cpu_cookie_match(rq, owner)`）时不再代理，堵上 core scheduling cookie 被 proxy 绕过的语义漏洞 |
| 5/9 | `sched: Switch rq->next_class in proxy_reset_donor()`（`1f8805138593`，`Fixes: f13beb010e4a`） | 补一行 `rq->next_class = rq->curr->sched_class;` |
| 6/9 | `sched: Break out core of attach_tasks() helper into sched.h`（`6b73a09e943f`） | 链式 enqueue 核心抽成 `__attach_tasks()`（fair.c -16/+19） |
| 7/9 | `sched: Migrate whole chain in proxy_migrate_task()`（`772d9ffbfd26`） | 沿 `blocked_donor` 指针一次迁完整条链，替代 `find_proxy_task()` 里的逐跳迁移 |

**未进树的 8/9**（`Add deactivated (sleeping) owner handling to find_proxy_task()`）才是系列标题所指的本体：owner 睡下去后把 waiter 挂到 owner 上的链表、owner 醒来时激活。补丁正文自带 NOTE：

> "This has been particularly challenging to get working properly, and some of the locking is particularly awkward. I'd very much appreciate review and feedback for ways to simplify this."

#### 效果

六个合入补丁全是正确性修复（每个 1~19 行），无 benchmark。可用的效果证据是**故障面**：2/9 的 commit message 给出可复现后果（`put_prev_entity()` WARN_ON_ONCE）；4/9 堵的是 Prateek 报告的 cookie 绕过漏洞；7/9 减少 `find_proxy_task()` 的循环次数。

反面证据更有信息量：**合入不到 4 小时，Hui Su 就报出 runtime 记账错误**——`task_sched_runtime()` 用 `task_current_donor(rq, p)` 取调度上下文、却用 `p->sched_class->update_curr(rq)` 记账，代理运行时被记给错误对象：

```c
-	p = task_current_donor(rq, p); /* 调度上下文 */
-	p->sched_class->update_curr(rq);
+	p = task_current(rq); /* 执行上下文 */
+	rq->donor->sched_class->update_curr(rq);
```

该报告带实测（"Before the change, CPUCLOCK_SCHED reads repeatedly returned unchanged runtime during confirmed proxy-execution windows. After the change, no stale reads were observed."），说明 donor/curr 二义性在外围路径尚未收敛：9/2~9/5 连续出现 5 条后续修正（runtime 记账、wq_worker_tick、RT watchdog、cgroup 记账、tick 系列）。8/9 自身的性能影响没有任何数字。

#### 社区态度

- **调度侧对 v31 九个补丁零回帖**。封面第一句自嘲："Didn't get much feedback last round, as a number of folks were on vacation."
- **Peter Zijlstra**：以行动投票——一次 queue 六个（CommitterDate 09-02 09:37:20/21 +02:00），无 NAK、无附带条件、无书面意见；但也没有任何人接手 8/9。
- **Vasily Gorbik / Christian Loehle / Andrea Righi**：作为分片作者出现在系列里（2/9、4/9、1/9），无评审交锋。
- **Tejun Heo / Tim Chen / Chen Yu**：态度体现在后续修正线上——Tejun 对 wq_worker_tick 给无条件 Acked-by 并主动问路由；Tim Chen 从 09-03 起接手 sched/cache 侧讨论。
- 评估：已合入的六个为 merged；8/9+9/9 为 unclear——8/9 是 PE 路线上第一块真正改锁语义的代码，在无人回帖、作者公开求简化建议的状态下，不会被单独 queue；1/9 还需 DL 侧（Juri Lelli 已 Acked-by）继续背书，9/9 与 Andrea 的 sched_ext/PE 系列有两行交叉依赖。


### 2.2 sched: Make proxy execution compatible with sched_ext（v13→v14）

> **系列**：`[PATCHSET v13 0/18]`（18 补丁）· **作者**：Andrea Righi（NVIDIA）· **目标分支**：sched_ext/for-7.4 · **线程根**：`<20260831134338.1531664-1-arighi@nvidia.com>`（2026-08-31）
> **状态**：under_review；09-10 Peter Zijlstra 的正式评审到达（8 个补丁 10 条意见），等 v14
> **日报**：`sched-20260910-002`（演进见 09-04/09-08 各篇）

#### 背景与问题

PE 把调度上下文（`rq->donor`）与执行上下文（`rq->curr`）拆开以缓解优先级反转，但 `CONFIG_SCHED_PROXY_EXEC` 目前依赖 `!SCHED_CLASS_EXT`——**开 PE 就不能用 sched_ext**。本系列的目标是解除这个互斥：sched_ext 全面改用 `rq->donor` 记账、引入 `SCX_OPS_ENQ_BLOCKED`、把 proxy donor 的准入委托给 BPF 调度器（`scx_allow_proxy_exec()`），最后删除 Kconfig 互斥。到 09-08 为止技术争议面已基本清零（Prateek/Tejun/Richard 的意见全部处理完），唯一瓶颈是 Peter 的正式评审——09-10 评审落地。

#### 技术方案

09-10 无新代码，全部是 Peter 对 v13 的设计反馈，按性质分三档：

**被直接质疑的设计**（v14 必须重构或撤回）：

- **08/18（WF_ON_RQ 唤醒标志）**：`wakeup_preempt()` 本来就只会对已在 runqueue 上的任务调用，这正是 wake-preemption 的语义。Peter 连问两层："If we're distinguishing that, wouldn't move_queued_task() also want that flag? … What actual distinction are you needing?"
- **09/18（跨调度类转换阻塞 donor）**：Peter 认为补丁在每次调度类转换时都调 `sched_proxy_block_task()`，且未用 `scx_allow_proxy_exec()` 门控："We most certainly don't want to do this on every sched class change." 他直接给出想要的形式：

```c
	/* 放在切入 ext 调度器的"大切换"函数 switching_to_scx() 里 */
	if (!scx_allow_proxy_exec(p))
		sched_proxy_block_task(rq, p);
```

**前提被否（补丁假设的场景「不可能发生」）**：

- **03/18**（NOHZ CFS bandwidth checks follow proxy donor）："how can we ever have rq->donor be FAIR and rq->curr be RT? That makes no sense. If an RT task is runnable, pick should just straight up pick that."——并要求把 proxy 特有逻辑收进单一的 `sched_proxy_exec()` 分支。
- **14/18**（donor/curr 引用拆分）：作者穷举的 donor/curr 组合里，组合 3、4 被判不可达："If there is a runnable FAIR task, then pick will pick that directly."
- **05/18**（类不会变的假设）："Uh, yes it can. That's what {EN,DE}QUEUE_CLASS are for, no?"
- **04/18**（假迁移警告）："I'm not sure why we're not hitting this upstream?"——若该问题是真实的，主线应该触发过。

**给出明确可接受改法的**：

- **15/18**（准入委托 BPF）：入口封装成带 `scx_enabled()` 判断的 inline；准入检查 "Just have it be always instead of for ext-ext only"（总是执行，而非只在 ext→ext 场景）。
- **07/18**：要求作者解释 `scx_proxy_resolved()` 这个 hook 的必要性。

#### 效果

09-10 邮件均为设计评审，无 benchmark 或复现数据。该系列的效果只能等 v14 落地后观察；当前可引用的量化信息是系列的接口面（`SCX_OPS_ENQ_BLOCKED`、`scx_allow_proxy_exec()`、18 补丁删除 Kconfig 互斥）——它决定 BPF 调度器作者在 PE 开启时的记账实现方式（14/18 的 donor/curr 引用拆分语义直接进入 BPF API）。

#### 社区态度

- **Peter Zijlstra**：一人在 8 个补丁上留下全部 10 条意见。判断信号：评审细到给出具体代码建议（09/18 的 `switching_to_scx()` 方案、15/18 的 inline 写法），说明**方向被接受**；没有任何针对系列整体的 NAK。卡点只剩 08/18 的语义要重新论证（或撤回）、09/18 按给定方案重构。
- **Andrea Righi（作者）**：09-10 尚未公开回应这批评审；同日他在另一线程（2.3 的 tick 系列）主动向 Hui Su 表示两个系列「很快会兼容」，说明已在考虑协调。
- **Tejun Heo**：sched_ext 侧维护者，本日未参与该线程（系列走他的 for-7.4 分支，收取需他与 Peter 双方点头）。
- 评估：likelihood medium，v14 工作量已完全清晰。


### 2.3 sched: Handle split scheduling and execution contexts in task ticks（v4→v5）

> **系列**：`[PATCH v4 0/5]`（5 补丁）· **作者**：Hui Su · **线程根**：`<20260909092901.2989564-1-sh_def@163.com>`（2026-09-09）· 5/5 带 `Fixes: aa4f74dfd42b`
> **状态**：under_review；09-09 Peter 对 3/5 提重排要求、对 4/5 明确 NAK，09-10 作者逐条给出 v5 新设计
> **日报**：`sched-20260910-003`

#### 背景与问题

PE 拆分上下文后，`task_tick()` 的各消费者该跟谁走出现不一致：NUMA tick、cache-aware tick、RT watchdog（RLIMIT_RTTIME）、core scheduling slice 消费的可能是 donor 也可能是 curr。v4 的回答是按消费者逐个归属：NUMA/cache 移到 FAIR 执行上下文（2/5、3/5），RT 类状态留 donor、watchdog 跟 curr（4/5），core slicing 度量 donor 已消耗的 slice（5/5）。1/5 是基础设施：把 `task_tick()` 的 task 参数去掉、引入「donor 类先、curr 类后」的公共分发器。

#### 技术方案

**v4 结构**（09-09 发出）：1/5 改 `sched_class::task_tick()` 签名波及全部调度类；5/5 的 slice 检查关联 `rq->donor`，但已消耗服务改在 task-clock 域度量：

```c
	rtime = se->exec_start - rq->core_sched_start;
```

proxy 执行期间 `update_se()` 用 `rq_clock_task()` 推进 donor 的 exec_start，使比较两侧同域。baseline 存 `struct rq` 而非每个 `sched_entity`——每 rq 只有一个活跃 donor，按 entity 存会在 i386 + `CONFIG_SCHED_CORE=y` 下把 `sched_entity` 从 224 字节撑到 256。

**v5 新设计**（09-10 作者对 Peter 四条意见的逐条回应）：

- **3/5 重排**（回应「合并成单个 donor_class 与单个 curr_class 块」）：`task_tick_fair()` 最终形态为 donor 是 FAIR 时执行 `entity_tick(); reweight_eevdf(); misfit/overutilized/core(donor);`，然后 `if (queued) return;`，curr 是 FAIR 时执行 `task_tick_numa(rq, curr); task_tick_cache(rq, curr);`。作者确认「不存在第二个 donor 块」。
- **4/5 推倒重来**（回应 Peter 的 NAK「不接受在 `__schedule()` 中间散落 RT 代码」）：从 `__schedule()` 移除全部 RT 特判，改为 **sched_class 生命周期回调**上报通用的 proxy 转换事件，RT 类消费这些事件以保持 RLIMIT_RTTIME 区间语义。所有权规则：**RT service applicability follows the effective donor scheduling class; watchdog state is charged to `rq->curr`**。回调不取锁不睡眠（core 调用方持 rq->lock；mutex handoff 路径关抢占）。作者放弃了最初的 per-task generation state 方案——它会让 `task_struct` 在 x86-64 与 i386 上各增加一个 64 字节分配单元。
- **1/5 与 sched_ext 的协同**：Andrea Righi 主动提示其 v13 系列（见 2.2）会让两系列「很快兼容」。作者回应：本地草稿中 `task_tick_scx()` 显式 donor-gated；曾用 v13 + 早期 5 补丁系列建过集成树，唯一文本冲突就在 `task_tick_scx()` hunk，`CONFIG_SCHED_CLASS_EXT=y + CONFIG_SCHED_PROXY_EXEC=y` 下能构建并启动，但没有稳定的 EXT↔FAIR、RT/DL→EXT 全混合运行时矩阵。

#### 效果

无 benchmark。有的量化信息全部是**结构开销**：per-task generation state 方案 +64 字节/task_struct（已放弃）；per-entity baseline 使 sched_entity 224→256 字节（i386 + SCHED_CORE，已改存 struct rq）；「集成树能构建并启动」属作者自述，未见运行时测试数据。

#### 社区态度

- **Peter Zijlstra（09-09，评审的直接对象）**：3/5 要求重排（单 donor 块 + 单 curr 块）；4/5 明确 NAK——不接受在 `__schedule()` 中散落 RT 代码。09-10 当天他尚未对作者的新设计表态。
- **Andrea Righi（09-10）**：跨系列协调而非 review——确认 v13 与本系列在 `task_tick_scx()` 上的冲突面，愿意协调所需改动。
- **未解决的焦点**：4/5 的回调设计是否满足 Peter 的底线（新设计把判断移进 RT 类自身消费回调，方向一致但未获确认）；1/5 的 `task_tick()` 签名改动必须由 Peter 收下；两系列的合入顺序待协调。
- 评估：likelihood 从 low 上调到 medium——全部 blocking 意见都有了具体且方向正确的新设计，v5 路线清晰。


### 2.4 sched: Account cgroup CPU time to the execution context（v2）

> **系列**：`[PATCH v2]`（单补丁，`kernel/sched/fair.c` 单行）· **作者**：Hui Su · **线程根**：`<20260904034707.268416-1-sh_def@163.com>`（2026-09-04）
> **状态**：under_review；Tejun Heo 定调 + John Stultz「Tentatively: Acked-by」，等 Peter Zijlstra 收取（likelihood: high）
> **日报**：`sched-20260910-016`

#### 背景与问题

PE 拆分上下文后，per-task 与 thread-group 的 user/system 时间已跟随实际执行者，但 `cgroup_account_cputime()` 仍记给 donor。当 donor 与锁持有者（owner）分属不同 cgroup 时，`cpu.stat` 的 `usage_usec` 会落到另一个组头上——**容器内 CPU 用量在 PE 下变得不可解释**。

争议点不是代码而是设计意图：`aa4f74dfd42b`（"sched: Fix runtime accounting w/ split exec & sched contexts"）当初刻意记给 donor。John Stultz（该 commit 作者）的动机是按 CPU 带宽控制器来想——「该被限流的组」就是 donor 的组，即便 donor 把时间借给 owner、甚至因此突破 owner 组的限流，也应记在 donor 账上。

#### 技术方案

```c
--- a/kernel/sched/fair.c
-	cgroup_account_cputime(rq, rq->donor);
+	cgroup_account_cputime(rq, rq->curr);
```

作用域刻意划清：只改 usage 归属，不动 `update_curr()` → `account_cfs_rq_runtime()` 的带宽路径——John 设想的限流行为完全不变。09-10 Tejun 的回帖把「usage 口径与 bw 口径要不要一致」正面定调：

> "Yeah, I want the cgroup base stats to agree with what's reported for threads. This makes it disagree with bw enforcement but I think it makes more sense to bridge that gap with explicit stats for proxy execution like you're suggesting."

拆开是三层决定：(1) cgroup base stats 必须与 per-thread 上报一致（`cpu.stat` 与 `/proc/<pid>/stat` 不能对不上）；(2) 由此产生的 usage/bw 口径分离是被接受的设计结果；(3) 缺口用 **proxy execution 显式统计**（John 提的 per-task "donated"/"gifted" 时间，经 rstat 聚合到 cgroup）补齐，而不是让 usage 迁就 bw。

#### 效果

无性能数据（只改统计归属）。效果论据是 Tejun 给出的可检验一致性约束：改之前，donor 与 owner 跨 cgroup 的 PE 场景下 `cpu.stat:usage_usec` 与 `/proc/<pid>/stat` 的 utime+stime 之和会对不上；改之后一致。仍无实测：「bandwidth 与 throttling 行为不变」只有作者的代码路径论证；补丁会改变监控/计费口径读数，对既有采集侧的迁移影响邮件中无人讨论。

#### 社区态度

时间线（三天内三方对齐）：

- **Tejun Heo（cgroup 维护者）**：09-04 给条件式 ack（"Provided John is okay with going this way"）→ 09-10 直接回复 John 定调（引文见上），把条件变成他本人的设计主张。
- **John Stultz（`aa4f74dfd42b` 作者）**：09-09 给出 "Tentatively: Acked-by"（原话含 "I'll trust your judgement"）；**09-10 缓存截止前未回复 Tejun 的定调邮件**——Tentatively 是否转正、是否接受口径分离，是本线程唯一悬着的确认。
- **Peter Zijlstra**：未参与本线程。同日他在同作者的相邻补丁（2.5）上表态走 sched/urgent，说明 PE 记账类小修复的收取通道是通的——本补丁完全可以一并提出。
- **后续工作已被点名无人认领**：donated/gifted 统计（per-task + rstat 聚合）是 cgroup 维护者明确认定为正确方向的独立特性，也是本批 PE 工作里离 cgroup/cpuset 主线最近的一个参与点。


### 2.5 sched/core: Call wq_worker_tick() for the execution context（v1）

> **系列**：`[PATCH]`（单补丁，`kernel/sched/core.c` +5/-4，`Fixes: af0c8b2bf67b`）· **作者**：Hui Su · **线程根**：`<20260902150208.1209922-2-sh_def@163.com>`（2026-09-02）
> **状态**：under_review；Tejun Heo 无条件 Acked-by（09-03），Peter Zijlstra 承诺走 sched/urgent（09-10）
> **日报**：`sched-20260910-017`

#### 背景与问题

`sched_tick()` 里调度侧记账走 donor、`sum_exec_runtime` 走 curr，唯独 `wq_worker_tick()` 挂错了边——它做的是「当前真正在跑的 kworker」的 CPU 时间统计与 `WORKER_CPU_INTENSIVE` 判定，属于**执行上下文**。作者给出两种错误模式：

> donor 不是 worker 而 curr 是 worker 时，kworker 代跑期间的 workqueue 记账被跳过，"can delay WORKER_CPU_INTENSIVE handling and pool concurrency management, which can delay pending kernel work and userspace operations depending on it"；
> donor 是 worker 而 curr 是别的任务时，会给一个**已经阻塞**的 kworker 记时间。

触发前提：`CONFIG_SCHED_PROXY_EXEC` 依赖 `EXPERT` 且与 `!PREEMPT_RT`、`!SCHED_CLASS_EXT` 互斥，默认关闭；未开启时 donor 恒等于 curr，无可观测影响（这也解释了线程无 `Cc: stable`）。

#### 技术方案

```c
--- a/kernel/sched/core.c
 	curr = rq->curr;
-	if (donor->flags & PF_WQ_WORKER)
-		wq_worker_tick(donor);
+	if (curr->flags & PF_WQ_WORKER)
+		wq_worker_tick(curr);
```

`psi_account_irqtime(rq, donor, NULL)` 等调度侧记账刻意保留 donor——「只切消费者、不动拆分本身」是这一批 donor/curr 修正的共同形态。日报作者对照本地内核树确认：Linux 7.2-rc6 的 `kernel/sched/core.c:5803-5804` 仍为 `wq_worker_tick(donor)`，缺陷在当前主线依然存在。

#### 效果

线程内**零测试数据**：没有 worker CPU 时间偏差量、`WORKER_CPU_INTENSIVE` 误判次数或 pool 并发管理延迟的数字，也没人报告过线上症状。可核实的只有代码层面两条：缺陷未修（主线核对）；影响面限于显式开启 PE 的调试/专用内核。同作者的 `task_sched_runtime()` 补丁（2.1 效果节）带了实测，本补丁可复用同一套测试骨架，至今无人做。

#### 社区态度

- **Tejun Heo（workqueue 维护者）**：09-03 无条件 `Acked-by`，并把路由问题抛给调度侧："Peter, how do you want to route this patch? It can go through either sched or wq."——内容层面自始无对手。
- **Peter Zijlstra**：调度侧沉默七天后，09-10 回复："Sorry, seems this got lost in the email deluge :/ I can take it through sched/urgent." 未要求任何改动、未要求与同作者其他 donor/curr 修正合并成系列。措辞是「愿意收」而非「已收」，缓存内无 tip-bot 回帖。
- **当日对照样本**：Peter 同日还对 PE+scx v13 逐条评审、把 Olympus v5 从收取队列撤下——可见其收取标准：小、正确、带 `Fixes:`、已被对口维护者 ack 的修复走 urgent 快通道。
- **无人提出的重叠风险**：本补丁与 2.3 的 v4/v5 tick 系列改同一片 `sched_tick()`，两条线同作者、同函数但分散在两条线程，先后顺序无人协调（urgent 落地后 tick 系列必然 rebase）。


### 2.6 同族其他修正

**A. `sched/core: fix task_sched_runtime() for proxy execution`（v1）**

> **作者**：Hui Su · **线程根**：`<20260902112539.879979-1-sh_def@163.com>`（2026-09-02）· **状态**：零回帖 · **日报**：`sched-20260902-001`

#### 背景与问题
`task_sched_runtime()` 用 `task_current_donor(rq, p)` 取调度上下文、又用 `p->sched_class->update_curr(rq)` 记账——代理运行时的记账对象应是 donor，语义互相矛盾（代码见 2.1 效果节）。

#### 技术方案
改成 `task_current()` + `rq->donor->sched_class->update_curr(rq)`，`Fixes: 7de9d4f94638`。

#### 效果
带实测（本族修正里唯一有数据的）："Tested with both RT and fair donors proxy-executing a fair mutex owner. Before the change, CPUCLOCK_SCHED reads repeatedly returned unchanged runtime during confirmed proxy-execution windows. After the change, no stale reads were observed."

#### 社区态度
**自 09-02 起零回帖**。2.5 被承诺收取说明这条语义线整体被认可——接手评审/给 Tested-by 是当前性价比最高的参与点。

**B. `sched/rt: Fix RT watchdog accounting for proxy execution`（v1）**

> **作者**：Hui Su · **状态**：v1 评审中，09-10 被 2.3 的 v4/v5 系列吸收（4/5 的「watchdog 记 rq->curr、service 跟 effective donor class」规则）· **日报**：`sched-20260903-005`

#### 背景与问题
RT watchdog（RLIMIT_RTTIME）在 PE 下对 donor/curr 的归属未定义。

#### 技术方案
独立补丁形态已被 v4 4/5 的 sched_class 生命周期回调设计取代，不再单独推进。

#### 效果 / 社区态度
见 2.3——该问题的最终形态由 tick 系列决定。

**C. NUMA/cache tick 从执行上下文驱动**（`sched-20260908-001`）：Peter 否定 v3 的 core 侧 hook——"So I'm not liking this, like at all. In fact, this is pretty terrible."，PoC 改为 `task_tick(rq, queued)` 让各类自取 curr/donor；该方向已并入 2.3 的 v4/v5 系列，不再独立存在。

**小结**：PE 的「上下文二义性」正在成为新的语义坐标系——runtime 记账、workqueue、NUMA/cache tick、cgroup 统计、RLIMIT_RTTIME、core slicing 逐一被重新审视。已收敛的规则是「消费者跟执行上下文、调度器内部状态跟 donor」，但每个具体路径都需要单独论证，且 `sched_tick()` 已是多个系列（PE tick v5、PE+scx v14、wq_worker_tick）共同触碰的最热点。


---

## 三、虚拟化：preferred CPUs 与 steal 驱动的 vCPU 退让

### 3.1 sched, steal_governor: Introduce preferred CPUs and steal-driven vCPU backoff（v13）

> **系列**：`[PATCH v13 0/13]`（13 补丁，23 files changed，+804/-19）· **作者**：Shrikanth Hegde（IBM）· **线程根**：`<20260909135617.871006-1-sshegde@linux.ibm.com>`（2026-09-09）
> **状态**：under_review；已正式请求排入 sched/core、目标 7.4，Peter/Ingo 未表态
> **日报**：`sched-20260909-010`（整系列）、`sched-20260910-012`（07/13）、`sched-20260907-011`（08/13）

#### 背景与问题

大规模机器上客户普遍 CPU 超配：给 VM 配很多 vCPU、背后是更小的共享 pCPU 池。多个 VM 同时高负载时 pCPU 池被争抢，hypervisor 必须为公平 preempt 某个 vCPU；如果被 preempt 的 vCPU 正持锁或关中断，整体前进能力就崩了——隐性代价包括锁持有者被抢占、临界区拉长、TLB/cache miss、host 调度开销。已有的手段都不合适：CPU 热插拔与隔离 cpuset 是重量级、需要管理动作且重建拓扑、还会破坏用户态亲和性；显式任务亲和性对用户几乎不可管理。需要的是**快的、协作式的、内核里的**退让机制，且不违反亲和性契约。建模上用 guest 已看到的 **steal time** 作为争抢程度的量化信号。

#### 技术方案

两层架构，策略与机制刻意分离：

**Layer A（调度器机制，preferred CPUs）**——新增 CPU 状态 preferred，经 `cpu_preferred_mask` 暴露，严格维持为 `cpu_active_mask` 的子集；三个介入点：

1. **唤醒**：`is_cpu_allowed()` 检查目标 CPU 是否 preferred，否则走 `select_fallback_rq()` 选 preferred CPU（前提是亲和性允许）。
2. **tick 推送**：`sched_tick()` 里非 preferred CPU 上的当前任务用 `stop_one_cpu_nowait()` 排队推走（`struct rq` 新增 `npc_push_work_pending` 去重标志）。
3. **负载均衡**（07/13，v12 起定型，3+/5-）：

```c
--- a/kernel/sched/fair.c
-	cpumask_and(cpus, sched_domain_span(sd), cpu_active_mask);
+	cpumask_and(cpus, sched_domain_span(sd), cpu_preferred_mask);

-	/* Do not pull tasks towards !active CPUs... */
-	if (!cpu_active(this_cpu))
+	/* Do not pull tasks towards !preferred CPUs */
+	if (!cpu_preferred(this_cpu))
 		return 0;
```

设计取舍被作者显式记录：只绑到 non-preferred CPU 的任务留在原地（**绝不破坏用户亲和性**）；idle balance 放行（需维持 `nohz.next_balance` 更新）；刻意不给 `find_new_ilb()` 加过滤（steal_governor 按降序摘核、`find_new_ilb()` 按升序找 idle，常见场景天然一致，"Adding additional complexity to it for rare edge cases is not necessary"）。

**Layer B（策略引擎）**——`drivers/virt/steal_governor.c` 可加载驱动（296 行，`CONFIG_STEAL_GOVERNOR`），按 steal 比例低/高阈值（默认 1000ms 周期、200/500）折叠/展开 vCPU，带 sysfs ABI 文档（151 行）与 s390 `hiperdispatch` 适配。

#### 效果

PowerPC（VM1 60VP/30EC + VM2 30VP/20EC，共享池 50 核 SMT8，默认参数，两 VM 同负载报总和；三列对照 baseline/disabled/enabled）：

| 负载 | baseline → disabled → enabled |
|---|---|
| hackbench 10 groups | 5.20 → 5.40(-3.85%) → **4.65（+10.58%）** |
| hackbench 20 groups | 11.39 → 12.01(-5.44%) → **7.09（+37.75%）** |
| hackbench 40 groups | 20.32 → 19.80(+2.56%) → **11.31（+44.34%）** |
| kernbench elapsed | 231 → 235(-1.7%) → **199（+14%）** |
| Daytrader（DB2 真实负载）30% / 60% | 1x → 0.96x/0.94x → **1.53x / 1.41x** |
| memcached GET 1:1000 | 1x → 0.99x → **1.2x** |
| schbench | enabled +1.71~+2.11%，但 disabled 列更高（+0.18~+5.90%）→ 噪声内，作者自陈 "Effectively means no-improvements or regressions" |
| 无 steal 的独占 LPAR | enabled/disabled 吞吐相同 → 框架自身开销可忽略 |

注意：x86（hackbench +90.73%±9.97%、pgbench +31.77%±2.44%）与 s390（pgbench +73.50%±35.91% 等）数据**基于 v2 实现，作者明确标注已过期**；用 v13 重跑是当前最大的证据缺口。已知限制（作者自陈）：依赖 steal time 记账准确（PowerVM 单 VM 场景报异常 steal，已交 hypervisor 团队）；纯 CPU-time 负载可能小幅回退；只覆盖 FAIR 类；push 只推 `rq->curr` 不推排队任务。

#### 社区态度

- **Yury Norov（cpumask/bitmap 维护者，最严格评审者）**：v11~v13 连续三轮实质意见（v11 steal 分母、v12 `cpumask_intersects_and`、v13 rq 字段布局）。关于 `struct rq` 新字段的放置，他的意见值得记录："The struct rq is highly configurable. Depending on your config, the holes will migrate to different places. I'd not rely on just 'optimizing holes' problem. Just put the new field next to logically related existing fields." 作者以 pahole 双 cacheline 尺寸对照回应（128B line 下 `struct rq` 前后均 5632 字节/44 cachelines），当场承诺并发 v13。09-10 Yury 对 07/13 给出 `Reviewed-by`——负载均衡这一最具侵入性的设计点已获长期评审者背书。
- **作者（v13 封面）**："Could this series be considered for queuing in sched/core, targeting inclusion in 7.4? The feature could also benefit from a good testing cycle in the tip tree."——系列第一次明确请求入队时机；同时主动列出限制与 deferred 项（push 扩展到全部排队任务、RT/sched_ext 类、NUMA 感知 splicing）。
- **Peter Zijlstra / Ingo Molnar**：对排队请求无回应。
- **跨子系统维护者全部空白**：改动横跨 sched、bitmap/cpumask（已有 Yury）、driver core、kernel/cpu、drivers/virt、s390、procfs——除 Yury 外没有一个对应维护者表态，这是合入前最实际的缺口。
- **Vincent Guittot**：公平类维护者，对本补丁族改的 `sched_balance_rq`/`sched_balance_newidle` 主干至今未表态。


### 3.2 sched/core: Try to use a preferred CPU in is_cpu_allowed（v11 系列 05/12）

> **系列**：steal_governor / preferred CPU v11 的第 05/12 片 · **作者**：Shrikanth Hegde（IBM）· **状态**：under_review（架构启用争论 09-01 收敛于全架构默认启用）· **日报**：`sched-20260901-010`

#### 背景与问题

`is_cpu_allowed()` / `select_fallback_rq()` 在任务亲和性受限时优先挑选仍被允许的 preferred CPU。争议点不在代码，而在**启用范围**：作者只在 PPC+pSeries LPAR 与 x86+KVM 上实测过，Yury Norov 主张 arm64 等数据再开（"ARM64 testing is obviously missed."）。

#### 技术方案

新增 `task_can_sched_on_preferred()`：只对 `fair_sched_class` 生效；任务正在改亲和性（`task_cpu(p)` 已不在 `p->cpus_ptr` 内）时忽略偏好状态；对存在架构专属 CPU 掩码的情形（典型是 arm64 上跑 32 位任务），不直接用 `cpumask_intersects()`，而是 `for_each_cpu_and(i, p->cpus_ptr, cpu_preferred_mask)` 再逐个与 `valid_mask` 求交——**本轮争论的实质就是这个分支值不值得为它单独设架构门槛**。

#### 效果

本日 3 封回帖全部是可达性与配置普遍性论证，无任何 arm64 实测数字。前序版本的 steal_governor 基准数据不在本日邮件范围。

#### 社区态度

- **Vincent Guittot**：坚持全架构默认启用——"It's always better to support all arch by default, unless something is missing which is not the case here."，再补一刀："But the cpumask is already available not like if you need to create a new one."
- **Dietmar Eggemann（Arm）**：把风险精确切到唯一配置上——"IMHO, when testing the steal_governor on arm64 w/o 'allow_mismatched_32bit_el0', I wouldn't expect much difference in this respect compared to the architectures already tested."，并指出 `task_cpu_possible_mask()`（默认即 `cpu_possible_mask`）已在 `kernel/sched/core.c` 与 `kernel/cgroup/cpuset.c` 中服务同一约束——**等于把 Yury 的「arm64 没测过」转化为「没测的那个分支在主流 arm64 配置下不可达」**（该配置主要见于 Android 13 之前的 32 位用户态设备）。
- **Yury Norov**：未回应 Dietmar 的可达性论证——分歧未正式关闭，但已孤立。
- 结论：v12 按「全架构默认启用」发出（Vincent 在 v11→v12 间明确要求去掉架构 kconfig gating）；arm64 开/关 `allow_mismatched_32bit_el0` 的对照实测仍是缺失项，也是最容易补的数据点。


### 3.3 sched/core: Make fallback CPU selection NUMA-aware（v1）

> **系列**：`[PATCH]`（单补丁，`kernel/sched/core.c` +25/-22）· **作者**：Yury Norov（NVIDIA）· **线程根**：`<20260905033656.311477-1-ynorov@nvidia.com>`（2026-09-05）
> **状态**：under_review；零回帖 · **日报**：`sched-20260905-003`

#### 背景与问题

`select_fallback_rq()` 是「任务无法放在期望 CPU」时的兜底（wakeup 失败、cpuset/亲和性收紧、CPU 下线等）。旧实现先查本地节点、找不到就按 `p->cpus_ptr` 的**数值顺序**取第一个允许的 CPU——数值顺序与拓扑距离无关，三节点以上系统里本地节点无可用 CPU 时可能直接跳到编号靠后但物理更远（hop 更多）的节点。旧代码还为「节点下线导致 `cpu_to_node()` 返回 -1」写了专门分支。

#### 技术方案

- 用 `for_each_numa_hop_mask(cpus, nid)` 按拓扑距离逐层遍历，配 `for_each_cpu_andnot(dest_cpu, cpus, prev)` 每层只考察新到达的 CPU（天然去重）；整段遍历搬进原来的 `for(;;)` 内，`cpuset → possible` 亲和性放宽后仍沿用同一局部性顺序。
- hop 掩码在拓扑重建期间可能不完整，放宽亲和性**之前**额外扫描 `p->cpus_ptr & ~prev`（未被掩码覆盖的 CPU）兜底。
- 遍历用 `rcu_read_lock()` 包住（hop 掩码受 RCU 保护）；`nid` 初始化改为 `IS_ENABLED(CONFIG_NUMA) ? cpu_to_node(cpu) : NUMA_NO_NODE`。

#### 效果

无任何数据：无 fallback 落点分布、无迁移距离、无 workload 数字。最省事的补证方法（日报建议）：在 >2 NUMA 节点机器上对比打补丁前后 fallback 实际选中的 CPU 与其 `node_distance()`（加 tracepoint 或读 `sched:migrate_task_rq` 判断跨了几跳）。

#### 社区态度

**尚无人 review**（不是「review 后沉默」）。可站得住的观察：

- 该函数是 preferred CPU 系列的关键依赖：v12 的 06/13 让 `is_cpu_allowed()` 优先挑 preferred、08/13 的 push stopper 直接调 `select_fallback_rq()` 找落点——hop-mask 化的 fallback 顺序会直接改变推送落点，两件事必须理清先后。
- 作者同一天在 08/13 线程里追问的正是 `select_fallback_rq()` 拿锁后释放到后续 `rq_lock()` 的竞争窗口，与本补丁新增的 RCU 临界区是同一处代码。
- `!CONFIG_NUMA` 与节点下线（`NUMA_NO_NODE`）时 hop 遍历的退化行为正文未说明，而旧代码对后者有显式分支——维护者大概率会问。
- **与 cpuset 的交叉点**：fallback 顺序变化影响「cpuset 收紧后任务落到哪个节点」；同理，`cpu_preferred_mask` 与 cpuset 划分、`housekeeping_cpu()`/nohz_full 的重叠语义在整个系列里都未收口——系列目标 7.4，合入前是提意见的窗口。


---

## 四、Cache-aware scheduling：从单 LLC 到 NUMA/LLC 两级

### 4.1 sched: Scale cache-aware aggregation at LLC granularity（RFC v2，23 片）

> **系列**：`[RFC PATCH v2 00/23]`（23 补丁）· **作者**：Jianyong Wu（Hygon）· **线程根**：`<20260827122816.756234-1-wujianyong@hygon.cn>`（2026-08-27）· v1 2026-06-25
> **状态**：RFC；Peter Zijlstra 逐片精读中（09-01 单日 24 封邮件），v3 待发 · **日报**：`sched-20260901-015`（整系列）、`-004/-005/-006/-007`（分片）、`sched-20260908-010`（20/23）

#### 背景与问题

上游 cache-aware 负载均衡（`CONFIG_SCHED_CACHE`）目前只在 LLC 粒度做聚合与迁移决策，跨 NUMA 节点的放置交给独立的 NUMA balancing，两者互不知情——任务在打分时看不到「离它的偏好内存有多远」，负载均衡无法在「跨节点」与「换 LLC」之间统一取舍。作者对问题的定性是 **"fixed aggregation scope，跨 LLC 无法扩展"**：单 LLC 容量成为聚合上界，超过之后放置退化；当负载铺满整机、每个 LLC 的 CPU 数又少时，单层偏好 LLC 频繁漂移。系列要回答两个问题（cover 原话的复述）：LLC 按什么顺序被考虑，线程组要沿这个顺序铺多远。

#### 技术方案

系列分五段：1-6 拓扑基础设施；7-10 收集 preferred-NUMA 信息与 per-sd 状态；11-16 迁移决策；17-19 与 NUMA balancing 的交互；20-22 线程组利用率估算与 LLC 容量范围；23 调试接口。核心三层：

- **拓扑层（02/23）**：两级距离矩阵——每行数值唯一的 NUMA 节点距离矩阵（贪心边着色去重，海光这类非全对称互连平台上节点间距离不是单一常数）+ 单节点内 LLC 距离矩阵（只用于排序、无物理含义），拼成 affinity sequence。
- **打分层（12/23）**：用连续量替代「任务偏好 LLC 是否等于目的 LLC」的二值判断：

```c
	/* LLC 层：枚举"离 dst 比离 src 更近"的 LLC */
	affi[j] = clamp(src_llc - dst_llc, 1, 1024);   /* NUMA 层下限为 4 */
	score += sd->llc_counts[affi_llc[i]] * affi[i];  /* 偏好任务数 × 距离增益 */
```

即 `Σ(偏好该目标的任务数 × 距离增益)`；输入取自 10/23 在 sched_domain 上开的 per-sd scratch，避免热路径分配。
- **铺开层（20-23/23）**：按线程组整体利用率估算（非对称 EWMA，上升 1/2、下降 1/8）取「能装下它的最小 LLC 前缀」，前缀内的 LLC 只要自身装得下就进，不要求前序先饱和。

被放弃的备选（cover 明写）：给每个进程维护线程组 LLC mask——mask 在 `task_cache_work()` 更新、负载均衡读取，快速变化时读到过期值；且负载均衡路径没有 task 上下文可取对应 mask。

#### 效果

2S/8node/每 node 4LLC 的 Hygon 机器，`numa_balancing=0`、`aggr_tolerance=90`，每项 ≥20 次取均值：

- **hackbench -T -p**（18 配置）：16 个更快，**中位 +27.7%**，中段最明显（`-f 8 -g 1` +34.6%、`-f 12 -g 1` +35.4%）；两处变慢中 `-f 48 -g 2` **-4.1%** 是唯一超出噪声的真回退（根因作者自陈未定位）；12/18 配置的 run-to-run 方差改善（小端最明显：baseline 30-59% vs llc_gran 4-27%）。
- **schbench p99 wakeup latency**（11 线程数）：**全部改善，中位 +16.8%**，10/11 超出噪声，峰值 48/64 线程 +33.0%/+35.3%；但 96/128 线程的方差反而高于基线（15-18% vs 3-5%）。

#### 社区态度

Peter Zijlstra 是唯一评审者，09-01 逐片精读，意见分四层：

- **认可方向并给指引**：affinity sequence + 按需扩范围的骨架未被质疑；09-09 的 commit message 批评值得原文记录："So in general I would really appreciate a few words on *why* you're doing things. I mean, I can read the patch and see what it does, but I cannot divinate … This is esp. important for large series -- or series that do complicated things -- or like this case: both!"
- **要求删除冗余状态**（08/23，已定案）："Consider the trade-off. Adding the accounting adds a cache-miss to every enqueue/dequeue, while re-computing the value on-demand adds some little cost to the balancing (slow) path." → v3 将删除 `numa_counts[]` 改为按需累加。
- **代码级正确性**：12/23 用不稳定全局 `max_lid` 做数组上界被否（应传 base sd 的 `llc_max`）；11/23 的 `can_migrate_node()` 与既有 `can_migrate_llc()` 存在 3 处口径分叉 + 1 处「跳过的正是后面用来否决的最近节点」的自相矛盾。
- **架构级反对**（17/23，唯一未决的方向性分歧）：作者要给 NUMA task/page 迁移拆独立开关，Peter 以第一性原理否掉："At every point NUMA migration should take precedence over LLC. The remote node penalty is much greater than the 'other' llc penalty." 以及 "Disabling page-migration or numa task-migration separately completely wrecks things and you might as well just disable NUMA balancing."，并给出替代方向——"if the process spans multiple nodes we should go do the same again as this patch set does for llc, spread/interleave over the minimal set of nodes that do fit."
- **作者**：07/23 上以粒度冲突反驳（`numa_preferred_nid` 是 per-task、LLC 锚点 `mm->sc_stat.cpu` 是 per-process，硬优先任何一个都会让进程级锚点在节点间弹跳），当日无人接；作者的求方向声明："This patch set is far from perfect and still contains some unresolved issues. Before proceeding further, I would like to confirm whether I am heading in the right direction."
- 评估：likelihood medium 但本季度进 tip 可能性低——17/23 决定系列后三分之一是否重写，硬件证据只有 Hygon 一家（作者自己也写 "Further testing across a wider range of workloads and hardware platforms is needed"）。


### 4.2 sched/fair: avoid creating misfits during cache-aware balancing（已合入 tip/sched/urgent）

> **系列**：`[PATCH]`（单补丁，`kernel/sched/fair.c` 45+/5-）· **作者**：Tim Chen（Intel）· 首发 2026-08-25，重发 09-01
> **状态**：merged_tip（`f0d243a96f2684ad771d678767d17972cf840bd7`，0day 58 config 构建通过，09-04 确认为 sched/urgent 分支 HEAD）
> **日报**：`sched-20260904-006`

#### 背景与问题

cache-aware 负载均衡会偏向任务的 preferred LLC。在 CPU 容量不对称的系统（hybrid / big.LITTLE，`SD_ASYM_CPUCAPACITY`）上，目标 LLC 里可能装着容量太小、跑不动该任务的 CPU：把任务拉过去等于用一次缓存局部性的收益换一次更伤性能的容量损失（人为制造 misfit）。另一处反向问题：active balance 侧 `alb_break_llc()` 因 LLC 聚合否决迁移时，若源 CPU 上已有 misfit 任务，否决方向是反的——更好的匹配 CPU 带来的收益大于更好的缓存局部性。

#### 技术方案

```c
static bool task_misfits_asym_cpu(struct lb_env *env, struct task_struct *p)
{
	return (env->sd->flags & SD_ASYM_CPUCAPACITY) && p &&
	       !task_fits_cpu(p, env->dst_cpu) &&
	       task_fits_cpu(p, env->src_cpu);
}
```

三个落点：判定刻意做成「**源能装下、目标装不下**」才否决——已经不适配源 CPU 的任务仍交给既有 LLC 策略（不挡 misfit 向大核上迁）；对称系统因 `SD_ASYM_CPUCAPACITY` 门控零影响；`can_migrate_llc_task()` 签名改为接收 `struct lb_env *` 并在入口 `return mig_forbid`；`alb_break_llc()` 对 `migrate_misfit` 类型直接放行并把 misfit 迁移优先级提到 LLC 聚合之上。

#### 效果

无 benchmark：Ricardo Neri 给了 Tested-by 但未附数据；0day 的 58 config 构建成功（覆盖 21 个架构、gcc 11.5~16.1 与 clang 17~24）是唯一量化证据。misfit 计数下降、hybrid 平台吞吐收益在邮件中未量化。

#### 社区态度

- **Peter Zijlstra**：合入前只有两条格式性意见，均已照办——"Tim sends patch, Tim adds SoB, yes?"（08-26 作者自己补发了 SoB）与 "Also, we start $subject with capital after subsystem: part."（09-01 重发时标题已大写）。无技术异议。
- **技术背书**：`Reviewed-by: Ricardo Neri` + `Tested-by: Ricardo Neri` + `Reviewed-by: Chen Yu`——两位正是 hybrid / 非对称容量方向的相关人；收件人含 K Prateek Nayak（AMD）、Vincent Guittot、Len Brown、Aubrey Li。
- **事后重要修正**（见 4.4）：AMD 大小核依赖 `SD_ASYM_PACKING` 而非 `SD_ASYM_CPUCAPACITY`——本补丁对 AMD 混合 CPU 场景无效，Tim Chen 本人 09-10 确认。
- 评估：merged；补丁不带 `Fixes:`，按「新 cache-aware 行为的配套修正」处理，大概率不进 stable。


### 4.3 sched/cache: Per-task control of cache aware scheduling via prctl（RFC 0/7）

> **系列**：`[RFC 0/7]`（7 补丁）· **作者**：Tim Chen（Intel）· **线程根**：`<cover.1787955777.git.tim.c.chen@linux.intel.com>`
> **状态**：RFC，接口形状未定 · **日报**：`sched-20260909-016`

#### 背景与问题

cache-aware scheduling 在异构 L3 与大小核场景下无法可靠推断「哪些任务应被视为同一缓存分组」——前置事实是 CAS 在 AMD 大小核上表现不佳的持续报告（见 4.4）。RFC 的思路是把决定权交给用户态：应用/运行库通过 prctl 显式声明任务分组。

#### 技术方案

prctl 级 per-task 控制（具体 ABI 形态在 RFC 中，v1 细节未全部进入缓存）。真正的开放问题是接口载体：prctl（必须改应用）vs cgroup（运行时可管理、有现成策略工具）vs `sched_setattr()` 扩展。

#### 效果

零数据：CAS 在异构平台「效果不好」至今没有归因清楚的对照实验，因此这个逃生口能带来多少收益无法量化。

#### 社区态度

- **Shrikanth Hegde（IBM，09-09）**：对该方案提出四个当天无人回答的可用性质疑，值得整段引用：

  > "So, As you said, this is effectively asking user to make the decision. But what tools do user space have today to make effective decisions? Application changes could turn out to be tricky to do and how an application developer will know whether to group them together or not? What's guidance there?"

  四问中两条是新的：用户态**决策依据**缺失；**能否在应用已跑起来之后再分组**（决定不能改代码的二进制是否可用，若不能，绝大多数现网负载这条路是死的）。另两条：cgroup 被否决的理由是否仍成立（"I remember you guys discussed about cgroup and decided it is not a good option. That argument still holds?"）。
- **作者方（Intel）**：截至当日未回应。这类「要求提供材料」的问题若不被回答，RFC 会一直停在「设计未定」。
- 评估：unknown；与 5.2 的 NUMA prctl 系列撞在同一个「per-task 接口没有配套用户侧决策工具能否落地」的问题上，两份接口的取舍如果不一致，本身就是需要向社区提出的问题。

### 4.4 Cache-aware scheduling does not work well with amd big/little cores（bug 报告线，stalled）

> **系列**：无补丁（用户报告 + 维护者诊断）· **报告者**：Klaus Kusche · **状态**：stalled（报告者休假，验证悬空）· **日报**：`sched-20260910-010`

#### 背景与问题

Klaus 报告 cache-aware scheduling 在 AMD Strix/HX 类大小核机器上表现不佳。此前讨论一直把 Tim Chen 的 `SD_ASYM_CPUCAPACITY` 补丁（即已合入的 4.2）当作对照组——**这个前提是错的**。

#### 技术方案（诊断修正）

09-10 的关键技术修正：Tim Chen 经 Ricardo 提醒确认 **AMD 混合 CPU 依赖 `SD_ASYM_PACKING` 而非 `SD_ASYM_CPUCAPACITY`**，因此他的补丁（`20260825174112`）对 Klaus 的系统根本无效。新的候选修复是 Chen Yu 的 ITMT 与 cache-aware scheduling 协调补丁（`20260810033742`），作用是防止任务卡死在错误的 LLC（ITMT 场景）。Tim 请 Klaus 把它与 Mario 的 ITMT/debugfs 补丁叠加测试；Chen Yu 跟进索要三项诊断信息：调度域 dump、`sched_itmt_enabled`、`sched_core_priority`。

#### 效果

无：报告者休假中，按新组合（基线 / +Chen Yu ITMT 补丁 / +Mario debugfs 补丁）的复现与归因数据至今缺失——**CAS 在异构平台「效果不好」被反复报告了十几天，仍没有一份对照数据**。

#### 社区态度

- **Tim Chen**：主动修正自己补丁的适用范围（对照组前提不成立），并把方向指向 Chen Yu 的 ITMT 补丁——维护者自我纠错的样本。
- **Chen Yu**：接手诊断，索要三项信息，等待复现。
- 评估：unknown；该线同时是 4.3 prctl RFC 的动机来源——根因未定，逃生口的必要性就无法论证。

### 4.5 sched/cache: Honor migrate_llc_task semantics in active load balance（v4）

> **系列**：`[PATCH v4]` · **作者**：Lu Wang · **状态**：under_review，likelihood high · **日报**：`sched-20260903-011`；配套分母讨论 `sched-20260910-011`

#### 背景与问题

active load balance（ALB）路径没有遵守 `migrate_llc_task` 语义，导致 cache-aware 聚合意图在 ALB 场景失效。配套的口径争论：`nr_pref_llc_running`（判定 LLC 聚合是否应否决迁移的计数）的分母该用哪个域计数。

#### 技术方案

ALB 决策路径接入 `migrate_llc_task` 语义（v4 细节见日报）。分母口径由 Tim Chen 以 T1/T2 反例收口：设 T1 偏好在当前 LLC 运行、T2 不偏好且处于 delay-queued 状态——若用 `cfs_rq->h_nr_queued`（含 delay-queued）作分母，T2 会把计数抬高、错误触发 active balance 把任务搬出本 LLC；runnable 域计数则不受 delay-queued 影响。

#### 效果

无 benchmark；Chen Yu 对分母结论启动 sanity 测试，结果待回报。

#### 社区态度

- **Tim Chen**：给出 T1/T2 反例并指出 Lu Wang 的补丁只缓解 `migrate_llc` 一种迁移原因（LLC 聚合还有其他迁移路径）。
- **Chen Yu**：接受反例（"09-09 的两连问由 Tim 完整回答"），维持 runnable 域计数——分母口径之争基本落定。
- 评估：high，补丁方向干净、争议已从「改不改」转移到「补丁覆盖面是否够」。


---

## 五、NUMA balancing

### 5.1 sched/numa: stop VMA scan filters from gating promotion（v1，2 补丁）

> **系列**：`[PATCH 0/2]`（含 2/2 `sched/numa: scan read-only file mappings in tiering mode`）· **作者**：Gregory Price（Meta）· **线程根**：`<20260904182006.1562449-1-gourry@gourry.net>`（2026-09-05）
> **状态**：under_review；v1 有已知缺陷，v2 待发（并发扫描 + mode=3）· **日报**：`sched-20260905-006`（系列）、`sched-20260907-009`（2/2）

#### 背景与问题

分层内存（`numa_balancing=2`，`NUMA_BALANCING_MEMORY_TIERING`）下，hint fault 不再只是「socket 驻留信号」，而是**提升机制本身**——慢层 folio 只有先被扫描标记、再被访问产生 fault，才会被考虑搬到顶层。而 `task_numa_work()` 的 VMA 级过滤器还是「驻留信号」年代写的：被过滤的 VMA 等于**永不被扫描 = 永不被提升**。两个具体过滤器：

1. **per-VMA PID 过滤器**：`vma_is_accessed()` 要求扫描线程在 `vma->numab_state->pids_active[]` 里有 hash 位，而唯一的设置者 `vma_set_access_pid_bit()` 只在 hint fault 时被调用——PROT_NONE 扫描又是 hint fault 的唯一来源，形成**自我锁死**（新扫描可数小时甚至数天不产生 fault）。既有三个逃生机制（`numa_scan_offset`、`f22cde4371f3` 的 `nr_threads` 轮 horizon、`vma_pids_forced`）都不解决问题。
2. **只读文件映射排除**（`4591ce4f2d22`）：

```c
	if (vma->vm_file &&
	    (vma->vm_flags & (VM_READ|VM_WRITE)) == (VM_READ)) {
	        trace_sched_skip_vma_numa(mm, vma, NUMAB_SKIP_SHARED_RO);
	        continue;
	}
```

其前提「这类页会被 cache 复制、不会迁移，trap 了纯亏」在分层下失效——共享库/可执行主段会单向沉积到慢层。

#### 技术方案

不移除任何过滤器，而是新增 `vma->numab_state->slow_only`：被拒的 VMA 仍被扫描，但**只把非顶层节点的 folio 置为可 hint fault**——顶层 folio 的标记范围与原来完全一致，即「只新增提升候选、不改放置」作为不变式（这是为降低 mm+调度两侧接受门槛的刻意框定）。patch 2 把只读文件映射的跳过条件改为仅在未开 tiering 时生效，并设 `slow_only = ro_file`。作者有意不动 `prev_scan_seq`：受限扫描未完整扫过 VMA，若在那里更新会永久解除 `get_nr_threads()` horizon。总改动 +47/-10，两补丁各带 `Fixes:`（`fc137c0ddab2` / `c574bbe91703`）与 `Assisted-by: Claude`。

#### 效果

768G DRAM + 256G CXL、两个 ~430GB 高线程数据库服务：

| 指标 | 修复前 | 修复后 |
|---|---|---|
| DRAM 带宽 | 200→150GB/s（持续衰减） | 稳定 200–250GB/s |
| CXL 带宽 | 5→45GB/s 后被卡住 | 稳定 7–10GB/s |
| 请求延迟 | 800us→5ms（跟随 CXL 带宽） | 800us–2ms（跟随请求负载） |
| 20G 哈希表 | 100% 落 CXL | DRAM/CXL 各 50% |
| 主程序二进制 185M | 169M（91%）积在 CXL | 跟随运行时负载 |

归因：大 shmem VMA 占满一整轮扫描游标，另有 **84G 分散在 2537 个 VMA 因「不活跃」被跳过**。缺失：受限扫描的额外 CPU 开销与 `ptl` 争用只有推理、无实测。

#### 社区态度

- **sashiko（自动评审）**：测出 v1 的真实缺陷（`slow_only` 无条件复位会让分两轮扫完的 VMA 被提前重新纳入），作者当天给出两行修正——机器人评审在这条线上是唯一「reviewer」。
- **作者（09-07 自我修正，值得整段记录）**："On a second look, there are a few issues bundled in with this, and the change required to handle the concurrent scan + mode=3 (`_NORMAL|_TIERING`) requires a bit more complex of a change to fully resolve. … the existing tests still stand. As-is, any mode with `_TIERING` set is very broken at the moment because of the filtering mechanisms."——把问题定性从「一个扫描例外」升级为「任何带 `_TIERING` 的 mode 目前都是坏的」，这是本系列最有利于走 fixes 通道的一句话。
- **人类维护者**：零回帖。改动涉及 `mm_types.h`/`mempolicy.c` 与分层提升路径，需要 mm 与调度两侧同时认可，目前都没有出现。
- 评估：medium（问题真实、数据硬、带 `Fixes:`、改动范围克制），但 v1 当前版本不可合。


### 5.2 sched/numa: Add per-process automatic NUMA balancing control（v1，4 补丁）

> **系列**：`[PATCH 0/4]`（12 files，+201/-4）· **作者**：Li Zhe（ByteDance）· **线程根**：`<20260908122446.56708-1-lizhe.67@bytedance.com>`（2026-09-08）
> **状态**：under_review，零 review · **日报**：`sched-20260908-007`

#### 背景与问题

自动 NUMA 平衡只有两个粒度可选：全局 `kernel.numa_balancing` sysctl（一关全关）与 memory policy（间接、语义不是「关掉平衡」）。封面给出的用例形状：

> "That works well as a system default, but it is too coarse for workloads where a launcher wants most processes to use the default policy while a selected process opts out because it already manages NUMA placement or cannot afford the sampling overhead."

即 launcher 让个别自管 NUMA 放置、或吃不起采样开销的进程整体退出扫描。

#### 技术方案

状态分两处（本系列最关键的设计取舍）：`signal_struct` 存用户可见的 `numa_balancing_enabled`（线程组语义），`task_struct` 存调度快照 `numa_balancing_sched_enabled`（热路径零额外开销读取）。设置路径先改 signal，再在 `tasklist_lock` 读侧逐线程以 `sched_change` 更新快照：

```c
	if (old_enabled != enabled) {
		sched_numa_balancing_change_task(current, enabled);
		read_lock(&tasklist_lock);
		for_other_threads(current, t)
			sched_numa_balancing_change_task(t, enabled);
		read_unlock(&tasklist_lock);
	}
```

fair.c 共 9 处热路径按快照早退（`task_numa_fault()`、`task_tick_numa()`、`update_scan_period()`、`task_numa_compare()` 等），`account_numa_{enqueue,dequeue}()` 的计数与 enabled 相与。uAPI：`PR_SET/GET_NUMA_BALANCING`（82/83，两态），ABI 刻意「弱且可预测」——"PR_GET_NUMA_BALANCING returns the configured process mode, not the effective state after combining the global sysctl/static key and memory policy restrictions." 不主动清理已装 hinting PTE，任其自然排空。

#### 效果

零数据：没有「关掉扫描省多少」的量化，`cannot afford the sampling overhead` 只是动机陈述。

#### 社区态度

**零回帖**（无 review、无 Ack、无 NAK）。cover 的可取之处是直面并放弃了三个前案——Chen Yu 的 per-cgroup 提案（当时的共识是自动平衡本就按 task/process 粒度工作，cgroup/cpuset 应继续只描述分组与放置域）与 2023 两版 prctl 提案（per-mm 三态 + 可覆盖全局 static key）。未论证的硬伤：与 `numa_group`（按 mm 跨线程组聚合）的粒度错配——同 mm 的其他线程组仍在扫描时，统计与迁移决策可能把该进程拖回去；`read_lock(tasklist_lock)` 下逐线程 `task_rq_lock` 的锁序在数千线程进程上的代价未量化。与 4.3 的 prctl 系列撞在同一个「per-task 接口没有配套用户侧决策工具」的问题上。

### 5.3 sched/fair: Reset NUMA fault locality after scan period update（已合入 tip/sched/core）

> **系列**：`[PATCH]`（单补丁，`kernel/sched/fair.c` +5/-2）· **作者**：Eric Kim（Reported-by: Binwon Song）· AuthorDate 2026-08-18
> **状态**：merged_tip（`e81ee06308379a5f2ededf997bcf17551bce5db7`，Committer Peter Zijlstra 2026-09-10，**Cc: stable**）
> **日报**：`sched-20260910-006`

#### 背景与问题

NUMA balancing 用 `p->numa_faults_locality[]` 统计上一扫描窗口的 remote/local 故障数与迁移失败次数（下标 2），`update_task_scan_period()` 据此调扫描节奏。当「无故障记录或上次窗口有迁移失败」时走早退分支：`numa_scan_period` 直接翻倍（封顶 max）后 return。问题：**该早退路径跳过了函数末尾的 `memset(p->numa_faults_locality, 0, ...)`**——陈旧的非零计数（尤其迁移失败标记）残留到下一窗口，任务每次评估都命中早退，扫描周期被无意一路翻倍到上限，即使实际既无迁移失败也无故障，NUMA balancing 对这类任务近乎停摆。

#### 技术方案

```c
-	return;
+	goto out;
...
 out:
+	memset(p->numa_faults_locality, 0, NUMA_NUM_LOCALITY * sizeof(u64));
```

把早退分支改走 `out:` 标签，保证两条路径都清空 locality——「locality 统计窗口与扫描周期更新严格同步」。日报作者对照主线确认缺陷存在（早退仍是裸 `return`，memset 只在正常路径末尾）。

#### 效果

合入邮件未附 benchmark。可推断收益：受影响任务的 `numa_scan_period` 不再被陈旧计数锁死在上限，NUMA balancing 恢复正常节奏调节；具体量化未获取到。

#### 社区态度

- **Peter Zijlstra**：合入 tip/sched/core 并 Cc stable——走 sched/core 而非 urgent，定级为常规修复而非紧急回归；缺陷自 `numa_faults_locality` 引入起长期存在，stable 回合价值明确（自家分支 OLK-6.6 等若启用 NUMA balancing 可直接评估回合，注意 out 标签重构与本地代码差异）。
- 中间评审过程未进入缓存；合入邮件中无分歧。


---

## 六、负载均衡与 EEVDF

### 6.1 sched/fair: A series of load balance patches to improve real-time performance of CFS tasks（RFC v1 RESEND，10 补丁）

> **系列**：`[RFC PATCH RESEND 0/10]`（4 files，+224/-25）· **作者**：Xin Zhao · **线程根**：`<20260910042950.1619727-1-jackzxcui1989@163.com>`（2026-09-10，v1 首发 08-15）
> **状态**：RFC；核心补丁 05/10 被拒，需按 nr_idle_scan 方向重构 · **日报**：`sched-20260910-001`

#### 背景与问题

嵌入式平台常用 CONFIG_HZ_250，测试发现大量「不合理 CPU 空闲」事件：**CPU 进入 idle 的整个时长内，存在可运行、不受 cgroup 限制的任务却超过 2.5ms 未被调度**。作者统计 95% 以上此类事件短于 4ms，但仍有 4-5ms 甚至 5-10ms 的实例——对实时系统，超过 4ms 的调度延迟就是性能尖刺。全部补丁来自对每个捕获事件的 ftrace 与负载均衡代码流日志分析。

#### 技术方案

10 补丁分层（封面自述）：1 通用修复（`rd->online != env->cpus` 时不置 overload）；2/3 独立前置；4 定义 `LB_PROMOTE` sched_feat（features.h +24）；5 面向嵌入式的 `select_task_rq_fair_thin()`；6/7 改造 `active_load_balance_cpu_stop()` 支持抢占式 active balance；8 移除 newly idle 的 `avg_idle` 提前退出；9/10 newly idle 尽力找可迁移任务。本质是**用本会 idle 的 CPU 时间（sys% 上升）换调度延迟**。5/10 讨论中暴露的关键设计点：wake 快速路径只在 LLC 内选 idle CPU 对 CPU 数少的机器不友好，作者的折中是——

```c
	want_affine = !wake_wide(p) && cpumask_test_cpu(cpu, p->cpus_ptr) &&
		      !sched_feat(LB_PROMOTE);   /* LB_PROMOTE 开启时强制走慢路径 */
```

#### 效果

作者单一平台（18 CPU、多 cluster、每 cluster 一个 LLC；fillback 场景）：

- **60 秒事件分布**：开启 LB_PROMOTE 后三组测试的 2.5-3ms / 3-4ms / 4ms+ 事件**全部为 0**（关闭时分别为 4/13/1、6/3/0、1/1/0）。
- **25 分钟×15 轮端到端延迟**：max 172（on）vs 180（off）；median of avg 166 vs 167.68。
- **代价**：sys% max 9.68 vs 9.35，median of avg 8.81 vs 8.55。
- 5/10 讨论中补充分测量：`select_task_rq_fair()` 耗时 avg 460ns→328ns（内核模块累计计时，脚本有 insmod 报错输出，可信度一般）。

#### 社区态度

RESEND 当天引来 Vincent、Prateek、Kayra 三人 11 封讨论：

- **Vincent Guittot（05/10，方向性拒绝）**："We don't want yet another select idle cpu function." 但随后给出可接受路径——`nr_idle_scan` 是为数百 CPU 的大 LLC 设计的，"当只有几个核时，扫描数量可以放得更宽"，即**小 LLC 场景放宽 nr_idle_scan 上限**（该补丁无人认领）；并指出主线 `sched_balance_find_dst_cpu()` 本就看得更宽、需要 SD_BALANCE_WAKE（作者平台该 flag 默认为 0）。
- **K Prateek Nayak（01/10、03/10）**：01/10 质疑对无法被帮助的 CPU 置 overload 的意义并给出 rq->flag 替代方案（与 Vincent 就 `LBF_DST_PINNED` 清 dest_cpu 的原因完成一轮澄清）；03/10 直说 "I'm not convinced by the justification for this in the commit message"（detach 时 PELT 信号已摘除，commit message 论证不准确）——作者接受把清 flag 移到开中断前。
- **Kayra Cizmeci（02/10）**：质疑 `smp_processor_id()` 与 `busiest_cpu` 等价性的论证，作者当天未正面回答；另注意 02/10 subject 有 "scbed/fair" 笔误，尚无人指出。
- 评估：likelihood low——05/10 需推倒重来，但讨论未关门；前置修复 1/2/3/9 可拆出独立推进。


### 6.2 sched/fair: Rework/fix task_h_load()（Peter 4 补丁系列之 4/4）

> **系列**：`[PATCH 0/4]`（4/4 为 `Rework/fix task_h_load()`）· **作者**：Peter Zijlstra · **线程根**：`<20260828075558.660152190@infradead.org>`（2026-08-28）
> **状态**：under_review；192 核启动 panic 已定位，fixlet 已获确认（"I'll fold it in"），等重发 · **日报**：`sched-20260902-007`

#### 背景与问题

`task_h_load()` 计算任务沿 cgroup 调度层级的「层级负载」。旧实现依赖 `for_each_sched_entity()` 遍历时顺带设置的 backlink，而 `__update_blocked_fair()` 这类调用方走 `leaf_cfs_rq_list`、不做逐级上溯——4/4 的 rework 把层级信息参数化，引入了会**改写循环变量**的 `for_each_sched_entity_bl(se, cfs_rq)`。09-02 Chen Yu 报出 192 核机器**启动即 panic**：`systemd-udevd` → `sched_autogroup_create_attach` → `__schedule` → `pick_task_fair`，`Oops: general protection fault, kernel NULL pointer dereference 0x69`。

#### 技术方案

Chen Yu 的根因分析（原文）：

```c
	After the following top->down backlink traverse,
	for_each_sched_entity_bl(se, cfs_rq)
	    update_cfs_rq_h_load(group_cfs_rq(se), se, cfs_rq);

	cfs_rq is not the root->cfs_rq anymore, but a middle cfs_rq(autogroup
	in above example). …
	se = &p->se;
	cfs_rq->curr = se; /*wrong cfs_rq*/
```

即 `pick_eevdf()` 在错误的中间层空树上返回 NULL，`se->sched_delayed` 读空指针。Peter 的修法不是「恢复 cfs_rq」（Chen Yu 建议），而是**把遍历挪到函数尾部**：第一版移到 `if (task_on_rq_queued(p))` 之前；第二版（最终）进一步移到 `list_move(&se->group_node, &rq->cfs_tasks)` 与 `WARN_ON_ONCE(se->sched_delayed)` 之后，并把 `if (!first) return;` 挪到遍历之后。

#### 效果

无 benchmark，效果证据是「崩溃消失」：Chen Yu 的 192 核 GPF 与 Vincent 的 "I faced the same crash while testing" → "Yes, this fixes it for me too"。层级负载计算本身的正确性收益未量化（Vincent 8-31 的 "the rework looks good to me" 是代码审读判断）。重要触发条件：Vincent 补充 "Some of my platforms didn't crash until I added +cpu in cgroup.sub_controller"。

#### 社区态度

- **Peter Zijlstra（作者）**：两次自我归因——"I think I misread the `se = &p->se; cfs_rq->curr = se;` to reset both se and cfs_rq, but clearly it doesn't."，以及复现环境的无奈："Different physical machine.. *splat*, virtual machine it lives. Argh I hate computers."
- **Chen Yu（Intel）**：唯一问题报告者，给出完整栈、机制解释和一种修法；其 `cfs_rq = &rq->cfs` 方案未被采纳（Peter 用移动遍历位置替代）。
- **Vincent Guittot**：独立复现者（8-31 承诺的测试兑现）；两版 fixlet 均给正向确认；遗留意见 "`Might be good to save pse = p->se`"（遍历同样 clobber `se`）与 `for_each_sched_entity_bl()` 是否隐含「必须从 root cfs 起」的前置条件，无人回答。
- 评估：likely——补丁出自维护者本人、崩溃双人复现、方案收敛到「遍历放哪一行」；等包含 fixlet 的重发。`h_curr`/`h_load` 语义（含已合入的 `cfs_rq->h_curr` 带宽路径修复 `sched-20260901-002`）会决定后续几年 cpuset/cgroup 场景的负载估算口径。


### 6.3 sched/fair: Preserve newidle cost decay across domains（v1）

> **系列**：`[PATCH]`（单补丁，`kernel/sched/fair.c` 1+/1-）· **作者**：Li RongQing（百度）· **线程根**：`<20260909094523.2314-1-lirongqing@baidu.com>`（2026-09-09）
> **状态**：under_review，零回帖 · **日报**：`sched-20260909-014`

#### 背景与问题

`rq->max_idle_balance_cost` 是 newidle balance 的时间预算参考，由各调度域的 `sd->max_newidle_lb_cost` 汇总，仅在「本次遍历有域 decay」时更新。`e60b56e46b38` 把 `update_newidle_cost()` 改成有返回值后，循环里 `need_decay` 变成了**逐次赋值**——多层拓扑（SMT/MC/DIE/NUMA）下只要最后一个被遍历的域不需要 decay，前面任何域报告的 decay 都被抹掉，`rq->max_idle_balance_cost` 停止衰减。

#### 技术方案

```c
-		need_decay = update_newidle_cost(sd, 0, 0);
+		need_decay  |= update_newidle_cost(sd, 0, 0);
```

`Fixes: e60b56e46b38`。作者刻意不动循环内 `if (!continue_balancing) { if (need_decay) continue; break; }`——那里读的是当前域的瞬时值（赋值语句之后立即读取，累积值此时等价于当前域值），`|=` 不破坏它；但同一变量在循环外承担「是否有域 decay」，语义混合是脆弱点。

#### 效果

无数据：无 `max_idle_balance_cost` 的取值曲线、无受影响负载的迁移行为偏移。「恢复聚合语义」在代码层面可验证（日报作者核对主线 fair.c:13784 仍是赋值），行为差异大小完全未量化。补证方法：多层拓扑机器上用 `/proc/sched_debug` 观察该值是否长期贴着上界、打补丁后正常衰减。

#### 社区态度

零回帖。有分量的事实：`Fixes:` 指向的 `e60b56e46b38` 是 Peter 的提交，本次是把被引入的行为回归恢复回去；改动单行、方向保守（只会让 rq 级值更常更新）。卡点纯流程性——单行无数据的调度器修复易被淹没，通常需要有人追问「什么负载会看到影响」。commit message 结尾两段重复，值得顺手清理。

### 6.4 sched: Remove sched_class::balance()（Peter core-sched 系列之 7/7）

> **系列**：`[PATCH 0/7] sched: core-sched fixes and balancing`（7/7 为删除 balance()，净 -63 行；前身 6/24 的 0/2）· **作者**：Peter Zijlstra · **线程根**：`<20260828104018.996963405@infradead.org>`（2026-08-28）
> **状态**：under_review（likely，但必须等一次重投）· **日报**：`sched-20260902-015`

#### 背景与问题

`sched_class::balance()` 是 `__schedule()`/`pick_next_task()` 路径上按调度类反向遍历的均衡钩子。Peter 在 7/7 给的删除理由：自从 `50653216e4ff`（pick functions 可取 rf）之后，`balance()` 与 `pick_task()` 功能重叠——两者都会 drop `rq->lock` 去搬任务；更糟的是 core-sched 下 `prev_balance()` 只对**单个** rq 调用，造成 "missed balance opportunities"。真正的技术难点是**前向进展保证**：均衡从「一次性有界遍历」变成「pick 过程中随时可能 break lock 重试」后，重试次数失去上界（Peter 自己的 hack 是 retry count + 几个 cycle 后 `rf = NULL` 强制进展）。

#### 技术方案

删除 `prev_balance()`（core.c 23 行）、`struct sched_class` 的 `balance` 成员、`balance_idle()`、`balance_stop()`；`balance_rt()`/`balance_dl()` 返回值改 void 并前置进 pick：

```c
static struct task_struct *pick_task_rt(struct rq *rq, struct rq_flags *rf)
{
	rq_modified_begin(rq, &rt_sched_class);
	balance_rt(rq, rf);
	if (rq_modified_above(rq, &rt_sched_class))
		return RETRY_TASK;
```

其余 6 补丁：1/7 修 `pick_next_task()` 自递归（`core_task_seq` 对抗 sibling 竞争）、2/7 时间戳简化（`opt_update_rq_clock()`）、3/7 允许 core-sched newidle、4/7 RT 均衡早退、5/7 重排 `pick_task_fair()`/newidle、6/7 把 `sched_balance_newidle()` 的 unlock 下沉。

#### 效果

无性能数据（判据是正确性）：`queue.git/sched/hackery` 活过 Prateek 的 `coresched new -t pid -- perf bench sched messaging -p -l 100000 -g 8`（no-splat 判据）与 Aaron Lu 的 nop+bandwidth 脚本（带/不带 quota 均触发过原 panic）。结构性收益可静态核实：少一次类遍历、`struct sched_class` 少一个函数指针；Tejun 提到的收益（SCX 可去掉 ugly 的 lock-drop 追踪）要等落地后量化。

#### 社区态度

- **Tejun Heo（sched_ext 维护者）**：方向背书者（8/20 解释 SCX 只在确有任务要迁时才 drop lock，"if nothing has changed since the last time, there won't be a task to migrate and thus no lock drop"，并认可 `core_seq` 方案可让 SCX 去掉 lock-drop 追踪）；但 9/2 用两条意见把**本轮发布**判空——7/7："diffstat has fair.c ... but the patch body doesn't have any fair.c changes."；2/7："I don't think this is correct. A sibling rq wouldn't necessarily have RQCF_UPDATED cleared from whenever it scheduled / ticked the last time, so the following pick_task() can run with pretty stale rq clock."
- **Peter Zijlstra**：当晚认账——"Ah, indeed. We should clear clock_update_flags on unlock, rather than on lock. Thanks!"；且 8/22 就自陈 "the patches need to be redone, they're a bit of a mess"，1/7 正文仍留 `XXX words on forward progress go here` 占位。
- **Aaron Lu / K Prateek Nayak**：回归门槛提供方（崩溃用例 + no-splat 判据），非意见方。
- 评估：likely（删接口本身无反对者、依赖补丁同批在手），卡点是漏发 hunk + clock 判据 + 前向进展论证未写完；等重投。


### 6.5 sched/fair: Rework pick_task_fair() control flow（v1）

> **系列**：`[PATCH]`（单补丁，`kernel/sched/fair.c` 27+/24-）· **作者**：Yury Norov（NVIDIA）· **状态**：under_review，缓存内无人回帖 · **日报**：`sched-20260910-014`

#### 背景与问题

`pick_task_fair()` 的控制流由 `again:` / `idle:` 两个 goto 标签承担，且同一个 goto 标签承担两种回跳语义——可读性差。改的是调度器最热的挑选路径，属纯清理。

#### 技术方案

把「从 rq 上挑任务」的段落抽成静态 helper `pick_task_fair_rq()`，用 `while (cfs_rq->h_nr_queued)` / 外层 `do { … } while (new_tasks > 0)` 取代两个标签，最终 `return new_tasks ? RETRY_TASK : NULL;`。自陈 "No functional changes intended"；日报作者对照 diff 逐条核过控制流，三条返回路径与原实现等价，未发现语义漂移。

#### 效果

体积数据（作者自测，GCC 15.2.0）：`x86_64_defconfig` **省 96 字节**；`+CONFIG_SCHED_CORE` + `CONFIG_CFS_BANDWIDTH` **省 124 字节**。缺失：arm64 defconfig（含/不含这两项）与 clang 下的对比。无运行时性能主张。

#### 社区态度

缓存内**无人回帖**（Peter/Vincent 均未表态；评审空白，一周后可 ping 并附反汇编差异）。无反对、无支持。同日另一篇小清理：`sched: clarify ptrace's effect on task_struct->parent`（`sched-20260910-013`，纯注释 1+/1-，Oleg Nesterov 认为 v1 是 overdocumentation 并给出一行措辞，作者 13 分钟后发 v2 完全采用——该字段实际维护者亲授措辞，合入阻力很小）。

### 6.6 sched/eevdf: Fix rb augmented with multi fields + Fix augmented max_slice（均已合入 tip/sched/urgent）

> **系列**：两枚独立补丁——`Fix rb augmented with multi fields`（v2，`51b0e68cfa0a`）与 `Fix augmented max_slice`（v1，`9a8bc9bb4c3f`）· **作者**：Vincent Guittot · **状态**：merged_tip（Committer Peter Zijlstra，2026-09-10 10:22 +0200）· **日报**：`sched-20260910-004/005`

#### 背景与问题

EEVDF 用 augmented rbtree 缓存子树的 `min_vruntime`、`min_slice`、`max_slice` 三个增广字段以避免整树遍历。两处缺陷：rb_augmented 回调在插入/拷贝时**只拷贝 `min_vruntime`**，`min_slice/max_slice` 在 cgroup 层级下取到过期值；`max_slice` 的初始化路径也有错误值。

#### 技术方案

补齐 RBCOMPUTE 的三个字段计算与初始值设置（细节见两篇日报的 diff 分析）。v2 阶段 Kayra Cizmeci 补了一轮独立 review（给出 Reviewed-by）。

#### 效果

无 benchmark（正确性修复）；影响面是 cgroup 层级下 EEVDF 的 slice 计算。**回合提示**：自家分支若回合 `6e3c0a4e1ad1`（引入多字段增广的提交），必须同时带上这两枚配套修复。

#### 社区态度

- **Peter Zijlstra**：同日 10:22 两枚连收进 tip/sched/urgent——按「当前周期修复」处理。
- **Kayra Cizmeci**：独立 review 后给 Reviewed-by，并与 Peter 就 `min_vruntime_update()` 的冗余 bool 参数（RBCOMPUTE 两个函数签名不一致）交锋两轮，结论 "该删但没有干净的删法"，留作后续清理——**无人认领**。
- 无分歧、无 NAK。

### 6.7 sched/fair: reuse the ENQUEUE_DELAYED calculation in enqueue_task_fair()（撤回 1/2，续推 2/2）

> **系列**：`[PATCH 0/2]` · **作者**：Kayra Cizmeci · **状态**：1/2 放弃（作者自行），2/2（`reduce repeated work in enqueue path`）继续 · **日报**：`sched-20260908-011`

#### 背景与问题

`enqueue_task_fair()` 中已有 `flags & ENQUEUE_DELAYED` 的计算，紧接着又算一遍局部 `delayed`，1/2 想改名后两处共用。三天口味之争，无性能主张——作者自己承认 "I knew It was getting optimized by the compiler"。

#### 技术方案

争议 hunk（最终被放弃的形态）：

```c
-	if (!p->se.sched_delayed || (flags & ENQUEUE_DELAYED))
+	if (!p->se.sched_delayed || delayed)
```

#### 效果

无、也不该有——无性能主张，编译器都会优化掉。

#### 社区态度

- **K Prateek Nayak**："nit. This reads funny now - not delayed or delayed? Maybe wakeup_delayed but all of this should be optimized by compiler at the end and a big ENQUEUE_DELAYED is better for humans who are reading the code no?"
- **Kayra Cizmeci（作者，最终表态）**："I thought about this the meantime and I changed my mind. flags & ENQUEUE_DELAYED reads better and more clear than a bool. And I can't really see a big advantage of renaming it over this version."——顺带接受 Prateek 指出的标题口径问题（标题让人误以为有性能主张）。
- 评估：1/2 不进主线；2/2 为 enqueue 路径的重复工作消减，等评审。线程里还有个插曲：作者把 ping 误发到另一个补丁线程后九分钟内道歉并回到正确线程。


---

## 七、SMT 拓扑不对称：NVIDIA Olympus preferred siblings

`sched-20260909-007`（v5 全貌）、`sched-20260910-007/008`（后续）。

**动机**：Olympus 一个核两个对称 PE，单 PE 活跃时独占全部核资源；从双线程回单线程需兄弟核 WFI 后持续空闲一个 qualification interval（10K cycles）。`293f9611ae735` 挡住了 NOHZ 均衡唤醒忙 PE 的兄弟，但**普通任务放置**仍可能选中空闲核的任意 sibling，反复切换活跃 PE 让核滞留双线程模式。POWER7 同形（共享容量 SMT 层用 `SD_ASYM_PACKING` 排序硬件线程）。

**方案**：调度器侧在 `select_idle_sibling()` 加统一收口点 `select_idle_smt_cpu()`——原先五处直接 return 的出口全部 `goto select_smt_priority`，在已选核内改指向优先级最高的可用 sibling（要求共享最低层调度域 span——isolcpus 可能把同核 sibling 切进不同域；`SD_ASYM_CPUCAPACITY` 与 `SD_ASYM_PACKING` 两条序独立）。架构侧给 arm64 补带 `SD_ASYM_PACKING` 的 SMT 域（按 MIDR 匹配 Olympus）。偏好不是指认更快的 PE（稳态容量相等），而是**一致地选同一个 sibling**——PE1 更久空闲、更多核留在全资源单线程模式。

**性能数据**（aarch64 Vera，88 线程绑 NUMA0，performance governor，5 次重复）：

| 指标 | mainline → patched |
|---|---|
| OpenBLAS sgemm 吞吐 | 7.119±0.067 → 7.347±0.019 TFLOP/s（**+3.20%**，方差同步塌缩） |
| NVPL（内部）吞吐 | 9.647±0.173 → 10.297±0.018 TFLOP/s（**+6.73%**） |
| ST→SMT 模式切换完成数/次运行 | 10145.6±1835 → 1981.6±94（**-80.47%**） |
| ST→SMT 切换延迟周期 | 15.785M → 2.477M（-84.30%） |

Prateek 在 4 代 EPYC 与 128C Ampere ARM 上 Reviewed-by + Tested-by（快速路径正确内联、无性能影响）——这正是「2/2 对现有 `SD_ASYM_PACKING` 用户零回归」的证据。

**现状**：09-09 Peter tentatively picked up（前提 arm64 ack）→ 22 分钟后 Will Deacon NAK 架构侧（"Detecting topology based on MIDR is a non-starter, sorry"）→ 09-10 Peter 把系列从收取队列**撤下**（"Andrea is a wee bit fast with re-posting. I'll drop this"）。同日 static key 争议让步：v6 去掉新增 static key、改用既有 `sched_smt_active()`。**唯一硬阻塞是 arm64 侧的非 MIDR 优先级来源（固件/ACPI PPTT/CPPC 类描述），邮件里无人给出方案**；2/2 能否先行独立进 tip 是个值得有人明确提出的问题（Prateek 的双架构零影响数据就是现成论据）。

---

## 八、频率不变性与 cpufreq 交互

本月三条线撞在同一个语义点上：**压力/容量参考频率在 boost 开关下该怎么定义**。

### 8.1 cpufreq pressure 只在频率不变时施加

`sched-20260910-009`（演进见 09-02/03/07/08/09 各篇）。问题：`get_actual_cpu_capacity()` 无条件计入 `cpufreq_get_pressure()`，但非频率不变平台上参考回退到含 boost 的 `policy->cpuinfo.max_freq`，而 `policy->max` 来自不含 boost 的 `_PSS` 表——无真实限频时 capacity 凭空缩水（Hygon：`cpuinfo_max_freq` 3100000 vs 最高 `_PSS` 档 2700000，capacity 回不到 1024；AMD 5900X 同病）。方案之争收敛：放弃 sched 侧门控（掩盖症状），走 cpufreq 侧 `__resolve_freq()` 上界不越过 policy 实际可给频率 + policy 对象缓存。09-10 Vincent 给出硬约束——**压力参考频率必须在 boost 开/关下保持固定**；Jianyong 指出 intel_pstate 下 `cpuinfo.max_freq` 随 boost 变化（4GHz vs 3GHz），提出「最大可持续频率」方向，遗留问题是该频率从哪里取（intel_pstate/amd-pstate/acpi-cpufreq 各自的接口梳理无人认领）。共识已形成但**那枚 cpufreq 侧补丁至今没人发出**（Prateek 兜底时点为下周初）。

### 8.2 arm64 >4.19 GHz 的两个叠加 bug

`sched-20260907-003`。Snapdragon X2 Elite（Glymur）是第一颗 boost OPP（4723200 kHz）越过 `2^32 / SCHED_CAPACITY_SCALE = 4194304 kHz` 的 arm64 芯片，同时暴露：`arch_freq_get_on_cpu()` 里 u64 乘积截断成 `unsigned int` 回绕；`capacity_freq_ref` 只在 `CPUFREQ_CREATE_POLICY` 锁存一次（开机 boost 关着就永远停在持续频率）。后果是「内核认为 boost 中的 CPU 比实际更慢」：AMU scale 饱和 1024、utilization 被低估、`cpuinfo_avg_freq` 报荒谬值。钉频实测三行对照（`cpuinfo_avg_freq`：修复前 524283 → 只修溢出 4032000 → 两补丁 4718587；计时比 2.011/1.726 与频率比 1.171 自洽，证明硬件始终正确、错的只是内核的观察）。patch 2 抽 `topology_update_freq_ref()` 挂进 `policy_set_boost()`（v3 已至，cpufreq 与 arch_topology 两侧维护者仍无表态）。影响面只在 arm64（x86 的 aperfmperf 全程 u64 且参考天生含 boost）。

### 8.3 schedutil 的 boost 频率处理

`sched-20260908-006`。Ananthu C V（Qualcomm）v2 两补丁：boost 打开后 schedutil 打不到 boost 档（`capacity_freq_ref` 锚定过时）、关掉后上限回不来（`cpuinfo.max_freq` 只增不减，根因 `538b0188da46` 的护栏）。方案是跟踪表内最高非 boost 频率 `max_base_freq` 供 `policy_set_boost()` 下发 QoS。`time_in_state` 前后：boost 档从 0 驻留 → 569 个采样。两个风险：依赖**尚未进主线的 `cpuinfo.max_table_freq` 前置系列**；「一次播种含 boost 锚点」与 8.2 的「随 boost 状态刷新 ref」方向相反，两条线互不引用——先做对照的人对社区有直接价值。

---

## 九、sched_ext：修复与优化

- **v7.3-rc1 修复集已进主线**（`sched-20260901-012`）：Tejun pull 于 09-01 被 Linus 收下（merge `bf1079577a11`），12 commits——`scx_bpf_dsq_move()` 所有权检查竞态（假性 abort，检查移入队列锁内）、`ops.cgroup_set_bandwidth()` 允许 sleepable + capability marker、cgroup CPU 旋钮（`cpu.max`/`cpu.idle`）的 BPF 回调语义文档化（**同一旋钮在不同 BPF 调度器下语义可不同**——容器侧需知）。
- **built-in DSQ 的 per-CPU 内存优化**（`sched-20260901-013`，v2，high）：deferred reenqueue 只对 user DSQ 有意义，`scx_init_dsq()` 却给每个 DSQ 都 `alloc_percpu(struct scx_dsq_pcpu)`；built-in DSQ 个数本身随 `nr_cpu_ids` 增长，浪费是**平方级**。改名 `->pcpu_user` + 跳过分配，按评审意见去掉 `Fixes:`（纯内存优化，走 7.4 特性窗口）。预期落点 sched_ext/for-7.4；缺一组大规格机器上的 per-CPU 内存前后对比数字。
- **vtime 顺序约束文档化与强制**（v3，已合入）、**NMI 上下文拒绝锁类 kfunc**（v3，已合入）、**scx_qmap keep-last/两个放置循环修复**（已合入）。
- **自测套件扩充**（09-06~09-10 多篇，均已 Applied to sched_ext/for-7.4）：CPU 热插拔写失败处理、中断运行判失败、DSQ 重复创建与 ID 复用、`select_cpu_and` 掩码约束（v2；注意 Tejun 09-09 的两条意见回复的是 v1）、lib.bpf.mk 共享构建、去掉 `-rdynamic`/停止覆盖 `LDFLAGS`（`LDFLAGS =` 覆盖式赋值在整个 selftests 里唯一一例）、ext.h 相邻 ifdef 合并。
- PE 兼容线见 2.2——这是 sched_ext 本月最大的一块增量特性。

---

## 十、其他特性与性能相关

| 系列 | 状态 | 要点 |
|---|---|---|
| PREEMPT_DYNAMIC 简化（Mark Rutland，6 补丁） | **已合入** tip/sched/core（`d3d16750693b` 等）+ 回归修复 `ef9293b3b797` | `PREEMPT_DYNAMIC` 依赖 `ARCH_HAS_PREEMPT_LAZY`，dynamic 可选模型只剩 full/lazy；`preempt_modes[]` 与 enum 两份定义的结构性问题未根除（Mark 自陈需 rework） |
| `for_each_process_rculock` / `for_each_thread_rculock`（Ye Liu，8 片） | 高（1/8 已有 Hocko ack + 三份 R-b） | 全树机械替换，把 RCU 锁定并入遍历宏；等落实缩进的 v3 |
| 调度器废弃 static key API 清零（Hongyan Xia） | v2，无人回帖 | `__cfs_bandwidth_used` 迁 `DEFINE_STATIC_KEY_FALSE` 等，无功能变化 |
| sched_clock 绝对时间选项（Feng Tang） | **被拒**（Thomas Gleixner："stop pestering us with your firmware debug hacks"） | 想让 kernel/SCP/ATF 三方日志对齐时间轴；Marc Zyngier 指出所谓 absolute 并不绝对 |
| RT PUSH_IPI 回归（`dd29c017aed6`，pro-audio） | 停滞，已入 Leemhuis 回归清单 | 非 PREEMPT_RT 系统默认不发 RT push IPI，DAW 场景 PI-boost 饥饿到多秒级；无修复补丁 |
| cgroup 更新锁上移（Michal Blaszczyk v3） | high | 防止 CFS/SCX 在 cgroup 权重更新上的分歧；`sched-20260901-003` |
| `cpu.max`/`cpu.max.burst` 写序依赖移除（Zhe Liu v2） | **已合入** | 用户态可用性修复，与配额语义相关的少数已合入项之一 |
| tcp `cond_resched()` 在 BPF 上下文跳过（Jiayuan Chen v2） | 无人回帖 | `bpf_sock_destroy()` 触发 might_sleep；范围外补记 |
| sched/debug `scan_size_mb` 校验、`avg_idle`/`idle_stamp` 修复、isolcpus 越界读（折叠进 multiqueue v16）等 | 各篇 | 见附录总表 |

---

## 十一、横向观察

1. **PE 是 9 月的绝对主线**：138 篇日报中约 1/5 与 donor/curr 语义直接相关。核心机制（v31 前置）已进 tip，但 sleeping owner 本体、sched_ext 兼容、tick 归属三块大项都还在评审；「usage 跟执行者、bw 跟调度上下文」这类口径决策开始由维护者显式做出。对下游内核，PE 全面落地后所有 per-task 记账/限流消费者都要回答「跟哪个上下文」。

2. **云与虚拟化场景进入调度器核心**：steal_governor（IBM）、Olympus SMT（NVIDIA）都是 hypervisor 侧痛点向 guest 内核传导的解法；两者都在「机制进 sched/、策略留驱动或架构」的分层上花了大量评审精力。steal_governor 若按计划进 7.4，将是继 NUMA balancing 之后又一个大范围改变选核行为的特性。

3. **Peter 的收取行为模式清晰可辨**（09-10 单日三个样本）：小、正确、带 `Fixes:`、已被对口维护者 ack 的修复走 sched/urgent 快通道（wq_worker_tick）；评审细到给出具体代码建议说明方向被接受（PE+scx v13）；有争议或重发过快的系列直接 drop（Olympus v5）。投稿节奏本身已成为合入因素。

4. **性能数据的覆盖严重不均**：steal_governor、Olympus、Gregory Price、Hygon RFC 四个系列有完整数据表；而约半数特性（prctl 系列、fallback NUMA 感知、built-in DSQ 内存、LB_PROMOTE 的第三方复现）完全零数据。「补数据」几乎是每个系列当前最低成本、最高杠杆的参与方式。

5. **两个反复出现的接口设计争论**：(a) per-task/per-process 控制该走 prctl 还是 cgroup（CAS prctl vs NUMA prctl 两条线同时被问「用户态凭什么决策」）；(b) 平台差异该怎么进内核（MIDR 检测被 NAK、steal_governor 的架构 gate 被要求去掉）——前者关系到容器生态，后者关系到固件/ACPI 描述的边界。

6. **对 cpuset/cgroup 主线的直接影响**：`task_h_load()`/`h_curr` 重构决定层级负载估算口径；PE cgroup 记账与 donated/gifted 统计决定容器内 CPU 用量的可解释性；`cpu_preferred_mask` 与 cpuset 的重叠语义未收口；CFS/SCX cgroup 锁分歧修复已接近合入。这四条是 10 月值得持续跟踪、且最适合从 cgroup 视角回帖的线。

---

## 十二、附录：系列合入状态总表

按主题分组；「状态」取各系列最新版本的评估。合入分支/commit 仅在已确认时给出。

### 已合入（tip / sched_ext / 主线）

| 系列 | 合入位置 | 备注 |
|---|---|---|
| PE v31 前置（2/9~7/9） | tip/sched/core（09-02） | 8/9、9/9 未进 |
| sched_ext v7.3-rc1 修复集 | 主线（merge `bf1079577a11`，09-01） | 12 commits |
| PREEMPT_DYNAMIC 简化 + 字符串回归修复 | tip/sched/core | dynamic 模型只剩 full/lazy |
| EEVDF 增广树两修复（`51b0e68cfa0a`、`9a8bc9bb4c3f`） | tip/sched/urgent（09-10） | 回合 `6e3c0a4e1ad1` 需同带 |
| cache-aware misfit 修复（`f0d243a96f26`） | tip/sched/urgent | 对 AMD（ASYM_PACKING）无效 |
| NUMA fault locality 修复（`e81ee0630837`） | tip/sched/core（Cc stable） | 长期存在缺陷 |
| `cfs_rq->h_curr` 带宽路径、`update_curr_eevdf()` 根调用、`avg_idle`/`idle_stamp`、schedutil/preempt 字符串、qmap/vtime/NMI kfuncs、scx pull 批次、错字修复、`cpu.max.burst` 写序、cgroup idle 初始态等 | tip / 主线 / sched_ext 各分支 | 见对应日报 |
| selftests/sched_ext 系列（7 枚，含 `select_cpu_and`、`-rdynamic`/`LDFLAGS`、ext.h ifdef 等） | sched_ext/for-7.4（09-10） | 等 7.4 合入主线 |

### 评审中（高）

| 系列 | 版本 | 关键卡点 |
|---|---|---|
| wq_worker_tick 执行上下文 | v1 | Peter 已承诺 sched/urgent；零测试数据 |
| cgroup CPU 时间记执行上下文 | v2 | John 的 Tentatively 待转正；等 Peter 收取 |
| task_h_load() 重做 | v1+fixlet | fixlet 待折回重发；`se` clobber 残留 |
| 删除 sched_class::balance() | 0/7 | 7/7 漏发 hunk；前向进展论证未写完 |
| Lu Wang ALB migrate_llc 语义 | v4 | 基本干净 |
| cgroup 锁上移（CFS/SCX 分歧） | v3 | 接近合入 |
| for_each_*_rculock | v2 | 1/8 ack 齐备，等 v3 收尾 |
| built-in DSQ per-CPU 内存 | v2 | 预期 sched_ext/for-7.4 |

### 评审中（中）

| 系列 | 版本 | 关键卡点 |
|---|---|---|
| PE + sched_ext 兼容 | v13 | Peter 10 条意见待 v14 落实 |
| PE tick 拆分上下文 | v4→v5 | 回调设计待 Peter 点头；与 v13 冲突待协调 |
| steal_governor / preferred CPUs | v13 | 跨子系统 ack 空白；x86/s390 数据过期 |
| Hygon cache-aware 23 片 RFC | v2 | 17/23 方向分歧；v3 待发 |
| Olympus SMT preferred siblings | v5（被 drop） | arm64 非 MIDR 机制无人给出 |
| VMA 扫描/分层提升（Meta） | v1（v2 待发） | 并发扫描 + mode=3；无人类 review |
| arm64 >4.19GHz | v3 | cpufreq/arch_topology 两侧无表态 |
| schedutil boost 处理 | v2 | 依赖未合入的 `max_table_freq` |
| cpufreq pressure 不变语义 | 共识未成码 | cpufreq 侧补丁无人发出 |
| per-process NUMA balancing prctl | v1 | 零 review；`numa_group` 粒度错配 |
| fallback CPU NUMA 感知 | v1 | 零回帖、零数据 |
| isolcpus 越界读（superseded） | v1 | 折叠进 multiqueue v16 |

### 低 / 未知 / 停滞 / 被拒

| 系列 | 评估 | 说明 |
|---|---|---|
| LB_PROMOTE RFC | low | 05/10 被拒，改做 nr_idle_scan 方向 |
| AMD 大小核 CAS | stalled（unknown） | 等报告者复现 |
| sched_clock 绝对时间 | rejected | Thomas Gleixner 明确拒绝 |
| RT PUSH_IPI 回归 | stalled | 无修复补丁 |
| CAS per-task prctl RFC | unknown | 四问未答 |
| pick_task_fair() 清理、newidle decay、ENQUEUE_DELAYED 2/2、static key 清零、tcp cond_resched、其他小修复 | unknown/medium | 多为零回帖等待期 |

---

*生成时间：2026-09-11；覆盖窗口：2026-09-01 ~ 2026-09-10 的 LKML 调度子系统邮件缓存。*

