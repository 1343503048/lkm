---
date: 2026-08-07
series: sched-ext-find-parent-sched
version: v1
status: in-review
tags:
- sched_ext
- cgroup
related_articles: []
submitter: Cui Jian
emails:
- uid: 26883
  subject: '[PATCH] sched_ext: Add NULL check in find_parent_sched()'
- uid: 26514
  subject: '[PATCH] sched_ext: Fix NULL dereference in find_parent_sched()'
- uid: 26779
  subject: 'Re: [PATCH] sched_ext: Fix NULL dereference in find_parent_sched()'
title: 'sched_ext: find_parent_sched() 健壮性修复（NULL 检查争议）'
layout: article
---

## 概述

围绕 `find_parent_sched()`（`kernel/sched/ext/sub.c`）的健壮性，Cui Jian 提交了两版补丁并引发评审讨论：一版新增 `parent` 的 NULL 检查（返回 `-ENODEV`），一版修复 `cgrp->scx_sched` 解引用前的 NULL 检查。

## 原始补丁意图

`find_parent_sched()` 在解引用 `cgrp->scx_sched` 前未检查 NULL。原作者认为 `cgroup_get_from_id()` 可能返回任意层级（含 cgroup v1，其 `scx_sched` 永远未设置）的 cgroup，若 BPF 程序传入一个 v1 cgroup id 作为 `sub_cgroup_id`，会在 `parent->cgrp` 处触发 NULL 解引用致内核崩溃。

补丁新增：

```c
/* no SCX sched */
if (!parent)
    return ERR_PTR(-ENODEV);
```

## 评审质疑

Zhan Xusheng 在 Re 中指出 changelog 描述不成立：

- `cgroup_get_from_id()` 的 id 仅在 v2 kernfs root 中查找（`cgrp_dfl_root.kf_root`），v1 id 在此即返回 `-ENOENT`；即便找到，也会经 `cgroup_is_descendant()` 以 `cgrp->root != ancestor->root` 拒绝，v1 cgroup 实际上到不了 `find_parent_sched()`。
- 并对是否存在其他可达窗口表示存疑（因 `sub.c` 尚未合入上游，正对照 `ext.c` 阅读）。

结论：作为加固检查无害，但 changelog 写成"可触达的崩溃"会误导 backport 与 CVE 判定，措辞需修正。

## 状态

补丁处于评审阶段，主要待修正 changelog 表述，避免夸大为可触达崩溃。

## 参考链接

- 补丁与讨论：uid 26883 / 26514 / 26779
