# sched: core-sched fixes and balancing

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20260828-001：Peter Zijlstra 8/28 发出 7 补丁系列，一次性处理 core scheduling 的三类问题：`pick_next_task()` 在 `pick_task()` 放掉 rq->lock 期间被兄弟 CPU 重入、core-wide 任务选择状态被踩踏（可致 NULL deref）；core-sched 下 newidle balance 被整条关掉造成的漏平衡；以及 `sched_class::balance()` 与 `pick_task()` 职责重叠。当日无人回帖，patch 1/7 缺 forward-progress 论证、patch 6/7 缺性能数据。
- sched-20261107-001（今天）：**v2 发出，扩到 12 补丁**。核心变化是 rq_clock/rq_lock 语义整体重做——cover 明说「主差异是 rq_clock 的重做，因为 TJ（Tejun Heo）指出上一版把它彻底搞错了」。新增 `rq_drop_lock()`、把 `update_rq_clock()` 分解、引入 `RQCF_NOP_MASK` 让已 UPDATED 的 rq 跳过重复更新，用新语义取代 v1 里「靠 `core_clock_updated` 布尔量猜时钟是否更新」的绕路逻辑。补丁 1（`pick_next_task()` 自重入）也额外补了「锁间隙兄弟 CPU 建立 core-wide cookie 时重启」的 fast-path 检查。刚发出，当日无人回帖。

## 背景与问题

（承接 sched-20260828-001）Peter Zijlstra 自己在 6/11 那次改动里弄坏了 core scheduling，一路修补；期间 Tejun Heo 8/07 又为 sched_ext 提了一组 core-sched 修复，两条路线在 `pick_next_task()`/balance 这块重复劳动。原系列处理四个问题：① `pick_next_task()` 自重入（`sched_class::pick_task()` 可放 core-wide rq->lock，另一 sibling 趁机重入踩踏 `core_pick` 等状态，可能 NULL deref）；② 时间更新靠 `core_clock_updated` 布尔量推断，`pick_task()` 内部做负载均衡会 lock+unlock 调用者自己的 rq 从而丢掉 `RQCF_UPDATED`；③ newidle 会「偷走」SMT0 已选中的任务；④ `sched_class::balance()` 与 `pick_task()` 功能重叠。

今天 v2 的动机来自 TJ（Tejun Heo）对 v1 的 review：**v1 的 rq_clock 重做方向错了**。作者在 cover 里承认「新补丁有时显得漫无目的，因为最初修这个问题的想法没走通，但保留了部分铺垫工作，因为它（希望）让代码更简单」。代码在 `git://git.kernel.org/pub/scm/linux/kernel/git/peterz/queue.git sched/hackery` 分支。

## 技术方案

v2 共 12 补丁，与 v1 的 7 补丁对应关系：v1 的 patch 2（Simplify/fix time updates）被拆解扩充为 v2 的 patch 02–07（6 个补丁），其余补丁基本保留、序号顺延。按补丁顺序：

- **01/12 `Fix pick_next_task() self recursion`**（= v1 1/7）：把 `core_task_seq++` 改成先取进本地 `seq`，重入检测从「指望 `p == RETRY_TASK`」改为 `seq != rq->core->core_task_seq || WARN_ON_ONCE(p == RETRY_TASK)`。v2 额外新增：在无 cookie 的 no-sync fast path 里检查 `if (unlikely(rq->core->core_cookie)) goto restart;`——`pick_task()` 经 newidle balance 放锁期间，若兄弟 CPU 建立了 core-wide cookie，无 cookie 的 fast path 不再有效。
- **02/12 `Introduce rq_drop_lock()`**：`rq_unpin_lock()` 目前身兼「临时放锁」与「最终放锁」两职，与 `rq_pin_lock()`/`rq_repin_lock()` 都配对。为把临时 drop 与最终 drop 区分开，新增 `rq_drop_lock()` 用于 `rq_pin_lock() → rq_drop_lock() → rq_repin_lock() → rq_unpin_lock()` 里的临时 drop，替换 core.c/deadline.c/ext.c/fair.c/rt.c 中所有「临时放锁再 repin」的调用点。
- **03/12 `Decompose update_rq_clock()`**：把 `update_rq_clock()` 分解成「取时钟增量」与「更新 rq->clock」两部分，为后续 patch 04–07 的新语义打底。
- **04/12 `Make __update_rq_clock() skip updates on UPDATED`**：引入 `RQCF_NOP_MASK = (RQCF_ACT_SKIP | RQCF_UPDATED)`；已 up-to-date 的 rq 再调 `update_rq_clock()` 不再推进时钟（此前会推进并触发 WARN_DOUBLE_CLOCK 告警）。`WARN_ON_ONCE` 条件同步改为 `(rq->clock_update_flags & RQCF_NOP_MASK) == RQCF_UPDATED`。
- **05/12 `Abstract/fix rq_clock_start_loop_update()`**：抽离 rq_clock 循环更新的入口，修正其语义。
- **06/12 `New rq_{pin,drop,repin,unpin}_lock() semantics`**：落实 patch 02 铺垫的新锁语义，明确 pin/drop/repin/unpin 四种操作的配对关系。
- **07/12 `Simplify/fix time updates`**（= v1 2/7 的重做）：直接用 `__update_rq_clock()` 与 patch 04 的新语义，删掉 v1 里 `core_clock_updated` 布尔量加 `if (!(rq->clock_update_flags & RQCF_UPDATED)) update_rq_clock(rq)` 的绕路推断——在 `pick_next_task()` 的 no-sync 路径与 sibling 循环里统一改成无条件 `__update_rq_clock(rq)`/`__update_rq_clock(rq_i)`（由 patch 04 保证已更新者自动跳过），净 -19/+6 行。
- **08/12 `Allow newidle for core-sched`**（= v1 3/7）：新增 `task_on_core(rq, p)` 并把「已被 core 选中的任务」加入 `affine_move_task()`、`can_migrate_task()`、`task_is_pushable()` 三处拒绝条件，防 newidle「偷走」已选中任务；作者注明这步仍只防偷、未真正开启 newidle。
- **09/12 `sched/rt: Add early exit on balance path`**（= v1 4/7）：`pull_rt_task()`/`pull_dl_task()` 双锁前加 `has_pushable_tasks()`/`has_pushable_dl_tasks()` 早退判断。
- **10/12 `sched/fair: Reflow pick_task_fair() / newidle`**（= v1 5/7）：删掉 core-sched 下彻底不做 newidle 的老限制，改走 `RETRY_TASK` 协议重新启用 balance。
- **11/12 `sched/fair: Push sched_balance_newidle() unlock down`**（= v1 6/7）：把 `this_rq` 解锁时机下推到真正需要 `busiest` 双锁之前（v1 时此 patch commit message 只有「XXX needs numbers」）。
- **12/12 `sched: Remove sched_class::balance()`**（= v1 7/7）：删 `prev_balance()` 与 `sched_class::balance()`，把 `balance_rt()`/`balance_dl()` 并入 `pick_task_rt()`/`pick_task_dl()`。

## 版本演进与当前进展

*current_version: v2（2026-11-07 发出，msgid 20261107115913.261163891）*。

- v1（2026-08-28，7 补丁）：<20260828101659.812011872@infradead.org>。当日无回帖；作者自留 XXX（1/7 缺 forward-progress 论证，6/7 缺性能数据）。
- v2（2026-11-07，12 补丁）：主要响应 Tejun Heo 对 v1 rq_clock 重做的批评，把时间更新拆成 6 个补丁重做，并给 patch 1 补了 core-wide cookie 竞态检查。代码在 peterz/queue.git 的 sched/hackery 分支。当日无人回帖。

## Maintainer 意见与讨论焦点

今日 v2 刚发出，无任何回帖。关键上下文是 cover 中自述的驱动因素：**Tejun Heo 在 v1 review 中指出 rq_clock 重做「all wrong」**，v2 的 02–07 六补丁即为此重做。v1 时代的两点社区关系仍在：与 Tejun Heo 面向 sched_ext 的 core-sched 修复存在功能重叠（作者希望本系列落地后再简化他那套）；测试责任挂在 Aaron Tomlin 与 K Prateek Nayak 的复现用例上。

## 合入评估

*likelihood=medium*。作者是 sched/core 主要维护者、改的是自己引入的回归，1/12 与 8/12 是明确正确性修复且带 WARN 兜底；但系列同时动 `pick_next_task()`/`pick_task_fair()`/`sched_balance_rq()` 最热路径，v2 又大幅重做 rq_clock，需重新走一轮 review。*blocking_issues*：① v2 刚发出、无人 review；② rq_clock 重做（02–07）是全新代码，需 Tejun 复看确认这次方向对了；③ 11/12 的性能数据是否已补上未确认（v1 时为 XXX needs numbers）。*next_action*：等 Tejun Heo、Aaron Tomlin、K Prateek Nayak 跑回归并回帖；确认 11/12 是否已附 benchmark。

## 效果评估

今日邮件无性能数据。v1 阶段唯一功能性证据是「these patches survive both Aaron's test case and Prateek's」（崩溃/错误行为不复现，非性能结论）。v2 的 rq_clock 重做与 patch 1 的 cookie 竞态检查带来的运行时收益/开销未量化，作者亦未在本批邮件给出数字。

## 我可以参与的点

- **testing**：在启用 `CONFIG_SCHED_CORE` 的平台上（尤其 ARM64、虚拟化）跑 core-sched 复现用例与 schbench/wakeup-latency，回帖 Tested-by——这类 core-wide 状态机改动上游最需要实测背书。
- **review**：核对 v2 的 rq_clock 重做（patch 02–07）是否真正覆盖了 Tejun 指出的 v1 错误点，以及 `task_on_core()` 是否遗漏其它以 `task_on_cpu()` 作「不可搬动」判据的路径。
- **extend**：8/12 只防偷任务、未真正开启 core-sched newidle，可跟进后续使 10/12 与 8/12 语义对齐。

## 参考链接

- lore thread（v2 cover）: https://lore.kernel.org/all/20261107115913.261163891@infradead.org/
- 前一版（v1，2026-08-28）: https://lore.kernel.org/all/20260828101659.812011872@infradead.org/
- Tejun Heo 的 sched_ext core-sched 修复（v1 cover 引用）: https://lore.kernel.org/r/20260807210221.232543-1-tj@kernel.org
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20261107-001
date: '2026-11-07'
subject: "sched: core-sched fixes and balancing"
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: "<20261107115913.261163891@infradead.org>"
lore_url: "https://lore.kernel.org/all/20261107115913.261163891@infradead.org/"
authors: ["Peter Zijlstra"]
maintainers_involved: ["Tejun Heo"]
current_version: v2
patch_series:
  - version: v1
    msgid: "<20260828101659.812011872@infradead.org>"
    date: '2026-08-28'
    summary: "7 补丁：core_task_seq 重入检测、RQCF_UPDATED 直测、task_on_core() 防偷任务、rt/dl balance 早退、重新启用 core-sched newidle 并 reflow pick_task_fair()、newidle 解锁下推、删除 sched_class::balance()"
    review_outcome: "当日无回帖；Tejun Heo 后续 review 指出 rq_clock 重做方向错误"
  - version: v2
    msgid: "<20261107115913.261163891@infradead.org>"
    date: '2026-11-07'
    summary: "12 补丁：rq_clock/rq_lock 语义整体重做（rq_drop_lock、update_rq_clock 分解、RQCF_NOP_MASK 跳过已更新、pin/drop/repin/unpin 新语义），patch 1 补 core-wide cookie 竞态检查"
    review_outcome: "刚发出，无人回帖"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "v2 刚发出、无人 review"
    - "rq_clock 重做（patch 02-07）需 Tejun 复看确认方向"
    - "patch 11 性能数据是否已补上未确认"
  next_action: "等 Tejun Heo / Aaron Tomlin / K Prateek Nayak 跑回归并回帖；确认 patch 11 benchmark"
contribution_opportunities:
  - kind: testing
    description: "在启用 CONFIG_SCHED_CORE 的平台跑 core-sched 复现用例与 schbench/wakeup-latency，回帖 Tested-by"
  - kind: review
    description: "核对 v2 rq_clock 重做是否覆盖 Tejun 指出的 v1 错误点，及 task_on_core() 的覆盖面"
  - kind: extend
    description: "8/12 只防偷任务未真正开启 newidle，可跟进对齐 10/12 语义"
generated_at: "2026-11-08T09:00:00+08:00"
source_email_count: 13
related_articles: [sched-20260828-001]
tags: [core_sched, cfs, load_balance]
---
