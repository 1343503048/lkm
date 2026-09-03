---
title: "sched/fair：对剩余 root cfs_rq 调用方改用 update_curr_eevdf()（已合入 tip/urgent）"
date: 2026-09-02
tags: [sched/fair, eevdf]
series: "update_curr_eevdf root cfs_rq callers"
type: fix
severity: low
status: merged_tip
related_articles: ["sched-20260826-011-sched-fair-update-curr-eevdf-root-cfs-rq.md", "sched-20260825-011-sched-fair-update-curr-eevdf-root-cfs-rq.md"]
lore: ""
---

## 概述

（本文为增量更新，完整背景见 related_articles 中 08-25/08-26 的文章）

EEVDF 路径中，仍有部分直接操作 `root cfs_rq` 的调用点未统一走 `update_curr_eevdf()`
的当前语义。此前提议把这些剩余调用方统一改为使用 `update_curr_eevdf()`。

**本期进展：该改动已合入 `tip/sched/urgent`**（UID 73123 `[tip: sched/urgent]`）。

## 改动内容 / 核心补丁

- `sched/fair: Use update_curr_eevdf() for the remaining root cfs_rq callers`（合入
  tip/sched/urgent）。

## 状态与讨论

- 当前状态：**merged_tip**（已进入 `tip/sched/urgent`，将随紧急修复窗口进入主线）。
- 合入可能性：**high/已合入**。属 EEVDF 内部一致性清理，风险低。

## 关联

- 08-26 011 同主题讨论（原处于 discussion/under_review，本期合入）
