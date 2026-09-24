---
id: sched-20260914-003
date: '2026-09-14'
subject: 'kcov: Suppress timer and scheduler coverage leaks'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260914054632.12877-1-kmehltretter@gmail.com>
lore_url: https://lore.kernel.org/all/20260914054632.12877-1-kmehltretter@gmail.com/
authors:
- Karl Mehltretter
maintainers_involved:
- Alexander Potapenko
current_version: v3
patch_series:
- version: v1
  msgid: <20260811154111.64669-1-kmehltretter@gmail.com>
  date: 2026-08-11
  summary: 'kcov_pause guard 首版，三处 sched/core open-code 标注，挂 Fixes: 5c9a8750a640'
  review_outcome: Peter 抱怨只发半串；Potapenko 要求压缩插入点并把合入判断推给调度侧
- version: v3
  msgid: <20260914054632.12877-1-kmehltretter@gmail.com>
  date: 2026-09-14
  summary: rebase mainline 22098763a10d；共享 flag helper + READ_ONCE/WRITE_ONCE/编译器屏障；try_to_wake_up
    pause 提前到 preempt 前；删 sched 补丁宽泛 Fixes；完整多架构/压测矩阵
  review_outcome: Potapenko 对 4/6 提注释措辞建议（Callees instrumented with KCOV）；Peter 对
    sched/core 侧最终认账仍待
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 注释措辞需按 Peter 口径定稿
  - sched/core 内联 guard 的调度侧最终认可未获取到
  next_action: 作者改措辞发 v4，等 Peter 对 sched/core 部分表态
contribution_opportunities:
- kind: review
  description: 核对 v4 措辞与三处 guard 是否覆盖全部泄漏 callee（SCHED_HRTICK 装填、sched_clock 类）
- kind: testing
  description: 在 arm64/s390 复现 KCOV selftest 的 interrupt 泄漏用例，验证跨架构一致性
generated_at: '2026-09-15T09:30:00'
source_email_count: 5
related_articles:
- sched-20260902-016
tags:
- preempt
- rt
title: 'kcov: Suppress timer and scheduler coverage leaks'
layout: article
---

## TL;DR
增量更新，v1/v2 全貌见 sched-20260902-016。Karl Mehltretter 发出 v3（6 补丁，其中 4/5/6 落在 kernel/sched/core.c）：相对 v2，rebase 到 mainline `22098763a10d`、按 Potapenko 意见共享 pause 与上下文切换抑制的 flag helper 并加 READ_ONCE/WRITE_ONCE/编译器屏障、把 try_to_wake_up 的 pause guard 提到 preempt guard 之前、删掉 sched 补丁的宽泛 Fixes 标签，并给出覆盖多架构/多编译器/KCOV selftest/fork+futex 压测/USB 覆盖保持的完整测试矩阵。当日 Potapenko 对 4/6 提措辞建议（"Callees instrumented with KCOV"），说明 Peter 期望的注释措辞仍待定稿。

## 背景与问题
KCOV 的契约是排除中断与调度器自身覆盖、让 syscall 覆盖率保持「与输入相关」。漏洞在于 `kernel/sched/` 目录本身不插桩，但它**调用的**函数插桩——`sched_clock()`、arch 的 CPU-capacity helper（`arch_scale_cpu_capacity()`）、`profile_hits()`、`kthread_is_per_cpu()`、`SCHED_HRTICK` 装填等。当未插桩的 timer/sched 路径在 `in_task()` 为真时运行，这些被调用者的 PC 被记进当前任务，形成非确定性覆盖污染。PREEMPT_RT 下最明显：RT 把 timer softirq 放进内核线程跑，唤醒发生在任务上下文，selftest 自旋期间 `try_to_wake_up()` 泄漏；fork 路径同理（`wake_up_new_task()` 把 sched/hrtimer/clockevent 覆盖记进父进程）。

## 技术方案
v3 三个 sched/core 补丁（每处 +2~3 行，用 `guard(kcov_pause)()`）：

- **4/6 `__schedule()`**：guard 置于函数入口（trace 之前）。`KCOV_PAUSED` 在任务切出后保持置位，由被 resume 的 `__schedule()` 帧恢复先前状态——嵌套 + 任务切换正确性的关键。
- **5/6 `try_to_wake_up()`**：guard 放在 `guard(preempt)()` **之前**——先 pause KCOV 再禁抢占，抢占恢复时 KCOV 仍暂停；只包 `select_task_rq()` 会漏掉 enqueue 路径的 SCHED_HRTICK 装填。
- **6/6 `wake_up_new_task()`**：guard 包整函数，把调度器排除扩展到新任务唤醒。

v3 相对 v2 的实质变化：共享 flag helper（pause 与上下文切换抑制共用）、一致使用 READ_ONCE/WRITE_ONCE 与编译器屏障（Potapenko 意见）、try_to_wake_up pause 提前到 preempt 前、明确 guard 使用者必须无 KCOV 插桩、patch 1 加 Potapenko Reviewed-by、删除 sched 补丁的宽泛 Fixes 标签。

## 版本演进与当前进展
- v1（08-11）/ v2（09-01）：见 sched-20260902-016；v2 已将 patch 1 变为 `kcov: Add a kcov_pause guard` 并引入 READ_ONCE/WRITE_ONCE。
- v3（09-14，本文窗口）：rebase mainline `22098763a10d`；上述收敛性改动；测试矩阵——GCC 15.2 x86-64 全量（KCOV / KCOV+RT / KCOV=n）、arm64 / RISC-V64 / s390 构建；KCOV selftest 10/10 x86-64 boots（含/不含 RT）、3/3 s390、Clang 21.1.8 x86-64 3/3；GCC 8.1 x86-64 受影响对象、ARM32 / LoongArch64 / RISC-V32 / RISC-V64 RT / arm64 RT；1200 次 KCOV fork + 3600 次 futex handshake（21609 个非空非饱和 probe）；USB 40 次 disconnect/reconnect 覆盖保持。

## Maintainer 意见与讨论焦点
- **Alexander Potapenko（kcov 维护者）**：当日对 4/6 提措辞 "Here and in other patches, I believe Peter expected different wording. How about 'Callees instrumented with KCOV'?"——即 Peter 期望的注释措辞（v3 已把 "sched/ is uninstrumented" 改成 "built without KCOV instrumentation"，但补丁内注释仍未完全对齐 Peter 的口径）。
- **Peter Zijlstra**（承 v1/v2）：此前抱怨 v1 只发半串、主张过 IRQ-exit preempt count 替代方案；对 sched/core 内联 guard 的最终认账仍是合入前提（承 sched-20260902-016）。
- 分歧/未闭合处：注释措辞待定稿（Potapenko 还在替 Peter 把关）；sched/core 三处 open-code guard 是否被调度侧最终接受仍无正面信号。

## 合入评估
*likelihood=medium*：v3 已按意见高度收敛、测试矩阵极充分；但 Peter 对 sched/core 内联 guard 的最终认可仍待获取。*blocking_issues*：注释措辞需按 Peter 口径定稿；sched/core 侧最终 Ack 未获取到。*next_action*：作者按 Potapenko 建议改措辞后发 v4，等 Peter 对 sched/core 部分表态。

## 效果评估
无性能数字——这是抑制覆盖泄漏的正确性修复，收益是「覆盖率不再被调度器内部行为污染」。可量化的是测试规模（见版本演进）与正确性：KCOV selftest 全绿、无 buffer 饱和或 disable 竞态、USB 目标符号与 task tracing 保持存活。

## 我可以参与的点
- kind=review：核对 v4 是否落实 Potapenko 的措辞建议，以及三处 guard 插入位置是否覆盖全部泄漏 callee（尤其 enqueue 路径的 SCHED_HRTICK 装填与 sched_clock 类调用）。
- kind=testing：在 arm64 / s390 等次要架构复现 KCOV selftest 的 interrupt 泄漏用例，验证跨架构一致性。

## 参考链接
- v3 cover：https://lore.kernel.org/all/20260914054632.12877-1-kmehltretter@gmail.com/
- v3 4/6（__schedule）：https://lore.kernel.org/all/20260914054632.12877-5-kmehltretter@gmail.com/
- Potapenko 措辞回帖：https://lore.kernel.org/all/CAG_fn=VwN-1pdK_3=qrwpDb=EsyOdoNgNK19zB7Ga0puQZgScw@mail.gmail.com/
