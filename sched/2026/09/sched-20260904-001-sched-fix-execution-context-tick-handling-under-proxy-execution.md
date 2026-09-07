# sched: Fix execution-context tick handling under proxy execution

## TL;DR

代理执行把调度上下文（`rq->donor`）和执行上下文（`rq->curr`）拆开后，`task_tick_numa()` / `task_tick_cache()` 仍挂在 `task_tick_fair()` 下，导致 fair 任务替 RT/deadline donor 执行时这两个 hook 完全不跑。Hui Su 的 v3 把这两处 tick 处理收进统一的 `sched_tick_exec_ctx()` helper，由 `sched_tick()` 和 `sched_tick_remote()` 共同调用，`Fixes:` 分别指向 `7de9d4f94638` 与 `df0d98475954`。Tim Chen 已在 v3 上给出 Reviewed-by，Chen Yu 表示准备跑一轮验证，系列已接近可合入。

## 背景与问题

代理执行（proxy execution）将 `rq->donor`（调度上下文）与 `rq->curr`（执行上下文）分离，`sched_tick()` 只对 donor 的调度类调用 `task_tick()`。当 donor 属于 RT/deadline 而执行者是 fair 任务时，`task_tick_fair()` 根本不会被调用：

- NUMA：`task_tick_numa()` 操作的是执行任务及其 `mm` 的状态，任务级执行时间也已改为按 `rq->curr` 记账，tick 驱动周期 NUMA 扫描的一方却仍是 donor，导致执行任务的 NUMA work 不被投递。
- cache：`update_se()` 已把 `account_mm_sched()` 记到执行任务，但 `task_tick_cache()` 不推进对应的 `mm` scan epoch；epoch 变陈旧后 `account_mm_sched()` 会把该 `mm` 的 preferred LLC 判为失效。

补丁 1/2 的 `Fixes:` 为 `7de9d4f94638`（"sched: Start blocked_on chain processing in find_proxy_task()"），2/2 为 `df0d98475954`（"sched/cache: Introduce infrastructure for cache-aware load balancing"），两位 Suggested-by 分别是 Tim Chen 与 K Prateek Nayak。

## 技术方案

- 新增 `static void sched_tick_exec_ctx(struct rq *rq)`（`kernel/sched/core.c`）：`rq->curr->sched_class != &fair_sched_class` 时直接返回，否则调用 `task_tick_numa()`（仍受 `sched_numa_balancing` static key 保护）与 `task_tick_cache()`。
- `task_tick_numa()` / `task_tick_cache()` 由 `static` 改为导出（`kernel/sched/sched.h` 增加声明），从 `task_tick_fair()` 中移出。
- `sched_tick()` 在 `donor->sched_class->task_tick()` 之后调用该 helper；`sched_tick_remote()` 保留自身基于 `curr` 的调度类分派不变，在其后追加同一 helper，以保持 full-dynticks 语义。
- `task_tick_fair()` 中剩余记账（`update_misfit_status()`、`check_update_overutilized_status()`、`task_tick_core()`）显式保留 `curr`（donor）参数，并加注释说明 misfit / overutilized / core scheduling 属于调度上下文。

整体改动规模很小：`core.c` +15、`fair.c` +9/-9、`sched.h` +2。

## 版本演进与当前进展

- v1：缓存中未保留其正文，只有 v2 封面转述的 changes 列表；v2 是 2 补丁系列（`20260903041154.2479761-1-sh_def@163.com`）。
- v2：把 NUMA/cache 的执行上下文 tick 处理从 `task_tick_fair()` 移到 `sched_tick()`，只在 `rq->curr` 是 fair 任务时调用；`sched_tick_remote()` 补上对应调用以保住 full-dynticks 行为。
- v3（本日，`20260904085244.799276-1-sh_def@163.com`）：按 Tim Chen 意见把 NUMA 与 cache 两处抽成公共 `sched_tick_exec_ctx()`，`sched_tick()` 与 `sched_tick_remote()` 共用，且不再改动 `sched_tick_remote()` 原有的基于 `curr` 的调度类分派；改写 NUMA 的动机说明（从「`sum_exec_runtime` 记到执行任务」上升为「`task_tick_numa()` 操作的是执行上下文状态及其 `mm`」）；补上 misfit/overutilized/core-sched 为何留在调度上下文的注释；把 review 中发现的 `task_tick_core()` 已消耗时间片核算问题明确剥离出本系列。
- 本日匹配到 9 封邮件（v3 封面 + 2 补丁 + 6 封讨论回复）。09-05 Tim Chen 在 v3 上给出 `Reviewed-by: Tim Chen <tim.c.chen@linux.intel.com>`，只留一条可选 nit。

## Maintainer 意见与讨论焦点

**Tim Chen（Intel，主要 reviewer）**
- 09-04 01:23（2/2）：建议把执行上下文相关处理收敛成一个 helper 并加注释，直接给出了 `sched_tick_exec_ctx()` 命名与注释草稿——这正是 v3 的主要变化。
- 09-04 05:30（1/2）：认为 `task_tick_core()` 必须留在 donor 侧「it is the scheduling context」，并顺带指出一个独立 bug：代理执行下 `se->sum_exec_runtime` 不推进，`__entity_slice_used()` 的 `sum_exec_runtime - prev_sum_exec_runtime` 恒接近 0，force-idle resched 可能永远不触发；附了一版基于 vruntime/deadline 的 compile-tested 原型，并说明「this is somewhat orthogonal ... It should be fixed separately」。
- 09-05：对 v3 给 Reviewed-by，仅剩「可以把 `sched_tick_exec_ctx()` 放进 `fair.c` 并导出，从而让两个函数保持 static」的 nit，「No big deal either way」。

**Chen Yu（Intel）**：09-04 23:52 对 v3 表态 "Both patches look good to me, let me launch a test and verify it works as expected and report back later."；09-05 在衍生讨论中提出单任务长跑场景下按片内比较会收紧 force-resched 触发条件的问题。

**Hui Su（作者）**：09-04 10:37 / 12:03 / 13:16 逐条接受上述意见；09-04 22:10 用实测数据反驳了自己先前的 deadline 原型——`update_deadline()` 会先推进 deadline，导致重建出的 `vused` 落回接近 0（HZ=1000 nice-0 时 10/10 tick 均 used=0），并提出改为 `set_next_entity()` 处取 vruntime 快照的方案；Tim Chen 09-05 04:15 承认「you have a good point」并按快照思路重发原型。该问题独立于本系列。

**分歧点**：本系列本身已无实质反对意见；争论集中在被剥离出去的 `__entity_slice_used()` 代理执行核算修复上（deadline 重建 vs pick 时快照 vs task-clock 基线），作者 09-05 进一步观察到 fair-group scheduling 下 reweight-after-pick 会使 vruntime 口径失真。

## 合入评估

likelihood: **likely**。

依据：两个补丁都带 `Fixes:` 标签，属代理执行框架的行为正确性修复；review 意见（收敛 helper、补注释、改写动机）已在 v3 全部落实；Tim Chen 09-05 给出 Reviewed-by，Chen Yu 亦已表态准备验证；改动面小（3 文件 26 行新增），与 cache/NUMA 主线（`sched/cache` 系列）无接口冲突。

卡点：仅剩 `sched_tick_exec_ctx()` 放 `core.c` 还是 `fair.c` 的位置 nit；以及是否有调度器维护者（Peter Zijlstra / Ingo Molnar）在本轮给出 Acked-by——缓存中未获取到。被剥离的 `__entity_slice_used()` 问题若在同一时间窗内重新提出，可能牵动 series 的排序，但不影响本系列两补丁本身。

## 效果评估

邮件中未提供性能/吞吐数据，只有功能性验证证据（v3 封面）：

- 在 `CONFIG_SCHED_PROXY_EXEC=y` 下覆盖 NUMA/cache 四种配置组合，做了 `W=1` 调度器对象构建、完整 `bzImage`/modules 构建，并单独构建第一个补丁；`CONFIG_NO_HZ_FULL=y` 内核构建并启动。
- QEMU + 临时 proxy-mutex reproducer（QEMU 11.1.0 暴露两个 L3 域）：未打补丁的内核在代理执行期间完全不调用 `task_tick_numa()` / `task_tick_cache()`；打上后两个 hook 反复以 `rq->curr` 被观察到，同时 `rq->donor` 保持为 RT 调度上下文；NUMA task work 已排队，cache work 已排队且 `mm` scan epoch 前进；三次代理过程完成，正常 fair 路径下 `rq->curr == rq->donor`；full-dynticks 远端 tick 路径在 CPU 1 上观察到调用 `sched_tick_exec_ctx()`；无 warning/BUG/oops/panic。作者说明插桩与 reproducer 不进入系列。

## 我可以参与的点

- **回合价值判定**：OLK-6.6 若无 `rq->donor`/`rq->curr` 拆分，本系列不适用；但只要回合过 proxy-execution 或 `sched/cache` 的 `mm` scan epoch 机制，就要检查 `task_tick_fair()` 是否也在被替执行的 fair 任务路径上跳过——这是同一类「tick hook 归属上下文」错误。可直接复核点：`update_se()` 里 `account_mm_sched()` 的入参、`account_mm_sched()` 判定 epoch 失效的分支、`task_tick_cache()` 推进 `mm` scan epoch 的位置。
- **可补的验证**：Chen Yu 已说要跑测试但缓存中未见结果。可以在 `CONFIG_SCHED_PROXY_EXEC=y` + `CONFIG_NUMA_BALANCING=y` 下用 RT donor（`SCHED_FIFO`）+ mutex 代理一个 CPU-bound fair 任务，插桩统计 `task_tick_numa()`/`task_tick_cache()` 的调用次数与 `rq->donor != rq->curr` 的时间占比，回帖给出量化数据。
- **可替的 nit**：Tim Chen 建议把 `sched_tick_exec_ctx()` 移入 `fair.c` 并保持两个函数 static。这是零风险改动，值得先做一版并附上 `W=1` 构建结果。
- **可接的衍生补丁**：`__entity_slice_used()` 在代理执行下的核算修复已被明确剥离，目前只有 Tim Chen 的原型和 Hui Su 的对比数据（含 fair-group reweight 后的口径分歧）。若愿意投入，pick 时快照（`core_slice_vruntime`）vs task-clock 基线两条路线的取舍、以及 `CONFIG_FAIR_GROUP_SCHED` 下 reweight 后是否需要重定基线，都是还没有结论的空位。

## 参考链接

- 邮件线程：
  - v3 cover letter: <https://lore.kernel.org/all/20260904085244.799276-1-sh_def@163.com/>
  - v3 1/2 `sched/numa: Drive NUMA task tick from execution context`: <https://lore.kernel.org/all/20260904085244.799276-2-sh_def@163.com/>
  - v3 2/2 `sched/cache: Drive cache task tick from execution context`: <https://lore.kernel.org/all/20260904085244.799276-3-sh_def@163.com/>
  - Tim Chen 对 v3 的 Reviewed-by: <https://lore.kernel.org/all/84f83c4dab930ff41cafbe614bbfa866003caa21.camel@linux.intel.com/>
  - v2 cover letter（上一版）: <https://lore.kernel.org/all/20260903041154.2479761-1-sh_def@163.com/>
- 相关文章/系列：
  - [[sched-20260903-001]] 代理执行下执行上下文 tick 处理（v2）。
- 相关代码/commit：
  - `kernel/sched/core.c` `sched_tick()` / `sched_tick_remote()` / `sched_tick_exec_ctx()`
  - `kernel/sched/fair.c` `task_tick_fair()` / `task_tick_numa()` / `task_tick_cache()`
  - `Fixes: 7de9d4f94638` ("sched: Start blocked_on chain processing in find_proxy_task()")
  - `Fixes: df0d98475954` ("sched/cache: Introduce infrastructure for cache-aware load balancing")

---
id: sched-20260904-001
date: '2026-09-04'
subject: 'sched: Fix execution-context tick handling under proxy execution'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: 20260904085244.799276-1-sh_def@163.com
lore_url: https://lore.kernel.org/all/20260904085244.799276-1-sh_def@163.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v3
generated_at: '2026-09-07'
authors:
- Hui Su
maintainers_involved:
- Tim Chen
- Chen Yu
patch_series:
- 'sched/numa: Drive NUMA task tick from execution context'
- 'sched/cache: Drive cache task tick from execution context'
merge_assessment:
  likelihood: likely
  blocking_issues:
  - sched_tick_exec_ctx() 放 core.c 还是 fair.c 的位置 nit（Tim Chen 09-05 提出，非阻塞）
  - 缓存中未见调度器维护者（Peter Zijlstra / Ingo Molnar）的 Acked-by 或排队动作
  next_action: 等 Chen Yu 的验证结果回帖；作者可顺手处理 sched_tick_exec_ctx() 位置 nit 并收集 Tim Chen 的 Reviewed-by 发下一版或直接等维护者排队。
contribution_opportunities:
- 在 CONFIG_SCHED_PROXY_EXEC=y + NUMA balancing 下量化 RT donor 代理执行时两个 tick hook 的缺失比例并回帖
- 把 sched_tick_exec_ctx() 移入 fair.c、恢复 task_tick_numa()/task_tick_cache() 为 static，并附 W=1 构建结果
- 接手已被剥离的 __entity_slice_used() 代理执行核算修复（pick 时 vruntime 快照 vs task-clock 基线，含 fair-group reweight 口径问题）
- 复核 account_mm_sched() 的 mm scan epoch 失效判定与 task_tick_cache() 的推进点是否同上下文
source_email_count: 9
related_articles:
- sched-20260903-001
tags:
- sched/core
- sched/fair
- sched/cache
- proxy_execution
---
