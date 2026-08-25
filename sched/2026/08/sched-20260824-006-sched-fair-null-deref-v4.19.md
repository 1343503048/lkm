# sched/fair: NULL deref in pick_next_task_fair (v4.19)

## TL;DR
两个独立生产环境（HiSilicon Kunpeng 920 ARM64，v4.19 内核）报告了相同的 `pick_next_task_fair()` NULL 解引用崩溃：`nr_running` 为 -1（0xFFFFFFFF），导致非零检查通过但红黑树为空，`rb_leftmost` 返回 NULL。超长运行时间（290-738 天）后才触发。

## 背景与问题
两个不相关的生产环境报告了相同的崩溃签名：
- **Site A**：aarch64 Kunpeng 920，96 CPUs，内核 4.19.90-23.43，运行 738 天
- **Site B**：aarch64 Kunpeng 920，128 CPUs，内核 4.19.90-89.17，运行 290 天

崩溃现场：
```c
again:
    if (!cfs_rq->nr_running)    /* 0xFFFFFFFF != 0, no idle */
        goto idle;
```
`nr_running` 值为 `0xFFFFFFFF`（即 -1 的无符号表示），非零检查通过，但实际红黑树为空，`pick_next_entity()` 从空树取 `rb_leftmost` 得到 NULL。

触发进程：`ksoftirqd/65`，在软中断处理期间触发调度。

## 技术方案
这是一个 bug 报告，暂无修复补丁。`nr_running` 变为 -1 表明某处对 `nr_running` 做了多余的 `dec` 操作（或漏了 `inc`）。可能原因：
- `dequeue_task_fair()` 被多调用了一次
- 竞态条件导致 `nr_running` 计数不一致
- v4.19 特有的代码路径（主线可能已修复）

## 版本演进与当前进展
- v1：bug 报告，附带两个完整的生产环境 vmcore 分析

当前无修复补丁，社区尚未回复。

## Maintainer 意见与讨论焦点
暂无维护者回复。由于是 v4.19 老内核，主线维护者可能不会优先处理，但如果问题在主线也存在则需要关注。

## 合入评估
不适用（这是 bug 报告，不是补丁系列）。
- 需要先确认主线是否也存在此问题
- 如果是 v4.19 特有的，可能由发行版自行修复

## 效果评估
生产环境崩溃，影响系统可用性。两个站点均为长时间运行的服务器，崩溃导致服务中断。

## 我可以参与的点
- 如果了解 v4.19 到主线之间 `nr_running` 相关代码的变更，可以帮忙判断主线是否已修复
- 可以帮忙分析 `ksoftirqd` 在软中断处理期间的调度路径，看是否有特殊的 `dequeue` 场景
- 如果有类似的 ARM64 长时间运行环境，可以帮忙复现

## 参考链接
- lore thread: 未获取到

---
id: sched-20260824-006
date: 2026-08-24
subsystem: sched
type: bug
status: under_review
severity: critical
thread_root_msgid: "<unknown>"
lore_url: "未获取到"
authors:
- unknown reporter
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<unknown>"
    date: 2026-08-24
    summary: "报告 pick_next_task_fair NULL 解引用，nr_running==-1"
    review_outcome: "暂无回复"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["需要确认主线是否存在同样问题"]
  next_action: "等待社区分析，确认是否为 v4.19 特有问题"
contribution_opportunities:
  - kind: review
    description: "分析主线是否已修复此问题"
  - kind: testing
    description: "在 ARM64 长时间运行环境中尝试复现"
generated_at: "2026-08-25T10:40:00"
source_email_count: 1
related_articles: []
tags: [sched/fair, cfs, race_condition]
---
