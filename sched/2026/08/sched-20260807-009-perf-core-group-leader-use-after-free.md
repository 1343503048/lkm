# perf/core: Fix group leader use-after-free after sibling detach

## 概述

修复 perf 事件组中，sibling 事件被 detach 后 group leader 指针被错误释放/访问导致的 use-after-free。

## 问题

当某个 perf 事件组的 sibling 被 detach 时，若 group leader 的引用计数或链表处理不当，后续对 leader 的访问会落到已释放内存，表现为内核崩溃（UAF）。相关调用栈涉及 `perf_ioctl()` 等路径。

## 变更

补丁修正 sibling detach 时 group leader 生命周期的引用处理，确保 leader 在仍有引用期间不被释放。

## 状态

处于评审/讨论阶段。

## 参考链接

- 邮件：uid 26855 / 25485 / 26209

---
subject: "perf/core: 修复 sibling detach 后 group leader 的 use-after-free"
date: 2026-08-07
series: "perf-core-group-leader-uaf"
version: "v1"
status: "in-review"
tags: [perf, crash]
related_articles: []
submitter: "社区"
emails:
  - uid: 26855
    subject: "[PATCH] perf/core: Fix group leader use-after-free after sibling detach"
  - uid: 25485
    subject: "Re: [PATCH] perf/core: Fix group leader use-after-free after sibling detach"
  - uid: 26209
    subject: "Re: [PATCH] perf/core: Fix group leader use-after-free after sibling detach"
---
