# sched/cputime: Don't warn when the tick period starts after idle exit

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261025-005（v1）：Stian Halseth 修 `kcpustat_dyntick_stop()` 的误报 WARN——时钟源从 refined-jiffies 切到 tsc-early（或 KVM 下 jiffies→hpet）时 ktime 落后 tick 至多一个 tick，NOHZ 排的 sched timer 可能在 now 之后一个 tick 以上才到期，idle 提前退出就命中 `now < tick_start` 的 `WARN_ON_ONCE`；该场景记账本就正确，WARN 是误报，直接去掉。
- sched-20261027-008（今天）：Frederic Weisbecker 追问触发场景的机理，作者澄清是 `tick_next_period` 跑在前面（非 ktime 倒退），并给出 KVM 客户机 HZ=250 下 2.3ms/0.66ms 的具体量化。

## 背景与问题
（承接 20261025-005）由 Paul Menzel 的 WARN 报告触发（Dell XPS 13 9360，Kaby Lake）。作者的判断是「警告本身就是 bug、记账本身正确」。今日澄清的关键点：NOHZ 下 refine-jiffies 不是合适的 clocksource（不该更新 `last_tick`），但 `last_tick` 的首值来自 sched timer expiry（`tick_next_period` 向上取整到 tick 倍数），在 KVM 客户机上首个 expiry 被推后了 2.3ms。

## 技术方案
（承接 v1）把 `if (!WARN_ON_ONCE(now < tick_start))` 改为 `if (now > tick_start)`，并加注释解释 jiffies clocksource 切换后 tick 可能被 arm 到 one tick 之后、period 可能尚未开始。今日无代码变更，为讨论机理。

## 版本演进与当前进展
*current_version: v1*（`<20261025100202.2584654-1-stian@itx.no>`）。Frederic 与作者就触发机理往返一轮。

## Maintainer 意见与讨论焦点
Frederic Weisbecker 起初困惑「ktime 是否倒退」，并指出 refine-jiffies 不适合 nohz 时钟源、`last_tick` 不应在 refine-jiffies 期间更新。作者澄清非倒退而是 `tick_next_period` 超前：jiffies 下 ktime 只在 tick 移动，切源后 ktime 在 tick 间继续走，而下一个 tick 仍加满 `TICK_NSEC`，`tick_next_period` 就跑到 now 前面。作者邀 Frederic 继续 challenge 其推理（自认新手、可能有误读）。

## 合入评估
*likelihood=medium*。方向（去 WARN）无异议，但 Frederic 尚未完全认可触发机理，可能还需收敛 `last_tick` 在非 nohz 时钟源下的处理方式。*blocking_issues*：触发机理的解释尚未获 Frederic 最终确认。*next_action*：作者与 Frederic 继续核对机理，必要时调整补丁范围。

## 效果评估
无性能数据。属误报 WARN 清理。

## 我可以参与的点
- *kind: discussion*：协助核对 refined-jiffies 时期 `last_tick` 更新与 nohz sched timer 排布的正确性。

## 参考链接
- 线程: https://lore.kernel.org/all/20261025100202.2584654-1-stian@itx.no/

---
id: sched-20261027-008
date: 2026-10-27
subject: "sched/cputime: Don't warn when the tick period starts after idle exit"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20261025100202.2584654-1-stian@itx.no>'
lore_url: 'https://lore.kernel.org/all/20261025100202.2584654-1-stian@itx.no/'
authors:
  - 'Stian Halseth'
maintainers_involved:
  - 'Frederic Weisbecker'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20261025100202.2584654-1-stian@itx.no>'
    date: 2026-10-25
    summary: '去掉 now < tick_start 的误报 WARN，改为 now > tick_start'
    review_outcome: 'Frederic 追问机理，作者澄清 tick_next_period 超前'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - '触发机理解释尚未获 Frederic 最终确认'
  next_action: '与 Frederic 继续核对机理，必要时调整补丁范围'
contribution_opportunities:
  - kind: discussion
    description: '核对 refined-jiffies 时期 last_tick 更新与 nohz sched timer 排布的正确性'
generated_at: '2026-10-28T09:00:00'
source_email_count: 2
related_articles:
  - sched-20261025-005
tags:
  - nohz
---