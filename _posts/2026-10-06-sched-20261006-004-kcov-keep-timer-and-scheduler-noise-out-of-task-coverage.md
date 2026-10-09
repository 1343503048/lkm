---
id: sched-20261006-004
date: '2026-10-06'
subject: 'kcov: Keep timer and scheduler noise out of task coverage'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260807205027.31972-1-kmehltretter@gmail.com>
lore_url: https://lore.kernel.org/all/20261005185803.39170-1-kmehltretter@gmail.com/
authors:
- Karl Mehltretter
maintainers_involved:
- Alexander Potapenko
- Andrew Morton
current_version: v4
patch_series:
- version: v4
  msgid: <20261005185803.39170-1-kmehltretter@gmail.com>
  date: '2026-10-06'
  summary: 改题 + fuzzing 数据领篇 + 措辞统一 + rebase（无代码变化）
  review_outcome: 当日无回帖；kcov 侧意见全部消化，余 Peter 的 sched 侧认可
related_articles:
- sched-20260902-016
- sched-20260914-003
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: Peter 对 sched/core 内联 guard 的认可未获取
  next_action: Peter 表态后经 -mm 汇合进主线
generated_at: '2026-10-07T01:00:00'
title: 'kcov: Keep timer and scheduler noise out of task coverage'
layout: article
---

> **subject**：`kcov: Keep timer and scheduler noise out of task coverage`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/02/sched-20260902-016-kcov-suppress-timer-and-scheduler-coverage-leaks.html">sched-20260902-016</a> / <a class="article-ref" href="/lkm/2026/09/14/sched-20260914-003-kcov-suppress-timer-and-scheduler-coverage-leaks.html">sched-20260914-003</a>：Karl Mehltretter 的 KCOV 覆盖泄漏抑制系列（v1/v2/v3）——`kernel/sched/` 自身不插桩但其调用的插桩函数（`sched_clock()`、CPU capacity helper、deferred hrtimer rearm 等）在任务上下文运行时把 PC 记进当前任务，污染 syscall 覆盖、破坏「覆盖 = 输入的函数」契约；修法为 nestable `KCOV_PAUSED` bit + `kcov_pause` guard，落在 deferred hrtimer rearm、`__schedule()`、`try_to_wake_up()`、`wake_up_new_task()`；v3 已高度收敛（共享 flag helper、READ_ONCE/WRITE_ONCE、guard 位置定稿），卡在 Potapenko 的注释措辞与 Peter 的 sched 侧认可。
- <a class="article-ref" href="/lkm/2026/10/06/sched-20261006-004-kcov-keep-timer-and-scheduler-noise-out-of-task-coverage.html">sched-20261006-004</a>（今天）：**v4 发出并改题**（Andrew Morton 建议）——「Suppress timer and scheduler coverage leaks」→「Keep timer and scheduler noise out of task coverage」，cover letter 改以 **fuzzing 收益**领篇：syzkaller 上 triage（重跑程序甄别伪覆盖）占比从 26-34% 降到 10%（Pi 400 RT），20 分钟跑完 corpus 大 26-82%；KCOV_SELFTEST 崩溃从 3/3 复现降到 10/10 通过；措辞按 Potapenko 意见统一为「instrumented with KCOV」；rebase mainline（无代码变化）。当日无回帖。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/02/sched-20260902-016-kcov-suppress-timer-and-scheduler-coverage-leaks.html">sched-20260902-016</a> / <a class="article-ref" href="/lkm/2026/09/14/sched-20260914-003-kcov-suppress-timer-and-scheduler-coverage-leaks.html">sched-20260914-003</a>）KCOV 契约（Documentation/dev-tools/kcov.rst）：覆盖应是 syscall 输入的稳定函数、不含调度器等非确定性部分。`kernel/sched/` 不插桩，但它调用的插桩代码（`sched_clock()`、CPU capacity helper）与 deferred hrtimer rearm（任务上下文中断返回时执行）都被记进「当时恰好在内核里的任务」——同一 syscall 报不同覆盖，fuzzer 反复重跑甄别（triage），还令 KCOV_SELFTEST 主线 3/3 启动即崩（递归 fault）。直接把相关代码关 KCOV 会丢掉真 syscall（hrtimer/timekeeping）的覆盖，故用可嵌套 pause guard。

## 技术方案

（承 v3）6 补丁：1/6 `kcov_start()` mode 参数改 unsigned int；2/6 新增 nestable `KCOV_PAUSED` bit + `kcov_pause` guard（KCOV=n 时编译消失）；3/6 deferred hrtimer rearm 处 pause；4/6 `__schedule()` 入口 guard（切出后保持置位、由 resume 侧的 `__schedule()` 帧恢复）；5/6 `try_to_wake_up()` guard 置于 preempt guard 之前；6/6 `wake_up_new_task()` 包整函数。

v4 变化（非代码）：

- **改题**并重排 cover：fuzzing 数据领篇（Andrew Morton）。
- 措辞统一「instrumented with KCOV」（Alexander Potapenko）。
- rebase 到 mainline 551c722f4080；受影响对象与 v3 rebase 后逐位一致。

cover 同时给出系列边界：Peter 在 v2 讨论中的 IRQ-exit 记账想法已被作者拆成独立系列「softirq: Preserve interrupt context during IRQ exit」（v5 已 review），与本系列互补；arm64 无 deferred rearm 故 Pi 行只测 4-6 补丁；RISC-V 的 trap entry 记录问题需另行原型。

## 版本演进与当前进展

- v1（08-11，IRL 08-07）/v2（09-01）：<a class="article-ref" href="/lkm/2026/09/02/sched-20260902-016-kcov-suppress-timer-and-scheduler-coverage-leaks.html">sched-20260902-016</a>。
- v3（09-14）：收敛 + 大测试矩阵；Potapenko 措辞意见（<a class="article-ref" href="/lkm/2026/09/14/sched-20260914-003-kcov-suppress-timer-and-scheduler-coverage-leaks.html">sched-20260914-003</a>）。
- v4（10-06 02:57 北京，`<20261005185803.39170-1-kmehltretter@gmail.com>`）：改题 + fuzzing 数据领篇 + 措辞 + rebase。当日无回帖。

## Maintainer 意见与讨论焦点

- **Andrew Morton**（-mm/kcov 汇合层）：v3 后建议改题、以 fuzzing 结果领篇——v4 落实。
- **Alexander Potapenko**（kcov 维护者）：措辞「instrumented with KCOV」——v4 落实。
- **Peter Zijlstra**（sched 侧）：对 sched/core 内联 guard 的正面认可仍未发生（承 v1/v2 争论）；当日无表态。
- 焦点：v4 后 kcov 侧意见全部消化，唯一悬置项是 Peter 的 sched 侧最终认账。

## 合入评估

*likelihood=medium*。kcov 侧（Potapenko/Morton）意见清零、数据与测试矩阵充分（含真硬件）；但 sched/core 三处 guard 仍等 Peter 表态，系列横跨 kcov/sched/time 三个归属，汇合路径本身有摩擦。*blocking_issues*：Peter 对 sched/core 内联 guard 的认可未获取。*next_action*：Peter 表态（或 tacit acceptance）；系列经 -mm 树进主线。

## 效果评估

v4 新增 fuzzing 量化（syzkaller 29fd395f4ab6，空 corpus 起跑，行汇总 3 对（末行 5 对）跑次）：

| 平台/时长 | corpus | coverage | triage 份额变化 |
|---|---|---|---|
| Pi 400 native RT 20min | +26~82% | +18~45% | -71~-63% |
| Pi 500+ KVM RT 20min | +11~12% | +4~8% | -59~-52% |
| Pi 500+ KVM RT 60min | +5~10% | -1~+1% | -58~-53% |
| Pi 500+ KVM 60min | +0~2% | -3~+4% | -25~-16% |
| x86-64 QEMU RT 3h | +40~81% | +15~21% | -71~-59% |
| x86-64 QEMU 3h | +29~74% | +8~20% | -75~-68% |

无 fuzzing 佐证：1000 次相同 fork() 产生新 syzkaller signal 从 218-233 次降到 45-53 次（Pi 400 RT）。KCOV_SELFTEST：主线 3/3 崩 vs 本系列 10/10 过（x86-64 defconfig，含/不含 RT）。收益随覆盖饱和收窄（60min 后 coverage 持平、corpus +5-10%、triage 减半持续）。

## 我可以参与的点

- `review`：核对 v4 与 v3 受影响对象的逐位一致性声明（rebase 无代码变化）——独立构建 diff 一次，给汇合审一个第二确认。
- `testing`：在 s390/LoongArch64（v3 曾构建覆盖）跑 KCOV_SELFTEST，补 v4 未覆盖架构的自检数据。

## 参考链接

- v4 cover: https://lore.kernel.org/all/20261005185803.39170-1-kmehltretter@gmail.com/
- v3 cover: https://lore.kernel.org/all/20260914054632.12877-1-kmehltretter@gmail.com/
- 配套 softirq 系列 v5: https://lore.kernel.org/r/20260930191432.62760-1-kmehltretter@gmail.com
- selftest 诊断补丁: https://lore.kernel.org/r/20261002181357.14293-1-kmehltretter@gmail.com
