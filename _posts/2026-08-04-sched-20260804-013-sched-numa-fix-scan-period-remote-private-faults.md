---
id: sched-20260804-013
date: 2026-08-04
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <unknown>
lore_url: unknown
authors:
- Hongling Zeng
maintainers_involved:
- Peter Zijlstra
- Mel Gorman
- Raghavendra K T
current_version: v2
patch_series:
- version: v1
  msgid: <unknown>
  date: 2026-08-xx
  summary: 原补丁声称『加速远程私有 fault 的扫描周期』，但 Zhan Xusheng 精确 review 指出：在私有 fault 路径 numa_improved
    阈值下，slow/fast scan 的选择逻辑使得实际并未加速，原 commit message 的理由不成立。
  review_outcome: Zhan Xusheng 给出精确 review（量化分析），作者 Hongling Zeng 承认并发布 v2，改用正确的理由（修复某具体场景下的扫描周期偏差）。这是『review
    抓出错误理由』的典型。
- version: v2
  msgid: <unknown>
  date: 2026-08-04
  summary: v2 修正 commit message 与实际行为一致，仅保留真正成立的修正（远程私有 fault 扫描周期的正确处理），删除不成立的『加速』声称。
  review_outcome: 待 maintainer 对 v2 修正理由的认可。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - v2 需 maintainer 确认修正后的理由成立
  next_action: 等待 PeterZ/Mel 对 v2 的认可。
contribution_opportunities:
- kind: review
  description: 可审阅 v2 的修正是否真的解决了远程私有 fault 扫描周期偏差（用 trace 验证 fast/slow scan 选择），回帖验证数据补强（作者原
    v1 理由被 review 推翻，v2 需新实证）。
generated_at: '2026-08-05T00:25:00'
source_email_count: 1
related_articles: []
tags:
- numa
- scan_period
- sched_debug
title: 'sched/numa: Fix scan period for remote private faults'
layout: article
---

# sched/numa: 修正远程私有 fault 扫描周期（v2，review 抓出错误理由）

## TL;DR
Hongling Zeng 的「加速远程私有 fault 扫描周期」补丁被 Zhan Xusheng 精确 review 指出理由不成立（实际未加速），作者承认并发布 v2 改用正确的修正理由。这是「review 抓出错误 commit message」的典型案例，合入可能性 high（v2）。

## 背景与问题
NUMA 扫描周期（task scan period）在远程私有 fault 场景下的选择逻辑依赖 `numa_improved` 阈值切换 slow/fast scan。原补丁声称能「加速」该场景扫描，但 Zhan Xusheng 通过精确量化分析指出：在私有 fault 路径的阈值下，slow/fast 的选择使得实际扫描速率并未如声称那样提升，原 commit message 的理由与代码行为不符。

## 技术方案
- v1：声称加速远程私有 fault 扫描（理由被推翻）。
- v2：删除不成立的「加速」声称，仅保留真正成立的修正——修复远程私有 fault 场景下的扫描周期偏差（具体使 fast/slow scan 选择正确反映该场景），commit message 与实际行为一致。

## 版本演进与当前进展
- v1：理由被 Zhan Xusheng 精确 review 推翻。
- v2（2026-08-04）：作者承认并修正理由。

## Maintainer 意见与讨论焦点
Zhan Xusheng：给出量化 review，明确指出原理由不成立。作者 Hongling Zeng 承认。这是协作质量的良好示范—— reviewer 用数据纠正了作者的叙事。

## 合入评估
合入可能性 high。v2 已修正理由，无架构争议，属 numa 扫描逻辑的小修正。

## 效果评估
v1 的「加速」声称**无实证且被 review 推翻**；v2 转为正确性修正（扫描周期偏差），作者未附新 benchmark。恰是「author 缺数据被 review 抓出」的明确案例——可补 trace 验证。

## 我可以参与的点
- 用 trace 验证 v2 修正后远程私有 fault 的 fast/slow scan 选择是否正确，回帖验证数据（v2 修正理由后最缺的就是新实证）。

## 参考链接
- lore thread: 未获取到
