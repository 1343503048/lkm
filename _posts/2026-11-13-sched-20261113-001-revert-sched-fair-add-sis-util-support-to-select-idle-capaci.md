---
id: sched-20261113-001
subject: 'Revert "sched/fair: Add SIS_UTIL support to select_idle_capacity()"'
date: 2026-11-13
subsystem: sched
type: regression
status: under_review
severity: high
thread_root_msgid: <20261113153157.2495664-1-usama.arif@linux.dev>
lore_url: https://lore.kernel.org/all/20261113153157.2495664-1-usama.arif@linux.dev/
authors:
- Usama Arif
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261113153157.2495664-1-usama.arif@linux.dev>
  date: 2026-11-13
  summary: 回退 61ea17a63719，恢复 select_idle_capacity() 对 allowed domain 的全量搜索
  review_outcome: 刚发出，暂无 review 意见
upstream_commit: null
fixes_commit: 61ea17a63719
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: 等待 sched 维护者确认 revert 方案（或改为修正扫描预算计算）
contribution_opportunities:
- kind: testing
  description: 在其它非对称平台上复现该回归或验证 revert 后的延迟恢复，回帖补充数据
- kind: review
  description: 评估 revert（恢复全量扫描）与修正扫描预算两条路线的扫描成本取舍
generated_at: '2026-11-14T01:30:00'
source_email_count: 1
related_articles: []
tags:
- cfs
- load_balance
- regression
title: 'Revert "sched/fair: Add SIS_UTIL support to select_idle_capacity()"'
layout: article
---

## TL;DR
Usama Arif 提交 revert 补丁，回退 `61ea17a63719`（给 `select_idle_capacity()` 套用 SIS_UTIL 扫描预算）：该提交在非对称路径下因零扫描预算而跳过 allowed domain 的全量搜索，导致唤醒型延迟敏感负载的分钟级 p50 延迟从 129ms 恶化到 223ms。补丁带完整 benchmark 数据与 `Fixes:` 标签，并 Cc stable，属于明确的回归修复，但当日尚未有维护者表态。

## 背景与问题
`61ea17a63719`（"sched/fair: Add SIS_UTIL support to select_idle_capacity()"）把 SIS_UTIL 的扫描预算套用到 `select_idle_capacity()`。`select_idle_sibling()` 的早期检查会先看几个特定候选（target、previous、recently used CPU）；若都没选中，非对称路径会调用 `select_idle_capacity()` 搜索 allowed domain。但启用 SIS_UTIL 后，扫描预算为 0 时会让它在搜索之前就返回 -1，调用方随即返回所选 target，即使 domain 里还有未检查的 idle 且适配任务的 CPU。

扫描预算由聚合的 CFS utilization 推导。任务唤醒时，高聚合 utilization 可以与 idle CPU 并存——这正是问题所在。

作者在 72 核 NVIDIA Grace arm64 服务器上复现：单个 LLC 内 1013-1024 的微小 capacity 差异即触发非对称选择，reference 与受影响内核都观测到零扫描 hint；reference 内核忽略 hint 仍搜索 domain，受影响内核则直接返回。延迟敏感的唤醒密集型生产负载的分钟级 p50 延迟平均值：reference 129ms，受影响 223ms。

## 技术方案
直接 revert 该提交，恢复对 allowed domain 的搜索，同时保留 capacity、uclamp 与 SMT 选择规则及其早退逻辑。副作用是：domain 中无合适 idle CPU 时可能再次需要全量扫描，扫描 CPU 成本可能回升。

补丁附带关/开 SIS_UTIL 的对照数据：关闭后 worker 主线程的聚合非自愿上下文切换率从 71.6k/s 降到 13.3k/s，重新开启又升到 73.7k/s；五分钟关闭窗口内每请求内核 CPU 时间下降 10.9%，可用分钟级 p50 样本均值 149ms（试运行前为 241ms）。

## 版本演进与当前进展
v1 刚发出，尚无 review 意见。

## Maintainer 意见与讨论焦点
当日无维护者回帖。补丁带 `Reported-by: Arnav Aghav <aghav@meta.com>`、`Fixes: 61ea17a63719` 并 Cc stable，证据充分；后续需等 sched 维护者（Peter Zijlstra / Vincent Guittot / Ingo Molnar）确认 revert 而非修复扫描逻辑。

## 合入评估
属回归修复且证据链完整（真实硬件 + 生产负载 + 对照实验），合入概率偏高。唯一变数是维护者可能倾向"修 `select_idle_capacity()` 的扫描预算计算"而非整体 revert；暂无阻塞项，等待维护者表态。

## 效果评估
正文给出具体数字：分钟级 p50 延迟 129ms→223ms（+72.9%）；关闭 SIS_UTIL 后非自愿上下文切换率 71.6k/s→13.3k/s；每请求内核 CPU 时间 -10.9%。均为实测数据，非主观判断。

## 我可以参与的点
- **testing**：在其它非对称（big.LITTLE / Intel hybrid / AMD heterogeneous）平台上复现 `61ea17a63719` 引入的 `select_idle_capacity()` 跳过搜索问题，或验证 revert 后延迟恢复，回帖补充数据点。
- **review**：评估"恢复全量扫描"与"修正扫描预算计算"两条路线在扫描 CPU 成本上的取舍。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261113153157.2495664-1-usama.arif@linux.dev/
