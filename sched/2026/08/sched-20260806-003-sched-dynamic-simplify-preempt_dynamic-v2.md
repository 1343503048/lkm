---
id: sched-20260806-003
date: "2026-08-06"
title: "sched: 简化 PREEMPT_DYNAMIC（v2，Jinjie Ruan R-b）"
series: "Simplify PREEMPT_DYNAMIC"
type: feature
status: under_review
severity: none
merge_likelihood: high
tags: [preempt, topology]
authors: ["Mark Rutland <mark.rutland@arm.com>", "Jinjie Ruan <ruanjinjie@huawei.com>", "Shrikanth Hegde <sshegde@linux.ibm.com>"]
reviewers: ["Jinjie Ruan <ruanjinjie@huawei.com>", "Shrikanth Hegde <sshegde@linux.ibm.com>"]
related_articles: ["sched-20260805-003", "sched-20260804-009"]
emails: ["uid-24724@qq-imap", "uid-24531@qq-imap"]
---

# sched: 简化 PREEMPT_DYNAMIC（v2，Jinjie Ruan R-b）

## 摘要

Mark Rutland 的「简化 PREEMPT_DYNAMIC」系列 v2 在 08-06 收到 Jinjie Ruan（华为）的 `Reviewed-by`（针对 v2 3/6 `preempt_schedule{,_notrace}` 移除）。本日邮件 24724 是 Jinjie 对 3/6 的 review：确认「FULL 与 LAZY 两种模式下 `preempt_schedule`/`preempt_schedule_notrace` 始终启用、无需动态切换」，因此 dynamic 分支可整体删除，直接调 `preempt_schedule[_notrace]()`，给出 LGTM + R-b。

v2 整体（延续 08-05-003）：
- `PREEMPT_DYNAMIC` 现在仅限 FULL / LAZY 两种抢占模型，二者下 `preempt_schedule()` 与 `preempt_schedule_notrace()` 都始终调用、从不被禁用。
- 删除 arm64/s390/x86/asm-generic 的 `dynamic_preempt_schedule*()` 定义及 `kernel/sched/core.c` 中 52 行 static_call/static_key 样板（共约 111 行删除）。
- `__sched_dynamic_update()` 在 full/lazy 分支移除 `preempt_dynamic_enable(preempt_schedule*)` 调用。

## 技术细节

3/6 的关键改动（示意）：
```
// 删除 #ifdef CONFIG_PREEMPT_DYNAMIC 的 dynamic 分支
#define __preempt_schedule()      preempt_schedule()
#define __preempt_schedule_notrace() preempt_schedule_notrace()
// core.c 删除 DEFINE_STATIC_CALL(preempt_schedule, ...) 等
// __sched_dynamic_update(): 不再 enable preempt_schedule*
```

Jinjie 的 review 结论：因 full/lazy 下这两个函数恒启用，dynamic 切换纯属冗余，删除安全。

## 影响与风险

- 影响面：所有启用 `PREEMPT_DYNAMIC` 的架构（arm64/x86/s390/通用）。纯重构，不改变运行时抢占语义。
- 风险：低。已获 Jinjie R-b（在 Shrikanth R-b 基础上），逻辑等价；删除约 111 行样板，降低后续架构接入成本。
- 注意：删除的是 static_call 入口，需确认未有其他路径依赖 `sk_dynamic_preempt_schedule*` 符号（EXPORT 已一并移除）。

## 评价

健康的维护性重构，reviewer（Shrikanth、Jinjie）已介入并放行。合入可能性高，建议 Peter 收尾进 tip/sched/core。
