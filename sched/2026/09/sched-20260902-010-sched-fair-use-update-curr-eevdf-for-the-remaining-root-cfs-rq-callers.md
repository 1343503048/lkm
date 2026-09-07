# sched/fair: Use update_curr_eevdf() for the remaining root cfs_rq callers

## TL;DR

Zhan Xusheng（Xiaomi）的一行级修复已被 Peter Zijlstra 于 9/2 09:17(+0200) 合入 **tip/sched/urgent**
（Commit-ID `1719d035a6fa90b7467b6daf45a573f5180013b2`）。内容：`pick_task_fair()` 与 `yield_task_fair()` 里的
`update_curr(cfs_rq)` 改成 `update_curr_eevdf(cfs_rq)`。真实缺陷是 **cgroup 场景下这两处更新是 no-op**：作者实测
root cfs_rq 上 `->h_curr` 与 `->curr` 不一致时，10 秒 45211 次调用里有 45193 次是空操作。修复走 urgent 而不是
core，说明维护者按 fix 处理。

## 背景与问题

`update_curr()` 读的是 `cfs_rq->h_curr`；在 **root cfs_rq** 上 `h_curr` 是顶层 group entity，于是
`update_curr()` 在 `!entity_is_task()` 检查处直接返回，**根本没碰 vruntime**。可这两处代码随后读的是
`cfs_rq->curr`——用作者的话：

> Both then read ->curr, so the guard and the update disagree about which entity they mean.

也就是说 `pick_task_fair()` 的守卫条件 `if (cfs_rq->curr && cfs_rq->curr->on_rq)` 与实际被更新的实体不是同一个对象，
带 cgroup 时「先把 curr 更新到最新再看 eevdf 状态」这个意图没有生效。

作者量化了这一点（1 个 CPU、10 秒、3 个 busy 任务 + 1 个 200us 周期任务）：

```
  all tasks in the root cgroup        43321 calls,     0 no-ops
  busy tasks in G0, periodic in G1    45211 calls, 45193 no-ops
```

即启用 cgroup 分层后，接近 100% 的 pick 路径上这次更新是白做的。

哪些地方真的会因此出问题：自 `68e37487810a ("sched/fair: Fix flat hierarchy")` 之后，tick 与
enqueue/dequeue 都会正确更新 curr，所以普通重调度路径上只少了「那几微秒」，作者明确写了
"I could not measure a latency difference there."。真正前面什么都没有的三条路径是：

- core scheduling 下对同核 sibling rq 的 `pick_task()`（`kernel/sched/core.c`，那里正是为此先更新该 rq 的 clock）；
- `fair_server_pick_task()`；
- `yield_task_fair()`——这里的陈旧值会喂给 `entity_eligible()` 判断，而该判断决定要不要放弃剩余 vruntime。

在这三条路径上 curr 可以落后一整个 tick。

## 技术方案

改动只有 2 行（`kernel/sched/fair.c`，+2/-2）：

- `pick_task_fair()`（约 10057 行，注释 "Might not have done put_prev_entity()"）：
  `update_curr(cfs_rq)` → `update_curr_eevdf(cfs_rq)`
- `yield_task_fair()`（约 10160 行）：同样替换。

`update_curr_eevdf()` 不做 `->h_curr` 那层间接，直接更新传入 cfs_rq 的 curr，因此与守卫条件一致。作者特别强调
这**不给被更新实体引入新行为**：无 cgroup 时 `->h_curr` 本来就是 task，这两处原先已经跑完整的 `update_curr()`，
包括 `update_deadline()`、`dl_server_update()` 与末尾的 `resched_curr_lazy()`；本补丁只是让 cgroup 情形做同样的事。

## 版本演进与当前进展

- 8/22 18:59：Zhan Xusheng 发 v1（单补丁，`Fixes: 85570f10a4c6 ("sched/eevdf: Move to a single runqueue")`）。
- 8/25 00:07：Vincent Guittot 给 `Reviewed-by`（回帖正文只有标签，无附加意见）。
- 9/2 15:22（+08:00）：tip-bot2 通告已合入 tip/sched/urgent，Committer Peter Zijlstra，CommitterDate
  02 Sep 2026 09:17:49 +0200。
- 全程一个版本，未重发；线程内没有分歧、没有备选方案。

## Maintainer 意见与讨论焦点

- **Vincent Guittot（sched/fair 维护者）**：直接 `Reviewed-by: Vincent Guittot`，一个字都没多问。这说明他认可
  「根因分析 + 计数数据 + 影响面枚举」这套论证方式。
- **Peter Zijlstra（committer）**：接受进 `sched/urgent`，并在合并时补了 `Signed-off-by: Peter Zijlstra (Intel)`；
  注意他**没有**加 `Cc: stable`——线程里也没有，所以这个修复不会自动回流到已发布内核。
- 值得记录的口径：作者主动说明「正常路径无可测差异」，只把问题限定在 core scheduling / dl_server / yield 三条路径。
  这种自我限制反而让补丁更容易被 urgent 接收。

## 合入评估

**已合入**（tip/sched/urgent），会随紧急修复窗口进主线，无卡点。剩余不确定项只有一个：没有 `Cc: stable`，
所以已发布内核（含 6.6 这类长期分支，若含 `85570f10a4c6` 引入的 `->h_curr` 语义）不会自动拿到它，需要自行判断是否回合。

## 效果评估

作者给的是**机制计数**而非性能提升：root cgroup 43321 次调用 0 次 no-op vs 分组后 45211 次调用 45193 次 no-op。
性能层面作者明确说 "I could not measure a latency difference there."（正常重调度路径）。所以本补丁的价值在于
让 cgroup 场景下 `entity_eligible()` / vruntime 判断不再使用落后最多一个 tick 的 curr，属于正确性修复；对
core scheduling、`fair_server`（cputime 虚拟化/限流）与 yield 语义的间接影响，线程内无人测量。

## 我可以参与的点

- **回合判断（对 OLK-6.6 最直接）**：确认目标分支是否含 `85570f10a4c6 ("sched/eevdf: Move to a single runqueue")`
  与 `68e37487810a ("sched/fair: Fix flat hierarchy")`。前者决定 `->h_curr` 间接层是否存在（即 bug 是否存在），
  后者决定影响面有多大。若两条件不同时满足，回合方案要相应调整。
- **补 `Cc: stable` 的判断**：既然无 cgroup 场景行为不变、有 cgroup 场景是纯修复，值得向维护者提议加 stable；
  目前线程里没人提。
- **量化线程内缺的那块**：core scheduling（`coresched`）与 `fair_server_pick_task()` 路径下的实际延迟影响，
  作者只做了定性说明。手上有 core scheduling + cgroup 组合场景的人可以直接给出数字。
- 若使用 cgroup cpu 控制器 + 周期性低延迟业务，可以在自己的机器上复刻作者那个 no-op 计数（`->h_curr != ->curr`
  计数），这是判断是否受影响的最省事方法。

## 参考链接

- v1 原始补丁：https://lore.kernel.org/all/20260822105930.2352761-1-zhanxusheng1024@gmail.com/
- Vincent Guittot Reviewed-by：https://lore.kernel.org/all/CAKfTPtCg78iZ=LYxVVtGm3QMqtHSX9jeqKhkU8QT1S_5aUYjgQ@mail.gmail.com/
- tip-bot2 合入通告：https://lore.kernel.org/all/178833372528.3717435.3041801435295808244.tip-bot2@tip-bot2/
- commit：https://git.kernel.org/tip/1719d035a6fa90b7467b6daf45a573f5180013b2 （引自合入通告正文）
- 相关：[[sched-20260901-002]]（`->h_curr` 在 bandwidth 路径的使用）、[[sched-20260902-007]]（flat-hierarchy/h_load 同期问题）

---
id: sched-20260902-010
date: '2026-09-02'
subject: 'sched/fair: Use update_curr_eevdf() for the remaining root cfs_rq callers'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <20260822105930.2352761-1-zhanxusheng1024@gmail.com>
lore_url: https://lore.kernel.org/all/20260822105930.2352761-1-zhanxusheng1024@gmail.com/
upstream_commit: 1719d035a6fa90b7467b6daf45a573f5180013b2
fixes_commit: 85570f10a4c6
merged_branch: tip/sched/urgent
current_version: v1
generated_at: '2026-09-07'
authors:
- Zhan Xusheng
maintainers_involved:
- Vincent Guittot
- Peter Zijlstra
patch_series:
- '[PATCH] sched/fair: Use update_curr_eevdf() for the remaining root cfs_rq callers'
merge_assessment:
  likelihood: likely
  blocking_issues: []
  next_action: 已合入 tip/sched/urgent；关注其随紧急修复窗口进主线，以及是否补 Cc stable（线程未提）
contribution_opportunities:
- 确认 OLK-6.6 是否同时含 85570f10a4c6 与 68e37487810a，据此判断 bug 是否存在及回合方案
- '提议为该修复补 Cc: stable（线程中无人提出）'
- 量化 core scheduling 与 fair_server_pick_task 路径下 curr 陈旧的实际延迟影响
- 在 cgroup + 周期任务场景复刻 ->h_curr != ->curr 的 no-op 计数，判断自身是否受影响
source_email_count: 1
related_articles:
- sched-20260826-011-sched-fair-update-curr-eevdf-root-cfs-rq.md
- sched-20260825-011-sched-fair-update-curr-eevdf-root-cfs-rq.md
tags:
- sched/fair
- eevdf
---
