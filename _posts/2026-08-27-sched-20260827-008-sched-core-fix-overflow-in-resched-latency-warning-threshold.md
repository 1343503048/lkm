---
id: sched-20260827-008
date: '2026-08-27'
subject: 'sched/core: Fix overflow in resched latency warning threshold'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260827080152.2544683-1-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20260827080152.2544683-1-sh_def@163.com/
authors:
- Hui Su
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260827080152.2544683-1-sh_def@163.com>
  date: 2026-08-27
  summary: latency_warn_ms 换算 u64 化 + kstrtouint + unsigned 统一，修 32-bit 溢出与符号错位
  review_outcome: 暂无 review
upstream_commit: null
fixes_commit: c006fac556e4
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待维护者 review/收队列
contribution_opportunities:
- kind: testing
  description: 在 32-bit 或带该问题的基线上验证 debugfs 写入 >2147ms 的告警行为并回帖 Tested-by
generated_at: '2026-09-07T22:05:00'
source_email_count: 1
related_articles: []
tags:
- preempt
- sched_debug
title: 'sched/core: Fix overflow in resched latency warning threshold'
layout: article
---

## TL;DR
Hui Su 的单补丁修复：32-bit 内核上 `latency_warn_ms * NSEC_PER_MSEC` 以 32-bit 有符号运算求值，>2147 ms 即溢出，导致 need_resched 长延迟告警阈值算错（该报的不报、不该报的乱报）；顺带修了 debugfs 接口 u32 与底层 int 类型不一致。纯诊断路径修复，当日无人回复。

## 背景与问题
`sched_resched_latency_warn_ms`（`/sys/kernel/debug/sched/latency_warn_ms`，`debugfs_create_u32()` 暴露）用于"need_resched 挂起过久"告警阈值。两个类型问题：(1) 换算 `latency_warn_ms * NSEC_PER_MSEC` 时 NSEC_PER_MSEC 是 long，32-bit 下 2148 ms 以上溢出后再与 u64 的 resched latency 比较，阈值随机化；(2) 底层变量是 int，debugfs 按 u32 写入超 INT_MAX 会以负数解释，boot 参数解析同样用有符号类型。只影响告警诊断，不影响调度决策。

## 技术方案
统一为 `unsigned int`、boot 参数改用 `kstrtouint()`、毫秒转纳秒前先提升到 u64 再乘。改动 `kernel/sched/core.c` 与 `sched.h` 共 8+/6-。

## 版本演进与当前进展
v1（本日发出，msgid `<20260827080152.2544683-1-sh_def@163.com>`），暂无 review。带 `Fixes: c006fac556e4`（"sched: Warn on long periods of pending need_resched"）。

## Maintainer 意见与讨论焦点
无人表态，无分歧。该补丁出自近期活跃的同一作者（同日还有 sched/numa 修复，见 sched-20260827-009）。

## 合入评估
**likely**。范围小、意图清晰、有 Fixes 标签、不触碰调度决策路径，此类类型修复维护者接受度高。卡点仅在被淹没在待办里没人捡。`next_action`：等 review 或轻微 ping。

## 效果评估
无 benchmark（诊断修复无需数据）；症状描述（>2147 ms 溢出、u32/int 错位）来自代码推导，可信。

## 我可以参与的点
- OLK-6.6 若带 `c006fac556e4` 同源改动，32-bit（或 `CONFIG_DEBUG_KERNEL` + 小类型平台）配置下该 bug 同样成立，可作为低风险回合候选；回帖 Tested-by 也是助力。

## 参考链接
- lore: https://lore.kernel.org/all/20260827080152.2544683-1-sh_def@163.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到
