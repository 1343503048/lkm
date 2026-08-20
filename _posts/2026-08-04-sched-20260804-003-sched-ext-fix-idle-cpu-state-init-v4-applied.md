---
subject: 'sched_ext: Fix idle CPU state initialization and validation'
id: sched-20260804-003
date: 2026-08-04
subsystem: sched
type: fix
status: merged
severity: medium
thread_root_msgid: <unknown>
lore_url: unknown
authors:
- Andrea Righi
- Kuba Piecuch
maintainers_involved:
- Tejun Heo
current_version: v4
patch_series:
- version: v4
  msgid: <unknown>
  date: 2026-08-04
  summary: 内置 idle 掩码初始化为 busy（而非把全部 online CPU 标 idle），并在 bypass 解除时由真实 idle 转换填充。Kuba
    Piecuch 给 Reviewed-by，Tejun 在 08-04 以 tag sched_ext-for-7.3 合入。
  review_outcome: 'Kuba Piecuch: Reviewed-by。Tejun Heo: APPLIED to sched_ext/for-7.3。'
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.3
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入 for-7.3，等待进入主线 7.3 周期。
contribution_opportunities: []
generated_at: '2026-08-05T00:25:00'
source_email_count: 1
related_articles:
- sched-20260803-002-sched-ext-initialize-idle-masks-as-busy
tags:
- sched_ext
- idle
title: 'sched_ext: Fix idle CPU state initialization and validation'
layout: article
---

# sched_ext: 修复 idle CPU 状态初始化（v4，已合入 for-7.3）

## TL;DR
sched_ext 内置 idle 掩码初始化为 busy 的修复（08-03-002）在 08-04 发 v4，获 Kuba Piecuch Reviewed-by，并由 Tejun 以 tag `sched_ext-for-7.3` **合入**。这是 08-03-002 的收尾，状态更新为 merged。

## 背景与问题
`reset_idle_masks()` 原把全部 online CPU 标为 idle，在收敛窗口内把 busy CPU 错误广播给调度器，导致任务被派发到实际正忙的 CPU。改为初始化为空（全部 busy），bypass 解除后由真实 idle 转换填充（详见 08-03-002）。

## 技术方案
同 08-03-002：idle 掩码初始化为空，bypass 解除时每 CPU 重调度并经 idle-to-idle re-pick 填充真实 idle 掩码。v4 含 per-node 变体的同样修正 + Kuba 的 R-b。

## 版本演进与当前进展
- 08-03：v1（08-03-002）。
- 08-04：v4，Kuba Piecuch Reviewed-by，Tejun APPLIED to sched_ext/for-7.3。

## Maintainer 意见与讨论焦点
Tejun 直接合入，Kuba R-b。无反对。

## 合入评估
已 **merged**（sched_ext/for-7.3）。这是 08-03-002 的定稿状态。

## 效果评估
正确性修复，消除 busy→idle 误报。无基准，属「正确性优先」。

## 我可以参与的点
当前已合入，可关注 7.3 周期是否出现 idle-mask 相关回归报告。

## 参考链接
- 08-03 文章：sched-20260803-002-sched-ext-initialize-idle-masks-as-busy
