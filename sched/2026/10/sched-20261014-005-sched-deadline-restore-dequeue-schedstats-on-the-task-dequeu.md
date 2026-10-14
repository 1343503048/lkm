# sched/deadline: Restore dequeue schedstats on the task dequeue path

> **subject**：sched/deadline: Restore dequeue schedstats on the task dequeue path

## TL;DR
Zhan Xusheng（小米）修复 SCHED_DEADLINE 任务的 schedstats 回归：`update_stats_dequeue_dl()` 本应记录 `sleep_start`/`block_start`，但它唯一的调用点走了 throttle 路径且 `flags=0`，`DEQUEUE_SLEEP` 分支永不执行，导致 deadline 任务在 `/proc/PID/sched` 里 sleep/block 统计全为 0、不产生任何 `sched_stat_*` 事件。修复把该调用搬回 `dequeue_task_dl()`（带 `on_dl_rq()` 守卫），并顺带修好迁移路径的 wait 记账。当日无 review。

## 背景与问题
`update_stats_dequeue_dl()` 只写 `p->stats.sleep_start`/`block_start`，deadline.c 里没有别处再写这两个字段。它唯一的调用者是 `update_curr_dl_se()`（throttle 路径），且传入 `flags = 0`，于是 `DEQUEUE_SLEEP` 分支从不执行，两字段恒为 0；`__update_stats_enqueue_sleeper()` 又因 `if (sleep_start)`/`if (block_start)` 短路。结果是 deadline 任务在 `/proc/PID/sched` 里 `sleep_max`、`sum_sleep_runtime`、`block_max`、`sum_block_runtime`、`iowait_sum`、`iowait_count` 全为 0，不产生 `sched_stat_sleep`/`sched_stat_blocked`/`sched_stat_iowait`，对 latencytop 也无贡献。

根因：`b5eb4a5f6521` 曾从 `__dequeue_task_dl()`（任务 dequeue 路径）带 flags 调用它（对照 `update_stats_dequeue_fair()`）；`63ba8422f876 ("sched/deadline: Introduce deadline servers")` 把 `__dequeue_task_dl()` 换成 `dequeue_dl_entity()`，并改为加 throttle 路径调用，却没把旧调用点带过来。`Fixes: 63ba8422f876`。

## 技术方案
在 `dequeue_task_dl()` 里、`DEQUEUE_MIGRATING` fixup 之后加：

```c
if (on_dl_rq(&p->dl))
    update_stats_dequeue_dl(&rq->dl, &p->dl, flags);
```

放在 `dequeue_dl_entity()` 之前。刻意不用 `dequeue_dl_entity()`：`dl_server_stop()` 会带着 server entity 走到它，而 `dl_task_of()` 对 server 拿不到 task。`on_dl_rq()` 守卫与 `set_next_task_dl()`/`put_prev_task_dl()` 一致——否则 throttled 任务会被计两次（throttle 路径 dequeue 一次 + 这里一次，第二次 `update_stats_wait_end_dl()` 会跑在已被清掉的 `wait_start` 上）。迁移路径也因此受益：`deactivate_task()` 在 dequeue 前置 `TASK_ON_RQ_MIGRATING`，`__update_stats_wait_end()` 走 `task_on_rq_migrating()` 分支、把累积 wait 时间结转进 `wait_start` 而非终结——这正是 `c0e1832ba6da ("sched: Fix incorrect schedstats for rt and dl thread")` 想在 deadline 上做而没做到的。

## 版本演进与当前进展
v1（今日首发，`<20261014132704.1200766-1-zhanxusheng@xiaomi.com>`）。当日无 review。

## Maintainer 意见与讨论焦点
当日无维护者/评审表态。补丁自带完整根因推演（含 `flags=0` 为何跳过、为何不用 `dequeue_dl_entity()`、为何加 `on_dl_rq()` 守卫），逻辑自洽但尚待 SCHED_DEADLINE 维护者（Juri Lelli 等）确认。

## 合入评估
*likelihood=unknown*。v1 刚发、无 review。修复对象明确（`Fixes:` + 逐字段根因）、影响面窄（仅 schedstats/latencytop，不动调度决策），属低风险统计修复，但需 deadline 维护者审阅。*blocking_issues*：无 review。*next_action*：Juri/Valentin 等 SCHED_DEADLINE 维护者 review 并确认 `on_dl_rq()` 守卫与迁移分支的正确性。

## 效果评估
无性能数据；问题表现为统计缺失（`/proc/PID/sched` sleep/block 字段恒 0、无 `sched_stat_*` tracepoint），修复以恢复统计正确性为目标。

## 我可以参与的点
- testing：在启用 CONFIG_SCHEDSTATS 的内核上对 SCHED_DEADLINE 任务跑 sleep/block 场景，对比修复前后 `/proc/PID/sched` 的 `sleep_max`/`sum_sleep_runtime`/`block_max` 与 `sched_stat_*` 事件是否恢复。
- review：核对 throttled 任务「dequeue 两次」的守卫逻辑，以及 `dl_server_stop()` 经 `dequeue_dl_entity()` 是否会误触发新调用点。

## 参考链接
- 补丁 lore：https://lore.kernel.org/all/20261014132704.1200766-1-zhanxusheng@xiaomi.com/

---
id: sched-20261014-005
subject: 'sched/deadline: Restore dequeue schedstats on the task dequeue path'
date: 2026-10-14
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20261014132704.1200766-1-zhanxusheng@xiaomi.com>'
lore_url: 'https://lore.kernel.org/all/20261014132704.1200766-1-zhanxusheng@xiaomi.com/'
authors:
  - 'Zhan Xusheng'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20261014132704.1200766-1-zhanxusheng@xiaomi.com>'
    date: 2026-10-14
    summary: '把 update_stats_dequeue_dl() 搬回 dequeue_task_dl()（on_dl_rq 守卫）'
    review_outcome: '当日无 review'
upstream_commit: null
fixes_commit: '63ba8422f876'
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - '无 review'
  next_action: 'SCHED_DEADLINE 维护者 review 后收取'
contribution_opportunities:
  - kind: testing
    description: 'CONFIG_SCHEDSTATS 下验证 deadline 任务 sleep/block 统计与 sched_stat_* 事件恢复'
  - kind: review
    description: '核对 throttled 双计守卫与 dl_server 经 dequeue_dl_entity 的边界'
generated_at: '2026-10-15T01:00:00+08:00'
source_email_count: 1
related_articles: []
tags: [deadline]
---