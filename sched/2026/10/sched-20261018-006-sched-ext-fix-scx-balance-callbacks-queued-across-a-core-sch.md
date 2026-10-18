# sched_ext: Fix scx balance callbacks queued across a core-sched pick

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261010-009：Andrea Righi 发往 `sched_ext/for-7.3-fixes` 的修复——dispatch 路径在 `pick_task_scx()` 尚未结束时（`RETRY_TASK` 或 dl_server 返回 NULL 后挑更低优先级类）就排好 `rq->scx.deferred_bal_cb`，期间 rq 锁可被再次释放，任何此窗口拿锁的 CPU 都撞 pending balance callback 触发 `rq_pin_lock()` WARNING；改为只在 pick 确定时才排队 callback，其余 defer 到 irq_work。带 `Fixes: 4c95380701f5`、`Cc: stable v6.19+`。
- sched-20261015-020：Tejun Heo review——要求更新 `dispatch_pick()` 上方过时注释，并建议 core pick（本地与远端）一律 punt 到 irq_work、把 callback 处理折进 `do_pick_task_scx()` 单一出口。
- sched-20261017-002：Andrea Righi 发 v2（`Don't leave balance callbacks queued across a pick retry`），落实 Tejun 两点——把 callback/后续工作折进 `do_pick_task_scx()` 单一出口 `out:`、更新注释；非终态 pick 改走 `schedule_deferred()` irq_work。此 v2 以 `ff0545e0c263` 落地。
- sched-20261018-006（今天）：Andrea Righi 发 `Fix scx balance callbacks queued across a core-sched pick`（2 补丁）修复 ff0545e0c263 遗留的 core-sched 缺口——core-sched 下返回任务的 pick 非终态，sibling dispatch 会掉共享 rq 锁而 callback 仍排队。1/2 已被 Tejun 应用到 `sched_ext/for-7.3-fixes`；2/2（kick_sync wait）Tejun 建议改到 for-7.4 按新思路做。

## 背景与问题

（承接 20261010-009 → 20261015-020 → 20261017-002）dispatch 路径可请求「下次从 balance callback 跑 deferred work」，而 `pick_task_scx()` 在 dispatch 后立即排 `deferred_bal_cb`；balance callback 必须在 rq 锁释放前被消费，但 `pick_task_scx()` 未必是 pick 终点：RETRY_TASK、dl_server 返回 NULL 后挑更低类，rq 锁可被再次释放——任何此窗口拿锁的 CPU 都在 `rq_pin_lock()` 触发 WARNING。v2（ff0545e0c263）已把非终态 pick 的 callback 转走 irq_work。

今天的新缺口：commit ff0545e0c263 只在 pick「最终确定」时才排队 balance callback，但 core scheduling 下「返回任务的 pick」并非终态——`pick_next_task()` 会继续挑 SMT sibling，其 dispatch 可能在 callback 仍排队时释放共享 rq 锁。任何在此窗口拿 rq 锁的 CPU 触发 `rq_pin_lock()` 的 WARNING。此点由 Tejun 与 sashiko 在 ff0545e0c263 的 review 中提出（[1][2]），本系列是后续修复。

## 技术方案

（承接 20261017-002）2 补丁（`kernel/sched/ext/`）：

- **1/2 `Don't queue balance callbacks from a core-sched pick`**：core scheduling 下，本地与 sibling 的 pick 一律把 pending work defer 到 irq_work，`SCX_RQ_BAL_CB_PENDING` 留给正在进行的 dispatch 自己设置。
- **2/2 `Don't leave the kick_sync wait queued across a core-sched pick`**：kick_sync wait 不能走 irq_work，改为在每次 core-wide 选择期间的 dispatch 前把它从本地 rq 取下，若 rq 锁未释放再排队回去。

测试：1/2 场景在 16-CPU SMT VM（8 核 2 线程）上复现，`scx_qmap -I` + 两个打不同 cookie 的 stress-ng sleeper 组（其一 SCHED_FIFO）+ 未打 tag CPU-bound 负载；用 debug 检查（非系列内）报告 rq 锁释放时 core 上仍排队的 callback。仅 ff0545e0c263 时 5/10 次触发、带 WARNING；加 1/2 后 0/16 次。2/2 场景用同 setup + 临时改 scx_qmap 以 `SCX_KICK_WAIT` 踢另一 core 的 CPU 复现。

## 版本演进与当前进展

*current_version: v3*（系列演进，前两版见 related 010-009/017-002，本次为针对 core-sched 的新 2 补丁版本）。

- v1（20261010-009）：只在 pick 确定时排队 callback，其余 defer irq_work。
- v2（20261017-002）：折进 `do_pick_task_scx()` 单一出口，落实 Tejun 重构意见，commit ff0545e0c263。
- v3（20261018-006，今天）：拆为 2 补丁，专门补 core-sched 下 sibling dispatch 掉锁的缺口（1/2）+ kick_sync wait（2/2）。

## Maintainer 意见与讨论焦点

Tejun Heo（sched_ext 维护者）：

- 对 1/2：「Applied to sched_ext/for-7.3-fixes。」——直接收取。
- 对 2/2：不认同「每次 dispatch 前取下、必要时再排」的做法，建议从 `set_next_task_scx()` 在 `SNT_PICK` 与 `SNT_REPICK` 时排队（`put_prev_set_next_task()` 在 pick 最终确定、core-wide 选择之后才调它，rq 锁不会带着 callback 被掉）；若 CPU 最终跑 idle 或更高类任务，则无 SCX 任务可等。`SNT_REPICK` 由 c72945693b90（"sched: Restart fair hrtick after same-task repicks"）引入，仅在 for-7.4，故**建议放到 for-7.4** 并带 stable 依赖标签（`Cc: stable # v7.0+: c72945693b90`）。另指出 for-7.4 的 proxy exec 会 zap balance callback、`find_proxy_task()` 失败后再次 pick，故 `kick_sync_pending` 应在 callback 运行时清除而非排队时。

## 合入评估

*likelihood=high*。1/2 已进 `sched_ext/for-7.3-fixes`（核心缺口已修复）；2/2 方向明确、只是实施位置与依赖（c72945693b90，7.4-only）需要作者改版后放 for-7.4。*blocking_issues*：2/2 需按 Tejun 建议从 `set_next_task_scx()` 排队并移到 for-7.4、附带 stable 依赖标签；`kick_sync_pending` 清除时机需调整。*next_action*：Andrea 重做 2/2 发到 for-7.4。

## 效果评估

作者给出复现数据：仅 ff0545e0c263 时 debug 检查在 10 次中 5 次触发（sibling 与本地 re-pick 皆 deferred_bal_cb）、并伴随 WARNING；加 1/2 后 16 次 0 触发。2/2 的 kick_sync 场景同样可复现。无性能数字，属正确性修复。

## 我可以参与的点

- `testing`：在 SMT + SCHED_CORE 机器上复现 core-sched 掉锁场景，验证 1/2（for-7.3-fixes）后 WARNING 不再触发，并对 2/2 的 kick_sync wait 路径做压力测试。
- `review`：2/2 改到 for-7.4 后，`set_next_task_scx()` 的 SNT_PICK/SNT_REPICK 排队与 proxy exec 下 `kick_sync_pending` 清除时机的交互值得复核。

## 参考链接

- 系列封面信：https://lore.kernel.org/all/20261017202025.3834954-1-arighi@nvidia.com/
- Tejun 应用 1/2：https://lore.kernel.org/all/6681132130d7fc4742396c4103ecbf97@kernel.org/
- Tejun 对 2/2 的反馈：https://lore.kernel.org/all/feaffac58ebad408885c8adae931ab27@kernel.org/

---
id: sched-20261018-006
date: 2026-10-18
subject: "sched_ext: Fix scx balance callbacks queued across a core-sched pick"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261017202025.3834954-1-arighi@nvidia.com>"
lore_url: "https://lore.kernel.org/all/20261017202025.3834954-1-arighi@nvidia.com/"
authors: ["Andrea Righi"]
maintainers_involved: ["Tejun Heo", "Andrea Righi"]
current_version: v3
patch_series:
  - version: v1
    msgid: "<20261010095208.276806-1-arighi@nvidia.com>"
    date: 2026-10-10
    summary: "只在 pick 确定时排队 balance callback，其余 defer irq_work（见 related 010-009）"
    review_outcome: "Tejun 要求更新注释并建议单一出口重构"
  - version: v2
    msgid: "<20261017152226.3690249-1-arighi@nvidia.com>"
    date: 2026-10-17
    summary: "折进 do_pick_task_scx() 单一出口，commit ff0545e0c263"
    review_outcome: "Tejun 与 sashiko 指出 core-sched sibling dispatch 仍会掉锁"
  - version: v3
    msgid: "<20261017202025.3834954-1-arighi@nvidia.com>"
    date: 2026-10-18
    summary: "2 补丁：core-sched 下 defer 到 irq_work（1/2，已应用 for-7.3-fixes）+ kick_sync wait 处理（2/2）"
    review_outcome: "1/2 应用；2/2 Tejun 建议改到 for-7.4 从 set_next_task_scx 排队"
upstream_commit: null
fixes_commit: "4c95380701f5"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["2/2 需按 Tejun 建议从 set_next_task_scx() 排队并移到 for-7.4", "kick_sync_pending 清除时机调整"]
  next_action: "Andrea 重做 2/2 发到 for-7.4，带 c72945693b90 stable 依赖标签"
contribution_opportunities:
  - kind: testing
    description: "SMT+SCHED_CORE 复现 core-sched 掉锁场景，验证 1/2 后 WARNING 不再触发、压测 kick_sync wait 路径"
  - kind: review
    description: "复核 2/2 改到 for-7.4 后 SNT_PICK/SNT_REPICK 排队与 proxy exec 下 kick_sync_pending 清除时机的交互"
generated_at: "2026-10-19T09:00:00"
source_email_count: 5
related_articles: ["sched-20261010-009", "sched-20261015-020", "sched-20261017-002"]
tags: [sched_ext, core_sched]
---