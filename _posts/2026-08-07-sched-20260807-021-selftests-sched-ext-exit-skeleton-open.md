---
subject: 'selftests/sched_ext: 检查 exit 测试骨架打开失败'
date: 2026-08-07
series: selftests-sched-ext-exit
version: v1
status: in-review
tags:
- sched_ext
- crash
related_articles: []
submitter: Liang Luo
emails:
- uid: 25953
  subject: '[PATCH] selftests/sched_ext: check skeleton open failure in exit test'
title: 'selftests/sched_ext: Check skeleton open failure in exit test'
layout: article
---

## 概述

Liang Luo 修复 sched_ext selftest 中 `exit.c` 未检查 `exit__open()` 返回值导致的 NULL 解引用。

## 问题

`exit.c` 未检查 `exit__open()` 的返回值。若其返回 NULL（skeleton wrapper 分配对象或打开 BPF ELF 失败时），下一行通过 `SCX_ENUM_INIT()`（展开为 `SCX_ENUM_SET()`，访问 `skel->rodata`）即触发 NULL 指针解引用。除 `exit.c` 外，其他 selftest 都用 `SCX_FAIL_IF(!skel, ...)` 做了守卫。Fixes `a5db7817af78`（"sched_ext: Add selftests"）。

## 修复

在 `skel = exit__open();` 后新增 `SCX_FAIL_IF(!skel, "Failed to open");`，与其他 selftest 保持一致。

## 状态

v1，处于评审阶段。

## 参考链接

- 邮件：uid 25953
