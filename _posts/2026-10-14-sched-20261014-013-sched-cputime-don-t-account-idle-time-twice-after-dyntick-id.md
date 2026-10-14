---
id: sched-20261014-013
subject: 'sched/cputime: Don''t account idle time twice after dyntick-idle'
date: 2026-10-14
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261007142950.547604-1-stian@itx.no>
lore_url: https://lore.kernel.org/all/20261007142950.547604-1-stian@itx.no/
authors:
- Stian Halseth
maintainers_involved:
- Frederic Weisbecker
current_version: v3
patch_series:
- version: v1
  msgid: <20261004184701.4112237-1-stian@itx.no>
  date: 2026-10-04
  summary: kernel_cpustat 记录 overlap，首个 tick 剔除
  review_outcome: Frederic 认可思路，指出嵌套覆盖边界
- version: v2
  msgid: <20261005194010.168299-1-stian@itx.no>
  date: 2026-10-05
  summary: overlap 按 tick 周期累积；helper 替代 ifdef
  review_outcome: Frederic 三问澄清边界
- version: v3
  msgid: <20261007142950.547604-1-stian@itx.no>
  date: 2026-10-07
  summary: 四条 nit 落实：WARN 防护、去原子化、last_tick 总是更新、删 nohz_full 特判
  review_outcome: Frederic 给出 Reviewed-by
upstream_commit: null
fixes_commit: cf6444c3e1bb
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - Frederic 的收取/应用动作未发生
  next_action: '预期进 tick/sched 修复通道并 Cc: stable'
contribution_opportunities:
- kind: review
  description: 复核 WARN 误报率与 cputime 签名改动单位一致性
generated_at: '2026-10-15T01:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261004-002
- sched-20261005-002
- sched-20261006-003
- sched-20261007-002
tags:
- nohz
- idle
title: 'sched/cputime: Don''t account idle time twice after dyntick-idle'
layout: article
---

> **subject**：sched/cputime: Don't account idle time twice after dyntick-idle

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/04/sched-20261004-002-tick-sched-proc-stat-idle-time-exceeds-wall-time-since-v7-2.html">sched-20261004-002</a>：Stian Halseth 报告 v7.2-rc1 起回归——NO_HZ_IDLE + TICK_CPU_ACCOUNTING 下 `/proc/stat` idle 时间超墙钟（SPARC T7-1 最差 1.44x、KVM guest 1.53x），根因 `cf6444c3e1bb` 统一记账后 dyntick-idle 与重启 tick 首周期双计。
- <a class="article-ref" href="/lkm/2026/10/05/sched-20261005-002-sched-cputime-don-t-account-idle-time-twice-after-dyntick-id.html">sched-20261005-002</a>：v1 修复发出，Frederic 认可思路但指出嵌套边界。
- <a class="article-ref" href="/lkm/2026/10/06/sched-20261006-003-sched-cputime-don-t-account-idle-time-twice-after-dyntick-id.html">sched-20261006-003</a>：v2 改为按周期累积，Frederic 三连追问澄清边界。
- <a class="article-ref" href="/lkm/2026/10/07/sched-20261007-002-sched-cputime-don-t-account-idle-time-twice-after-dyntick-id.html">sched-20261007-002</a>：Frederic 对 v2 给「Looks good, just a few nits」；Stian 当晚发 v3 逐条落实，跨架构复测通过。
- <a class="article-ref" href="/lkm/2026/10/14/sched-20261014-013-sched-cputime-don-t-account-idle-time-twice-after-dyntick-id.html">sched-20261014-013</a>（今天）：**Frederic Weisbecker 对 v3 给出 `Reviewed-by`**（「Reviewed-by: Frederic Weisbecker，Thank you very much!」），review 闭环，只差收取动作。

## 背景与问题
（承接 20261004-002 → 20261007-002）`cf6444c3e1bb` 统一 idle cputime 记账后，idle 退出时 `kcpustat_dyntick_stop()` 已计到当下，重启 tick 首周期又整记一个 `TICK_NSEC`——重叠双计，`/proc/stat` idle 超墙钟。v3 已落实四条 nit（WARN 防护、去原子化、`last_tick` 总是更新、删 nohz_full 特判）。今日无新背景，为最终 review 收取。

## 技术方案
（承接 v3，`<20261007142950.547604-1-stian@itx.no>`）今日无新代码，Frederic 对 v3 正式 `Reviewed-by`，确认 v3 的 `kernel_cpustat` 三字段（`idle_dyntick_entry`/`idle_tick_period`/`idle_tick_overlap`）、`kcpustat_dyntick_stop(now, tick_start)` 签名、`irqtime_account_process_tick()` 收 cputime、首个 tick 只记 `TICK_NSEC − overlap` 等改动方向全部通过。

## 版本演进与当前进展
v1（10-04）→ v2（10-05）→ v3（10-07）→ 今日 Frederic `Reviewed-by`。四轮同周完成，每版跨架构复测，v3 落实全部 nit 后无新增问题。

## Maintainer 意见与讨论焦点
- **Frederic Weisbecker**（涉事代码维护者，今日）：对 v3 给出 `Reviewed-by` 并致谢，无剩余意见。
- 无分歧；review 完全闭环，只差应用/收取动作。

## 合入评估
*likelihood=high*。维护者全程驱动 review、v3 已获 `Reviewed-by`、`Fixes:` + regzbot 回归登记齐全。*blocking_issues*：Frederic 的收取/应用动作未发生。*next_action*：预期进 tick/sched 修复通道并 `Cc: stable`（回归自 v7.2-rc1，stable 窗口开放）；回合 OLK-6.6 前需确认目标内核有 `cf6444c3e1bb` 的对应回合。

## 效果评估
v3 复测：SPARC T7-1 与 x86_64 KVM guest 的 `/proc/stat` idle/墙钟比回到 ~1.000x（v1 时代实测 SPARC 1.44→1.0000、KVM 1.53→0.998）。已知残余（steal time + 3.7ms 睡眠 ping-pong 下 +0.3%~+1.3%）为预存问题、超本系列范围。

## 我可以参与的点
- review：v3 已获 `Reviewed-by`，剩余可复核点——`WARN_ON_ONCE(now < tick_start)` 在 clocksource 回拨（如 KVM 迁移）下的误报率，及 `irqtime_account_process_tick()` 签名从 ticks 到 cputime 后所有调用方单位一致性。
- 回合视角：OLK-6.6 若已回合 `cf6444c3e1bb`，此修复应同步回合；`idle_tick_*` 三字段是 `kernel_cpustat` 内部结构变更，回合时注意与发行版 `/proc/stat` 读取路径兼容。

## 参考链接
- v3 补丁：https://lore.kernel.org/all/20261007142950.547604-1-stian@itx.no/
- Frederic 的 RB：https://lore.kernel.org/all/as9y6gQSpDPq3z9A@localhost.localdomain/
