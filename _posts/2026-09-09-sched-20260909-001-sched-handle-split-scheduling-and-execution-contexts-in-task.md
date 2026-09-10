---
id: sched-20260909-001
date: '2026-09-09'
subject: 'sched: Handle split scheduling and execution contexts in task ticks'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: 20260909092901.2989564-1-sh_def@163.com
lore_url: https://lore.kernel.org/all/20260909092901.2989564-1-sh_def@163.com/
upstream_commit: null
fixes_commit: 7de9d4f94638
merged_branch: null
current_version: v4
generated_at: '2026-09-10T00:30:00'
authors:
- Hui Su
maintainers_involved:
- Peter Zijlstra
- Tim Chen
patch_series:
- version: v2
  msgid: 20260903041154.2479761-1-sh_def@163.com
  date: '2026-09-03'
  summary: 只处理 NUMA/cache 两个 tick 消费者，用公共 helper 取执行上下文；core scheduling 的 donor slice
    记账问题尚未纳入。
  review_outcome: Tim Chen 于 09-09 00:01 确认应保持实时（task-clock）域比较，该意见最终成为 v4 的 5/5。
- version: v3
  msgid: 20260904085244.799276-1-sh_def@163.com
  date: '2026-09-04'
  summary: 把 NUMA 与 cache 两处收敛到一个 execution-context helper。
  review_outcome: Peter Zijlstra 否定这种局部 helper 修法，要求从 sched_class::task_tick() 接口本身解决；09-09
    16:37 又在 v3 1/2 上回了 Indeed/Whoopsie 承认缺陷成立。
- version: v4
  msgid: 20260909092901.2989564-1-sh_def@163.com
  date: '2026-09-09'
  summary: 5 补丁：去掉 task_tick() 的 task 参数并引入 donor 先/curr 后的公共分发器（1/5），NUMA 与 cache
    移到 FAIR 执行上下文（2/5、3/5），RT 调度类状态留 donor、看门狗跟 curr（4/5），新增 core-slicing 用 task-clock
    域度量 donor 已消耗 slice（5/5，Fixes aa4f74dfd42b）。
  review_outcome: Peter Zijlstra 同日两条意见：3/5 要求合并成单个 donor_class 与单个 curr_class 块；4/5
    明确 NAK（不接受在 __schedule() 中间散落 rt 代码）。1/5 与 2/5 暂无人表态。
merge_assessment:
  likelihood: low
  blocking_issues:
  - Peter Zijlstra 对 4/5 的实现方式明确 NAK：不接受把 RT 判断散落到 __schedule() 中，且他自陈还没想过这个问题该落在哪
  - Peter Zijlstra 要求 3/5 重排为单个 donor_class 块加单个 curr_class 块，当前 task_tick_fair()
    出现两个 donor 块
  - 1/5 改动 sched_class::task_tick() 签名，波及 deadline/ext/idle/fair/rt/stop_task 全部调度类，必须由
    Peter 收下才可能进 tip
  - sched_ext 分支目前是纯接口适配，作者以 CONFIG_SCHED_PROXY_EXEC 依赖 !SCHED_CLASS_EXT 说明其不可达；该前提会受
    proxy+sched_ext 兼容系列影响
  next_action: 作者需要对 4/5 给出不侵入 __schedule() 的替代落点（例如收进 task_tick_rt() 或新增类内 hook），并按
    Peter 的要求重排 3/5 的 task_tick_fair()，然后发 v5
contribution_opportunities:
- kind: discussion
  description: 4/5 的替代实现目前是空的：可提出把 RT 看门狗派发收进 task_tick_rt()（它已能同时看到 rq->donor 与 rq->curr），或为
    sched_class 增加一个「tick 后按执行上下文推进」的钩子，避免 core.c 里出现 rt 特判
- kind: review
  description: 直接给出把 3/5 中两个 donor 块合并为一个 donor_class 块与一个 curr_class 块的改写，这是 Peter
    明确要求且改动量最小的收尾
- kind: testing
  description: 在非作者的机器上重跑 5/5 的谓词等价性对比（HZ=100/250/1000 与 nice -10/0/+10）以扩大样本，并在 CONFIG_SCHED_CORE
    + proxy execution + force-idle 组合下实测 SMT 兄弟恢复是否因该修复而真正触发
- kind: new_patch
  description: 若自家分支同时启用 proxy execution 与 SCHED_CORE，5/5 描述的 force-idle 永不触发可独立复现并先行回合，Fixes
    需引用自家分支 commit 而非上游 aa4f74dfd42b
source_email_count: 13
related_articles:
- sched-20260908-001
- sched-20260905-001
- sched-20260904-001
- sched-20260903-001
- sched-20260903-005
tags:
- cfs
- numa_balancing
- rt
- core_sched
title: 'sched: Handle split scheduling and execution contexts in task ticks'
layout: article
---

## TL;DR

本文为增量更新，v1/v2/v3 的完整背景见 related_articles 中的 sched-20260908-001 / sched-20260905-001 / sched-20260904-001 / sched-20260903-001。09-09 这条线有两处实质变化：作者 Hui Su 在 17:28 按 Peter Zijlstra 的意见把 2 补丁的 v3 重构成 5 补丁的 v4——彻底去掉 `sched_class::task_tick()` 的 `task_struct *` 参数，改由一个公共 `task_tick()` 分发器先调 donor 类、再调执行类；同一天 19:03/19:04 Peter 对 v4 的 3/5 与 4/5 各给了一条**结构性反对**（"that is rather weird given how task_tick() works"、"we're not going to be sprinkling rt bits like this in the middle of __schedule()"）。也就是说接口方向被认可了，但 4/5 的落地方式需要重做。

## 背景与问题

proxy execution（`CONFIG_SCHED_PROXY_EXEC`）把「调度上下文」`rq->donor` 与「执行上下文」`rq->curr` 拆开：一个任务可以代替另一个任务上 CPU。内核里各处 `task_tick()` 的消费者并不都属于同一个上下文——调度类自身的状态（RT 的 `rt.time_slice`、RR 轮转）与 core scheduling 的 slice 判定属于 donor，而 NUMA 扫描、cache-aware 工作和 RT 的 RLIMIT_RTTIME 看门狗跟着真正在跑的那个任务。

v3 及以前只处理了 NUMA/cache 两个消费者，用一个「取执行上下文」的公共 helper 打补丁。Peter 在 09-08 的 review（`20260908104407.GD687043@noisy...`）里否掉了这种局部修法，要求从接口本身解决：既然 tick 可能属于两个类，就该让两个类都被调到，各自从 runqueue 里挑自己拥有的状态。v4 就是照这个方向重写的。

v4 还顺带收了两个 review 期间发现的独立缺陷：

- **RT 看门狗跟错了任务**（4/5，`Fixes: 7de9d4f94638`）。`update_curr_rt()` 把执行时间记到 `rq->curr`，`run_posix_cpu_timers()` 也在 tick 之后检查执行任务，但 `watchdog()` 之前是按 donor 调的——于是 RT donor 替别人挨了 SIGXCPU / RLIMIT_RTTIME 计时。
- **core scheduling 的 donor slice 永不消耗**（5/5，`Fixes: aa4f74dfd42b`）。`task_tick_core()` 用 `se->sum_exec_runtime - se->prev_sum_exec_runtime` 判断 slice 是否用完，这个比较对象是 donor（正确，slice 属于调度上下文），但 proxy 下 donor 的 `sum_exec_runtime` 根本不推进（时间记在 `rq->curr` 上），差值恒近 0，force-idle 的 SMT 兄弟永远等不到 reschedule 条件。

## 技术方案

**patch 1/5** 引入分发器并把 `task_tick()` 的签名从 `(struct rq *rq, struct task_struct *p, int queued)` 改成 `(struct rq *rq, int queued)`（`kernel/sched/sched.h:2682` 处主线仍是老签名）：

```c
static inline void task_tick(struct rq *rq, int queued)
{
	const struct sched_class *curr_class = rq->curr->sched_class;
	const struct sched_class *donor_class = rq->donor->sched_class;

	donor_class->task_tick(rq, queued);
	if (sched_proxy_exec() && curr_class != donor_class)
		curr_class->task_tick(rq, queued);
}
```

donor 先跑是为了保住现有的 runtime 记账顺序（执行上下文的消费者依赖 donor 的时间先更新完）；同类 proxy 只回调一次。涉及 8 个文件（core/deadline/ext/fair/idle/rt/sched.h/stop_task），`+65/-30`。**本 patch 刻意保留各类原有的 donor-gated 行为**，只换接口不改语义，后续 patch 才把归属逐项搬正。

**patch 2/5、3/5** 把 `task_tick_numa()` / `task_tick_cache()` 从 donor 侧移到 FAIR 执行上下文侧（`curr->sched_class == &fair_sched_class` 的块里），并把它们留在 fair.c 内部。

**patch 4/5** 拆分 RT：调度类状态与 RR slice 留在 `rq->donor`，`watchdog()` 改跑 `rq->curr`；对于「执行类是 RT 但 donor 属于别的类」的情况只跑 watchdog、不做 donor 记账。另外补了三处 `rt.timeout` 生命周期：proxy 下阻塞（mutex 阻塞的任务可留在 runqueue 上、绕过通常负责复位的 `ENQUEUE_WAKEUP`）要复位；非 RT 策略任务被选中且两个上下文都不在 RT 类时要清掉陈旧区间；RT 任务被 PI 提升进 DL 类期间要**保留**原策略的超时。

**patch 5/5** 换掉 core slice 的度量域：不再用 `sum_exec_runtime` 差值，改为在挑选 donor 时打一个 `se->core_sched_start` 时间戳（`struct sched_entity` 里新增，`#ifdef CONFIG_SCHED_CORE` 包裹），用 `se->exec_start` 推进的 task-clock 域来量 donor 已消耗的服务时间。作者特别指出这不只是绕开 `sum_exec_runtime` 不推进的问题——task-clock 域还顺带摆脱了权重依赖：`vruntime` 差值是跨不同权重累积的，而 slice 是按当前权重换算的，两者本来就不该直接比。只对 task 级 entity 打快照，因为 `task_tick_core()` 的消耗判定就作用在 donor task 上。

## 版本演进与当前进展

- v1/v2/v3（`sched: Fix execution-context tick handling under proxy execution` → `sched/numa|cache: Drive ... task tick from execution context`）：只处理 NUMA/cache，公共 helper 取执行上下文。
- v3 → v4（09-09 17:28，`<20260909092901.2989564-1-sh_def@163.com>`）：按 Peter 的意见整体换成「per-class 分发」；donor 类先于执行类；`task_tick()` 移出 `CONFIG_SCHED_HRTICK` 并保留 queued/hrtick 行为；`task_tick_numa()`/`task_tick_cache()` 回到 fair.c 并保持普通 FAIR tick 顺序；把此前的独立补丁 `sched/rt: Fix RT watchdog accounting for proxy execution` rebase 后折叠为 4/5；新增 5/5 的 core-slice 修复；reproducer 扩到 FAIR/RT/DL 跨类与同类分发、NUMA/cache 工作、RT 看门狗与 core slice 记账。
- 09-09 17:38 作者主动在该独立补丁线程回帖宣布 superseded（`<0c064defe3ae8a522150ead7ee1980dd.sh_def@163.com>`），并给出 v4 与 Peter review 的链接。
- 09-09 16:37 Peter 在 v3 1/2 上回了 "Indeed! Whoopsie ;-) Thanks!"（`<20260909083735.GK776954@noisy.programming.kicks-ass.net>`）——认可该缺陷确实存在。
- 09-09 00:01 Tim Chen 在 v2 线程确认「保持实时（task-clock）比较」的方向（`<e91848b651fbe163676813fffff76970d6895cf9.camel@linux.intel.com>`），作者 18:55 回复说该建议已作为 5/5 进 v4，用的是 `exec_start` + 挑选时的 `core_sched_start` 基线而不是 vruntime 快照。
- 09-09 18:42 作者回 Patch 1/5 下关于 sched_ext 的疑问：`CONFIG_SCHED_PROXY_EXEC` 依赖 `!SCHED_CLASS_EXT`，所以「SCX 与 proxy 同时开启」的当前不可达，`task_tick_scx()` 用 `rq->donor` 与 `update_curr_scx()` 用 `rq->curr` 指向同一任务；真正的 donor/执行归属要等两者兼容时再处理（这也是 09-08 `sched: Make proxy execution compatible with sched_ext` 那条线的前置问题）。
- v4 发出当天即得到 Peter 两条 review，1/5 与 2/5 尚无人表态。

## Maintainer 意见与讨论焦点

三条不同性质的意见，都需要处理：

1. **Peter Zijlstra（3/5，认可语义但否掉当前形状）**：他直接贴出 patch 应用后 `task_tick_fair()` 的中间形态，指出结果是「先一个 donor 块、又两个 curr 块、再一个 donor 块」——`for_each_sched_entity` 循环夹在 donor 判断里，而 `update_misfit_status()`/`check_update_overutilized_status()`/`task_tick_core()` 被拆到最后一个 donor 块。他的要求很明确："Please order things in a single donor_class and a single curr_class block. A second donor_class block makes no sense." 这是可读性/结构问题，不是方向分歧。
2. **Peter Zijlstra（4/5，明确的 NAK）**："It might come as no surprise that this isn't going to fly. I've not thought about the problem yet, but we're not going to be sprinkling rt bits like this in the middle of __schedule()." 注意他的措辞：问题本身（他刚在 v3 上说过 Indeed/Whoopsie）他没否认，否认的是把 RT 判断散落进 `__schedule()`。作者需要在 rt.c 内部或用别的钩子表达这个归属，而不是在 core 里插 rt 位。
3. **无人质疑 patch 1/5 的分发器本身**，但作者自己承认 SCX 分支目前是「形同虚设的适配」。

分歧点集中在 4/5。目前没有人提出替代实现，这实际上是一个开放请求。

## 合入评估

`likelihood=low`（按 v4 当前形态）。理由：4/5 被 Peter 明确判定 "isn't going to fly"，3/5 要求重排结构，这两条都在合入路径上且没有现成解法；1/5 的接口改动会波及全部 sched_class，属于必须先被 Peter 收下的那一类改动。

不过要区分两层：**问题成立度很高**（两个 `Fixes` 都有明确 commit 指向、Peter 亲自承认 v3 那个是 whoopsie、5/5 有可验证的谓词对比数据），**方案形态成熟度低**。历史上这类「接口重构 + 归属修正」系列平均要再迭代 2-3 版。卡点不是缺 ack，而是缺一个 Peter 认可的 RT 看门狗归属落点。

`next_action`：作者需要回 3/5 做单 donor 块 / 单 curr 块的重排，并对 4/5 提出不侵入 `__schedule()` 的替代写法（例如把 watchdog 派发收进 `task_tick_rt()` 自身，或用一个类内 hook）。

## 效果评估

v4 没有性能 benchmark，作者给的是**正确性验证数据**，且都是自陈、未见第三方复核：

- 逐 patch 构建 `kernel/sched/` 并构建最终 x86_64 bzImage；额外覆盖 `CONFIG_SCHED_HRTICK=n`、`CONFIG_POSIX_TIMERS=n`、`CONFIG_SCHED_CLASS_EXT=y`（proxy 关闭）、`CONFIG_SCHED_CORE=n`、`CONFIG_NUMA_BALANCING=n`、`CONFIG_SCHED_CACHE=n`、`CONFIG_FAIR_GROUP_SCHED=n`。
- 两节点、两 SMT 对的 QEMU 客户机里，FAIR/RT/DL 三种 donor 下验证了 NUMA 与 cache 的执行上下文 tick；也跑了 NO_HZ_FULL 的 remote tick。
- 6 种跨类/同类 split-context 组合（RT→FAIR、DL→FAIR、FAIR→FAIR、RT→RT、DL→RT、DL→RR）+ queued=1 的 hrtick。
- 看门狗归因：baseline 上 FIFO/RR donor 产生 donor 目标的 trace，打上补丁后变成执行 owner 目标；DL donor + RT owner 时 SIGXCPU 投给 owner，而 RR owner 的 `rt.time_slice` 不变。
- 复现了一个具体的错误复位：SCHED_FIFO owner 被 PI 提升进 DL 类时 `rt.timeout` 从 123 被清零；加策略保护后提升期间与 deboost 之后都保持 123，而 FAIR owner 离开 RT proxy 区间仍然从 123 复位到 0。
- 5/5 的谓词等价性：89,900 个 non-proxy 采样，跨 HZ=100/250/1000 与 nice -10/0/+10，新旧谓词**零失配**；proxy 下 donor 的 `sum_exec_runtime` 差值保持 0，而 task-clock 差值推进并触发到 force-idle reschedule 条件。

「零失配 + 触发条件恢复」是这轮里最有说服力的一组数字，因为它同时排除了误伤普通路径和修复无效两种可能。其余说法（比如「更 predictable」）没有数据支撑。

## 我可以参与的点

- `discussion`：4/5 缺一个替代实现，这是当前最有价值的切入点。可以把 RT 看门狗的派发收进 `task_tick_rt()`（它已经能同时看到 `rq->donor` 与 `rq->curr`），或者给 `sched_class` 加一个只负责「tick 之后按执行上下文推进的 per-class 状态」的钩子，避免 `__schedule()` 里出现 rt 位。Peter 说了 "I've not thought about the problem yet"，说明这个位置现在是空的。
- `review`：3/5 的重排是小而明确的工作，可以直接给出把两个 donor 块合并的版本，作者当天就能发 v5。
- `testing`：5/5 的谓词对比是纯用户空间可复现的——`HZ=100/250/1000` 重跑 non-proxy 对比即可扩展作者的样本量；另外 core scheduling + proxy execution + force-idle 的组合下实测 SMT 兄弟恢复时间，能验证「task-clock 度量恢复触发条件」是否真的转化为可观测行为。
- `new_patch`：如果自家分支已启用 proxy execution（`CONFIG_SCHED_PROXY_EXEC`）与 `CONFIG_SCHED_CORE`，5/5 描述的 force-idle 不触发是独立可复现的，可以先按自家代码结构回合——按 OLK 规范 `Fixes` 需指向自家分支的对应 commit，而不是上游 `aa4f74dfd42b`。
- `review`：作者自陈 patch 1/5 的 sched_ext 分支依赖「`CONFIG_SCHED_PROXY_EXEC` 依赖 `!SCHED_CLASS_EXT`」这一 Kconfig 事实。这个前提一旦因 09-08 那条 `sched: Make proxy execution compatible with sched_ext` 系列而改变，`task_tick_scx()` 的 donor 语义就需要立刻补上——值得在那条系列推进时提醒一句。

## 参考链接

- v4 cover letter: https://lore.kernel.org/all/20260909092901.2989564-1-sh_def@163.com/
- v4 1/5（分发器）: https://lore.kernel.org/all/20260909092901.2989564-2-sh_def@163.com/
- v4 3/5 + Peter 的结构意见: https://lore.kernel.org/all/20260909110348.GZ4120091@noisy.programming.kicks-ass.net/
- v4 4/5 + Peter 的 NAK: https://lore.kernel.org/all/20260909110438.GA4120091@noisy.programming.kicks-ass.net/
- v4 5/5（donor slice 记账）: https://lore.kernel.org/all/20260909092901.2989564-6-sh_def@163.com/
- Peter 在 v3 1/2 上的 "Indeed! Whoopsie": https://lore.kernel.org/all/20260909083735.GK776954@noisy.programming.kicks-ass.net/
- 作者宣告独立 RT watchdog 补丁 superseded: https://lore.kernel.org/all/0c064defe3ae8a522150ead7ee1980dd.sh_def@163.com/
- Tim Chen 关于保持 task-clock 比较的确认: https://lore.kernel.org/all/e91848b651fbe163676813fffff76970d6895cf9.camel@linux.intel.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到
