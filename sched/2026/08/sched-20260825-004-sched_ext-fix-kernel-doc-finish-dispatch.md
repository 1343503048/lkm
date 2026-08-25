---
title: "sched_ext：修复 finish_dispatch() kernel-doc 缺失的 @slice/@vtime 描述"
date: 2026-08-25
tags: [sched_ext, documentation]
series: "sched_ext finish_dispatch kernel-doc"
type: fix
severity: low
status: under_review
lore: ""
---

## 概述

`finish_dispatch()` 的 kernel-doc 注释缺失了 `@slice` 与 `@vtime` 两个参数的描述，
导致 `make htmldocs`/sparse 文档检查报缺失。本期补上这两处描述（UID 56490）。

## 改动内容 / 核心补丁

- 在 `finish_dispatch()` 的 kernel-doc 中补充 `@slice`、`@vtime` 参数说明。
- 纯文档/注释修正，无逻辑改动。

## 状态与讨论

- 当前状态：**under_review**。
- 属于 sched_ext 文档整洁度维护，合入概率高。

## 关联

- 001 / 003 sched_ext cgroup 相关补丁
