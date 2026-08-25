# tag: core_sched

共 16 篇

- [sched-20260823-011](../../2026/08/sched-20260823-011.md) `discussion/medium/under_review` — `sched: Flatten the pick` (v3 0/7) 后续讨论：Peter 让报告者确认 flat_cg 数是基于 flat-hierarchy fix (68e3748781) 还是 single-runqueue (85570f10a4c6)；并提醒 0day 曾 pin 该系列 patch 6/7 导致网络吞吐回退（ksoftirqd 更少运行）。报告者用 0day 复现脚本
- [sched-20260821-005](../../2026/08/sched-20260821-005-sched-remove-sched-class-balance.md) `discussion/under_review` — PeterZ 提议移除 `sched_class::balance()` 回调，这是 core_sched 重构的一部分。ByteDance 的 Xuewen Yan 提供了带宽测试脚本帮助验证，讨论仍在进行中。
- [sched-20260820-011](../../2026/08/sched-20260820-011.md) `discussion/medium/under_review` — `Remove sched_class::balance()` 系列与 core_sched pick_task 竞态在 08-20 继续交织：Peter 给出 core_seq 跟踪多 pick 的 sketch、Tejun 确认 SCX 下锁丢弃可前进、idle pick 传 NULL rf。forward-progress（活锁）保证仍未敲定，原始 cover 仍缺。属 08-19 011/
- [sched-20260819-011](../../2026/08/sched-20260819-011-sched-remove-sched-class-balance-core-sched-discussion.md) `feature/low/under_review` — `[PATCH 0/2] sched: Remove sched_class::balance()` 系列在 8/19 有多封回复，讨论焦点是与 core_sched 的交互正确性（在 pick 内做 balance 可能错移任务、core-sched 下 RETRY_TASK 语义存疑）。本次抓取未拿到原始 cover，方案全貌与作者待补；合入前景 medium，受同日 core_sched 竞
- [sched-20260819-002](../../2026/08/sched-20260819-002-core-sched-pick-task-race-null-deref-discussion.md) `discussion/high/under_review` — core_sched 在 `pick_task()` 释放 core-wide 锁后未触发 `RETRY_TASK` 而继续，造成 `rqX->core_pick` 被对端置 NULL 后空指针解引用。Peter 8/19 回复承认这是个漂亮竞态，但尚无好修复，且 sched_ext 参与让问题更复杂。属于 08-17→08-18 core_sched/proxy_exec 讨论线的延续。
- [sched-20260817-003](../../2026/08/sched-20260817-003-scheduler-updates-for-v7-3.md) `feature/high/merged_tip` — Ingo Molnar 发出 v7.3 合并窗口的 **Scheduler updates for v7.3** PR，规模巨大：flatten-the-pick cgroup 调度（扁平权重、运行在 per-CPU 队列而非 cgroup 层级）、EEVDF 核心拆解到单 run queue（CFS 去掉每 cgroup 内部队列）、short-slice 延迟优化、RT 抢占下限、scx 的 
- [sched-20260816-002](../../2026/08/sched-20260816-002-sched-ext-drop-the-dead-scx-deq-core-sched-exec-test-in-dequ.md) `fix/medium/merged_tip` — Tejun Heo 的 4-patch 系列修正在 `sched_ext` core-sched 任务排序的实现：修复 `ops.core_sched_before()` 被倒置调用的 bug（`Fixes: 7b0888b7cc19`，stable v6.12+）、用 `p->scx.runnable_at` 统一等待追踪、让跨两个调度器的任务对按最近公共祖先排序、删除 dequeue 路径里已
- [sched-20260815-012](../../2026/08/sched-20260815-012-sched-ext-set-up-ops-sub-ecaps-updated-dispatch-context-on-t.md) `feature/low/under_review` — Tejun Heo 让 `ops.sub_ecaps_updated()` 回调期间处于 dispatch 上下文，使 sub-scheduler 在能力和权重更新时能直接调用 `scx_bpf_dispatch*()` 等 dispatch 类 kfunc。已规划 follow-up 重构（删 rbtn / 层级权重）。v1 刚发出。
- [sched-20260810-006](../../2026/08/sched-20260810-006-sched-core-make-core-sched-flips-wait-for-in-flight-selectio.md) `fix/medium/under_review` — Tejun Heo 提交 6-patch core-sched 稳定性系列（core-sched flips 等待在途选择、pick_task() 释放 rq 锁的竞态处理）。Peter 在 PATCH 1/6、2/6 给出详细反馈。under_review。
- [sched-20260809-003](../../2026/08/sched-20260809-003-sched-fair-make-is-core-idle-check-all-cpus-in-a-core.md) `discussion/low/under_review` — Mete Durlu 在 2026-08-09 对前一天（08-08）提交的 `is_core_idle()` 修改 patch 发起讨论/追问，延续该系列。属 discussion，尚无定论。
- [sched-20260808-003-sched-ext-core-scheduling-fixes.md](../../2026/08/sched-20260808-003-sched-ext-core-scheduling-fixes.md) `in-review`
- [sched-20260807-001-proxy-execution-sleeping-owner-v31.md](../../2026/08/sched-20260807-001-proxy-execution-sleeping-owner-v31.md) `in-review`
- [sched-20260806-011](../../2026/08/sched-20260806-011-sched-wake_q-stable-6.12y-helper.md) `fix/low/under_review`
- [sched-20260806-010](../../2026/08/sched-20260806-010-sched-ext-proxy-execution-conservative-terminate.md) `feature/under_review`
- [sched-20260805-001](../../2026/08/sched-20260805-001-sched-ext-proxy-exec-reject-dsq-class-transition.md) `feature/under_review`
- [sched-20260730-001](../../2026/07/sched-20260730-001-sched-fix-sched-flag-keep-params-side-effects.md) `fix/medium/under_review` — Andrea Righi 修复了 `SCHED_FLAG_KEEP_PARAMS` 标志的两个副作用：即使设置了该标志，`__sched_setscheduler()` 仍会错误地触发 class 切换回调和 deadline 带宽记账。v1 刚发出，PeterZ 已 review，合入可能性高。
