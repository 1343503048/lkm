---
id: sched-20261031-001
date: 2026-10-31
subject: 'sched/cputime: Don''t warn when the tick period starts after idle exit'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261025100202.2584654-1-stian@itx.no>
lore_url: https://lore.kernel.org/all/20261025100202.2584654-1-stian@itx.no/
authors:
- Stian Halseth
maintainers_involved:
- Frederic Weisbecker
current_version: v2
patch_series:
- version: v1
  msgid: <20261025100202.2584654-1-stian@itx.no>
  date: 2026-10-25
  summary: 删掉 kcpustat_dyntick_stop() 的误报 WARN；commit message 写错变量名与时钟源
  review_outcome: Paul Menzel、Breno Leitao 报告命中该 WARN
- version: v2
  msgid: <20261031081408.3378884-1-stian@itx.no>
  date: 2026-10-31
  summary: 代码不变，重写 commit message，补 Breno/Linus Reported-by
  review_outcome: Kayra Reviewed-by；Frederic 核对 clocksource 切换记账中
upstream_commit: null
fixes_commit: 96a494c9cfd8
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - Frederic 对 clocksource 切换记账的最后确认尚未完成
  next_action: Frederic 给最终 ACK 后合入 sched/urgent 或随 v7.4 修复进 tip
contribution_opportunities:
- kind: testing
  description: x86 上复现 clocksource 切换后首个 idle 周期的 WARN，验证 v2 后消失并回帖 Tested-by
- kind: review
  description: 核对 ts->last_tick / tick_start 时序推演，确认删警告后无重复或漏记账
generated_at: '2026-11-01T09:00:00'
source_email_count: 7
related_articles: []
tags:
- nohz
- tick
- regression
title: 'sched/cputime: Don''t warn when the tick period starts after idle exit'
layout: article
---

## TL;DR
Stian Halseth 的 v2 补丁删掉 `kcpustat_dyntick_stop()` 里一条误报的 `WARN_ON`：x86 在 jiffies→tsc-early 时钟源切换后的第一个 idle 周期里，idle 结束可能早于下一个 tick 周期的起点，此时**并没有重复记账**，只是警告判断写错。Linus 本人、Paul Menzel、Breno Leitao 各自在真机/boot 时命中该 WARN splat。Kayra Cizmeci 已给 Reviewed-by，Frederic Weisbecker（nohz 维护者）正深入核对时钟源切换的记账细节，准备给最终 ACK。

## 背景与问题
v2 补丁正文给出的机制（这也是回归根源）：在 jiffies 时钟源上 ktime 只在 tick 时前进。时钟源在某 tick 之后 `d` 时间切换到 tsc-early，这 `d` 被丢掉——ktime 从上一个 tick 的值继续，而下一次 tick 在 `TICK_NSEC` 后到来，此时 ktime 只前进了 `TICK_NSEC - d`，但 `tick_periodic()` 仍给 `tick_next_period` 加上完整 `TICK_NSEC`，于是它领先 ktime 约 `d`。NOHZ 启动时 `tick_init_jiffy_update()` 把它取整到 `TICK_NSEC` 倍数并把 sched timer 武装在那里（几乎两个 tick 之后），tick stop 把它存为 `ts->last_tick`，于是「idle 结束早于 `ts->last_tick - TICK_NSEC`」时看到的 tick 周期起点还在未来。该 `WARN_ON` 由 `96a494c9cfd8`（"sched/cputime: Don't account idle time twice after dyntick-idle"）引入，但这里并无重复记账，纯属误报。

## 技术方案
补丁直接**删除该警告**（`kernel/sched/cputime.c`，+6/-1）。Stian 在 v2 回帖中说明为何不改 tick 对齐本身：当前是 v7.3/v7.4 窗口内的回归修复，改动 tick 初始化（例如时钟源离开 jiffies 时重对齐 `tick_next_period`）风险更大，留作后续 follow-up。Kayra Cizmeci 用 4 个 tick 的时序图核对后确认「这段代码现在算得对」。

## 版本演进与当前进展
*current_version: v2*。

- v1（2026-10-25，`<20261025100202.2584654-1-stian@itx.no>`）：初版补丁，commit message 写错了变量名与时钟源。
- v2（2026-10-31，`<20261031081408.3378884-1-stian@itx.no>`）：代码与 v1 完全一致，仅重写 commit message，并把 Breno Leitao、Linus Torvalds 补进 Reported-by（`Fixes: 96a494c9cfd8`）。

## Maintainer 意见与讨论焦点
- **Frederic Weisbecker（nohz maintainer）**：正在核对 `tk_setup_internals()` 是否真如 Stian 所说保留旧时钟的最后值——他用 `change_clocksource()` 加了 printk 实测 jiffies→tsc-early 切换时 ktime 只动 3µs、实际经过 736µs，向 Stian 求证。在 GIT PULL 线程里也表态「Sorry about that, Stian has a fix, I'm just trying to wrap my head around it before giving a final ACK.」
- **Kayra Cizmeci**：给出时序图核对后给 Reviewed-by，但提出「是否从根上修（tick_next_period 对齐）更好」。
- **Stian Halseth（作者）**：坚持 v2 只删警告——这是当前 release 的回归，tick 对齐改动留作 follow-up。
- 无 NAK；分歧仅在「删警告 vs 根修 tick 对齐」的取舍，已由作者说明取舍理由。

## 合入评估
*likelihood=high*。回归修复、改动极小（删一条误报 WARN）、已有 Reviewed-by、nohz 维护者正在做最终 ACK，且命中者包含 Linus（sched 维护层压力）。*blocking_issues*：Frederic 对 clocksource 切换记账的最后确认尚未完成。*next_action*：Frederic 给出最终 ACK 后合入 sched/urgent 或随 v7.4 修复进入 tip。

## 效果评估
无性能数据。作者明确「Nothing is accounted twice / the warning is the only problem / 这个 warning 是错的」，属作者基于代码路径的分析性结论；实证层面是 Linus、Paul Menzel、Breno Leitao 三人在真实硬件上命中同一 WARN splat（Breno 给出了完整寄存器与 call trace）。

## 我可以参与的点
- **testing**：在 x86 平台上复现「时钟源 jiffies→tsc-early 切换后首个 idle 周期」的 WARN，验证 v2 后 WARN 消失，回帖补 Tested-by（作者已在向 Breno 征集 Tested-by）。
- **review**：核对 `ts->last_tick` 与 `tick_start` 的时序推演，确认删警告后确实无重复/漏记账。

## 参考链接
- v2 patch: https://lore.kernel.org/all/20261031081408.3378884-1-stian@itx.no/
- v1 patch: https://lore.kernel.org/all/20261025100202.2584654-1-stian@itx.no/
- Linus 报告: https://lore.kernel.org/all/CAHk-=winC2u2D1FAX5grfq9F=bxmARxhuiQ4MvHAiJFu3iF6gw@mail.gmail.com/
- Breno Leitao 报告: https://lore.kernel.org/all/auTCQauaU733PY5z@gmail.com/
