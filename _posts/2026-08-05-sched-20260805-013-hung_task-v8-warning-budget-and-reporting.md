---
id: sched-20260805-013
date: '2026-08-05'
title: 'hung_task: Improve warning budget handling and task reporting'
series: 'hung_task: Improve warning budget handling and task reporting'
type: feature
status: under_review
severity: none
merge_likelihood: medium
tags:
- hang
- sched_debug
authors:
- Aaron Tomlin <atomlin@atomlin.com>
- Lance Yang <lance.yang@linux.dev>
- Andrew Morton <akpm@linux-foundation.org>
reviewers:
- Lance Yang <lance.yang@linux.dev>
- Andrew Morton <akpm@linux-foundation.org>
- Petr Mladek <pmladek@suse.com>
related_articles: []
emails:
- uid-20910@qq-imap
- uid-22617@qq-imap
layout: article
---

# hung_task: v8 改进警告预算处理与任务报告（含数据竞争修复）

## 摘要

`hung_task` watchdog 检测卡在 `TASK_UNINTERRUPTIBLE`(D) 超过阈值的任务。`sysctl_hung_task_warnings` 用预算限制日志条数，但原实现有两个缺陷：(1) 预算用尽后永久失明——单次临时 hang 后不再报告后续 hang；(2) 预算耗尽时连基本单行告警也完全抑制，管理员对「有任务在 hang」毫无感知。

Aaron Tomlin 的 v8 把**配置的预算**与**运行时计数**解耦：新增 `hung_task_warnings_printed` 跟踪剩余预算，当一次 watchcheck 未发现 hung task 时自动重置回配置值；预算耗尽时仍保留基本单行告警（仅抑制详细栈 dump）。

本日要点：
- **v8 0/2 与 1/2（20910）**：拆分 `sysctl_hung_task_warnings`（保持不变）与 `hung_task_warnings_printed`（运行时计数）；`proc_dohung_task_warnings` 在用户写入时同步重置计数；watchdog 在 `this_round_count == 0` 时重置计数。
- **Andrew Morton 转来 AI review（sashiko）两点反对**：
  1. 并发写 `sysctl_hung_task_warnings` 可能让 `hung_task_warnings_printed` 与配置失同步（数据竞争）；
  2. 无条件 `pr_err()` 不再受预算约束，hang 任务多时每次扫描每条任务都打一行会 flood 日志/console。
- **Aaron 的回复（22617）**：
  - 对 (1)：承认风险低（并发 sysctl 写仅 CAP_SYS_ADMIN，且 watchdog 发现零 hang 时会自愈合），但接受用 `READ_ONCE()`/`WRITE_ONCE()` 消除数据竞争；
  - 对 (2)：认同严重，提出把 per-task blocked 消息移回预算检查内，预算耗尽时在 `check_hung_uninterruptible_tasks()` 末尾打**单行聚合摘要**（如「N tasks blocked for >Xs (budget exhausted)」）。

## 技术细节

原实现问题：
```
if (sysctl_hung_task_warnings > 0)
    sysctl_hung_task_warnings--;   // 直接扣配置，配置被永久改小
```
v8：
```
if (hung_task_warnings_printed > 0)
    hung_task_warnings_printed--;  // 只扣运行时计数
// 预算耗尽：仍 pr_err 基本行
if (!this_round_count)
    WRITE_ONCE(hung_task_warnings_printed, READ_ONCE(sysctl_hung_task_warnings)); // 自动重置
```

Aaron 针对 AI review 的修订（示意）：
```
// 预算内才打详细 per-task 行；预算外仅聚合摘要
if (hung_task_warnings_printed || hung_task_call_panic) {
    if (hung_task_warnings_printed > 0) hung_task_warnings_printed--;
    pr_err("INFO: task %s:%d blocked ...", ...);
    ... 详细栈 ...
}
...
if (!hung_task_warnings_printed && !hung_task_call_panic)
    pr_info("khungtaskd: %lu tasks blocked for >%lds (budget exhausted)\n",
            this_round_count, timeout);
```
并用 `READ_ONCE`/`WRITE_ONCE` 包住两变量的读写消除数据竞争。

## 影响与风险

- 影响面：仅 hung_task watchdog 的日志/预算行为，不改变调度决策；对「系统恢复后 watchdog 重新生效」与「预算耗尽时仍可见基本告警」有直接改善。
- 风险：中。涉及 sysctl 写路径与 watchdog 读的并发，需用 `READ_ONCE/WRITE_ONCE` 收口（Aaron 已接受）；聚合摘要的措辞/频率需确认不会在极端 hang 风暴下仍 flood。
- 收益：修复了「单次 hang 永久失明」这一真实运维盲区。

## 评价

是 debugging/monitoring 侧的稳健改进，经 AI review（sashiko）抓出两个实质性问题后质量提升。属于 08-05 少有的「review 直接产出修订补丁」的良性往返。合入可能性中等，建议在 v9 落实 `READ_ONCE/WRITE_ONCE` 与聚合摘要后再推进。
