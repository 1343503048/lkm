# kcov: suppress timer and scheduler coverage leaks

## TL;DR

Karl Mehltretter 的 kcov 系列已推进到 v2（0/6），用可嵌套的 `KCOV_PAUSED` 位抑制定时器与调度路径的
覆盖污染。kcov 维护者 Alexander Potapenko 9/2 回了封面，调度侧尚未表态。跟调度器开发相关但优先级不高。

## 背景与问题

kcov（内核覆盖率工具）在调度器与定时器相关路径上会产生「覆盖泄漏」——即不应被采集的
上下文（如调度器内部、定时器软中断）被计入覆盖率，污染 fuzzing/覆盖率结果。本期
（v2，UID 73544 `0/6` Re:）提出抑制这类泄漏。

## 技术方案

- `[PATCH v2 0/6] kcov: Suppress timer and scheduler coverage leaks`：在定时器与调度器
  相关路径上抑制 kcov 的覆盖采集，使覆盖率聚焦于被测逻辑。

## 版本演进与当前进展

- 当前状态：**under_review**（v2，6 补丁系列）。
- 合入可能性 medium；属工具/可观测性改进，与调度器路径有交集。

## Maintainer 意见与讨论焦点

- 当天唯一实质回帖来自 kcov 维护者 Alexander Potapenko（73513，17:48），回复的是 Karl 9/1 的消息，
  而 Karl 那条又引用 8/11 的封面："Add a nestable KCOV_PAUSED bit and a kcov_…"（缓存中截断）。
- Peter Zijlstra 在该线程参与者列表中，但缓存内看不到他说了什么，无法判断调度侧是提了意见还是只是被 cc。
- 无 NAK。争议点是「把调度器/定时器路径从覆盖率里挖掉」是否可接受。

## 合入评估

**中**。kcov 侧由 Potapenko 把关即可，但被改的是 timer 与 sched 路径，还需要调度侧认账；调度侧当天的
意见正文缺失。另外系列从 v1 的 0/5 扩到 v2 的 0/6，说明评审要求过新增内容。

## 效果评估

无数据。无人给出「抑制前后覆盖率噪声比例」或 fuzzing 效率的对比——对一个覆盖率工具来说这是明显缺口。

## 我可以参与的点

- 这是调度开发者可以直接补位的地方：从 fuzzing 有效性角度质疑「抑制调度器覆盖」会让 syzkaller 少看到
  多少 sched 代码，值得给一个量化意见。
- review v2 中抑制点的具体位置：判断被 KCOV_PAUSED 包住的区间是否恰好只包含不该测的部分，别把真正的
  调度逻辑一起屏蔽。
- 若有人问，v2 比 v1 多的那 1 个补丁是什么——当日缓存只能看到数量变化，看不到内容。

## 参考链接

- 002 sched/core 清理（同属调度核心活跃改动）

---
id: sched-20260902-016
date: '2026-09-02'
subject: 'kcov: suppress timer and scheduler coverage leaks'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: null
lore_url: null
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: null
authors:
- Peter Zijlstra
- Karl Mehltretter
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: medium
  blocking_issues:
  - "调度侧（Peter Zijlstra）意见正文缺失，是否认可未知"
  - "无抑制前后覆盖率噪声或 fuzzing 效率的量化数据"
  - "系列从 0/5 扩到 0/6，新增内容未在当日缓存中体现"
  next_action: "从 fuzzing 有效性角度回 v2，并核对 KCOV_PAUSED 抑制区间是否过宽"
contribution_opportunities:
- "量化 KCOV_PAUSED 抑制调度器/定时器路径后会损失多少 sched 覆盖率，从调度侧给意见"
- "review v2 中抑制点的具体区间，确认未连带屏蔽真实调度逻辑"
- "确认 Peter Zijlstra 在该线程的实际立场（缓存缺正文）"
source_email_count: 2
related_articles: []
tags:
- sched/core
- documentation
---
