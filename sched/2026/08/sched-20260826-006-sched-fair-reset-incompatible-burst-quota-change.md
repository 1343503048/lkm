---
title: "sched/fair：CFS 带宽配额变更时重置不兼容的 burst"
date: 2026-08-26
tags: [sched/fair]
series: "reset incompatible burst on quota change"
type: fix
severity: low
status: under_review
lore: ""
---

## 概述

CFS 带宽控制（cpu.cfs_quota_us / cpu.cfs_period_us / cpu.cfs_burst_us）中，当任务的
quota 发生变更时，原有的 burst 设置可能与新 quota 不兼容（如 burst 超过新的 quota
上限，或在新配额下失去意义），导致带宽记账异常或超限行为不符合预期。本期（Re: UID
58377）提出在 quota 变更时重置不兼容的 burst。

## 改动内容 / 核心补丁

- 在 CFS 带宽配额更新路径中，检测并重置与原 quota 不兼容的 burst 状态，使其回到
  与新配额一致的合法区间。
- 目标：避免配额变更后 burst 语义混乱。

## 状态与讨论

- 当前状态：**under_review**（以 Re: 形式推进）。
- 合入概率 medium；影响 cgroup cpu 带宽控制的健壮性。

## 关联

- 003 sched/cpufreq：tickless idle 前重估频率（同为 fair 类参数修正）
