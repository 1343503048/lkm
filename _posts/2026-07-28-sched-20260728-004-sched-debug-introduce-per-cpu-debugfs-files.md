---
subject: 'sched/debug: Introduce per-CPU debugfs files'
id: sched-20260728-004
date: 2026-07-28
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260728020309.6169-1-atomlin@atomlin.com>
lore_url: https://lore.kernel.org/r/20260728020309.6169-1-atomlin@atomlin.com
authors:
- Aaron Tomlin
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <20260728020309.6169-1-atomlin@atomlin.com>
  date: 2026-07-28
  summary: Add /sys/kernel/debug/sched/cpu/cpu<N>/debug for per-CPU scheduler debug
    output
  review_outcome: PeterZ 质疑使用场景；作者回复将重写 commit message；另有用户表示支持（DPDK/realtime 调试场景）
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - PeterZ 要求更好地阐述 rationale
  - commit message 需要重写
  next_action: 作者发 v2 重写 commit message，说明 per-CPU debug 的具体使用场景
contribution_opportunities:
- kind: discussion
  description: 如果有在大型 SMP 系统上调试单 CPU 调度问题的经验，可以回帖支持并补充使用场景
generated_at: '2026-07-30T10:00:00'
source_email_count: 6
related_articles: []
tags:
- sched_debug
title: 'sched/debug: Introduce per-CPU debugfs files'
layout: article
---

## TL;DR

Aaron Tomlin 提出在 debugfs 下新增 per-CPU 调度调试文件 `/sys/kernel/debug/sched/cpu/cpu<N>/debug`，避免大型 SMP 系统上读取全量 debug 输出的开销。PeterZ 质疑使用场景，作者将重写 commit message 发 v2。有用户（DPDK/realtime 方向）表示支持。

## 背景与问题

当前 `/sys/kernel/debug/sched/debug` 输出所有在线 CPU 的调度信息。在大型 SMP 系统（如 128+ 核）上，如果只想调试某一个 CPU 的 runqueue 状态，需要读取并解析全量输出，既慢又冗余。

## 技术方案

在 `kernel/sched/debug.c` 中新增：
- 目录结构：`/sys/kernel/debug/sched/cpu/cpu<N>/debug`
- 读取时只调用 `print_cpu(m, cpu)` 输出指定 CPU 的 runqueue 信息
- 实现约 40 行代码，使用 `single_open` + `seq_file` 标准模式

## 版本演进与当前进展

v1（2026-07-28）：首次发出。PeterZ 回帖质疑（具体意见在 uid=5483 的 in-reply-to 中引用），作者回复将在 v2 中重写 commit message 以更好地阐述 rationale。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**：明确质疑动机，原话："You're failing to explain why though. In what situation does the overhead from sched/debug matter one whit? If you're dumping this at frequencies high enough for this to matter, you're doing something terribly wrong." 核心观点是：sched/debug 本身是低频调试工具，如果读取频率高到全量输出成为瓶颈，那使用方式本身就有问题
- **作者回复**：强调这不是用于高频轮询或生产监控，而是在调查特定 CPU 的延迟异常/调度问题时提供即时、定向的视图
- **支持意见**（uid=5483，疑似 DPDK/realtime 用户）：

> "I can imagine running a realtime app pinned on an isolated CPU (for example any DPDK app like FlexRAN on top of Kubernetes/OpenShift, etc.) and debugging system noise/starved victims on this CPU. Why dump sched details from other CPUs and look for a needle in the haystack?"

## 合入评估

可能性中等。代码本身简单（40 行），主要障碍是 commit message 需要让 PeterZ 认可使用场景。作者已承诺 v2 重写，预计不会有技术层面的阻塞。

## 效果评估

暂无性能数据。这是调试接口改进，不涉及运行时性能。

## 我可以参与的点

- **讨论**：如果在大型多核系统上有过"只想看某个 CPU 的调度状态但被全量输出淹没"的经历，可以回帖补充使用场景，帮助推动 v2 合入

## 参考链接

- lore thread: https://lore.kernel.org/r/20260728020309.6169-1-atomlin@atomlin.com
- tip-bot commit: 未获取到
