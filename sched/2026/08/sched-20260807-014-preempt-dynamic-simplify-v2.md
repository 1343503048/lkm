# preempt dynamic simplify v2

## 概述

提交 v2 的 6 片系列，对 `PREEMPT_DYNAMIC` 进行系统化简，移除冗余的静态键/分支路径，统一抢占模型访问接口。

## 变更内容

- 移除 `HAVE_PREEMPT_DYNAMIC_CALL` 这一静态键开关，简化动态抢占的启用条件。
- 简化 `preempt_dynamic` 初始化与选择逻辑。
- 简化 `irqentry_exit_cond_resched()`。
- 简化抢占模型访问宏/访问器。

## 测试反馈

作者在 Qemu 与 Kunpeng HIP09 服务器上以 `preempt=lazy` / `preempt=full` 启动测试通过；`preempt=none` / `preempt=voluntary` 在 Qemu 启动报 "Dynamic Preempt: unsupported mode"。但发现运行时通过 `/sys/kernel/debug/sched/preempt` 切换不正常（如 `echo full` 后 `cat` 显示 "full lazy"），提示调试接口与运行时切换仍有问题待修。

## 状态

v2，处于评审阶段，运行时切换路径存已知问题。

## 参考链接

- 系列：uid 26025 / 25979 / 25960 / 25967 / 25950 / 26006

---
subject: "preempt: 简化 PREEMPT_DYNAMIC（v2）"
date: 2026-08-07
series: "preempt-dynamic-simplify"
version: "v2"
status: "in-review"
tags: [preempt, sched_debug]
related_articles: []
submitter: "社区"
emails:
  - uid: 26025
    subject: "[PATCH v2 0/6] preempt: simplify PREEMPT_DYNAMIC"
  - uid: 25979
    subject: "[PATCH v2 1/6] ... remove HAVE_PREEMPT_DYNAMIC_CALL key"
  - uid: 25960
    subject: "[PATCH v2 2/6] ... simplify preempt-dynamic"
  - uid: 25967
    subject: "[PATCH v2 3/6] ... simplify irqentry_exit_cond_resched"
  - uid: 25950
    subject: "[PATCH v2 4/6] ... simplify preempt model accessors"
  - uid: 26006
    subject: "[PATCH v2 5/6] ... related"
---
