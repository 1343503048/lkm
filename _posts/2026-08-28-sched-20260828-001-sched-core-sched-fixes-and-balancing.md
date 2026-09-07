---
id: sched-20260828-001
date: '2026-08-28'
subject: 'sched: core-sched fixes and balancing'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20260828101659.812011872@infradead.org>
lore_url: https://lore.kernel.org/all/20260828101659.812011872@infradead.org/
authors:
- Peter Zijlstra
maintainers_involved:
- Peter Zijlstra
- Tejun Heo
- K Prateek Nayak
- Aaron Tomlin
current_version: null
patch_series:
- version: v1
  msgid: <20260828101659.812011872@infradead.org>
  date: '2026-08-28'
  summary: 7 补丁：core_task_seq 重入检测、RQCF_UPDATED 直测、task_on_core() 防偷任务、rt/dl balance
    早退、重新启用 core-sched newidle 并 reflow pick_task_fair()、newidle 解锁下推、删除 sched_class::balance()
  review_outcome: 当日无回帖；作者自留 XXX：1/7 缺 forward progress 论证，6/7 缺性能数据
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 当日无任何 review/Acked-by/Reviewed-by
  - patch 1/7 缺 forward-progress 论证（作者标注 XXX）
  - patch 6/7 缺性能数据（作者标注 XXX needs numbers）
  - 与 Tejun Heo 面向 sched_ext 的 core-sched 修复功能重叠，先后顺序未谈定
  next_action: 等复现用例作者的 Tested-by 与 review；作者补 6/7 benchmark 与 1/7 推进性说明
contribution_opportunities:
- kind: testing
  description: 实测 patch 6/7 newidle 解锁下推的收益/持锁时长，把数字回帖（作者明确缺数据）
- kind: review
  description: 核对 task_on_core() 是否覆盖了所有以 task_on_cpu() 作不可搬判据的路径
- kind: extend
  description: 3/7 只防偷任务、未真正开启 core-sched newidle，可跟进后续使 5/7 与 3/7 语义对齐
generated_at: '2026-09-07T22:08:24'
source_email_count: 8
related_articles:
- sched-20260821-005
- sched-20260828-003
tags:
- core_sched
- load_balance
- rt
- deadline
- hyperthreading
title: 'sched: core-sched fixes and balancing'
layout: article
---

## TL;DR

Peter Zijlstra 8/28 发出 7 补丁系列，一次性处理 core scheduling 的三类问题：`pick_next_task()` 在 `pick_task()` 放掉 rq->lock 期间被兄弟 CPU 重入、core-wide 任务选择状态被踩踏（可致 NULL deref）；core-sched 下 newidle balance 被整条关掉造成的漏平衡；以及 `sched_class::balance()` 与 `pick_task()` 职责重叠。作者自述这是在 6/24 那版基础上"vastly expanded"，并称补丁已通过 Aaron Tomlin 和 K Prateek Nayak 的复现用例。当日无人回帖，且 patch 1/6 里仍留着 `XXX` 占位（缺 forward-progress 论证、缺性能数字），是作者自己标注未完成的投递。对启用了 `CONFIG_SCHED_CORE` 的内核，1/7 与 3/7 属于可关注的崩溃/正确性修复。

## 背景与问题

Cover letter 交代了来龙去脉：起因是 Peter Zijlstra 自己在 6/11 那次改动里把 core scheduling 弄坏了（他直接贴了自己当时的邮件链接），随后一路修补；因为假期搁置，期间 Tejun Heo 在 8/07 又为 sched_ext 提了一组 core-sched 修复——PZ 明说"if/when this lands, can be simplified again"，即两条路线在 `pick_next_task()`/balance 这块是重复劳动，他的版本落地后 Tejun 那组可以简化。

具体问题有四个：

1. **`pick_next_task()` 自重入**。core-sched 的 `pick_next_task()` 会对每个 SMT sibling 依次调 `pick_task()`，而 `sched_class::pick_task()`（尤其 fair 的 newidle balance）可能释放 core-wide 的 `rq->lock`。此时另一个 sibling 也能进到 `pick_next_task()`，两者互相踩踏 `rq_i->core_pick` 等 core-wide 选择状态，"possibly leading to NULL derefs"。
2. **时间更新靠猜**。原来用 `core_clock_updated` 布尔量去推断各 rq 的 clock 是否已更新。PZ 指出 `pick_task()` 若在内部做负载均衡，会 lock+unlock **调用者自己**的 rq，从而把 `RQCF_UPDATED` 标记丢掉，进而把 `set_next_task()` 绊倒。
3. **newidle 会偷走已选中的任务**。SMT0 已经挑中任务 A、SMT1 空闲走 newidle balance 时，A 可能被迁到 SMT1 并同时在 SMT1 被选中。该问题由 Bytedance 一侧在 6/03 报出。
4. **`sched_class::balance()` 与 `pick_task()` 功能重叠**。自 commit 50653216e4ff ("sched: Add support to pick functions to take rf") 之后两者都会放 rq->lock 并搬任务；而 core-sched 路径下 `prev_balance()` 只对单个 RQ 调用，直接产生"missed balance opportunities"。

## 技术方案

按补丁顺序：

- **1/7 `sched/core: Fix pick_next_task() self recursion`**：把 `rq->core->core_task_seq++` 改成先把值取进本地 `seq`，重入检测从"指望 `p == RETRY_TASK`"改为 `seq != rq->core->core_task_seq`，并把 `RETRY_TASK` 降级成 `WARN_ON_ONCE`。理由是 `RETRY_TASK` 只可能在锁间隙有更高优先级任务入队时出现，而那必然也会推进 `core_task_seq`，所以序号比对已完全覆盖它。同时把 `idle_sched_class.pick_task(rq_i, rf)` 的 rf 参数改为 NULL。
- **2/7 `sched/core: Simplify/fix time updates`**：引入 `opt_update_rq_clock()`，直接测 `RQCF_UPDATED` 而不是用 `core_clock_updated` 推断；给 sibling 循环里的每个 rq 使用各自的 `struct rq_flags rf_i = *rf;` 副本，避免互相污染；循环结束后显式 `rq->clock_update_flags |= RQCF_UPDATED;` 补回被 sibling 的 LOCK+UNLOCK 弄丢的标记。
- **3/7 `sched/core: Allow newidle for core-sched`**：新增 `task_on_core(rq, p)`（`!CONFIG_SCHED_CORE` 下恒为 false；开启时判 `rq->core_pick == p`），并把它加进 `affine_move_task()`、`can_migrate_task()`、`task_is_pushable()` 三处拒绝条件——即"已被 core 选中的任务"视同"正在 CPU 上"不可再搬。注意作者明确说了这一步的边界：**"Avoids the 'stealing', but doesn't yet enable newidle just yet."**
- **4/7 `sched/rt: Add early exit on balance path`**：在 `pull_rt_task()`/`pull_dl_task()` 的双锁之前加 `has_pushable_tasks()`/`has_pushable_dl_tasks()` 判断，没有可推任务就不去拿 `double_lock_balance`。`pull_dl_task()` 原来那句 `src_rq->dl.dl_nr_running <= 1` 的粗略判断被替换掉。
- **5/7 `sched/fair: Reflow pick_task_fair() / newidle`**：删掉 `pick_task_fair()` 里 `idle:` 出口那个 `if (sched_core_enabled(rq)) return NULL;`——也就是 core-sched 下彻底不做 newidle 的老限制；改走 `rq_modified_begin()/rq_modified_above()` + `RETRY_TASK` 协议，`sched_balance_newidle()` 返回值从 `int`（<0/=0/>0 三态）改为 `void`。作者在此标注 **"Note: this also re-enables balance for core-sched."**
- **6/7 `sched/fair: Push sched_balance_newidle() unlock down`**：把 `sched_balance_rq()` 里对 `this_rq` 的解锁时机从 newidle 的整个 domain 循环内部下推到真正需要 `busiest` 双锁之前，使更多情况下 this_rq 的锁根本不会被放掉（`lock_rq`/`unlock_rq` 两个局部量配对管理，出口统一补回锁）。这一 patch 的 commit message 只有 **"XXX needs numbers"**。
- **7/7 `sched: Remove sched_class::balance()`**：删掉 `prev_balance()` 与 `sched_class::balance()` 钩子，把 `balance_rt()`/`balance_dl()` 并入 `pick_task_rt()`/`pick_task_dl()`。作者论证了语义等价性：`prev_balance()` 从 `prev->class` 起遍历、`pick_task()` 从最高 class 起遍历，差别只是 RT 任务 prev 时会多访问一次 `balance_dl()`、fair 任务 prev 时多访问 `balance_{dl,rt}()`，而 `need_pull_{dl,rt}_task()` 会自行判断，因此无害。净减 88 行、增 25 行。

取舍上值得注意的是：核心机制选型是**用 `core_task_seq` 序号快照来检测重入**，而不是新增锁或把 `pick_task()` 改成不释放锁——保持"fair 类可以在 pick 路径放锁做 newidle balance"这一既有前提不动，代价是需要一个能覆盖所有破坏场景的序号，这也正是作者留 `XXX words on forward progress go here` 的地方（序号方案只保证"检出"，不保证"有限次重试后能推进"）。

## 版本演进与当前进展

- 前一版为 2026-06-24 的 `<20260624121327.190063948@infradead.org>`（cover letter 里以 [1] 引用），作者表示本版扩充过大，"so I didn't really bother keeping count"，因此 subject 不带 vN。
- 8/28 本版：7 补丁。cover 只给功能性证据——"these patches survive both Aaron's test case [4] and Prateek's [5]"，即两个已知 core-sched 复现场景不再触发；没有性能数据，也没有说明跑过哪些 workload。（同日 PZ 的另一个系列 task_h_load 才写了 "Lightly tested."，见站内 sched-20260828-003。）
- 外部并行工作：Tejun Heo 8/07 面向 sched_ext 的 core-sched 修复（`<20260807210221.232543-1-tj@kernel.org>`），PZ 认为本系列落地后可简化它。

## Maintainer 意见与讨论焦点

8/28 当日该系列没有任何回帖，无 Acked-by/Reviewed-by，也无 NAK。可从 cover letter 读出的两点社区关系：

- 与 Tejun Heo 的 sched_ext 侧修复存在**功能重叠**，PZ 的态度是"等我这套落地再简化他那套"，因此两组补丁的先后顺序会成为实际争议点。
- 测试责任被显式挂在社区侧：作者点名 Aaron Tomlin 与 K Prateek Nayak 的复现用例作为验证依据，说明这类 core-wide 状态机改动上游的接受方式是"复现用例过一遍"。

作者自己留下的两个未解决问题（不是社区意见，但同样是卡点）：patch 1/7 缺 forward-progress 论证，patch 6/7 缺性能数据。

## 合入评估

**likelihood: possible**。

- 有利：作者是 sched/core 的主要维护者，改的是他自己引入的回归；1/7 与 3/7 是明确的正确性修复且带 `WARN_ON_ONCE` 兜底；7/7 删掉一个 `sched_class` 钩子属于长期收敛方向，此前站内 sched-20260821-005 已记过同类讨论。
- 卡点：系列同时动了 `pick_next_task()`、`pick_task_fair()`、`sched_balance_rq()` 三处最热的路径，且 3/7 只解决"偷任务"、并未真正打开 core-sched 的 newidle，5/7 却已经把 core-sched 的 newidle 禁掉那段删了——两个补丁之间读起来存在"5/7 依赖 3/7 的 `task_on_core()` 才安全"的顺序耦合，容易被要求拆分或重排。6/7 的 unlock 下推在没有数字的情况下很难被接受（作者自己标了 `XXX needs numbers`）。
- `blocking_issues`：无人 review；patch 1/7 缺 forward-progress 说明；patch 6/7 缺 benchmark；与 Tejun Heo 的 sched_ext core-sched 修复存在重叠。
- `next_action`：等 Prateek/Aaron 等人跑完回归并回帖测试结果；作者补 6/7 的数据与 1/7 的推进性论证。

## 效果评估

本批邮件里**没有任何性能数字**。patch 6/7 的 commit message 正文就是 `XXX needs numbers`，即作者知道下推解锁会改善 newidle 路径的开销但尚未量化。功能性验证只有一句"these patches survive both Aaron's test case and Prateek's"，属于崩溃/错误行为不复现的判断，不构成性能结论。7/7 的净 -88/+25 行是代码量而非运行时收益。

## 我可以参与的点

- **实测 patch 6/7**：这是作者明确还缺的东西，也是最容易产生有效回帖的入口。`sched_balance_newidle()` 把 `this_rq` 的锁持有时间延长后，idle 退出路径的持锁区间变长，值得用 wakeup latency / schbench 一类指标 + `perf lock` 对比，数字直接回 6/7。
- **`task_on_core()` 的覆盖面 review**：3/7 只改了 `affine_move_task()`、`can_migrate_task()`、`task_is_pushable()` 三处。可以核对一下 6.6/OLK 里所有以 `task_on_rq_running`/`task_on_cpu` 作为"不可搬动"判据的位置（含 proxy execution 的 `task_current_donor()`）是否存在同类漏判，这类"同一不变量少补一处"的 review 上游很欢迎。
- **回合判断**：OLK-6.6 若启用 `CONFIG_SCHED_CORE`，1/7 的 `core_task_seq` 重入检测是可直接评估的崩溃修复方向；但 5/7、7/7 强依赖 7.x 的 `pick_task()`/`rq_modified_*()`/`RETRY_TASK` 协议（commit 50653216e4ff 之后），6.6 上 `pick_next_task_fair()` 形态差异太大，整套回合成本很高——建议只挑 1/7、3/7、4/7 的思想做本地化，不要照抄 diff。
- 系列刚发出、无人回帖，任何平台（尤其 ARM64 与虚拟化下的 core-sched）的 Tested-by 都是稀缺输入。

## 参考链接

- cover letter: https://lore.kernel.org/all/20260828101659.812011872@infradead.org/
- 1/7: https://lore.kernel.org/all/20260828104018.378378994@infradead.org/
- 2/7: https://lore.kernel.org/all/20260828104018.483560652@infradead.org/
- 3/7: https://lore.kernel.org/all/20260828104018.583549667@infradead.org/
- 4/7: https://lore.kernel.org/all/20260828104018.681741017@infradead.org/
- 5/7: https://lore.kernel.org/all/20260828104018.787096901@infradead.org/
- 6/7: https://lore.kernel.org/all/20260828104018.890793421@infradead.org/
- 7/7: https://lore.kernel.org/all/20260828104018.996963405@infradead.org/
- 前一版（2026-06-24，cover letter 中 [1] 引用）: https://lore.kernel.org/r/20260624121327.190063948@infradead.org
- Tejun Heo 的 sched_ext core-sched 修复（[3] 引用）: https://lore.kernel.org/r/20260807210221.232543-1-tj@kernel.org
- tip-bot commit: 未获取到
- stable backport: 未获取到
