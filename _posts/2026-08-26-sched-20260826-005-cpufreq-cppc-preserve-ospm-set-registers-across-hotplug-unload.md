---
id: sched-20260826-005
date: 2026-08-26
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: unknown
lore_url: unknown
authors:
- Sumit Gupta
maintainers_involved:
- Rafael J. Wysocki
- Christian Loehle
current_version: v4
patch_series:
- version: v4
  msgid: unknown
  date: 2026-08-26
  summary: 4 篇补丁，添加 online/offline 回调和 save/restore 机制保持 CPPC 寄存器值
  review_outcome: 等待 Rafael 合入
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 Rafael 合入
contribution_opportunities: []
generated_at: '2026-08-27T01:18:00'
source_email_count: 2
related_articles: []
tags:
- cpufreq
title: 'cpufreq: CPPC: Preserve OSPM-set registers across hotplug and unload'
layout: article
---

## TL;DR

Sumit Gupta 提交了 v4 版本的 4 篇补丁，解决 CPPC cpufreq 驱动在 CPU hotplug 和驱动卸载时丢失 OSPM 设置的寄存器值（EPP、Autonomous Activity Window、Autonomous Selection）的问题。方案添加 `online()/offline()` 回调保持 policy 存活，并引入表驱动的 save/restore 机制。Rafael J. Wysocki 和 Christian Loehle 参与了 review。v4 正在等待合入。

## 背景与问题

CPPC cpufreq 驱动在最后一个 CPU 下线时会拆除 policy，重新上线时重建并重新读取 CPPC capabilities。这导致以下问题：
- CPU hotplug 或 suspend/resume 期间，平台可能重置已写入的寄存器值
- 驱动卸载时，驱动写入的值留在寄存器中而非恢复为驱动前的状态

## 技术方案

1. **Patch 1**：添加 `online()/offline()` 回调，使 core 在 CPU hotplug 期间保持 policy 存活
2. **Patch 2**：使 autonomous selection register helpers 接受 `u64` 参数
3. **Patch 3**：添加表驱动机制，在 `init()` 时捕获每个寄存器的固件值，从 `offline()` 恢复，从 `online()` 重新应用 OSPM 设置的值
4. **Patch 4**：将相同的 save/restore 扩展到系统 suspend/resume

## 版本演进与当前进展

- v4 已提交，Sumit 在 8/26 发了 gentle reminder 请求考虑合入
- Christian Loehle 和 Rafael J. Wysocki 参与了之前版本的 review

## Maintainer 意见与讨论焦点

Rafael J. Wysocki 作为 cpufreq 子系统维护者，正在被请求考虑合入。Christian Loehle 之前参与了 review。

## 合入评估

- **likelihood**: high（v4 已提交，维护者正在被请求合入，无明显反对意见）
- **blocking_issues**: 无已知阻塞
- **next_action**: 等待 Rafael 合入

## 效果评估

暂无性能数据，主要解决功能正确性问题。

## 我可以参与的点

当前阶段暂无明显参与空间，可持续观察合入进展。

## 参考链接

- lore thread: 未获取到
