---
title: "sched：文档化 WF_SYNC 唤醒放置语义（RFC）"
date: 2026-08-26
tags: [sched/core, documentation]
series: "document WF_SYNC wakeup placement semantics"
type: fix
severity: low
status: under_review
lore: ""
---

## 概述

同步等待队列唤醒（sync wakeup）的现有注释声称「被唤醒者不会被迁移到另一个 CPU」，
但当前调度器唤醒路径并不保证这一点。本 RFC（UID 58296 1/2、58208 2/2、58299/58433
0/2）修正 `kernel/sched/wait.c` 中 `__wake_up_sync_key()` / `__wake_up_sync()` 的
API 注释，去掉不正确的「不迁移」保证。

## 改动内容 / 核心补丁

核心改动（据 58296 正文）：
- 同步唤醒只是把 `WF_SYNC` 通过 waitqueue 唤醒函数转发给调度器。
- 对 fair-class 任务，`WF_SYNC` 仅作为「唤醒放置（wakeup-placement）与抢占提示」，
  并不保证被唤醒者运行在唤醒者所在 CPU，也不避免迁移。
- 在 UP 上可能避免一次不必要的抢占。
- 修正 `__wake_up_sync_key` / `__wake_up_sync` 两处注释（共 +16/-14 行）。

## 状态与讨论

- 当前状态：**under_review / RFC 阶段**（1/2 + 2/2 配套，2/2 澄清 `sched/wait`
  语义）。
- 纯文档修正，无逻辑改动，合入概率高；有助于消除对 `WF_SYNC` 的误解。

## 关联

- 001 sched/debug per-CPU debugfs v6（同为 sched 子系统注释/健壮性）
