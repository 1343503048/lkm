# sched/cputime: Don't account idle time twice after dyntick-idle

> **subject**：`sched/cputime: Don't account idle time twice after dyntick-idle`
> 本文为增量更新，完整脉络见下。

## TL;DR

- sched-20261004-002：Stian Halseth 报告 v7.2-rc1 起回归——NO_HZ_IDLE + TICK_CPU_ACCOUNTING 下 `/proc/stat` idle 时间超过墙钟时间（SPARC T7-1 最差 1.44x、KVM guest 1.53x），根因为 cf6444c3e1bb 统一记账后 dyntick-idle 与重启 tick 首个整周期双计。`#regzbot introduced: cf6444c3e1bb`。
- sched-20261005-002：修复 v1 发出（`kernel_cpustat` 记录 overlap、首个 tick 剔除，六组实测回到 1.000x）；Frederic Weisbecker 认可思路但指出嵌套场景——idle 退出后短期内重入时第二次 start 覆盖前一次 overlap，首个 tick 应扣两次之和（仅对 tick X 有效）；另要求 IS_ENABLED()。
- sched-20261006-003：v2 发出，overlap 改为按 tick 周期累积（新增 `idle_tick_period` 字段）；IS_ENABLED() 因字段仅存在于 NO_HZ_COMMON 而无法编译，改用 static inline helper + `#else` stub。Frederic 三连追问澄清边界（残余 steal time 超额系预存问题、v1/v2 实测无差）。
- sched-20261007-002（今天）：**Frederic 对 v2 给出「Looks good, just a few nits」+ 四条意见**（now < tick_start 应 WARN、xchg 可换普通读写、`ts->last_tick` 应总是更新避免二次除法、删掉 `tick_nohz_full_cpu()` 冗余检查）；Stian 当晚即发 **v3** 逐条落实，并在 SPARC T7-1 + x86_64 KVM（含 `nohz_full=1`、无 IRQ_TIME_ACCOUNTING、`highres=off` 变体）复测，结果与 v2 相同。review 闭环只差 Frederic 的正式收取。

## 背景与问题

cf6444c3e1bb 统一 idle cputime 记账后，idle 退出时 `kcpustat_dyntick_stop()` 已把 idle 时间计到当下，重启的 tick 首个周期又整记一个 TICK_NSEC——重叠部分双计，`/proc/stat` idle 超墙钟。v1 用「记录 overlap、首个 tick 剔除」修复；v2 把 overlap 语义改为按周期累积（`idle_tick_period` 记录当前周期起点，周期切换时清零累积），闭合「停-启-停-启」嵌套边界。今天无新背景，进入收尾打磨阶段。

## 技术方案

（承接 v2 框架）v3（`<20261007142950.547604-1-stian@itx.no>`，3 文件 +55/−13）四项改动，全部来自 Frederic 的 nit：

1. **加防护 WARN**：`kcpustat_dyntick_stop()` 里 `tick_start = max(tick_start, kc->idle_dyntick_entry)` 之后仍 `WARN_ON_ONCE(now < tick_start)`——时间倒退是异常状态，应显式报警而非静默记 0。
2. **去原子化**：overlap 的读清从 `__this_cpu_xchg()` 改为普通读写——该路径本就只在本地 CPU 的 dyntick stop/start 与 tick 之间流动，无并发读者，原子交换是多余开销。
3. **`ts->last_tick` 总是更新**：把 forward 后的到期值存进 `ts->last_tick`，紧随其后的 tick 重启不再重复做一次「向前推进周期」的除法/换算。
4. **删 `tick_nohz_full_cpu()` 前置检查**：该分支最终都会落入 `vtime_generic_enabled_this_cpu()` 判定，nohz_full 的特判是冗余层。

其余不变：`kernel_cpustat` 三字段（`idle_dyntick_entry`/`idle_tick_period`/`idle_tick_overlap`）、`kcpustat_dyntick_stop(now, tick_start)` 签名、`irqtime_account_process_tick()` 从「ticks 数」改为直接收 `cputime`（ticks * TICK_NSEC 的换算上移）、`tick_cputime()` 在首个 tick 只记 `TICK_NSEC − overlap`。

## 版本演进与当前进展

- v1（10-04）：overlap 记录 + 首个 tick 剔除（sched-20261005-002）。
- v2（10-05）：周期累积 + helper 化（sched-20261006-003）。
- v3（10-07 22:29，Stian）：四条 nit 全落实；复测 SPARC T7-1 与 x86_64 KVM guest，覆盖 `nohz_full=1`、无 IRQ_TIME_ACCOUNTING、`highres=off` 组合，**结果与 v2 相同**。
- Frederic 的 nit 邮件（19:38）与 v3（22:29）同日闭环，速度极快；差最后一步收取。

## Maintainer 意见与讨论焦点

**Frederic Weisbecker**（涉事代码维护者）10-07 对 v2 的四条意见（全文极简，均被 v3 采纳）：① `now < tick_start` 应 warn；② 不需要 atomic xchg，普通 swap 即可；③ 应总是更新 `ts->last_tick`，dyntick stop 时就不用再做第二遍除法；④ 不要检查 `tick_nohz_full_cpu()`，反正会落到 `vtime_generic_enabled_this_cpu()`。

焦点已从「方案对不对」完全转到「实现细节干净度」——这是收取前最后的打磨信号。无分歧。

## 合入评估

*likelihood=high*。维护者全程驱动 review（v1 思路确认 → v2 边界追问 → v3 nit 收尾）、三轮同周完成、每版都有跨架构复测、`Fixes:` + regzbot 回归登记齐全；v3 落实了全部意见且无新增问题。*blocking_issues*：Frederic 的正式收取/应用动作。*next_action*：预期进 tick/sched 修复通道并 `Cc: stable`（回归自 v7.2-rc1，stable 窗口开放）；回合 OLK-6.6 前需确认目标内核有 cf6444c3e1bb 的对应回合（该 commit 若未回合则无此 bug）。

## 效果评估

v3 复测与 v2 相同：SPARC T7-1 与 x86_64 KVM guest 的 `/proc/stat` idle/墙钟比回到 ~1.000x（v1 时代实测：SPARC 1.44→1.0000、KVM 1.53→0.998）。已知残余（steal time + 3.7ms 睡眠 ping-pong 下 +0.3%~+1.3%）为预存问题、超本系列范围，需另行调查（承自 sched-20261006-003）。

## 我可以参与的点

- `review`：v3 已接近收取，复核点剩两个——`WARN_ON_ONCE(now < tick_start)` 在 clocksource 回拨（如 KVM 迁移）下的误报率，以及 `irqtime_account_process_tick()` 签名从 ticks 到 cputime 后所有调用方的单位一致性。
- 回合视角：OLK-6.6 若已回合 cf6444c3e1bb（tick/sched 统一记账），此修复应同步回合；`idle_tick_*` 三字段是 `kernel_cpustat` ABI 内部结构变更，回合时注意与发行版 `/proc/stat` 读取路径的兼容。

## 参考链接

- v3 补丁: https://lore.kernel.org/all/20261007142950.547604-1-stian@itx.no/
- Frederic 的 nit: https://lore.kernel.org/all/asYvKTW5qrxi3Wlp@localhost.localdomain/
- 相关文章：[[sched-20261004-002]]（回归报告）、[[sched-20261005-002]]（v1）、[[sched-20261006-003]]（v2）

---
id: sched-20261007-002
date: '2026-10-07'
subject: 'sched/cputime: Don''t account idle time twice after dyntick-idle'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20261007142950.547604-1-stian@itx.no>'
lore_url: 'https://lore.kernel.org/all/20261007142950.547604-1-stian@itx.no/'
authors:
  - 'Stian Halseth'
maintainers_involved:
  - 'Frederic Weisbecker'
current_version: v3
patch_series:
  - version: v1
    msgid: '<20261004184701.4112237-1-stian@itx.no>'
    date: '2026-10-04'
    summary: 'kernel_cpustat 记录 overlap，首个 tick 剔除'
    review_outcome: 'Frederic 认可思路，指出嵌套覆盖边界'
  - version: v2
    msgid: '<20261005194010.168299-1-stian@itx.no>'
    date: '2026-10-05'
    summary: 'overlap 按 tick 周期累积；helper 替代 ifdef'
    review_outcome: 'Frederic 三问澄清边界；Stian 确认 v1/v2 实测无差'
  - version: v3
    msgid: '<20261007142950.547604-1-stian@itx.no>'
    date: '2026-10-07'
    summary: '四条 nit 落实：WARN 防护、去原子化、last_tick 总是更新、删 nohz_full 特判'
    review_outcome: '待 Frederic 正式收取'
upstream_commit: null
fixes_commit: 'cf6444c3e1bb'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - 'Frederic 的正式收取/应用动作未发生'
  next_action: '预期进 tick/sched 修复通道并 Cc: stable'
generated_at: '2026-10-08T01:00:00'
contribution_opportunities:
  - kind: review
    detail: '复核 WARN 误报率与 cputime 签名改动的单位一致性'
source_email_count: 2
related_articles:
  - sched-20261004-002
  - sched-20261005-002
  - sched-20261006-003
tags:
  - nohz
  - tick
---
