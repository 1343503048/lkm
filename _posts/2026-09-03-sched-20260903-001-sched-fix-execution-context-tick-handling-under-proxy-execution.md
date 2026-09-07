---
id: sched-20260903-001
date: '2026-09-03'
subject: 'sched: Fix execution-context tick handling under proxy execution'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260902163336.1552840-1-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20260902163336.1552840-1-sh_def@163.com/
upstream_commit: null
fixes_commit: 7de9d4f94638
merged_branch: null
current_version: v2
generated_at: '2026-09-07'
authors:
- Hui Su
maintainers_involved:
- Tim Chen
- K Prateek Nayak
- Chen Yu
patch_series:
- 'sched/numa: Drive NUMA task tick from execution context'
- 'sched/cache: Drive cache task tick from execution context'
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Chen Yu 关于 task_tick_core() 是否同样需要上移的追问无人回答，可能扩大系列范围
  - 本日无 Acked-by/Reviewed-by，整个 proxy-execution 修正簇的合入路由未定
  next_action: 等 v3 落地 helper 重构并回答 Chen Yu 的 sum_exec_runtime 提问
contribution_opportunities:
- 审 task_tick_core()/__entity_slice_used() 是否需改为 rq->curr 并回帖
- 验证 v3 helper 重构后 sched_tick() 与 sched_tick_remote() 调用顺序与 nohz_full 行为
- 补 DL donor 的代理执行复现用例
source_email_count: 10
related_articles:
- sched-20260902-012
tags:
- sched/core
- sched/fair
- sched/cache
- proxy_execution
title: 'sched: Fix execution-context tick handling under proxy execution'
layout: article
---

## TL;DR

代理执行把调度上下文（`rq->donor`）与执行上下文（`rq->curr`）拆开，而 NUMA 周期扫描与 cache 扫描仍挂在 `task_tick_fair()` 上：当 fair 任务替 RT/DL donor 执行时 `task_tick_fair()` 根本不会被调用，可 `account_mm_sched()` 仍在按 `rq->curr` 记执行时间，`mm->sc_stat.epoch` 因此停滞，超过 `llc_epoch_affinity_timeout` 后 preferred LLC 被直接清掉。Hui Su 的 v2（本日）把 `task_tick_numa()` / `task_tick_cache()` 上移到 `sched_tick()`，在 `rq->curr` 属于 fair 类时触发，并在 `sched_tick_remote()` 里补齐 nohz_full 路径。截至 09-03 为 v2，Intel/AMD 三位 reviewer 均已实质回帖，尚无人给 tag，作者已承诺 v3 做 helper 重构。

## 背景与问题

代理执行下 `sched_tick()` 用 `donor->sched_class->task_tick()` 派发调度类的 tick。`task_tick_numa()` 与 `task_tick_cache()` 原本都由 `task_tick_fair()` 调用，因此只有 donor 本身是 fair 任务时才会跑到。

Tim Chen 在 v1 的回帖里把漏洞说得更准确：donor 是 RT/DL 时 `task_tick_fair()` 完全不被调用，但 `update_curr_common() -> update_se()` 仍会走 `account_mm_sched()` 给 `rq->curr` 的 mm 记时间；只由 `task_tick_cache()` 推进的 `mm->sc_stat.epoch` 就此停滞，`account_mm_sched()` 在 `llc_epoch_affinity_timeout` 之后会把 `mm->sc_stat.cpu` 重置为 -1，preferred LLC 丢失。NUMA 侧同理：`task_tick_numa()` 负责按周期排队 `numa_work`，不被驱动则周期扫描错位。

## 技术方案

v2 的做法是把两个「执行上下文 tick」整体上移一层，而不是在 `task_tick_fair()` 里换成 `rq->curr`：

- `kernel/sched/core.c` `sched_tick()`：在 `donor->sched_class->task_tick(rq, donor, 0)` 之后加 `if (rq->curr->sched_class == &fair_sched_class)`，调用 `task_tick_numa(rq, rq->curr)`（受 `sched_numa_balancing` 静态分支保护）与 `task_tick_cache(rq, rq->curr)`。放在 donor 的 class tick 之后，是为了保持既有运行时间记账顺序。
- `sched_tick_remote()`：加同样的两段，否则 `nohz_full` CPU 会彻底失去这两个 tick。
- `task_tick_numa()` / `task_tick_cache()` 由 `static` 改为外部可见并在 `sched.h` 声明（含 `!CONFIG_NUMA_BALANCING` / `!CONFIG_SCHED_CACHE` 的空实现分支）。

改动量很小：`core.c +13`、`fair.c -9/+4`、`sched.h +2`。两个 patch 分别带 `Fixes: 7de9d4f94638`（"sched: Start blocked_on chain processing in find_proxy_task()"）与 `Fixes: df0d98475954`（"sched/cache: Introduce infrastructure for cache-aware load balancing"），并都加 `Suggested-by: Tim Chen`。

辅助说明：同日另有一封 `sched/core: Call wq_worker_tick() for the execution context` 是**独立补丁**，不属于本系列（它属于 09-02 的 [[sched-20260902-012]]）。

## 版本演进与当前进展

- v1（09-02，`[PATCH 1/2] ... Use execution context for ... task tick`）只在 `task_tick_fair()` 内改传 `rq->curr`，RT/DL donor 场景仍漏。
- 09-03 04:12 Tim Chen 回帖指出该空洞并直接给出「上移到 `sched_tick()` + 同步补 `sched_tick_remote()`」的方案；作者 10:53 回帖确认「the v1 cache change ... still misses the case where a fair execution task runs on behalf of an RT or deadline donor」。
- v2（09-03 12:11，封面 + numa/cache 两 patch）按此重做，标题从 "Use execution context" 改为 "Drive ... task tick from execution context"。
- 09-03 12:37 K Prateek Nayak 提重构建议，作者 12:51 接受并承诺下一版落地；09-03 20:41 Chen Yu 追问提交说明中的 `sum_exec_runtime` 论证。
- 本日为 v2；v3 尚未发出。姊妹补丁 wq_worker_tick() 本日已获 Tejun Heo `Acked-by`。

## Maintainer 意见与讨论焦点

- **Tim Chen（Intel）**：认可方向并给出 v2 的蓝图——"So maybe the check belongs one level up, in sched_tick(). There we can test whether rq->curr — the task actually running — is a fair task"；并强调 "sched_tick_remote() would then need the same two calls added. Without them, nohz_full CPUs would stop getting them at all."
- **K Prateek Nayak（AMD）**：nit，"Might be worthwhile to extract the above into a task_tick(rq, curr, donor) helper instead of duplicating in two places." 作者接受，理由是 helper 能让「调度上下文 vs 执行上下文」的切分显式化并保证 `sched_tick()` 与 `sched_tick_remote()` 不漂移。
- **Chen Yu（Intel）**：同意把 `task_tick_numa()` 上移一层，但质疑提交说明里对 `sum_exec_runtime` 的依赖论证；他给出两点：其一，`task_tick_numa()` 用 `curr->se.sum_exec_runtime` 判断是否到期触发 `task_numa_work()`，代理执行下该值只累积在 `rq->curr` 上，把「停摆」的 donor 值传进去不准确；其二，`task_tick_core()` 也通过 `__entity_slice_used()` 使用 `se->sum_exec_runtime - se->prev_sum_exec_runtime`，是否同样需要上移到 `sched_tick()` 并传 `rq->curr`。他还转述 Prateek 更早的结论：真正理由未必是 `sum_exec_runtime`，而是"with rq->curr->mm being the one that is being used on CPU"——cache 与 NUMA balancing 都符合这一条。**该提问在 09-03 尚无人回答。**
- 本日无 `Acked-by` / `Reviewed-by`；Peter Zijlstra、Ingo Molnar 未参与。

## 合入评估

likelihood: **possible**。

依据：两个 patch 都带指向已合入 tip 的 `Fixes:` 标签，属 proxy execution 落地后的上下文一致性修补簇（同日 005/008 与 09-02 的 wq_worker_tick 同源）；review 由 Intel/AMD 三方实质推动且已在一天内迭代出 v2，改动面小（19 增 9 删）、无 ABI 影响。

卡点：一是尚无任何 tag，且 Chen Yu 关于 `task_tick_core()` 是否同样需要上移的追问未回答——若答案是肯定的，本系列会从「两个 tick」扩成「sched_tick 执行上下文全面整改」，评审周期会拉长；二是提交说明的技术论证（`sum_exec_runtime` vs `rq->curr->mm`）需要与 Prateek/Chen Yu 的结论统一，否则 v3 仍会停在文字层面；三是姊妹补丁的路由问题（Tejun Heo 本日已 Ack 并问 "Peter, how do you want to route this patch? It can go through either sched or wq."）说明整个 proxy-execution 修正簇的分发路径还没定。

## 效果评估

邮件中未提供性能/收益数据，只有功能性验证：在双 NUMA 节点、双 LLC 的 QEMU 拓扑下，用 RT donor + fair mutex owner 构造代理执行，观察到 `task_tick_numa()` / `task_tick_cache()` 的入参 `p == rq->curr` 而 `rq->donor` 为另一 RT 任务，proxy 测试三轮无 warning/error；未打补丁的内存在同一场景下确认 cache tick 完全没有执行。另在 `nohz_full=1` 客户机上验证 `sched_tick_remote()` 约每秒进入一次 fair 执行上下文路径。NUMA/cache 特性组合与 `CONFIG_NO_HZ_FULL=y` 均通过编译，受影响对象通过 `W=1`。

## 我可以参与的点

1. 直接回答 Chen Yu 未解决的那个问题：审 `task_tick_core()` 的 `__entity_slice_used()`，判断它是否也应基于 `rq->curr` 上移到 `sched_tick()`，回帖即可推进系列。
2. 复核 v3 抽 helper 后 `sched_tick()` 与 `sched_tick_remote()` 的调用顺序未变（donor class tick 仍在 fair hooks 之前），避免记账顺序回归；可顺带覆盖 `CONFIG_SCHED_PROXY_EXEC=y` + `CONFIG_NO_HZ_FULL=y` + cache scheduling 的矩阵。
3. 有代理执行复现环境的话，补一个「donor 为 DL」的用例：本系列与 Tim Chen 的论证都只演示了 RT donor，DL donor 是同一条代码路径但未被显式覆盖。
4. 回合视角：OLK-6.6 无 `rq->donor` 拆分也无 `sched_tick_remote()` 的同形态实现，本系列不可直接 cherry-pick；可移植的是「tick 驱动的周期任务应归属于执行上下文」这一判据，回合时用它来检查 `task_tick_fair()` 的衍生改动。

## 参考链接

- 本系列邮件：
  - v2 封面：https://lore.kernel.org/all/20260903041154.2479761-1-sh_def@163.com/
  - v2 1/2：https://lore.kernel.org/all/20260903041154.2479761-2-sh_def@163.com/
  - v2 2/2：https://lore.kernel.org/all/20260903041154.2479761-3-sh_def@163.com/
  - v1 1/2：https://lore.kernel.org/all/20260902163336.1552840-1-sh_def@163.com/
- 关键回帖：
  - Tim Chen 促成 v2 的重做：https://lore.kernel.org/all/c5a2d651a5d647fb29f13fe483301b3b6e292b4d.camel@linux.intel.com/
  - K Prateek Nayak 的 helper 建议：https://lore.kernel.org/all/2bd1be66-25c6-455f-94d7-a44a147dba9a@amd.com/
  - Chen Yu 关于 sum_exec_runtime / task_tick_core 的追问：https://lore.kernel.org/all/4593a7a4-cde1-499c-bba8-2fbe24f35422@intel.com/
  - Prateek 更早关于「按 rq->curr->mm 判定」的结论：https://lore.kernel.org/all/78c81f74-7b27-4f28-9ca2-0d1e27ed9c56@amd.com/
- 相关文章/系列：
  - 独立补丁 wq_worker_tick 的执行上下文见 [[sched-20260902-012]]，本日已获 Tejun Heo Acked-by：https://lore.kernel.org/all/aphpMkGmuOrUByf3@slm.duckdns.org/
- 相关代码：
  - `kernel/sched/core.c` `sched_tick()` / `sched_tick_remote()`
  - `kernel/sched/fair.c` `task_tick_numa()` / `task_tick_cache()` / `account_mm_sched()`
