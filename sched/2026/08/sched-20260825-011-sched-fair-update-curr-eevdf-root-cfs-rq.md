---
title: "sched/fair：对剩余 root cfs_rq 调用方改用 update_curr_eevdf()"
date: 2026-08-25
tags: [sched/fair, eevdf]
series: "update_curr_eevdf root cfs_rq callers"
type: fix
severity: low
status: discussion
lore: ""
---

## 概述

EEVDF 路径中，仍有部分直接操作 `root cfs_rq` 的调用点未统一走 `update_curr_eevdf()`
的当前语义。本期讨论（Re: UID 55669 线程，主题为 `sched/fair: Use update_curr_eevdf()
for the remaining root cfs_rq callers`）提议把这些剩余调用方统一改为使用
`update_curr_eevdf()`，以收敛 EEVDF 的当前运行实体更新逻辑。

## 改动内容 / 核心补丁

- 识别并替换剩余的 root cfs_rq 调用点，使其与 `update_curr_eevdf()` 保持一致。
- 属于 EEVDF 内部一致性的持续清理（与 08-24 的「复用 ENQUEUE_DELAYED / 避免重算
  curr」同源方向）。

## 状态与讨论

- 当前状态：**discussion / under_review**（以 Re: 形式推进，未见独立 v1 封面）。
- 合入概率 medium；与 009（guest boot hang 涉及 detach/dequeue）无直接关联，但同属
  sched/fair 当期活跃话题。

## 关联

- 009 [Question] Combine detach into dequeue 导致 guest 启动挂起
- （前日）011 sched/fair：复用 ENQUEUE_DELAYED 避免重算 curr
