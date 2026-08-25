# sched/core: sporadic stale rq->curr (rq->curr != current) causing scheduler crashes on long-running arm64 servers

## TL;DR
超过十台 HiSilicon Kunpeng 920 ARM64 生产服务器报告了偶发内核崩溃，共同特征：`rq->curr != current`——CPU 已切换到 idle 但 `rq->curr` 仍指向旧任务。怀疑 `__schedule()` 中的 `rq->curr = next` 更新未生效或被回退。运行 23-300 天后触发。

## 背景与问题
从 2025 年开始，超过十台客户现场 ARM64 服务器出现偶发崩溃：
- **共同硬件**：HiSilicon Kunpeng 920 (HIP08)，TaiShan v110 核心，96/128/256 CPUs
- **共同配置**：64KB pages，48-bit VA，PREEMPT_VOLUNTARY，HZ_100，NO_HZ_FULL
- **内核版本**：基于 v4.19 的发行版内核
- **运行时间**：23 到 ~300 天

所有 dump 显示相同签名：崩溃时 CPU 正在运行 idle 任务，但 `rq->curr` 仍指向某个之前的任务。

报告者使用 `crash(8)` 工具分析，通过读取原始内存（因为部分命令会因过期数据而中止）确认：
```
offsetof(struct rq, curr)  = 0xa68
offsetof(struct rq, idle)  = 0xa70
```

## 技术方案
这是一个 bug 报告/求助帖，暂无修复方案。报告者请求社区帮助：
1. 确认是否有人见过类似问题
2. 提供缩小根因范围的建议

可能原因推测：
- `__schedule()` 中的 `rq->curr = next` 赋值被编译器优化或内存屏障问题影响
- 与 NO_HZ_FULL + CPU_ISOLATION 配置有关的竞态
- ARM64 弱内存序导致的可见性问题

## 版本演进与当前进展
- v1：详细的 bug 报告，附带两个代表性案例的完整分析

## Maintainer 意见与讨论焦点
暂无维护者回复。问题涉及调度器核心路径，如果确认是主线问题将需要高优先级处理。

## 合入评估
不适用（这是求助帖，不是补丁）。
- 需要先复现或缩小范围
- 如果是 ARM64 内存序问题，可能需要架构层面的修复

## 效果评估
生产环境崩溃，影响系统可用性。超过十台服务器受影响，属于高优先级问题。

## 我可以参与的点
- 如果有 ARM64 Kunpeng 920 环境，可以尝试复现
- 可以帮忙分析 `__schedule()` 中 `rq->curr` 更新的内存屏障是否充分
- 可以帮忙检查 NO_HZ_FULL 配置下是否有特殊的调度路径

## 参考链接
- lore thread: 未获取到

---
id: sched-20260824-007
date: 2026-08-24
subsystem: sched
type: bug
status: under_review
severity: critical
thread_root_msgid: "<unknown>"
lore_url: "未获取到"
authors:
- Li Wanwu
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<unknown>"
    date: 2026-08-24
    summary: "报告 rq->curr 过期导致调度器崩溃"
    review_outcome: "暂无回复"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["需要复现或缩小根因范围"]
  next_action: "等待社区分析和建议"
contribution_opportunities:
  - kind: review
    description: "分析 __schedule() 中 rq->curr 更新的内存序问题"
  - kind: testing
    description: "在 ARM64 Kunpeng 920 环境尝试复现"
generated_at: "2026-08-25T10:40:00"
source_email_count: 1
related_articles: []
tags: [sched/core, race_condition, memory_safety]
---
