---
id: sched-20261026-005
date: 2026-10-26
subject: '[QUESTION] sched/clock: Potential timestamp jump due to inter-CPU counter
  skew?'
subsystem: sched
type: discussion
status: rfc
severity: none
thread_root_msgid: <cf7a043c-384c-0642-204c-8f207eff3d42@huawei.com>
lore_url: https://lore.kernel.org/all/cf7a043c-384c-0642-204c-8f207eff3d42@huawei.com/
authors:
- Zhang Qiao
maintainers_involved:
- Peter Zijlstra
- Marc Zyngier
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: 无需推进；问题已获答复（硬件契约要求跨 CPU counter 一致，内核不兜底）
contribution_opportunities:
- kind: discussion
  description: 就 sched_clock 是否应加 max_delta 防护（防御性）发起后续讨论或补丁
generated_at: '2026-10-27T01:00:00'
source_email_count: 4
related_articles: []
tags:
- sched_clock
title: '[QUESTION] sched/clock: Potential timestamp jump due to inter-CPU counter
  skew?'
layout: article
---

## TL;DR
Zhang Qiao 在 LKML 提问：`update_sched_clock()` 用某个 CPU 读到的 counter 发布共享 `epoch_cyc`，其他 CPU 随后用它减自己读到的 counter，若某 CPU 观察到的 counter 值**严格小于**新 epoch（且非正常回绕），无符号减法会下溢、mask 后得到近一个完整周期的巨大 delta，`cyc_to_ns()` 可能乘法溢出或返回错误时间戳。Zhan Xusheng、Marc Zyngier、Peter Zijlstra 一致答复：这是**硬件契约问题**——RISC-V Zicntr/arm64 架构计时器都要求各 CPU 有一致的 counter 视图，实现做不到「任意两 CPU 读同一 counter 值」即为 broken、内核不兜底；`sched_clock` 也确无 `clocksource_delta()` 那种 max_delta 防护。问题获解答，无补丁。

## 背景与问题
作者在阅读 `kernel/time/sched_clock.c` 时提出一个理论场景：

```
cyc = (rd->read_sched_clock() - rd->epoch_cyc) & rd->sched_clock_mask;
res = rd->epoch_ns + cyc_to_ns(cyc, rd->mult, rd->shift);
```

`update_sched_clock()` 用「执行更新的 CPU」读到的 counter 值发布共享 `epoch_cyc`；其他 CPU 随后用自己读到的 counter 减这个共享 epoch。假设 CPU1 观察到 CPU0 新发布的 `epoch_cyc=1000`，但它随后读到的 counter 只有 993（落后 7 个 tick，非回绕），则 `(993 - 1000) & ((1ULL<<56)-1) = 2^56 - 7`，得到一个近整个 counter 周期的 delta，`cyc_to_ns()` 可能乘法溢出或返回完全错误的时间戳。该场景的前提是「跨 CPU counter skew 大于 CPU0 发布新 epoch 到 CPU1 观察并读自身 counter 的时延」。

作者的两个问题：(1) 有没有硬件/架构规范（arm64 architected timer、RISC-V）要求各 CPU（含跨 die/socket）的 counter 完全同步、允许 skew 的话最大允许多少？(2) 若上述序列理论上成立，generic `sched_clock()` 是否有机制处理「读到落后于共享 epoch_cyc 的 counter」？

## 技术方案
本贴为纯讨论，无补丁。社区答复集中在「硬件必须提供一致视图」这一契约上，并顺带澄清了 `sched_clock` 与 timekeeping 的实现差异：

- **Zhan Xusheng**：RISC-V Zicntr 扩展要求所有 hart 的 real-time clock 同步到**一个 tick 以内**；arm64 的 system counter 旨在给所有 PE 一个公共的时间视图，跨 die 副本的同步是实现方的职责，「内核不容忍 skew」。`arm_arch_timer.c` 里处理的 errata（Freescale A-008585、HiSilicon 161010101、Cortex-A73 858921、Allwinner A64）都是**单个 CPU 读回错误值**（靠读两遍规避），没有一个是在处理跨 CPU skew。关于防护机制：`__sched_clock()` 直接把差值 mask 掉后转换；timekeeping 的 `clocksource_delta()` 在 mask 后的 delta 超过 `max_delta` 时返回 0，但 **`sched_clock` 没有这样的检查**，所以「读落后于 epoch_cyc」会得到近整周期的 delta 并让 `cyc * mult` 溢出。
- **Marc Zyngier**：更直接——「如果实现无法让系统内任意两个 CPU 对 counter 有完全一致的视图，那么这个实现就是 broken、不被支持，没有讨论余地。」
- **Peter Zijlstra**：给出方向性结论——「限制是跨 CPU 时延：CPU 绝不能让软件发现时间在倒退。这不是要求时钟完美同步，只要误差小于观测限。所以一旦软件能察觉时钟『晃动』，就输了。」

## 版本演进与当前进展
*current_version: null*。纯问答讨论，无版本演进。原帖（`<cf7a043c-384c-0642-204c-8f207eff3d42@huawei.com>`）当日发出，收到 Zhan Xusheng、Marc Zyngier、Peter Zijlstra 三人答复，问题基本闭合。

## Maintainer 意见与讨论焦点
- **Marc Zyngier**（arm64 KVM/irqchip 维护者）：硬件契约硬约束，跨 CPU 视图不一致即 broken/unsupported，无商量余地。
- **Peter Zijlstra**（sched 维护者）：软件不允许观察到时钟倒退，误差须小于观测限。

无分歧：三方口径一致（硬件须保证一致性、内核不兜底）。唯一「未修」的观察是 Zhan 指出的 `sched_clock` 缺 `clocksource_delta()` 式 max_delta 防护——但这在一致 counter 契约下不会触发，社区未视其为需修复的 bug。

## 合入评估
*likelihood=unknown*。纯讨论、无补丁可合入。*blocking_issues*：无。*next_action*：无需推进；若作者认为 `sched_clock` 应对跨周期 delta 增加防护（哪怕只是防御性），可另行发起补丁讨论。

## 效果评估
无量化数据，属理论场景澄清。社区一致判定该场景对应「硬件违反一致性契约」，非内核需修复的软件缺陷。

## 我可以参与的点
- *kind: discussion*：就「`sched_clock` 是否应像 `clocksource_delta()` 一样对 mask 后的 delta 做 max_delta 防护（防御性）」发起后续讨论或补丁——这是本次问答中唯一未闭合、也未有人否定的技术点。

## 参考链接
- 原帖: https://lore.kernel.org/all/cf7a043c-384c-0642-204c-8f207eff3d42@huawei.com/
- Zhan Xusheng 答复: https://lore.kernel.org/all/20261026082730.2117173-1-zhanxusheng1024@gmail.com/
- Marc Zyngier 答复: https://lore.kernel.org/all/86zew0ygqr.wl-maz@kernel.org/
- Peter Zijlstra 答复: https://lore.kernel.org/all/20261026102332.GB2668200@noisy.programming.kicks-ass.net/
