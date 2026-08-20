---
id: sched-20260729-007
date: 2026-07-29
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260729144451.38286-1-atomlin@atomlin.com>
lore_url: https://lore.kernel.org/lkml/20260729144451.38286-1-atomlin@atomlin.com
authors:
- Aaron Tomlin
maintainers_involved: []
current_version: v4
patch_series:
- version: v3
  msgid: unknown
  date: 2026-07-26
  summary: 三 patch 结构定型：空表修复、单位自适应、--histogram/--hist-mode/--time；详见 sched-20260726-003
  review_outcome: review 意见指向 pipe mode 下 header 属性丢失与空表问题
- version: v4
  msgid: <20260729144451.38286-1-atomlin@atomlin.com>
  date: 2026-07-29
  summary: 注册 .attr/.tracing_data/.build_id 回调支持 pipe mode；post-processing pipe check
    防空表；map_switch_event() NULL guard；列宽格式对齐修正
  review_outcome: v4 刚发出，暂无 review 意见
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - v4 尚无 reviewer 表态，需要 perf tools 维护者（Arnaldo/Namhyung）确认 pipe mode 修复方案
  next_action: 等待 perf tools 维护者对 v4 的 review；作者已连续快速迭代回应意见
contribution_opportunities:
- kind: testing
  description: 在本地用 'perf sched record' + 'perf sched latency -i -'（pipe mode）验证 v4
    的空表修复与 histogram 输出，把测试结果回帖
- kind: review
  description: patch 2 的单位自适应改变了输出格式，可评估对既有解析脚本的兼容性影响并回帖
generated_at: '2026-07-30T11:20:00'
source_email_count: 4
related_articles:
- sched-20260726-003
tags:
- sched_debug
- perf
title: 'perf sched latency: Add histogram and time interval options'
layout: article
---

## TL;DR
Aaron Tomlin 的 perf sched latency 改进系列更新到 v4（07-26 的 v3 已收录为 sched-20260726-003，本篇为增量分析）：v4 集中解决 pipe mode 支持问题并加固 NULL 防护。工具类改动、迭代活跃、意见都被逐条回应，合入可能性高。

## 背景与问题
`perf sched latency` 存在三类问题：perf.data 缺少 tracepoint 事件时不报错而是打印空表和全零统计（返回 0）；所有时延列硬编码为 ms，微秒或秒级数据难读；缺乏直方图可视化和时间段过滤能力。详细背景见 sched-20260726-003，此处不重复。

## 技术方案
三 patch 结构与 v3 相同：
1. 空表修复——`perf_session__has_traces()` 失败时不再静默成功；
2. Runtime/Avg delay/Max delay 列按数值量级自动选择 ns/us/ms/s 单位；
3. 新增 `--histogram/-H`（ASCII 柱状图）、`--hist-mode`（log 对数桶 / linear 100us 等宽桶）、`--time`（[start,stop] 时间段过滤）。

v4 的增量改动（较 v3）：
- 在 cmd_sched() 的 perf_tool__init 配置中注册 `.attr`、`.tracing_data`、`.build_id` 回调——缺失这些回调时 pipe mode（`perf sched latency -i -`）会整体丢弃 header 属性，导致 session->evlist 里 tracepoint 无法填充；
- 引入显式的 post-processing pipe check，确保 pipe 流无 trace 样本时正确中止，不再输出多余空表；
- map_switch_event() 中对 thread__get_runtime() 加 NULL 检查，防内存分配失败下的空指针解引用；
- 修正格式化字符串使各行与表头列宽逐字符对齐。

## 版本演进与当前进展
v1→v3 演进记录在 sched-20260726-003。v4（2026-07-29）为回应 pipe mode 相关意见的迭代版本，发出当天尚无回复。作者三天内从 v3 迭代到 v4，响应速度快。

## Maintainer 意见与讨论焦点
v4 暂无新的 review 意见。从 v4 changelog 看，前一轮意见集中在 pipe mode 的正确性（header 回调缺失、空表输出），均已在 v4 处理；未见 NAK 或方向性反对。

## 合入评估
likelihood: high。理由：改动限于 perf 工具侧不触及内核核心、每版都逐条回应意见、无方向性争议。剩余不确定性是 perf tools 维护者对 v4 pipe mode 修复方式的最终确认。卡点仅为 review 带宽。

## 效果评估
该系列为工具功能改进，无性能数据语义。v4 未附带新的输出示例（v3 曾给出直方图效果示例，见 sched-20260726-003）。

## 我可以参与的点
- 实测 pipe mode：`perf sched record ... | perf sched latency -i -` 在 v4 打补丁前后对比行为，把 Tested-by 结果回帖，这类工具 patch 的实测反馈对合入很有帮助。
- patch 2 的单位自适应会改变输出文本格式，若有依赖 `perf sched latency` 输出的解析脚本，可评估兼容性影响并回帖提醒。

## 参考链接
- lore thread: https://lore.kernel.org/lkml/20260729144451.38286-1-atomlin@atomlin.com
- 前序分析: sched-20260726-003（v3）
- tip-bot commit: 未获取到
