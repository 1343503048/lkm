# sched: Flatten the pick v3 性能回退分析（增量更新）

## TL;DR
本文为增量更新，完整背景见 related_articles 中的文章。社区成员在类似硬件上成功复现了 0day 报告的性能回退，定位到 `wake_affine_weight()` 在 concur 模式下因 `task_h_load()` 返回值增大而改变了负载均衡决策，导致 L2 miss 率上升和吞吐量下降。Peter Zijlstra 表示 `task_h_load()` 行为异常，正在继续排查。

## 版本演进与当前进展
新增两封回复，提供了关键的复现数据和根因分析：

**复现者分析**（使用 192 核无 SMT 机器，每 4 核共享 L2）：
> The decision made by wake_affine_weight() seems to be affected by the increased weight of the wakee under concur mode. As a result, wake_affine_weight() became less likely to select this_cpu.

性能对比数据：
| 配置 | 吞吐量 (Mbps) | L2 miss% | LLC miss% |
|------|-------------|----------|-----------|
| smp + WA_WEIGHT | **470249** | **19.37%** | 60.08% |
| smp + NO_WA_WEIGHT | 305360 | 32.67% | 60.46% |
| concur + WA_WEIGHT | 338770 | 31.45% | 62.85% |
| concur + NO_WA_WEIGHT | 259358 | 36.24% | 61.95% |

关键发现：在 smp 模式下 `task_h_load(p)` 返回极小值（被 `wake_affine_weight` 忽略），而在 concur 模式下返回"正常"值，改变了负载均衡决策。

**Peter Zijlstra 回复**：
> There is something wonky with task_h_load(), it isn't behaving properly. I've not managed to put a finger on it yet. Let me continue poking at it.

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**：确认 `task_h_load()` 行为异常，正在排查
- 回退原因已初步定位：concur 模式改变了 `task_h_load()` 返回值，影响 `wake_affine_weight()` 决策

## 合入评估
合入可能性 **medium**：
- v3 已发出但存在性能回退
- 需要修复 `task_h_load()` 行为或调整 `wake_affine_weight()` 逻辑
- `blocking_issues`：性能回退需要解决
- `next_action`：Peter Zijlstra 继续排查 `task_h_load()` 问题

## 效果评估
**回退数据**（192 核机器）：
- smp → concur 模式：吞吐量从 470249 降至 338770 Mbps（-28%）
- L2 miss 率从 19.37% 升至 31.45%

## 我可以参与的点
- 可以在类似的多核平台上帮忙测试不同配置的性能影响
- 可以帮忙分析 `task_h_load()` 在 concur 模式下为何返回不同值
- 如果有 netperf/loopback 测试环境，可以帮忙验证修复效果

## 参考链接
- lore thread: 未获取到

---
id: sched-20260824-009
date: 2026-08-24
subsystem: sched
type: discussion
status: under_review
severity: high
thread_root_msgid: "<unknown>"
lore_url: "未获取到"
authors:
- Peter Zijlstra
maintainers_involved:
- Peter Zijlstra
current_version: v3
patch_series:
  - version: v3
    msgid: "<unknown>"
    date: 2026-08-21
    summary: "扁平化调度器选择路径"
    review_outcome: "0day 报告性能回退"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["性能回退需要解决"]
  next_action: "Peter Zijlstra 排查 task_h_load() 问题"
contribution_opportunities:
  - kind: testing
    description: "在多核平台测试不同配置的性能影响"
  - kind: review
    description: "分析 task_h_load() 在 concur 模式下的行为"
generated_at: "2026-08-25T10:40:00"
source_email_count: 2
related_articles: [sched-20260821-003]
tags: [sched/core, cfs, performance, load_balance]
---
