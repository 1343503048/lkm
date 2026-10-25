---
id: sched-20261025-005
date: 2026-10-25
subject: 'sched/cputime: Don''t warn when the tick period starts after idle exit'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261025100202.2584654-1-stian@itx.no>
lore_url: https://lore.kernel.org/all/20261025100202.2584654-1-stian@itx.no/
authors:
- Stian Halseth
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261025100202.2584654-1-stian@itx.no>
  date: 2026-10-25
  summary: 去掉 kcpustat_dyntick_stop() 的 now < tick_start 误报 WARN，改 now > tick_start
    才累计
  review_outcome: 无当日 review
upstream_commit: null
fixes_commit: 96a494c9cfd8
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 当日缓存未见 review
  next_action: 等 sched 维护者 review 收取
contribution_opportunities:
- kind: testing
  description: 不同 clocksource 切换时序/虚拟化环境复现 boot 期 WARN 消失
- kind: review
  description: 核对 now > tick_start 与 now >= tick_start 的边界差异
generated_at: '2026-10-26T09:00:00'
source_email_count: 3
related_articles: []
tags:
- nohz
- idle
title: 'sched/cputime: Don''t warn when the tick period starts after idle exit'
layout: article
---

## TL;DR
Stian Halseth 修 `kcpustat_dyntick_stop()` 的误报 WARN：时钟源从 refined-jiffies 切到 tsc-early（或 KVM 下 jiffies→hpet）时 ktime 落后 tick 至多一个 tick，NOHZ 排的 sched timer 可能在 now 之后一个 tick 以上才到期，idle 提前退出就命中 `now < tick_start` 的 `WARN_ON_ONCE`。该场景 tick restart 会保留 `last_tick`、首个 tick 覆盖 idle 退出后的区间、无重叠，记账本就正确，WARN 是误报，直接去掉。

## 背景与问题
由 Paul Menzel 的 WARN 报告触发（Dell XPS 13 9360，Intel Kaby Lake，commit `96a494c9cfd8` 之后 boot 首个 idle 期 WARN）。作者判断「警告本身就是 bug，记账本身正确」，随后发出本补丁。

## 技术方案
把 `if (!WARN_ON_ONCE(now < tick_start))` 改为 `if (now > tick_start)`，并加注释解释：jiffies clocksource 切换后 tick 可能被 arm 到 one tick 之后，period 可能尚未开始。`kernel/sched/cputime.c` +6/−1。

## 版本演进与当前进展
*current_version: v1*（`<20261025100202.2584654-1-stian@itx.no>`）。作者 10-25 先回帖（`<f18f9548127bbc...@itx.no>`）说明判断与后续补丁，随后发补丁。

## Maintainer 意见与讨论焦点
无维护者表态（当日）。Paul Menzel 为报告者，非维护者。

## 合入评估
*likelihood=high*。作者即该 WARN 引入补丁（`96a494c9cfd8`）的原作者，判断权威；补丁极小、去误报 WARN。*blocking_issues*：当日缓存未见 review。*next_action*：等 sched 维护者 review 收取。

## 效果评估
无量化数据。作者 instrumentation：KVM guest 中 HZ=250、jiffies→hpet 切换后 sched timer 被 arm 到 now 之后 5.9ms，tick stop 保存的 `last_tick` 超前一个 tick 以上；打补丁后无 warning。属去误报，记账正确性不受影响。

## 我可以参与的点
- *kind: testing*：在不同 clocksource 切换时序/虚拟化环境复现 boot 期 WARN 消失。
- *kind: review*：核对 `now > tick_start` 与 `now >= tick_start` 语义在边界上的差异。

## 参考链接
- patch: https://lore.kernel.org/all/20261025100202.2584654-1-stian@itx.no/
- bug report (Closes): https://lore.kernel.org/all/bfe9b14a-6e65-41c5-b638-26f6e033788b@molgen.mpg.de/
