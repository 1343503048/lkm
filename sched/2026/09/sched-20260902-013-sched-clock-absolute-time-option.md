---
title: "sched_clock：新增选项以对抗硬件时钟复位使用绝对时间"
date: 2026-09-02
tags: [sched/core]
series: "sched clock absolute time option"
type: feature
severity: low
status: under_review
lore: ""
---

## 概述

`sched_clock` 在某些平台上基于硬件计数（如 arch timer）。当硬件时钟发生复位（reset）
时，基于相对计数的 sched_clock 会跳变，造成时间回溯/不连续。本期（UID 73297）提出
新增一个选项，使 sched_clock 在硬件时钟复位时改用绝对时间基准，避免跳变。

## 改动内容 / 核心补丁

- `sched_clock: Add option to use absolute time against hardware clock reset`：引入配置
  选项/机制，在探测到硬件时钟复位时切换到绝对时间模式。
- 配套 Re: 讨论（UID 74455）。

## 状态与讨论

- 当前状态：**under_review**（新补丁）。
- 合入可能性 medium；影响时间基准稳定性，需平台维护者评审。

## 关联

- 002 sched/core 清理（同属调度核心改动）
