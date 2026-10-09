---
id: sched-20261006-003
date: '2026-10-06'
subject: 'sched/cputime: Don''t account idle time twice after dyntick-idle'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261004184701.4112237-1-stian@itx.no>
lore_url: https://lore.kernel.org/all/20261005194010.168299-1-stian@itx.no/
authors:
- Stian Halseth
maintainers_involved:
- Frederic Weisbecker
current_version: v2
patch_series:
- version: v1
  msgid: <20261004184701.4112237-1-stian@itx.no>
  date: '2026-10-05'
  summary: 记录 dyntick-idle 与 tick 周期重叠量，首个 tick 剔除
  review_outcome: Frederic 指出嵌套 overlap 覆盖丢失 + IS_ENABLED 风格项
- version: v2
  msgid: <20261005194010.168299-1-stian@itx.no>
  date: '2026-10-06'
  summary: overlap 按 tick 周期累积（idle_tick_period）；helper 替代 IS_ENABLED
  review_outcome: Frederic 三轮追问获数据澄清；steal 残余界定为预存超范围问题
related_articles:
- sched-20261004-002
- sched-20261005-002
upstream_commit: null
fixes_commit: cf6444c3e1bb
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: Frederic 正式收取动作未发生
  next_action: Frederic 复核 v2 后收进 tick/sched 修复通道并回合 stable
generated_at: '2026-10-07T01:00:00'
tags:
- nohz
- tick
title: 'sched/cputime: Don''t account idle time twice after dyntick-idle'
layout: article
---

> **subject**：`sched/cputime: Don't account idle time twice after dyntick-idle`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/04/sched-20261004-002-tick-sched-proc-stat-idle-time-exceeds-wall-time-since-v7-2.html">sched-20261004-002</a>：Stian Halseth 报告 v7.2-rc1 起回归——NO_HZ_IDLE + TICK_CPU_ACCOUNTING 下 `/proc/stat` idle 时间超过墙钟时间（SPARC T7-1 最差 1.44x、KVM guest 1.53x），根因为 cf6444c3e1bb 统一记账后 dyntick-idle 与重启 tick 首个整周期双计。
- <a class="article-ref" href="/lkm/2026/10/05/sched-20261005-002-sched-cputime-don-t-account-idle-time-twice-after-dyntick-id.html">sched-20261005-002</a>：修复 v1 发出（`kernel_cpustat` 记录 overlap、首个 tick 剔除，六组实测回到 1.000x）；Frederic Weisbecker 认可思路但指出嵌套场景——idle 退出后短期内重入时第二次 start 覆盖前一次 overlap，首个 tick 应扣两次之和（仅对 tick X 有效）；另要求 IS_ENABLED()。
- <a class="article-ref" href="/lkm/2026/10/06/sched-20261006-003-sched-cputime-don-t-account-idle-time-twice-after-dyntick-id.html">sched-20261006-003</a>（今天）：**v2 发出**，逐条落实 Frederic 意见——overlap 改为**按 tick 周期累积**（新增 `idle_tick_period` 字段：同周期内第二次 dyntick-idle 期间 `idle_tick_overlap += now − tick_start` 而非覆盖；周期切换时清零，天然满足「只对 tick X 有效」）；IS_ENABLED() 因字段仅存在于 NO_HZ_COMMON 而无法编译，改用 NO_HZ_COMMON 块内 static inline helper + `#else` stub（仿 `kcpustat_field_dyntick()`）。Stian 实测 Frederic 场景在无 cpuidle driver/单 state 时不自发出现（f4c31b07b136 后 tick 只在唤醒 idle loop 后才停），但用 test-only 改动可复现（guest 每秒约 900 次累积）。**Frederic 随后三连追问澄清边界**：残余超额是否本补丁引入（Stian：只有 steal time 场景且比 rework 之前更小，v7.1 下 steal+ping-pong 1.338 vs v2 1.001）、v1/v2 是否有实测差（Stian：仅 test-only 强制停 tick 场景有差，正常操作无差）。Stian 总结：预存的 steal time 问题超范围，需另行调查。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/10/04/sched-20261004-002-tick-sched-proc-stat-idle-time-exceeds-wall-time-since-v7-2.html">sched-20261004-002</a> → <a class="article-ref" href="/lkm/2026/10/05/sched-20261005-002-sched-cputime-don-t-account-idle-time-twice-after-dyntick-id.html">sched-20261005-002</a>）cf6444c3e1bb 统一 idle cputime 记账后，idle 退出时 `kcpustat_dyntick_stop()` 已把 idle 时间计到当下，重启的 tick 首个周期又整记一个 TICK_NSEC——重叠部分双计，`/proc/stat` idle 超墙钟。v1 用「记录 overlap、首个 tick 剔除」修复；Frederic 指出的边界是紧凑的「停-启-停-启」序列中第二次 start 覆盖未消费的 overlap。今天 v2 把 overlap 语义改为按周期累积，边界闭合。

## 技术方案

v2（`<20261005194010.168299-1-stian@itx.no>`，3 文件 +54/−11）相对 v1 的改动：

- **累积语义**：`struct kernel_cpustat` 新增 `idle_tick_period`（当前 overlap 所属的 tick 周期起点）。`kcpustat_dyntick_stop(now, tick_start)` 中：若 `idle_tick_period != tick_start`（新周期）则重置 overlap 为 0 并记录新周期；同周期时 `idle_tick_overlap += now − max(tick_start, idle_dyntick_entry)`——Frederic 的嵌套场景（两次停/启在同一 tick 周期内）自动累加，且周期切换时清零保证旧 overlap 不会污染下一周期。
- **IS_ENABLED() 的替代**：字段只在 `!CONFIG_HAVE_VIRT_CPU_ACCOUNTING_IDLE` 的 NO_HZ_COMMON 路径存在，直接 `IS_ENABLED(CONFIG_NO_HZ_COMMON)` 编译不过；改为 NO_HZ_COMMON 块内 `static inline u64 kcpustat_tick_overlap()`（`__this_cpu_xchg` 取走累积值）+ `#else` 返回 0 的 stub，仿既有 `kcpustat_field_dyntick()` 模式。
- 其余（`tick_cputime()` 等价逻辑、`irqtime_account_process_tick` 参数改 u64 cputime）承 v1。

**Frederic 的追问与 Stian 的澄清**（三轮回帖）：

1. 「残余超额是否 patchset 重写后才出现？」——Stian 给 v7.1 / ad5a9e14ec8b（cf6444c3e1bb 之父）/ v2 三方对照：非 steal 场景重写前无问题（0.995-0.997）；steal time 场景 v7.1 本来就把 idle 期间的 steal 同时记 idle+steal（`steal, pipe ping-pong` 行 v7.1 = 1.338），重写修掉了大部分（v2 = 1.001；`steal, sleep+spin` 从 1.029 → 1.008）。
2. 「v1 与 v2 有实测差吗？」——正常操作无差；仅 test-only「每次 idle 入口都停 tick」的改动下，v2 每秒约 900 次累积而 v1 丢失。
3. Stian 定性：预存 steal time 问题（spin after wakeup 时 +0.7%~+1.4%）**超范围**，若值得另案调查。

## 版本演进与当前进展

- 10-04：回归报告 + regzbot（<a class="article-ref" href="/lkm/2026/10/04/sched-20261004-002-tick-sched-proc-stat-idle-time-exceeds-wall-time-since-v7-2.html">sched-20261004-002</a>）。
- 10-05：v1 + Frederic review（嵌套 overlap + IS_ENABLED）+ Leemhuis 关联 Ahmed Shaltout（<a class="article-ref" href="/lkm/2026/10/05/sched-20261005-002-sched-cputime-don-t-account-idle-time-twice-after-dyntick-id.html">sched-20261005-002</a>）。
- 10-06（今天）：v2（累积语义 + helper 化）；Frederic `<asTJQHcGzJmB9u33@localhost.localdomain>` → Stian `<630a98619b9c5d04b01dd1c506d432d13f724218.camel@itx.no>` → Frederic `<asTWpV1xFQ4opyB7@localhost.localdomain>` → Stian `<f9449162aaea3b43154c3981c50d9bd40340c2c0.camel@itx.no>` → Stian 收尾 `<eb598b667e74be1e54aadfd266af4435ee013e8a.camel@itx.no>`（steal 超范围）。

## Maintainer 意见与讨论焦点

- **Frederic Weisbecker**：v2 未给正式 tag，转为边界确认式追问（残余来源、v1/v2 差异）——这是收编前的最后确认节奏。
- **Stian Halseth**：对每个问题给出三方对照数据（v7.1/父 commit/v2），把「本补丁引入 vs 预存问题」的边界切干净：非 steal 双计是 cf6444c3e1bb 引入并由本补丁修复；steal 时间重叠是**更老的预存问题**、本补丁顺带改善。
- 焦点已收敛：无未决技术分歧；steal 残余被双方接受为另案。

## 合入评估

*likelihood=high*。v2 完整落实维护者全部意见（累积语义 + helper 化），维护者三轮追问均获数据化澄清，回归本身 regzbot 跟踪 + `Fixes:` + `Cc` stable 呼之欲出；剩的是 Frederic 的正式收取动作。*blocking_issues*：Frederic 尚未给 Reviewed-by/收取；steal 残余另案无人认领（非阻塞）。*next_action*：Frederic 复核 v2 后收进 tick/sched 修复通道并回合 stable（v7.2 系列回归）。

## 效果评估

v2 测试（/proc/stat 对比 CLOCK_MONOTONIC，60s 窗口）：

| 平台/负载 | v1 | v2 |
|---|---|---|
| SPARC T7-1 HZ=100 busiest CPU | 1.0000 | 1.0001 |
| SPARC T7-1 3.7/25ms 睡眠 | 1.0001/0.9996 | 1.0000/0.9998 |
| SPARC T7-1 pipe ping-pong | — | 1.0000 |
| KVM guest HZ=250 3.7ms | 0.998（前 1.505） | 0.997 |
| 同 guest pipe ping-pong | — | 1.000（前 1.152） |
| 同 guest 9ms 睡眠 | 0.982 | 0.985 |

三方对照（steal 相关，loaded vCPU 每 wall 秒）：`steal+sleep+spin` v7.1=1.029 / 父 commit=1.028 / v2=1.008；`steal+ping-pong` 1.338/1.341/1.001。test-only 强制停 tick 下 v2 每秒 ~900 次累积（v1 丢失）。-1.5%（9ms 长睡眠）为 hypervisor 迟投递，承 v1 论证。

## 我可以参与的点

- `testing`：在 CONFIG_VIRT_CPU_ACCOUNTING_GEN（vtime）与 s390/POWER 等原生 VIRT_CPU_ACCOUNTING_NATIVE 平台复测——v2 的 stub 路径（无 NO_HZ_COMMON 字段）在这些配置下的行为尚无第三方数据。
- `new_patch`：认领 steal time 残余问题（spin-after-wakeup +0.7%~+1.4%）——Stian 已声明超范围，root cause（idle 期间 steal 与 idle 的重叠记账）有 v7.1 基线数据可用，适合独立小系列。

## 参考链接

- v2 补丁: https://lore.kernel.org/all/20261005194010.168299-1-stian@itx.no/
- Frederic 追问 1: https://lore.kernel.org/all/asTJQHcGzJmB9u33@localhost.localdomain/
- Stian 三方对照: https://lore.kernel.org/all/630a98619b9c5d04b01dd1c506d432d13f724218.camel@itx.no/
- Frederic 追问 2: https://lore.kernel.org/all/asTWpV1xFQ4opyB7@localhost.localdomain/
- Stian v1/v2 差异说明: https://lore.kernel.org/all/f9449162aaea3b43154c3981c50d9bd40340c2c0.camel@itx.no/
- Stian 范围界定: https://lore.kernel.org/all/eb598b667e74be1e54aadfd266af4435ee013e8a.camel@itx.no/
