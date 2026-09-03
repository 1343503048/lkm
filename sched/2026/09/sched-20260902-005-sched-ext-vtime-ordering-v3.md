---
title: "sched_ext：文档化并强制 vtime 排序约束（v3）"
date: 2026-09-02
tags: [sched_ext, documentation]
series: "sched ext vtime ordering constraints"
type: fix
severity: low
status: under_review
lore: ""
---

## 概述

sched_ext 的 dsq（调度队列）按虚拟时间（vtime）排序，其中 `dsq_vtime` 依赖
rolling-cursor 的取序要求；`scx_flatcg` 的 `cgv_node_less()` 在 vtime 回绕（wraparound）
时也存在比较错误风险。本期 v3 把这两点文档化并加强制/修复。

## 改动内容 / 核心补丁

系列 `sched_ext: document and enforce vtime ordering constraints`（v3，UID 72766 0/2
封面）：
- 1/2 `sched_ext: document the rolling-cursor requirement for dsq_vtime`（72767）
- 2/2 `sched_ext/scx_flatcg: make cgv_node_less() wraparound-safe`（72781）
- 演进：v2（UID 72288 1/2、72291 2/2）→ v3；Re: 72648（v3 2/2）、73048（v3 0/2）。

## 状态与讨论

- 当前状态：**under_review**（v3）。
- 合入可能性 medium/high；文档 + 回绕安全的明确修复。
- 与 004（NMI 拒绝）、006（NULL deref）同为当日 sched_ext 集群。

## 关联

- 004 sched_ext：拒绝 NMI 调用会拿锁 kfuncs
- 006 sched_ext：修复 select_cpu_and 空指针解引用
