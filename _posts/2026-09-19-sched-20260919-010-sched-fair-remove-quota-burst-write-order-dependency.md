---
id: sched-20260919-010
date: '2026-09-19'
subject: 'sched/fair: remove quota/burst write-order dependency'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260911092258.660771-1-liuzhe1@kylinos.cn>
lore_url: https://lore.kernel.org/all/20260911092258.660771-2-liuzhe1@kylinos.cn/
authors:
- Zhe Liu
maintainers_involved:
- Ben Segall
current_version: v3
patch_series:
- version: v3
  msgid: <20260911092258.660771-1-liuzhe1@kylinos.cn>
  date: '2026-09-11'
  summary: 移除 quota/burst 状态更新的写顺序依赖
  review_outcome: Ben Segall 本日给 1/3 Reviewed-by
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 维护者收取
contribution_opportunities: []
generated_at: '2026-09-20T09:00:00'
source_email_count: 1
related_articles:
- sched-20260911-014
tags:
- cfs
- cgroup
title: 'sched/fair: remove quota/burst write-order dependency'
layout: article
---

## TL;DR
增量更新：Zhe Liu 的 fair quota/burst 写顺序依赖移除系列（v3）本日获 CFS 带宽维护者 Ben Segall 的 Reviewed-by——他认为"依赖特定编辑顺序的状态校验既烦人又价值不高"。系列等待收取。

## 背景与问题
背景见 sched-20260911-014：cgroup CFS 带宽（quota/burst）的状态更新要求按特定顺序修改多个字段，否则会触发"状态校验"告警；这套顺序依赖烦琐且易错。系列旨在移除 quota/burst 的写顺序依赖。

## 技术方案
见 sched-20260911-014：重构 quota/burst 状态更新，使其不再依赖写的先后顺序。本日无方案变更。

## 版本演进与当前进展
- v3（2026-09-11，`<20260911092258.660771-1-liuzhe1@kylinos.cn>`）：3-patch 系列（见 sched-20260911-014）。
- 本日 Ben Segall（`<xm2633v6w83y.fsf@google.com>`）对 1/3 给出 Reviewed-by。

## Maintainer 意见与讨论焦点
- **Ben Segall（CFS 带宽维护者）**：Reviewed-by；评价"所有逼着按特定顺序编辑的状态校验都烦人、且在我看来价值不高"。
- 分歧/未决：无。

## 合入评估
likelihood=high。带宽维护者 Ben Segall Reviewed-by、无反对意见，等待收取。blocking_issues：暂无（需确认全系列 3 patch 均已覆盖 review）。next_action：维护者收取。

## 效果评估
本日无新增测试数据；该系列为正确性/健壮性改动（消除写顺序依赖），无性能数字。

## 我可以参与的点
当前阶段暂无明显参与空间（维护者已 Reviewed-by）；可观察后续是否还需对 quota/burst 其他状态更新做同样的去顺序化。

## 参考链接
- lore（v3 1/3 patch）: https://lore.kernel.org/all/20260911092258.660771-2-liuzhe1@kylinos.cn/
- lore（Ben Segall Reviewed-by）: https://lore.kernel.org/all/xm2633v6w83y.fsf@google.com/
