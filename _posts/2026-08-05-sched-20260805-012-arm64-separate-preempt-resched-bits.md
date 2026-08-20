---
subject: 'arm64: sched/preempt: Enable HAS_SEPARATE_PREEMPT_RESCHED_BITS'
id: sched-20260805-012
date: '2026-08-05'
title: 'arm64: sched/preempt: Enable HAS_SEPARATE_PREEMPT_RESCHED_BITS'
series: 'arm64: Separate resched bits for need_resched and preempt'
type: feature
status: under_review
severity: none
merge_likelihood: medium
tags:
- preempt
- arm64
- topology
authors:
- Boqun Feng <boqun.feng@gmail.com>
- Mark Rutland <mark.rutland@arm.com>
reviewers:
- Mark Rutland <mark.rutland@arm.com>
- Catalin Marinas <catalin.marinas@arm.com>
related_articles:
- sched-20260803-007
emails:
- uid-20432@qq-imap
- uid-20413@qq-imap
- uid-20423@qq-imap
layout: article
---

# arm64/sched/preempt: 分离 need_resched 与 preempt 的 resched 位（v4）

## 摘要

Boqun Feng 的系列（v4）为 arm64 引入**两套独立的 resched 指示位**：一套用于 `TIF_NEED_RESCHED`（普通的「该重新调度」），另一套用于 `TIF_NEED_RESCHED_LAZY` / preempt 相关的延迟重调度。当前 arm64 用单个 `TIF_NEED_RESCHED` 位同时承载「立即 resched」与「lazy/preempt 被禁用时延缓的 resched」，导致在某些抢占路径下需要额外的标志位或软件模拟。

本日要点（多个 Re，v4）：
- **Boqun 的 v4（20432/20413/20423 等）**：把 resched 触发从「单一 `TIF_NEED_RESCHED` + 软件判断」改为「两个独立线程标志位，由 entry 路径分别检查」，使 `PREEMPT_LAZY` / `PREEMPT_DYNAMIC` 在 arm64 上的语义与 x86 对齐。
- **Mark 的 review（20413 等）**：关注两个位在 `exit_to_user_mode` / `ret_to_user` 的检查顺序——必须保证「lazy 位只在真正可安全抢占时才消费」，否则会在持有 `rcu_read_lock` 等不可抢占区间误触发 resched。建议复用 x86 已有的 `resched_curr()` 分层逻辑。
- **Catalin 的参与**：确认与 arm64 的 `TIF_` 位号分配不冲突，并建议把位定义集中到 `asm/thread_info.h` 的注释里说明两套位的语义。

## 技术细节

现状：arm64 的 `TIF_NEED_RESCHED` 被 `resched_curr()` 与 preempt 逻辑共用，LAZY 抢占需要额外的 `need_resched_lazy()` 软件判断。

v4 方案（示意）：
```
TIF_NEED_RESCHED     // 立即：exit_to_user_mode 一定检查
TIF_NEED_RESCHED_LAZY // 延迟：仅在可抢占上下文（非 atomic/rcu 临界）消费
```
entry 路径：
```
if (test_thread_flag(TIF_NEED_RESCHED))       schedule();
else if (test_thread_flag(TIF_NEED_RESCHED_LAZY) && !preempt_count() && !rcu_preempt)
        schedule();
```

争议点：
- 两个位在「同一时刻都被置位」时的优先级与去重，避免双 schedule。
- `TIF_` 位号在 arm64 `thread_info` 里是否还有富余（Boqun 已确认有）。

## 影响与风险

- 影响面：arm64 的抢占/resched 路径，影响 `PREEMPT_LAZY` / `PREEMPT_DYNAMIC` 在 arm64 的正确性与性能。
- 风险：中。改动在架构关键路径，需多平台 boot + preempt 压力测试；但逻辑对齐 x86 已有实现，风险可控。
- 收益：让 arm64 的 lazy 抢占语义与 x86 一致，减少 PREEMPT_* 系列的架构分支维护成本。

## 评价

与 08-03-007（同系列前序）衔接的 v4 迭代，reviewer（Mark、Catalin）已深度介入。方向正确、向 x86 对齐，合入可能性中等—高。建议通过 arm64 的 preempt 压力测试（如 `rt-tests` cyclictest）后再进主线。
