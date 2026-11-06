# sched/core: Account I/O waits independently of delayed dequeue

## TL;DR

Christian Loehle（Arm）的修复今日合入 tip/sched/urgent（commit `0965587d00b84f0a3b0fc94930d4a5f8ff011eda`）：blkio delay 记账与 `rq->nr_iowait` 此前都绑在「任务从 runqueue 移除」（`__block_task()`）上，与 EEVDF delayed dequeue 冲突——延迟 dequeue 期间就醒来的任务漏记整段/首段 I/O 睡眠、`procs_blocked` 里缺失，且最终 dequeue 可能在别的任务上下文给错任务打时间戳。修复把两类记账挪到 `try_to_block_task()`（任务决定阻塞时）启动、`unblock_task()` 清除，并用 `iowait_cpu` 保存计费 CPU。此前已获 Zhan Xusheng（报告者）与 Kayra Cizmeci 双 Reviewed-by。

## 背景与问题

Zhan Xusheng 报告：`delayacct_blkio_start()` 在 `__block_task()` 里才调用，把记账区间绑在「从 runqueue 移除」时刻。EEVDF delayed dequeue 下，任务真正被 dequeue 前若被唤醒，就漏掉 I/O 睡眠的起始段（极端情况整段漏掉）；最终 dequeue 可能发生在另一任务的上下文（delayed dequeue / proxy execution），给错任务打时间戳。`rq->nr_iowait` 同理，延迟任务在 `procs_blocked` 里缺失。

## 技术方案

两类记账（`delayacct_blkio_*` 与 `rq->nr_iowait`）都改在 `try_to_block_task()`（当前任务决定阻塞时）启动，`unblock_task()` 清除——覆盖 queued wakeup 与 proxy execution 让当前任务继续的路径，且 `is_blocked` 检查排除「阻塞前的 wakeup」。新增 `task_struct.iowait_cpu` 保存计费 CPU：延迟任务在仍入队时可能迁移、proxy execution 也会移动阻塞任务，解除阻塞时按保存的 CPU 递减其计数器。改动 3 文件 +22/-18 行。

## 版本演进与当前进展

*current_version: v2（2026-10-15 发出）*。v1 只改 blkio delay，v2 把 `rq->nr_iowait` 一并纳入。今日合入 tip/sched/urgent。

## Maintainer 意见与讨论焦点

Zhan Xusheng（报告者）与 Kayra Cizmeci 双 Reviewed-by；Peter Zijlstra/Ingo Molnar 连带 Signed-off-by。无异议。

## 合入评估

*likelihood=merged*。已进 tip/sched/urgent，commit `0965587d00b84f0a3b0fc94930d4a5f8ff011eda`。*blocking_issues*：无。*next_action*：随 sched/urgent 进入主线。

## 效果评估

提交说明聚焦语义正确性（漏记/错记时间戳/`procs_blocked` 缺失），未附量化数据；报告者为 Zhan Xusheng（Closes 其报告线程）。

## 我可以参与的点

当前阶段无参与空间（已合入）。

## 参考链接

- tip commit: https://git.kernel.org/tip/0965587d00b84f0a3b0fc94930d4a5f8ff011eda
- 原补丁 lore: https://patch.msgid.link/fd8578a1-e60b-4993-ab51-2b5d63abcf77@arm.com

---
id: sched-20261106-025
date: 2026-11-06
subject: "sched/core: Account I/O waits independently of delayed dequeue"
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: "<179395863965.1009794.4319804414871563617.tip-bot2@tip-bot2>"
lore_url: "https://lore.kernel.org/all/179395863965.1009794.4319804414871563617.tip-bot2@tip-bot2/"
authors: [Christian Loehle]
maintainers_involved: [Ingo Molnar, Peter Zijlstra]
current_version: v2
patch_series:
  - version: v2
    msgid: "<fd8578a1-e60b-4993-ab51-2b5d63abcf77@arm.com>"
    date: 2026-10-15
    summary: "blkio delay/nr_iowait 记账挪到 try_to_block_task/unblock_task，iowait_cpu 保存计费 CPU。"
    review_outcome: "Zhan Xusheng/Kayra 双 Reviewed-by；11-06 合入 tip/sched/urgent。"
upstream_commit: "0965587d00b84f0a3b0fc94930d4a5f8ff011eda"
fixes_commit: "152e11f6df29"
merged_branch: "tip/sched/urgent"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "随 sched/urgent 进入主线"
contribution_opportunities: []
generated_at: "2026-11-07T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261015-004]
tags: [cfs, eevdf]
---