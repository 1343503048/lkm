---
subject: 'sched/fair: NOHZ 负载均衡优先选择完全空闲核心（已合入 tip）'
date: 2026-08-08
series: sched-fair-nohz-fully-idle
version: v4
status: merged
tags:
- sched/fair
- nohz
- load_balance
related_articles:
- sched-20260807-016-sched-fair-nohz-fully-idle-cores
submitter: Andrea Righi (NVIDIA)
emails:
- uid: 28237
  subject: '[tip: sched/core] sched/fair: Prefer fully idle cores for NOHZ balancing'
title: sched fair nohz fully idle cores merged
layout: article
---

## 概述

Andrea Righi 的 "sched/fair: Prefer fully idle cores for NOHZ balancing" 由 tip-bot2 合并进 **tip/sched/core** 分支（Commit-ID `293f9611ae73564febc553935830074f0f300694`，AuthorDate 2026-08-04，CommitterDate 2026-08-07）。这是 8/7 系列 **016** 的收官——该 RFC/v 系列历经多轮评审（Peter Zijlstra 把关）后合入。

## 问题

`find_new_ilb()` 选择第一个空闲的 housekeeping CPU，而不考虑同一物理核的另一个 SMT 兄弟是否在运行。在 SMT 系统上，idle 负载均衡器（ILB）可能因此激活一个核的两个兄弟，即使另一个 housekeeping CPU 拥有完全空闲的物理核。多数 SMT 系统上影响可忽略，但在 NVIDIA Olympus/Vera 核心上，短暂激活原本空闲的兄弟会削减另一兄弟可用性能，且这种干扰在 ILB 结束后不会立即恢复（需兄弟空闲达资格区间，测试 Vera 系统约 10 Ki 周期），重复短唤醒可长期维持干扰。

## 修复

在选择 ILB CPU 时优先挑选整个 SMT 核都空闲的 housekeeping CPU；若无完全空闲核则保留首个空闲 CPU 作为回退（保证 NOHZ 均衡继续推进）；一旦检查过部分繁忙核，则跳过其剩余 SMT 兄弟，避免宽 SMT 系统上重复 core-idle 检查。

## 效果数据

用每 SMT 核一个 CPU 密集型任务的 ad hoc GEMM benchmark 测试，性能从约 6.2 TFLOP/s 提升（tip 通知截断于此处，但表明明显改善）。

## 状态

**已合入 tip/sched/core**。与 8/7 系列 016 为同一 patchset，本次为合入进展更新。

## 参考链接

- tip 合并通知：uid 28237（Commit `293f9611ae73564febc553935830074f0f300694`）
- 前序分析：sched-20260807-016-sched-fair-nohz-fully-idle-cores
