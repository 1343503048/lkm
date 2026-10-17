# sched_ext: Don't leave balance callbacks queued across a pick retry

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261010-009：Andrea Righi 发往 `sched_ext/for-7.3-fixes` 的修复——dispatch 路径在 `pick_task_scx()` 尚未结束时（`RETRY_TASK` 或 dl_server 返回 NULL 后挑更低优先级类）就排好 `rq->scx.deferred_bal_cb`，期间 rq 锁可被再次释放，任何此窗口拿锁的 CPU 都撞 pending callback 触发 `rq_pin_lock()` WARNING；改为只在 pick 确定时才排队 callback，其余 defer 到 irq_work。带 `Fixes: 4c95380701f5`、`Cc: stable v6.19+`。
- sched-20261015-020：Tejun Heo review——要求更新 `dispatch_pick()` 上方过时注释，并建议 core pick（本地与远端）一律 punt 到 irq_work、把 callback 处理折进 `do_pick_task_scx()` 单一出口。
- sched-20261017-002（今天）：Andrea Righi 发 v2，落实 Tejun 的两点——把 balance callback/后续工作处理折进 `do_pick_task_scx()` 单一出口 `out:`，并把 `dispatch_pick()` 的过时注释改掉；非终态 pick（RETRY_TASK 或 dl_server 返回 NULL）改走 `schedule_deferred()` irq_work、kick-sync 等待留到下次 pick。当日 v2 刚发，暂无回帖。

## 背景与问题
（承接 20261010-009 → 20261015-020）dispatch 路径可请求「下次从 balance callback 跑 deferred work」，而 `pick_task_scx()` 在 dispatch 后立即排 `deferred_bal_cb`；balance callback 必须在 rq 锁释放前被消费，但 `pick_task_scx()` 未必是 pick 终点：① 高优先级类任务在 dispatch 释锁期间被 enqueue 时返回 `RETRY_TASK`；② dl_server pick 返回 NULL 后挑更低类。两种情况 callback 仍挂队列、核心继续挑任务，rq 锁可被 `prev_balance()` 或另一次 dispatch 再次释放——任何此窗口拿到 rq 锁的 CPU 都会在 `rq_pin_lock()` 触发 WARNING。Tejun 在 20261015-020 进一步指出 core-sched 下 sibling dispatch 会掉 core 锁造成同族 WARNING，并建议用单一出口重构。

## 技术方案
（承接 20261010-009 → 20261015-020）v2 单补丁（`kernel/sched/ext/ext.c`，+45/−28），落实 Tejun 的 review 要求：
- 移除 `dispatch_pick()` 与 `dispatch_core_pick()` 内排队 callback 的逻辑，并把 `dispatch_pick()` 上方注释更新为「Run dispatch for a pick. The follow-up work is queued by do_pick_task_scx() once the pick is final」。
- 在 `do_pick_task_scx()` 增加统一出口 `out:`：当 `p == RETRY_TASK` 或 dl_server 返回 NULL 时 `goto out`，出口处仅在 pick 最终确定（`p != RETRY_TASK && (p || !force_scx)`）时才排 balance callback 与 kick-sync；否则若 `SCX_RQ_BAL_CB_PENDING` 置位，则清位并 `schedule_deferred(rq)` 转走 irq_work（不依赖当前 rq 锁段），kick-sync 等待留给下次 pick。
- 这是 v1「只在 pick 确定时排队」思路的收敛实现：不再拆 `__do_pick_task_scx()`，而是按 Tejun 建议用单一出口的 if/else 折叠。

## 版本演进与当前进展
- v1（2026-10-10，`<20261010095208.276806-1-arighi@nvidia.com>`）：只在 pick 确定时排队 callback。
- v2（2026-10-17，`<20261017152226.3690249-1-arighi@nvidia.com>`）：折进 `do_pick_task_scx()` 单出口；更新注释；非终态走 irq_work。当日刚发，暂无回帖。

## Maintainer 意见与讨论焦点
Tejun Heo（sched_ext 维护者，v1 的 reviewer）此前提出的两点渐次被满足：v2 已折进 `do_pick_task_scx()` 单出口、已更新 `dispatch_pick()` 注释。尚未明确回应的是 Tejun 20261015-020 提出的 core-sched 场景统一处理（core pick 一律 punt 到 irq_work；sibling dispatch 掉 core 锁触发同族 WARNING）——v2 在远端 CPU 分支（`cpu_of(rq) != smp_processor_id()` 且 `SCX_RQ_BAL_CB_PENDING`）保留了 `schedule_deferred(rq)` 处理，但本地/远端 core pick 的统一性是否完全覆盖还需 Tejun 复核。无 NAK。

## 合入评估
*likelihood=high*。作者即 sched_ext 维护者、直发目标 fixes 分支、带 `Fixes:`/`Cc: stable v6.19+`、有真实 WARNING 栈与复现命令，v2 已按 v1 review 收敛。*blocking_issues*：Tejun 对 v2 的收取尚未发生；core-sched 边界是否需单独补丁待确认。*next_action*：等 Tejun applied v2 到 sched_ext/for-7.3-fixes，并确认 core-sched 场景是否需跟进补丁。

## 效果评估
作者在 v1 给过复现（16 CPU 虚拟机 `scx_qmap -I` + 频繁睡眠 SCHED_FIFO 负载，触发 `WARNING: kernel/sched/sched.h:1919 at rq_lock`，CPU#10 stress-ng-sleep）；今日 v2 无新增 benchmark，主要是结构重构与注释更新。

## 我可以参与的点
- *review*：复核 v2 单一出口中 RETRY_TASK / dl_server NULL 两条路径的 `schedule_deferred()` 覆盖，以及 Tejun 提出的 core-sched（sibling dispatch 掉 core 锁）同族 WARNING 是否仍需单独补丁。
- *testing*：用 v1 给出的 `vng + scx_qmap -I + stress-ng --sched fifo` 命令验证 v2 后不再 WARN。

## 参考链接
- v2 patch：https://lore.kernel.org/all/20261017152226.3690249-1-arighi@nvidia.com/
- v1 patch：https://lore.kernel.org/all/20261010095208.276806-1-arighi@nvidia.com/
- Tejun 的 v1 review：https://lore.kernel.org/all/2fab939d8ebe56a64bbd0061715b227e@kernel.org/

---
id: sched-20261017-002
subject: "sched_ext: Don't leave balance callbacks queued across a pick retry"
date: 2026-10-17
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261017152226.3690249-1-arighi@nvidia.com>"
lore_url: "https://lore.kernel.org/all/20261017152226.3690249-1-arighi@nvidia.com/"
authors: ["Andrea Righi"]
maintainers_involved: ["Tejun Heo"]
current_version: v2
patch_series:
  - version: v1
    msgid: "<20261010095208.276806-1-arighi@nvidia.com>"
    date: 2026-10-10
    summary: "只在 pick 确定时排队 balance callback，其余 defer 到 irq_work"
    review_outcome: "Tejun 要求更新注释、折进 do_pick_task_scx() 单出口、统一 core-sched 场景"
  - version: v2
    msgid: "<20261017152226.3690249-1-arighi@nvidia.com>"
    date: 2026-10-17
    summary: "折进 do_pick_task_scx() 单出口，非终态 pick 走 irq_work，更新 dispatch_pick() 注释"
    review_outcome: "当日刚发，暂无回帖"
upstream_commit: null
fixes_commit: 4c95380701f5
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["Tejun 对 v2 的收取尚未发生；core-sched 边界是否需单独补丁待确认"]
  next_action: "等 Tejun applied v2 到 sched_ext/for-7.3-fixes，确认 core-sched 场景是否需跟进"
contribution_opportunities:
  - kind: review
    description: "复核 v2 单出口 RETRY_TASK/dl_server NULL 路径的 irq_work 覆盖及 core-sched 同族 WARNING 是否仍需补丁"
  - kind: testing
    description: "用 vng + scx_qmap -I + stress-ng --sched fifo 验证 v2 后不再 WARN"
generated_at: "2026-10-18T01:12:00"
source_email_count: 1
related_articles: ["sched-20261010-009", "sched-20261015-020"]
tags: [sched_ext]
---