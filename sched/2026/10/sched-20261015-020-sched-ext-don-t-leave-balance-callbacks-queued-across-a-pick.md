# sched_ext: Don't leave balance callbacks queued across a pick retry

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261010-009：Andrea Righi 发往 `sched_ext/for-7.3-fixes` 的新修复——dispatch 路径可能在 `pick_task_scx()` 尚未结束时（RETRY_TASK 或 dl_server 返回 NULL 后挑更低优先级类）就排好 `rq->scx.deferred_bal_cb`，期间 rq 锁可被再次释放，任何在此窗口拿锁的 CPU 都会撞上 pending balance callback 触发 `rq_pin_lock()` WARNING；改为只在 pick 确定时才排队 callback，其余 defer 到 irq_work。
- sched-20261015-020（今天）：Tejun Heo review——指出 `dispatch_pick()` 上方注释仍说「排队后续工作」需更新；并指出 core scheduling 下本地 pick 返回任务也非终态，sibling dispatch 可能持 callback 掉 core 锁触发同样 WARNING，建议统一 callback 排队逻辑。

## 背景与问题
（承接 20261010-009）dispatch 路径可请求「下次从 balance callback 跑 deferred work」，而 `pick_task_scx()` 在 dispatch 后立即排 `deferred_bal_cb`。balance callback 必须在 rq 锁释放前被消费，但 `pick_task_scx()` 未必是 pick 终点：RETRY_TASK、dl_server 返回 NULL 后挑更低类、以及 core-sched 下 sibling 的 dispatch 都可能让 callback 仍挂在队列。

## 技术方案
（承接 20261010-009）今日 Tejun 提出两点后续：
1. 更新 `dispatch_pick()` 上方注释（仍错误声称会排队后续工作）。
2. core-sched 场景并非本补丁引入的新问题、但同族：本地 pick 返回任务后，若任务带 cookie 或 core 需 sync，`pick_next_task()` 会去挑 sibling，sibling 的 dispatch 可能在本地 rq 的 callback 仍排队时掉 core 锁；sibling 的 RETRY 也在 callback 仍排队时重启选择。Tejun 建议（可作为单独补丁）：core pick（本地与远端）一律把 deferred work punt 到 irq_work；`kick_sync` 不能走 irq_work，但每次 core 选择期间的掉锁都来自 scx dispatch 且已通过 `lock_drop_seq` 强制重启，`dispatch_core_pick()` 可先 unlink 本 CPU 的 `kick_sync_bal_cb` 再置 `kick_sync_pending`。最后建议把 `pick_queue_balance_callbacks()` 折进 `do_pick_task_scx()` 用单一出口的 if/else，替代拆出的 `__do_pick_task_scx()`。

## 版本演进与当前进展
- v1（2026-10-10）：只在 pick 确定时排队 callback。
- 今天：Tejun 给出 review，要求注释更新 + 提议扩展处理 core-sched 场景。

## Maintainer 意见与讨论焦点
Tejun Heo（sched_ext 维护者）认可修法方向，但指出覆盖范围不足：`dispatch_pick()` 的过时注释、以及 core-sched sibling dispatch 的同族 WARNING。无 NAK，需要作者按意见更新并可能拆分补丁。

## 合入评估
*likelihood=medium*。维护者在推进但要求扩展范围（注释 + core-sched 场景），作者需再出一版或补一个后续补丁。*blocking_issues*：Tejun 要求更新注释并考虑 core-sched 场景的统一处理。*next_action*：Andrea 更新注释、并就 core-sched 场景给出单独补丁或解决方案。

## 效果评估
作者在 20261010-009 给出过复现（RT 任务为 prev 时触发 WARNING）；今日无新数据。

## 我可以参与的点
- *review*：审视 Tejun 提议的「core pick 一律 punt 到 irq_work + kick_sync unlink/重排队」方案与 `do_pick_task_scx()` 单出口重构是否覆盖全部掉锁路径。
- *testing*：在 core scheduling + 多 cookie 场景复现 sibling dispatch 掉锁触发的 WARNING，验证后续修复。

## 参考链接
- Tejun 的 review：https://lore.kernel.org/all/2fab939d8ebe56a64bbd0061715b227e@kernel.org/
- 原始补丁：https://lore.kernel.org/all/20261010095208.276806-1-arighi@nvidia.com/

---
id: sched-20261015-020
date: 2026-10-15
subject: "sched_ext: Don't leave balance callbacks queued across a pick retry"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261010095208.276806-1-arighi@nvidia.com>"
lore_url: "https://lore.kernel.org/all/20261010095208.276806-1-arighi@nvidia.com/"
authors: ["Andrea Righi"]
maintainers_involved: ["Tejun Heo"]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261010095208.276806-1-arighi@nvidia.com>"
    date: 2026-10-10
    summary: "只在 pick 确定时排队 balance callback，其余 defer 到 irq_work"
    review_outcome: "Tejun 要求更新注释并扩展处理 core-sched 场景"
upstream_commit: null
fixes_commit: "4c95380701f5"
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["Tejun 要求更新注释并统一处理 core-sched 场景"]
  next_action: "Andrea 更新注释、就 core-sched 场景给单独补丁或方案"
contribution_opportunities:
  - kind: review
    description: "审视 core pick punt 到 irq_work + kick_sync unlink 方案是否覆盖全部掉锁路径"
  - kind: testing
    description: "在 core scheduling + 多 cookie 场景复现 sibling dispatch 掉锁 WARNING"
generated_at: "2026-10-16T01:05:00"
source_email_count: 1
related_articles: ["sched-20261010-009"]
tags: [sched_ext]
---