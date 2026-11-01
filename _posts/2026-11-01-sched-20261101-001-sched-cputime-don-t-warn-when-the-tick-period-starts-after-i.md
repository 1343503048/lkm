---
id: sched-20261101-001
subject: 'sched/cputime: Don''t warn when the tick period starts after idle exit'
date: 2026-11-01
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <20261031081408.3378884-1-stian@itx.no>
lore_url: https://lore.kernel.org/all/20261031081408.3378884-1-stian@itx.no/
authors:
- Stian Halseth
maintainers_involved:
- Ingo Molnar
- Frederic Weisbecker
current_version: v2
patch_series:
- version: v1
  msgid: null
  date: 2026-10-28
  summary: 初版与机制解释，回应 Frederic Weisbecker 对时钟源切换成因的追问
  review_outcome: Frederic 多轮追问后确认机制清晰（Ah yes! You got it!）
- version: v2
  msgid: <20261031081408.3378884-1-stian@itx.no>
  date: 2026-10-31
  summary: 正式补丁，补充完整成因说明与 Fixes/Reported-by 标签
  review_outcome: Frederic Weisbecker 与 Kayra Cizmeci Reviewed-by；Ingo 合入 tip/sched/urgent
upstream_commit: b327e63683a2b894b500027375342c25222b58ef
fixes_commit: 96a494c9cfd8
merged_branch: tip/sched/urgent
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入 tip/sched/urgent，Ingo 已发 GIT PULL 至 Linus，无需进一步动作
contribution_opportunities: []
generated_at: '2026-11-02T09:00:00'
source_email_count: 7
related_articles: []
tags:
- nohz
- idle
- tick
title: 'sched/cputime: Don''t warn when the tick period starts after idle exit'
layout: article
---

## TL;DR

修复 `kcpustat_dyntick_stop()` 在时钟源从 jiffies 切换到 tsc-early 后可能触发的 cputime 假阳性 WARN（日志噪音）。补丁已由 Ingo Molnar 合入 tip/sched/urgent（commit `b327e63683a2b894b500027375342c25222b58ef`），并随 [GIT PULL] scheduler fix 发往 Linus，将进入 v7.4-rc1。

## 背景与问题

Stian Halseth 发现 x86 上 CPU 首次进入 idle 且 tick 停止时会触发 `kcpustat_dyntick_stop()` 的 WARN。根因是 jiffies 时钟源下 ktime 只在 tick 时前进：当时钟源在某次 tick 之后 d 时间切换到 tsc-early，这段 d 会丢失——ktime 从上一次 tick 的值继续走，下一次 tick 在最后一次 tick 之后 TICK_NSEC 到来，但 ktime 只前进了 TICK_NSEC - d，而 `tick_periodic()` 仍把完整 TICK_NSEC 加到 `tick_next_period`，使其领先 ktime d。NOHZ 启动时 `tick_init_jiffy_update()` 将其向上取整到 TICK_NSEC 倍数，sched timer 被设在距 now 近两个 tick 之后，idle 退出早于 `ts->last_tick - TICK_NSEC` 时即误判 tick period 落在未来。实际上并不会重复记账——第一个 tick 覆盖的周期从 idle 退出之后才开始，现有代码已正确处理，因此该 WARN 是假阳性，应删除（降级）。

## 技术方案

删除该误告警，不再 WARN：因为「tick period 从 idle 退出后才开始」是合法场景，第一个 tick 已正确覆盖该周期。改动 `kernel/sched/cputime.c`（1 处，+6/-1）。`Fixes: 96a494c9cfd8`（"sched/cputime: Don't account idle time twice after dyntick-idle"）；`Reported-by:` Paul Menzel、Breno Leitao、Linus Torvalds。

## 版本演进与当前进展

- **v1**（2026-10-28，部分早于本次拉取窗口）：初版与机制解释，Frederic Weisbecker 多轮追问后在邮件里确认「Ah yes! You got it!」「Now that's clear!」。
- **v2**（2026-10-31）：正式补丁，补充完整成因说明与 Fixes/Reported-by/Reviewed-by 标签；Frederic 与 Kayra Cizmeci 给出 Reviewed-by。
- **当前**：已合入 tip/sched/urgent（Ingo 于 2026-11-01 提交），进入 [GIT PULL] scheduler fix（sched-urgent-2026-11-01）；kernel test robot 报告该 commit 42 个 config 构建成功。

## Maintainer 意见与讨论焦点

Frederic Weisbecker 全程 review：先质疑时钟源切换的成因，理解后给出「Makes sense」「Now that's clear!」，最终 Reviewed-by。Kayra Cizmeci 亦 Reviewed-by。无分歧、无 NAK。Ingo Molnar 直接提交并明确将其排入 v7.4-rc1（「I've queued up the fix and will send it to Linus soon so that it gets into -rc1」）。

## 合入评估

已合入（merged）。tip/sched/urgent commit `b327e63683a2b894b500027375342c25222b58ef`；Ingo 已发 [GIT PULL] scheduler fix，目标 v7.4-rc1。无阻塞项，无需进一步推进。

## 效果评估

消除假阳性 WARN（日志噪音），无性能影响。kernel test robot 在 tip/sched/urgent 该 commit 上 42 个 config 全部构建成功（1 个跳过）。

## 我可以参与的点

已合入，当前阶段暂无明显参与空间，可持续观察其是否随 v7.4-rc1 进入 mainline。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261031081408.3378884-1-stian@itx.no/
- tip-bot commit: https://git.kernel.org/tip/b327e63683a2b894b500027375342c25222b58ef
- GIT PULL: https://lore.kernel.org/all/aublQi32yfcCKZ98@gmail.com/
- 回归报告（Closes）: https://lore.kernel.org/all/bfe9b14a-6e65-41c5-b638-26f6e033788b@molgen.mpg.de/
