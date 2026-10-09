---
id: sched-20261009-002
date: '2026-10-09'
subject: 'cpufreq: qcom-cpufreq-hw: fix device node refcount leak in phandle parsing'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <20261008172442.2725544-1-vulab@iscas.ac.cn>
lore_url: https://lore.kernel.org/all/20261008172442.2725544-1-vulab@iscas.ac.cn/
authors:
- Haotian Zhang
maintainers_involved:
- Viresh Kumar
current_version: v1
patch_series:
- version: v1
  msgid: <20261008172442.2725544-1-vulab@iscas.ac.cn>
  date: '2026-10-09'
  summary: 在两处 phandle 解析点补 of_node_put(args.np)
  review_outcome: Viresh Kumar 应用（Applied. Thanks.）
upstream_commit: null
fixes_commit: 2849dd8bc72b
merged_branch: linux-pm/cpufreq
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 无，等 linux-pm pull request
contribution_opportunities: []
generated_at: '2026-10-10T01:30:00'
source_email_count: 2
related_articles: []
tags:
- cpufreq
- arm64
title: 'cpufreq: qcom-cpufreq-hw: fix device node refcount leak in phandle parsing'
layout: article
---

## TL;DR
Haotian Zhang（ISCAS）修复 qcom-cpufreq-hw 里 `of_parse_phandle_with_args()` 返回的 provider 节点引用从未被 `of_node_put()` 释放、每次成功调用都泄漏一个引用（`qcom_get_related_cpus()` 每个 present CPU 泄漏一次）的 bug。维护者 Viresh Kumar 当日即回复「Applied. Thanks.」，补丁已进入 cpufreq 维护树。

## 背景与问题
`of_parse_phandle_with_args()` 会把对 provider 节点的引用转移到 `out_args->np`，调用方有责任用 `of_node_put()` 释放。但 `qcom_get_related_cpus()` 与 `qcom_cpufreq_hw_cpu_init()` 都只 `of_node_put(cpu_np)`——而 `cpu_np` 是另一条路径 `of_cpu_device_node_get()` 拿到的不同节点。于是 `args.np` 的引用每次成功调用都泄漏，`qcom_get_related_cpus()` 按每个 present CPU 泄漏一次。带 `Fixes: 2849dd8bc72b`（"cpufreq: qcom-hw: Add support for QCOM cpufreq HW driver"）。

## 技术方案
在两处调用点读出解析到的 index 之后，补 `of_node_put(args.np)` 释放 provider 节点引用。`drivers/cpufreq/qcom-cpufreq-hw.c` 共 +3 行。补丁署名 `Assisted-by: DeepSeek-V4.1-Flash`（LLM 辅助）。

## 版本演进与当前进展
v1 首发（`<20261008172442.2725544-1-vulab@iscas.ac.cn>`）。维护者 Viresh Kumar 当日即回复「Applied. Thanks.」（`<ashueyfHcwGHziVG@vireshk-B250M-D3H>`），已应用进 cpufreq 维护树（linux-pm）。

## Maintainer 意见与讨论焦点
- **Viresh Kumar（cpufreq 维护者）**：直接「Applied. Thanks.」，无异议、无修改要求。干净的小修复，无争议。

## 合入评估
*likelihood=merged*。维护者已应用，无需再推进。*next_action*：无，等待合入下一轮 linux-pm pull request。

## 效果评估
纯资源泄漏修复，无性能数据。泄漏量级为「每次 `qcom_get_related_cpus()` 调用每个 present CPU 一次」的 of_node 引用，属长期累积的内存泄漏类问题，无运行时可见症状描述。

## 我可以参与的点
当前阶段暂无明显参与空间，补丁已被维护者应用。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261008172442.2725544-1-vulab@iscas.ac.cn/
- Viresh Kumar 应用回复: https://lore.kernel.org/all/ashueyfHcwGHziVG@vireshk-B250M-D3H/
