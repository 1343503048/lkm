# sched/cputime: Don't warn when the tick period starts after idle exit

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261025-005（v1）：Stian Halseth 修 `kcpustat_dyntick_stop()` 的误报 WARN——时钟源从 refined-jiffies 切到 tsc-early（或 KVM 下 jiffies→hpet）时 ktime 落后 tick 至多一个 tick，NOHZ 排的 sched timer 可能在 now 之后一个 tick 以上才到期，idle 提前退出就命中 `now < tick_start` 的 `WARN_ON_ONCE`；该场景记账本就正确，WARN 是误报，直接去掉。
- sched-20261027-008：Frederic Weisbecker 追问触发场景机理，作者澄清是 `tick_next_period` 跑在前面（非 ktime 倒退），并给出 KVM 客户机 HZ=250 下 2.3ms/0.66ms 的具体量化。
- sched-20261029-010（今天）：作者进一步用「jiffies → tsc-early」的时序图 + QEMU 客户机实测，把机理钉死：切换发生在 last tick 之后 d 时刻，一个 tick 的**真实时间**已过但 **ktime 没算**这段 d（tsc 从切换点才起算），于是 `ktime_get() == jiffies + TICK_NSEC - d`，`tick_next_period` 落在 `ktime_get() + d`（超前 d）。实测：切换时两者均为 329532326，下一 tick ktime 331212239（1.68ms 后），d=2.32ms，`tick_next_period` 变 333532326（超前 2.32ms）。

## 背景与问题
（承接 20261025-005）由 Paul Menzel 的 WARN 报告触发（Dell XPS 13 9360，Kaby Lake）。核心是 NOHZ 下 clocksource 从 jiffies 类切到 tsc-early 类时，`last_tick`/`tick_next_period` 与 `ktime_get()` 之间出现至多一个 tick 的错位：jiffies 没有把「切换前那一段 d」计入，而 tsc 只从切换点起算，导致 `tick_next_period` 相对 ktime 超前 d。idle 提前退出时 `ktime_get()` 还没走到 `tick_next_period`，命中 `now < tick_start` 的 WARN——但记账本身正确，WARN 是误报。

## 技术方案
（承接 v1）把 `if (!WARN_ON_ONCE(now < tick_start))` 改为 `if (now > tick_start)`，并加注释解释 jiffies clocksource 切换后 tick 可能被 arm 到 one tick 之后、period 可能尚未开始。今日无代码变更，是把「tick_next_period 超前 d」的机理用图与时序彻底讲清，支撑 v1 的「误报」结论。

## 版本演进与当前进展
*current_version: v1*（2026-10-25，`<20261025100202.2584654-1-stian@itx.no>`）。至今无 v2，处于机理澄清阶段：Frederic 追问 → 作者 20261027 澄清「tick_next_period 超前而非 ktime 倒退」→ 20261029 用图 + QEMU 实测把 d 的来源钉死。等 Frederic 接受该解释后补丁即可推进。

## Maintainer 意见与讨论焦点
- **Frederic Weisbecker（维护者）**：20261027 阶段追问「到底哪里出问题」、要求澄清触发机理——作者今日的图 + 实测正是回应此追问。
- 未解决焦点：Frederic 尚未对作者的完整机理给出最终 Ack；`tick_periodic()` 里 `tick_next_period += TICK_NSEC` 导致超前 d 的论证是否被完全接受，还需一次回帖确认。

## 合入评估
*likelihood=high*。补丁本身是 trivial 的 WARN 去除（改判断方向 + 注释），机理经作者三轮澄清已相当完整；只等 Frederic 对机理做最后确认。*blocking_issues*：Frederic 尚未显式 Ack 最终机理。*next_action*：Frederic 回帖确认后合入（或作者补 v2 附上图/时序说明）。

## 效果评估
无性能数据——这是去掉误报 WARN 的正确性修复。作者的量化是机理演示（QEMU 客户机：切换时 ktime==jiffies==329532326，下一 tick ktime 331212239 即 1.68ms 后，d=2.32ms，`tick_next_period` 超前 2.32ms），用于证明「一个 tick 已过但 ktime 没算 d」，非性能收益。

## 我可以参与的点
- **testing**：在含 refined-jiffies→tsc-early 切换路径（或 KVM jiffies→hpet）的机器上复现该 WARN，验证 v1 补丁后不再出现。
- **review**：核对 v1 把 `WARN_ON_ONCE(now < tick_start)` 改为 `now > tick_start` 后，是否仍覆盖「真的时间倒退」这一 WARN 原本要抓的异常情形。

## 参考链接
- lore thread（v1 补丁）: https://lore.kernel.org/all/20261025100202.2584654-1-stian@itx.no/
- 作者今日的机理图: https://lore.kernel.org/all/68f0450d47577dc4f83d32e5b0211c97ee8d24bd.camel@itx.no/
- 原始 WARN 报告（Paul Menzel）: https://lore.kernel.org/all/bfe9b14a-6e65-41c5-b638-26f6e033788b@molgen.mpg.de/

---
id: sched-20261029-010
date: 2026-10-29
subject: "sched/cputime: Don't warn when the tick period starts after idle exit"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261025100202.2584654-1-stian@itx.no>"
lore_url: "https://lore.kernel.org/all/20261025100202.2584654-1-stian@itx.no/"
authors: [Stian Halseth]
maintainers_involved: [Frederic Weisbecker]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261025100202.2584654-1-stian@itx.no>"
    date: 2026-10-25
    summary: "把 kcpustat_dyntick_stop() 里 now < tick_start 的 WARN_ON_ONCE 改为 now > tick_start 判断 + 注释"
    review_outcome: "Frederic 追问机理；作者 20261027/20261029 用图 + QEMU 实测澄清 tick_next_period 超前 d"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - "Frederic 尚未对最终机理给出显式 Ack"
  next_action: "Frederic 回帖确认机理后合入"
contribution_opportunities:
  - kind: testing
    description: "在 refined-jiffies→tsc-early（或 KVM jiffies→hpet）路径机器上复现 WARN 验证补丁"
  - kind: review
    description: "核对改判断方向后是否仍覆盖真正的时间倒退异常情形"
generated_at: "2026-10-30T09:30:00"
source_email_count: 1
related_articles: [sched-20261025-005, sched-20261027-008]
tags: [nohz]
---