# sched/delayacct: blkio_start recorded on the wrong task when a delayed task is blocked from pick

## TL;DR

kiln 报告 DELAY_DEQUEUE 引入的 delay accounting bug：`__block_task()` 调 `delayacct_blkio_start()` 时总是写 `current`，使 delayed 任务从 `dequeue_entities()` 路径被 block 时 `blkio_start` 保持 0，随后 `delayacct_blkio_end()` 一次性把整个 uptime 记到该线程。Christian Loehle 指出 Peter Zijlstra 的 queue/sched/urgent 已有修复（5d010dd27be9），Peter 确认分支已推、等机器人通过后进 tip。

## 背景与问题

`__block_task()` 调 `delayacct_blkio_start()`，该 helper 总是写 `current->delays->blkio_start`。从 `__schedule()` 为 prev 调用时没问题；但当任务被 delayed、之后从 `pick_next_task_fair() → pick_next_entity() → dequeue_entities() → __block_task()` 被 block 时，`current` 是那个 CPU 上正在调度的人，不是 `p`。于是 `p` 的 `blkio_start` 未设置（或残留旧值），I/O 完成时 `ttwu() → delayacct_blkio_end(p)` 把 `local_clock() - blkio_start` 计入 `p->blkio_delay`；对全新线程 `blkio_start` 为 0，一次性被记入整个 uptime。作者在 per-thread blkio delay（taskstats、`/proc/<pid>/task/<tid>/stat` 第 42 字段）上看到几秒龄的 Chromium 线程带 ~7,070,000 s 的 block I/O delay（恰为主机 uptime）。环境为其发版 6.6.102 内核（Alibaba Cloud Linux 4，携带 EEVDF/DELAY_DEQUEUE backport），主线 v6.12 与当前 master 的 `__block_task()` 仍无 task 参数。

## 技术方案

作者未附补丁（报告型）。附 bpftrace 实测：DELAY_DEQUEUE on 时「from dequeue_entities」路径 50-103 次/run、`blkio_end` 且 `blkio_start==0` 3-10 次（全是 Chrome 线程）；NO_DELAY_DEQUEUE 时该路径 0-2 次、`blkio_start==0` 为 0。Christian Loehle 指向 peterz queue 的 `5d010dd27be9`（sched/urgent）已修复。

## 版本演进与当前进展

*current_version: 报告（无补丁，2026-11-03，msgid tencent_6CFB6E9B26A308DC2800D4059DF93FEC9706@qq.com）*。当日 K Prateek Nayak、Christian Loehle、Peter Zijlstra 回帖。

## Maintainer 意见与讨论焦点

K Prateek Nayak 认可（"Good catch... you should send a patch"）。Christian Loehle 指出已有修复（peterz queue `5d010dd27be9`），并问 Peter 为何还没进 tip。Peter 答：「昨天（-rc1 之后）才推分支，在等机器人，之后推到 tip」。无分歧，属「报告已被现有修复覆盖」的情形。

## 合入评估

*likelihood=high*。问题已由 Peter 现有的 sched/urgent 修复（5d010dd27be9）覆盖，只差进 tip。作者即便发补丁也需要与既有修复对齐。

## 效果评估

作者 bpftrace 实测数据完整（两轮 DELAY_DEQUEUE on/off 的对照），证明 `blkio_start==0` 仅在有 DELAY_DEQUEUE 且走 `dequeue_entities` 路径时出现，关联明确。

## 我可以参与的点

- testing：作者可尝试 Peter 的 5d010dd27be9 补丁，回帖确认其修复了任务级 blkio_delay 误报（Christian 已建议"please give it a try"）。
- review：确认 `delayacct_blkio_start()` 是否还有其他无 task 参数的调用点。

## 参考链接

- lore thread: https://lore.kernel.org/all/tencent_6CFB6E9B26A308DC2800D4059DF93FEC9706@qq.com/
- 既有修复: https://git.kernel.org/pub/scm/linux/kernel/git/peterz/queue.git/commit/?h=sched/urgent&id=5d010dd27be92a68eaac3af4f5ef0555bcde6031

---
id: sched-20261103-004
date: 2026-11-03
subject: "sched/delayacct: blkio_start recorded on the wrong task when a delayed task is blocked from pick"
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: "<tencent_6CFB6E9B26A308DC2800D4059DF93FEC9706@qq.com>"
lore_url: "https://lore.kernel.org/all/tencent_6CFB6E9B26A308DC2800D4059DF93FEC9706@qq.com/"
authors: []
maintainers_involved: [Peter Zijlstra]
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "已被 peterz queue 5d010dd27be9 修复覆盖，等进 tip。"
contribution_opportunities:
  - kind: testing
    description: "在 5d010dd27be9 补丁上验证任务级 blkio_delay 误报消失。"
  - kind: review
    description: "排查 delayacct_blkio_start() 是否还有其它无 task 参数调用点。"
generated_at: "2026-11-04T09:00:00+08:00"
source_email_count: 4
related_articles: []
tags: [eevdf, cfs]
---