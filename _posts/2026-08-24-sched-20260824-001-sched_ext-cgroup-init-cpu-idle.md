---
id: sched-20260824-001
date: 2026-08-24
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260824142817.568085-1-cui.tao@linux.dev>
lore_url: 未获取到
authors:
- Tao Cui
maintainers_involved:
- Andrea Righi
- Tejun Heo
current_version: v2
patch_series:
- version: v1
  msgid: <20260824142817.568085-1-cui.tao@linux.dev>
  date: 2026-08-24
  summary: 在 scx_cgroup_init_args 中新增 idle 字段
  review_outcome: Andrea Righi 建议补充 Fixes 标签
- version: v2
  msgid: <20260824142817.568085-1-cui.tao@linux.dev>
  date: 2026-08-24
  summary: 补充 Fixes 标签
  review_outcome: Andrea Righi Reviewed-by
upstream_commit: null
fixes_commit: 347ed2d566da
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 sched_ext maintainer 确认合入
contribution_opportunities: []
generated_at: '2026-08-25T10:40:00'
source_email_count: 5
related_articles: []
tags:
- sched_ext
- cgroup
- cpuidle
title: 'sched_ext: pass the initial cpu.idle state in scx_cgroup_init_args'
layout: article
---

## TL;DR
sched_ext cgroup 初始化时遗漏了 cpu.idle 状态传递，导致已配置为 idle 的 cgroup 在调度器加载后被误报为 non-idle；v2 修复后获得 Andrea Righi Reviewed-by，合入前景良好。

## 背景与问题
`scx_cgroup_init_args` 负责将 cgroup 的初始权重、带宽控制参数传递给 `ops.cgroup_init()` 回调，但缺少 `cpu.idle` 状态字段。如果一个 cgroup 在调度器加载前（或在其被 online 之前）已被设置为 idle，调度器初始化时无法感知这一状态——BPF 调度器只会在后续 `cpu.idle` 被再次写入时才能获知。这导致 sched_ext 调度器对已标记为 idle 的 cgroup 做出了错误的调度决策。

## 技术方案
在 `scx_cgroup_init_args` 结构体中新增 `idle` 字段，并在两个构建 args 的位置填充它：
- `scx_tg_online()`：处理调度器加载后创建的 cgroup
- `scx_cgroup_init()`：处理调度器加载时已存在的 cgroup

修改量很小（单文件，几行代码），属于接口完善类修复。

## 版本演进与当前进展
- **v1**（Tao Cui）：首发，描述问题并提出修复方案
- **v2**（Tao Cui）：根据社区反馈补充了 `Fixes:` 标签

当前版本：v2。Andrea Righi 在 v2 回帖给出 `Reviewed-by`，并建议添加：
```
Fixes: 347ed2d566da ("sched/ext: Implement cgroup_set_idle() callback"
```

## Maintainer 意见与讨论焦点
- **Andrea Righi**：给出 `Reviewed-by`，认为方案正确，建议补充 Fixes 标签。无分歧。
- 未见其他维护者的反对意见或额外要求。

## 合入评估
合入可能性 **high**：
- 问题真实存在（接口遗漏）
- 修复简洁明确
- 已获得 Reviewed-by
- 无争议点
- `next_action`：等待 Tejun Heo 或 sched_ext maintainer 确认并合入

## 效果评估
无性能数据；属于接口正确性修复，影响的是 sched_ext 调度器对 idle cgroup 的初始感知。

## 我可以参与的点
当前阶段暂无明显参与空间，系列已获 Reviewed-by，可持续观察合入进展。

## 参考链接
- lore thread: 未获取到
