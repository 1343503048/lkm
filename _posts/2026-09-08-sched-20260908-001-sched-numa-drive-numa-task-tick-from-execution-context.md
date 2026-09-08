---
id: sched-20260908-001
date: '2026-09-08'
subject: 'sched/numa: Drive NUMA task tick from execution context'
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: <20260904085244.799276-1-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20260908083545.GM4121339@noisy.programming.kicks-ass.net/
upstream_commit: null
fixes_commit: 7de9d4f94638
merged_branch: null
current_version: v3
generated_at: '2026-09-09T00:30:02'
authors:
- Hui Su
maintainers_involved:
- Peter Zijlstra
- Chen Yu
patch_series:
- version: v1
  msgid: <20260902163336.1552840-1-sh_def@163.com>
  date: '2026-09-02'
  summary: 首版把 task_tick_numa() 从 task_tick_fair() 移到 sched_tick()，使执行上下文为 fair 任务时
    NUMA tick 一定被驱动。
  review_outcome: Chen Yu、Tim Chen 参与，作者随后补入 cache tick 同题处理。
- version: v2
  msgid: <20260903041154.2479761-1-sh_def@163.com>
  date: '2026-09-03'
  summary: 同时搬移 NUMA 与 cache tick，改为按 rq->curr 是否为 fair 类判断，并补 sched_tick_remote()
    以保 full-dynticks 行为。
  review_outcome: 评审建议在 sched_tick 与 sched_tick_remote 之间抽出公共 helper；task_tick_core()
    的 slice 消耗问题被要求另开系列。
- version: v3
  msgid: <20260904085244.799276-1-sh_def@163.com>
  date: '2026-09-04'
  summary: 抽出 sched_tick_exec_ctx() 供 sched_tick() 与 sched_tick_remote() 共用，补文档说明
    misfit/overutilized/core-sched 仍属调度上下文。
  review_outcome: '09-08: Chen Yu 对 1/2、2/2 各给 Reviewed-by；Peter Zijlstra 明确否定该形态（"pretty
    terrible"）并贴出改 task_tick 原型的替代 PoC；作者当场指出 PoC 两处缺陷并承诺 v4。'
merge_assessment:
  likelihood: medium
  blocking_issues:
  - v3 被 Peter Zijlstra 否定，需按「task_tick(rq, queued) + 各类自查上下文」的骨架重做
  - Peter 的 PoC 自身有两处已知缺陷未修：curr/donor 调用顺序会破坏记账先于消费者、task_tick() helper 落进 CONFIG_SCHED_HRTICK
    块内导致 HRTICK=n 编译失败
  - queued 在非 fair donor 时的语义（Chen Yu 之问）需在 v4 中明确
  next_action: 作者发 v4 落实 donor-first 顺序与 helper 位置，并由 Peter/Chen Yu 复核类检查与 queued
    语义
contribution_opportunities:
- kind: testing
  description: 对 v4 跑 CONFIG_SCHED_HRTICK=n / NO_HZ_FULL=y / SCHED_PROXY_EXEC=y 的构建与启动矩阵，并用
    RT donor + fair 执行任务验证 sum_exec_runtime 记账顺序
- kind: review
  description: 梳理 tick 路径上依赖 rq_clock_task/sum_exec_runtime 的消费者，给出 curr_class 与 donor_class
    的完整调用顺序约束回帖
- kind: new_patch
  description: 独立成帖修复代理执行下 task_tick_core() 消耗已用 slice 的问题（v3 cover 明确将其与本系列分离，至今无人跟进）
source_email_count: 7
related_articles:
- sched-20260905-001
- sched-20260904-001
- sched-20260903-001
tags:
- numa_balancing
- cfs
- nohz
title: 'sched/numa: Drive NUMA task tick from execution context'
layout: article
---

## TL;DR

本文为增量更新，完整背景见 related_articles 中的 sched-20260905-001 / sched-20260904-001 / sched-20260903-001。09-08 这条线发生了方向性变化：Chen Yu 先给 v3 的 1/2 和 2/2 都打了 `Reviewed-by`，但 Peter Zijlstra 随即明确否定 v3 的做法（"So I'm not liking this, like at all. In fact, this is pretty terrible."），并直接贴出一版替代 PoC——把 `task_tick()` 的签名改成 `(rq, queued)`，让每个调度类自己在回调里取 `rq->curr` / `rq->donor` 并按类判断。作者 Hui Su 当天接受该方向并承诺发 v4。v3 已实质作废，v4 的形态基本被 Peter 锁定。

## 背景与问题

代理执行（proxy execution）把调度上下文 `rq->donor` 与执行上下文 `rq->curr` 拆开。`task_tick_numa()` / `task_tick_cache()` 操作的是**正在执行的那个任务**的状态（它的 mm、NUMA work、`sum_exec_runtime`），但这两个 hook 原本挂在 `task_tick_fair()` 里，而 `sched_tick()` 只按 donor 的调度类派发 `task_tick`。于是当一个 fair 任务替 RT/DL donor 执行时，这两个 hook 根本不会被调用。v1→v3 的修法是把它们挪出 `task_tick_fair()`，在 `sched_tick()` / `sched_tick_remote()` 里补一个 `sched_tick_exec_ctx(rq)`：

```c
static void sched_tick_exec_ctx(struct rq *rq)
{
	struct task_struct *curr = rq->curr;

	if (curr->sched_class != &fair_sched_class)
		return;

	if (static_branch_unlikely(&sched_numa_balancing))
		task_tick_numa(rq, curr);
}
```

补丁带 `Fixes: 7de9d4f94638 ("sched: Start blocked_on chain processing in find_proxy_task()")`，`Suggested-by` 来自 K Prateek Nayak 与 Tim Chen。

## 技术方案

本日出现的方案与 v3 是互斥的两条路线，Peter 认为 v3 的「在 core 里塞一个 exec-context 专用 hook」是错的，正确做法是让 tick 本身携带足够信息、由各类自己决定看哪个上下文：

- 新增 core 侧 helper，`sched_tick()` / `hrtick()` / `sched_tick_remote()` 三处调用点统一改成调它：

```c
static inline void task_tick(struct rq *rq, int queued)
{
	const struct sched_class *curr_class = rq->curr->sched_class,
				*donor_class = rq->donor->sched_class;

	curr_class->task_tick(rq, queued);
	if (sched_proxy_exec() && donor_class != curr_class)
		donor_class->task_tick(rq, queued);
}
```

- `struct sched_class::task_tick` 原型由 `(rq, p, queued)` 缩为 `(rq, queued)`，`p` 由各实现自己从 `rq->donor` 取，并加类检查早退：`task_tick_rt()` / `task_tick_dl()` / `task_tick_scx()` / `task_tick_idle()` 都变成「不是我的类就 return」。
- `task_tick_fair()` 变成双上下文判断：donor 是 fair 时跑 `entity_tick()`/`reweight_eevdf()`/misfit/overutilized/`task_tick_core()`；curr 是 fair 时才跑 `task_tick_numa()` 与 `task_tick_cache()`。这样 numa/cache 天然跟着执行上下文走，不再需要 core 里的额外 hook。
- 被放弃的备选：v3 的 `sched_tick_exec_ctx()`（Peter 原文态度是"pretty terrible"，且他倾向把逻辑放进各类而非在 core 加钩子）。Chen Yu 认同这个取舍理由——"since the logic is added per scheduling class, rather than inserting random hooks into the core scheduler"。

## 版本演进与当前进展

- 09-04 16:52 Hui Su 发出 v3（cover `<20260904085244.799276-1-sh_def@163.com>`，1/2 numa、2/2 cache）。
- 09-08 13:38 Chen Yu 在 v2 线程里补上他此前分析的具体理由：`("sched/eevdf: Move to a single runqueue")` 之后 `task_tick_fair()` 会重算 `h_load.weight`，cgroup 运行时改份额会让 `se->load.weight` 变化，因此「快照 vruntime 与用最新权重算出的 slice 相比」不可靠，并抛出 `if (entity_is_task(se)) ?` 的写法建议。
- 09-08 15:40 / 15:45 Chen Yu 分别对 v3 的 1/2、2/2 回 `Reviewed-by: Chen Yu <yu.c.chen@intel.com>`（2/2 一句 "Thanks for the fix"）。
- 09-08 16:35 Peter Zijlstra 否定 v3 并贴出替代 PoC（8 文件，`+62/-32`）。
- 09-08 18:02 Chen Yu 认可按类拆分的方向，同时追问：donor 不是 fair 任务时，hrtick 路径下是否仍需 `queued` 判断来跳过 numa/sched_cache。
- 09-08 18:44 Peter 承认"我这份 PoC 赶得很急，没管细节"（"I very much rushed this PoC patch without minding the details very much"），承诺修类检查，并贴出更新版（fair.c 由 `+50/-32` 收敛为 `+49/-32`，把 `if (queued) return;` 改写成 `if (!queued) { ... }`，numa/cache 分支显式加上 `curr->sched_class == &fair_sched_class && !queued`）；另提出一个悬而未决的问题：`task_tick()` 里到底该先跑 `curr_class` 还是先跑 `donor_class`（"I also wondered if we should have task_tick() do curr_class->task_tick() last, rather than first. But I couldn't immediately find a compelling argument either way around."）。
- 09-08 20:10 Hui Su 接受按类拆分，给出两条具体修正并承诺 v4。
- 本日无 tip-bot、无 stable 回帖。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（决定性反对）**：对 v3 的实现方式评价极负——"So I'm not liking this, like at all. In fact, this is pretty terrible."。他反对的是「在 core 里加 exec-context 专用 hook」这个形态，不是问题本身；给出的替代是收缩 `task_tick` 原型、让 donor/curr 两个类各自跑一次并在类内判断。
- **Chen Yu（意见分裂后转向）**：先给 v3 打了两个 `Reviewed-by`，Peter 反对后改口支持按类拆分，但留下一个未闭环的问题：`queued` 语义在非 fair donor 时是否还需要。Peter 的更新版实际上已按「numa/cache 只在 `curr` 是 fair 且 `!queued` 时执行」处理。
- **Hui Su 对 Peter PoC 的两处反驳（本日最实质的技术分歧，且 Peter 尚未回应）**：
  1. 调用顺序应当是 **donor 先、curr 后**，而非 Peter 写的 curr 先。理由是 RT/DL donor + FAIR 执行上下文时，donor 类的 `update_curr_*()` 会经 `update_curr_common()/update_se()` 把本 tick 的运行时计入 `rq->curr->se.sum_exec_runtime`；若 FAIR 回调先跑，`task_tick_numa()` 读到的是**本 tick 记账之前**的 `sum_exec_runtime`。这也与 v3 中 donor tick 先于 `sched_tick_exec_ctx()` 的顺序一致。
  2. `task_tick()` 被放在 `hrtick_clear()` 之后，落进了 `CONFIG_SCHED_HRTICK` 条件块内，而 `sched_tick()` 无条件调用它 → `CONFIG_SCHED_HRTICK=n` 会编译失败，helper 必须移到块外。
- 无正式 NAK 标签，但 Peter 的表态事实上使 v3 不能再被收取。

## 合入评估

`likelihood=medium`。问题本身（fair 任务替 RT/DL donor 执行时 NUMA/cache tick 不触发）有明确 `Fixes` 标签、有 Chen Yu 的两个 `Reviewed-by`，社区无人质疑动机；卡点完全在实现形态：v3 已被 Peter 否定，而他给出的 PoC 自己承认是赶出来的、且被作者当场指出两处缺陷（调用顺序 + HRTICK 条件块）。因此既不会按 v3 合入，也不会在 v4 之前进入 tip。`next_action`：Hui Su 按 Peter 的骨架出 v4（含 donor-first 顺序与 helper 位置修正），并由 Peter 或 Chen Yu 复核 `queued` 与类检查的最终语义。考虑到改动面从 core.c 扩散到 rt/dl/idle/ext/fair 五个类的 tick 回调，v4 更可能走常规窗口而非 `sched/urgent`。

## 效果评估

- v3 cover 自述的验证：`CONFIG_SCHED_PROXY_EXEC=y` 下四种 NUMA/cache 配置组合 + `W=1` 构建 + 完整 bzImage/modules 构建 + `CONFIG_NO_HZ_FULL=y` 启动；QEMU 代理互斥复现程序观察到「未打补丁时 FAIR 执行任务在代理期间不调用 `task_tick_numa()`/`task_tick_cache()`，打补丁后两个 hook 都能带 `rq->curr` 触发、`rq->donor` 仍是 RT 上下文，三次代理周期完成，远程 tick 路径在 CPU 1 上观察到调用 `sched_tick_exec_ctx()`，无告警」——属功能复现级别，**无性能数字**。
- 09-08 全天讨论没有任何新 benchmark 或性能数据；Peter 的 PoC 未附带任何测量，属"应该更干净"的主观判断（作者自陈 "rushed this PoC"）。
- Chen Yu 关于 `h_load.weight` 与 vruntime 快照不可靠的论述是逻辑推演，本日同样未见数据支撑。

## 我可以参与的点

- `testing`：v4 出来后，Peter 的 PoC 里 `CONFIG_SCHED_HRTICK=n` 的编译是作者自己指出的缺陷，任何人跑一遍 HRTICK 关、NO_HZ_FULL 开、PROXY_EXEC 开这个最小 config 矩阵即可直接给出有用回帖；再配一个 RT donor + fair 执行任务的复现脚本，验证 donor-first 顺序对 `sum_exec_runtime` 的可观测影响。
- `review`：Peter 留下的「curr 先还是 donor 先」他自称没找到决定性理由，Hui Su 给了一个（记账先于消费者）。可以把其它依赖 `rq_clock_task`/`sum_exec_runtime` 的 tick 消费者（`update_misfit_status`、`task_tick_core`、`calc_global_load_tick`）逐个核对顺序敏感性，给出一个完整的排序约束清单回帖。
- `new_patch`：v3 cover 明确把 `task_tick_core()` 在代理执行下消耗已用 slice 的问题「与本系列分开处理」，目前无人跟进——这是一个边界清楚、可独立成帖的后续修复。若要在自家分支（OLK-6.6）回合，注意 `Fixes` 需引用 OLK-6.6 自身的 commit 而不是上游 `7de9d4f94638`。

## 参考链接

- v3 1/2（本日主线程）: https://lore.kernel.org/all/20260904085244.799276-2-sh_def@163.com/
- Peter Zijlstra 的否定与替代 PoC: https://lore.kernel.org/all/20260908083545.GM4121339@noisy.programming.kicks-ass.net/
- Peter 更新版 PoC: https://lore.kernel.org/all/20260908104407.GD687043@noisy.programming.kicks-ass.net/
- Chen Yu 对 v3 1/2 的 Reviewed-by: https://lore.kernel.org/all/9cdc6386-5f46-408f-a515-d13984b55530@intel.com/
- Chen Yu 对 v3 2/2 的 Reviewed-by: https://lore.kernel.org/all/d3d06a7d-1353-4007-9b05-80a2177266d6@intel.com/
- Hui Su 承诺 v4: https://lore.kernel.org/all/20260908121021.53837-1-sh_def@163.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到
