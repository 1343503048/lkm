---
id: sched-20260802-002
date: 2026-08-02
subsystem: sched
type: bug
status: under_review
severity: critical
thread_root_msgid: "unknown"
lore_url: "unknown"
authors: [Niels Pressel]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<uid-15200@qq-imap>"
    date: 2026-08-02
    summary: "在 rseq_grant_slice_extension() 中调用 hrtimer_rearm_deferred_tif() 前用 guard(irq)() 关中断，修复 hrtimer_bases.lock 的 IN-HARDIRQ-W → HARDIRQ-ON-W 反转导致的硬死锁。"
    review_outcome: "v1 当日刚发出，暂无 review 回帖。"
upstream_commit: null
fixes_commit: "15dd3a948855"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - "尚无 rseq / timer 维护者（Thomas Gleixner、Mathieu Desnoyers、Peter Zijlstra）回帖确认。"
    - "guard(irq)() 放在 rseq_grant_slice_extension() 内部是否为最优位置未经讨论——也可能维护者更倾向于在 __exit_to_user_mode_loop 侧统一处理，或直接修改 hrtimer_rearm_deferred_tif() 的契约。"
  next_action: "等待 tglx / Mathieu Desnoyers 对修复位置的意见；由于是 hard lockup 且有 lockdep 实证，预计会较快进 tip/sched/urgent 或 timers/urgent。"
contribution_opportunities:
  - kind: review
    description: "分析 guard(irq)() 的作用域是否覆盖了全部不安全路径——TSE 授予流程中是否还有其他在开中断下调用 hrtimer 重装的分支，可回帖补充分析。"
  - kind: testing
    description: "在开启 lockdep 的内核上跑 rseq selftests（尤其 slice_test）复现 inconsistent lock state 告警并验证补丁，回帖 Tested-by。"
  - kind: discussion
    description: "TSE 资格检查为什么放在 IRQ 使能状态下做、能否整体收紧这段路径的中断上下文契约，是一个尚无人展开的设计问题。"
generated_at: "2026-08-03T00:15:00"
source_email_count: 1
related_articles: []
tags: [hang, sched_clock, preempt, x86]
---

# rseq: 修复时间片扩展（TSE）授予路径上的硬死锁

## TL;DR

`rseq` 的时间片扩展（Time Slice Extension，TSE）在**开中断**状态下调用了要求**关中断**的 `hrtimer_rearm_deferred_tif()`，造成 `hrtimer_bases.lock` 的中断上下文锁反转，重负载使用 TSE 时会硬死锁。修复只有一行 `guard(irq)()`。有 lockdep 实证、有真实死锁现象，严重度 critical，合入基本无悬念。

## 背景与问题

`__exit_to_user_mode_loop()` 中会检查 TSE 资格 —— 此时 **IRQ 是使能的**。而授予一次 TSE 可能需要重新装载 hrtimer，走到 `hrtimer_rearm_deferred_tif()`。这个函数的契约明确要求调用者已关中断（见 `include/linux/hrtimer_rearm.h:17`）。

违反契约的后果不是理论风险：`__hrtimer_rearm_deferred()` 会获取一个 **raw spinlock 且不自行关中断**，而同一把锁在硬中断上下文的 `hrtimer_run_queues()` 中也会被获取。经典的 AA 型中断锁反转：

```
    CPU0
    ----
lock(hrtimer_bases.lock);
<Interrupt>
    lock(hrtimer_bases.lock);

                *** DEADLOCK ***
```

作者在 v7.2-rc5 上跑 rseq selftests 时被 lockdep 抓到：

```
WARNING: ./include/linux/hrtimer_rearm.h:17 at irqentry_exit, CPU#1: slice_test

WARNING: inconsistent lock state
inconsistent {IN-HARDIRQ-W} -> {HARDIRQ-ON-W} usage.
slice_test [HC0[0]:SC0[0]:HE1:SE1] takes:
ffff95b82ec5c698 (hrtimer_bases.lock){?.-.}-{2:2}, at: __hrtimer_rearm_deferred
```

`{IN-HARDIRQ-W}` 状态的注册路径来自 `hrtimer_run_queues` ← `update_process_times` ← `tick_periodic` ← `timer_interrupt`；而违规路径是 `__hrtimer_rearm_deferred` ← `irqentry_exit` ← `asm_sysvec_apic_timer_interrupt`。

关键在于**这不是纯 lockdep 理论告警**。作者说明：*"Originally, the issue was discovered because of intermittent lockups when heavily using rseq TSEs."* —— 问题最初是通过重度使用 rseq TSE 时的**间歇性真实死机**发现的，lockdep 只是事后用来定位根因的工具。这决定了严重度必须定为 critical。

引入 commit 为 `15dd3a948855`（"hrtimer: Push reprogramming timers into the interrupt return path"），即把定时器重编程下推到中断返回路径的那次改动 —— 那次改动建立了"必须关中断"的新契约，但 rseq TSE 这个调用点没跟上。

## 技术方案

一行修复，用 `guard(irq)()` 在调用前后自动关/开中断：

```c
static __always_inline bool rseq_grant_slice_extension(unsigned long ti_work, unsigned long mask)
{
	if (unlikely(__rseq_grant_slice_extension(ti_work & mask))) {
+		guard(irq)();
		hrtimer_rearm_deferred_tif(ti_work);
		return true;
	}
```

设计取舍分析：

- **作用域最小化**：`guard(irq)()` 放在 `if` 块内部而非函数开头，意味着只有真正要重装 timer 的慢路径才付出关中断代价；`__rseq_grant_slice_extension()` 的资格判断仍在开中断下跑。对于 `__always_inline` 的 hot path 出口代码，这个取舍是合理的。
- **用 `guard()` 而非显式 `local_irq_save/restore`**：符合内核近年的 cleanup.h 风格，且天然处理了 `return true` 提前退出的路径。
- **没有改 `hrtimer_rearm_deferred_tif()` 本身**：作者选择在调用者侧适配，而不是放宽被调用者的契约。这保持了 timer 侧语义不变，改动面最小 —— 但也正因如此，如果还有其他违规调用点，这个补丁并不能一网打尽。

邮件中**没有提及被放弃的备选方案**，属于直接给出最小修复的风格。

## 版本演进与当前进展

v1，2026-08-02 20:44（北京时间）发出，当日无回帖。

补丁基于 `f5098b6bae761e346ebcd9da7f95622c04733cff`，带 `Fixes:` 标签，作者声明"用 rseq selftests 测试了该修复"。改动仅 `include/linux/rseq_entry.h` 一个文件、一行新增。

## Maintainer 意见与讨论焦点

当日**无任何维护者回帖**，也没有 Reviewed-by / Acked-by。

需要如实指出几个**尚未被讨论的开放问题**（这些不是已知分歧，而是"还没人看"的空白）：

1. **修复位置是否最优未经审议**。把 `guard(irq)()` 放进 `rseq_grant_slice_extension()` 是一种选择；维护者也可能倾向于在 `__exit_to_user_mode_loop()` 侧统一处理，或者干脆让 `hrtimer_rearm_deferred_tif()` 自己保证中断状态。tglx 对这类中断上下文契约通常有明确偏好，最终形态未必是当前这版。
2. **是否存在其他违规调用点未被排查**。补丁只修了 rseq TSE 这一处，邮件没有说明是否审计过 `hrtimer_rearm_deferred_tif()` 的全部调用者。
3. **stable 归属未提及**。引入 commit `15dd3a948855` 的发布版本未在邮件中说明，作者也没有 Cc stable。考虑到这是可触发硬死锁的 bug，如果引入 commit 已在已发布版本中，回合 stable 应是必要的 —— 这一点目前是空白。

## 合入评估

合入可能性 **high**，但**具体形态可能变化**。支撑理由：

- 死锁场景由 lockdep 完整证实，锁反转链条清晰无歧义；
- 有真实间歇性 lockup 现象作为动机，不是纸面问题；
- `Fixes:` 标签明确，责任归属清楚；
- 修复代价极低（一行），风险可控；
- 作者已用 rseq selftests 验证。

风险在于：这类中断上下文问题，维护者（尤其 tglx）常常会要求换一种更彻底的修法，或者顺带审计全部调用点。所以"这个问题一定会被修"是高确定性的，"这一版补丁原样合入"则是中等确定性。

预计走 `tip/timers/urgent` 或 `tip/sched/urgent`。

## 效果评估

- **修复前**：跑 rseq selftests（`slice_test`）时 lockdep 报 inconsistent lock state；重度使用 rseq TSE 时出现间歇性真实 lockup。
- **修复后**：作者称"用 rseq selftests 测试了该修复"（*"Tested the fix using the rseq selftests."*）—— 但**没有给出补丁后的具体输出或运行时长**，属于作者声明的测试通过，未附证据。

**无性能数据**。理论上关中断窗口极短（仅包住一次 hrtimer 重装），且只在真正授予 TSE 的路径上生效，性能影响应可忽略 —— 但这是本文的推断，邮件中作者未做任何性能讨论，**未见测试数据支撑**。

## 我可以参与的点

- **审计其他调用点**（价值最高）：`grep` 出 `hrtimer_rearm_deferred_tif()` 的全部调用者，逐个检查中断上下文，看是否还有同类违规。如果找到第二处，这个发现足以让讨论方向从"打补丁"转为"收紧契约"，是有分量的贡献。
- **lockdep 复现验证**：开启 `CONFIG_PROVE_LOCKING` 编译 v7.2-rc5，跑 `tools/testing/selftests/rseq/` 复现告警，再验证补丁消除告警，回帖 Tested-by。门槛低、周期短。
- **推动 stable 归属讨论**：查明 `15dd3a948855` 首次出现在哪个发布版本，如果已在 stable 树中，回帖建议 Cc stable。这是当前明确的空白项。
- **设计层面提问**：TSE 资格检查为什么放在 IRQ 使能状态下做？能否把整段 TSE 授予流程都置于关中断上下文以简化推理？这是个尚无人提出的正当问题，适合在讨论中抛出。

这个系列的参与空间比 001 大，因为它触及中断上下文契约这类容易有分歧的设计问题。

## 参考链接

- lore thread: 未获取到（IMAP 邮件头未暴露原始 Message-ID）
- tip-bot commit: 未获取到
- stable backport: 未获取到（作者未 Cc stable）
