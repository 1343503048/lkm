---
id: sched-20260826-006
date: 2026-08-26
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: unknown
lore_url: unknown
authors:
- Huacai Chen
maintainers_involved:
- Zhongqiu Han
current_version: v1
patch_series:
- version: v1
  msgid: unknown
  date: 2026-08-26
  summary: 5 篇 Loongson3 cpufreq 驱动改进：依赖修复、SMC 参数、per-node mutex、全局 CPU ID、MMIO
  review_outcome: Zhongqiu Han 详细 review，作者已回应大部分意见
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 需确认 MACH_LOONGSON64 架构依赖
  next_action: 作者修正后发 v2
contribution_opportunities: []
generated_at: '2026-08-27T01:20:00'
source_email_count: 6
related_articles: []
tags:
- cpufreq
title: 'cpufreq: loongson3: driver improvements'
layout: article
---

## TL;DR

Huacai Chen 提交了 5 篇 Loongson3 cpufreq 驱动改进补丁：添加 `MACH_LOONGSON64` 依赖、调整 SMC 参数宽度、将 per-package mutex 替换为 per-node、使用全局物理 CPU ID 进行频率操作、将 IOCSR 读写替换为 MMIO。Zhongqiu Han (Qualcomm) 给出了详细 review。所有补丁标记了 `Cc: stable@vger.kernel.org`。

## 背景与问题

Loongson3 cpufreq 驱动存在以下问题：
1. 32 位 Loongson 机器没有 SMC 和 FreqCtrl 寄存器，但驱动仍可被选中
2. 服务器产品（如 Loongson-3D6000/3E6000）的全局物理 CPU ID 可以不连续，但驱动使用包内连续 core ID
3. IOCSR 读写只能在当前节点执行，无法跨节点操作
4. per-package mutex 在多节点场景下粒度不够

## 技术方案

1. **Patch 1/5**：添加 `depends on MACH_LOONGSON64`，排除 32 位机器
2. **Patch 2/5**：调整 `smc_message` 中 `id` 和 `val` 的宽度
3. **Patch 3/5**：将 per-package mutex 替换为 per-node mutex
4. **Patch 4/5**：使用 `cpu_logical_map(cpu)` 获取全局物理 CPU ID 进行频率 get/set 操作
5. **Patch 5/5**：将 IOCSR 读写替换为 MMIO，支持跨节点操作

## 版本演进与当前进展

v1 刚发出。Zhongqiu Han 给出了详细 review，包括：
- 建议添加 `Fixes:` 标签（Patch 1/5）
- 指出 `MACH_LOONGSON64` 在 loongarch 和 mips 两个架构中都存在，需要确认依赖的是哪个
- 对 Patch 4/5 的 `cpu_logical_map()` 使用提出了跨节点操作的疑问

Huacai Chen 已回应大部分 review 意见，确认会添加 Fixes 标签并修正 typo。

## Maintainer 意见与讨论焦点

Zhongqiu Han 的 review 详细且建设性，主要关注：
- 跨架构兼容性（loongarch vs mips 的 `MACH_LOONGSON64`）
- Fixes 标签的正确性
- 代码风格和改进建议

## 合入评估

- **likelihood**: high（作者已积极回应 review 意见，补丁标记了 stable）
- **blocking_issues**: 需要确认 MACH_LOONGSON64 的架构依赖
- **next_action**: 作者修正后发 v2

## 效果评估

暂无性能数据。改进主要面向正确性和跨节点支持。

## 我可以参与的点

当前阶段暂无明显参与空间，等待 v2 发布。

## 参考链接

- lore thread: 未获取到
