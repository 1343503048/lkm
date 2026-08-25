# sched/cpufreq: Reevaluate frequency before tickless idle

## TL;DR
`sugov_hold_freq()` 可能在 runqueue 转空时保持 UCLAMP_MIN 驱动的高频率，若随后 cpuidle 停掉 tick，CPU 将在整个 idle 期间维持不必要的高电压；此补丁在 tick 停止前发出最后一次频率更新。

## 背景与问题
`sugov_hold_freq()` 的设计意图是在 runqueue 变空时"保持"当前频率（避免因短暂空闲就降频）。但当 cpuidle 随后决定停止 tick 进入深度 idle 时，不会再有后续的 utilization 更新——这意味着如果最后一次更新因 UCLAMP_MIN 拉高了频率，CPU 会在整个 idle 周期维持不必要的高电压，浪费功耗。

## 技术方案
在 idle tick 实际从运行转为停止时，强制执行一次最终的 `cpufreq_update`：
- 在 `include/linux/sched/cpufreq.h` 新增接口声明
- 在 `kernel/sched/cpufreq_schedutil.c` 中，当检测到 tick 停止时，绕过 rate limit 强制 schedutil 重新计算频率
- 当 tick 保留时（浅层 idle），维持现有的 hold 行为不变

关键设计取舍：只在 tick 真正停止时触发，避免浅层 idle 场景的不必要频率抖动。

## 版本演进与当前进展
- **v1**（Christian Loehle）：首发

当前版本：v1，暂无 review 意见。

## Maintainer 意见与讨论焦点
暂无维护者回复。该补丁来自 ARM 的 Christian Loehle，涉及 schedutil governor 和 cpuidle 交互，可能需要 Rafael Wysocki（cpufreq maintainer）和 Peter Zijlstra 确认。

## 合入评估
合入可能性 **medium**：
- 问题真实（功耗浪费）
- 方案合理（精确在 tick 停止时触发）
- 但涉及跨子系统（sched + cpufreq + cpuidle），需要多方确认
- `blocking_issues`：需要 cpufreq maintainer 确认 rate limit bypass 是否安全
- `next_action`：等待相关子系统维护者回复

## 效果评估
无性能数据；属于功耗优化，影响的是 idle 期间的电压/频率保持。在 WFI 深度 idle 场景下可减少不必要的功耗。

## 我可以参与的点
- 如果有支持 UCLAMP_MIN 且使用 schedutil 的平台（如 ARM 服务器），可以测试该补丁是否确实降低了 idle 功耗
- 可以帮忙验证在 tick 保留的浅层 idle 场景下，频率保持行为是否不受影响

## 参考链接
- lore thread: 未获取到

---
id: sched-20260824-002
date: 2026-08-24
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<unknown>"
lore_url: "未获取到"
authors:
- Christian Loehle
maintainers_involved:
- Rafael Wysocki
- Peter Zijlstra
current_version: v1
patch_series:
  - version: v1
    msgid: "<unknown>"
    date: 2026-08-24
    summary: "在 tick 停止前强制一次频率更新"
    review_outcome: "暂无 review"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["需要 cpufreq maintainer 确认 rate limit bypass 安全性"]
  next_action: "等待 Rafael Wysocki 或相关维护者回复"
contribution_opportunities:
  - kind: testing
    description: "在支持 UCLAMP_MIN 的 ARM 平台上测试 idle 功耗变化"
generated_at: "2026-08-25T10:40:00"
source_email_count: 2
related_articles: []
tags: [sched/cpufreq, cpuidle, idle]
---
