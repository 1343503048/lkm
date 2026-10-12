# sched/deadline: keep nohz_full tickless while the fair server is deferred

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261005-004：Ionut Nechita 落成 RFC——在 nohz_full 核上把「武装 fair server 保 CFS 带宽」与「为 server 保持 tick」拆开，deferred（节流等 dl_timer）状态下不强制 tick。
- sched-20261012-019（今天）：Juri Lelli 回帖认可方向（"approach seems promising"），要求作者发 v3（补 SCX 支持）并基于 tip/sched/core，便于 review 与测试。

## 背景与问题

（承接 20261005-004）nohz_full 核上为保 CFS 带宽需要武装 fair server（`dl_server_start()`），但此前逻辑把「保 tick」与「武装 server」绑在一起，导致即使 server 处于 deferred（节流等待 dl_timer）状态也强制保持 tick，破坏 tickless。

## 技术方案

（承接 20261005-004）把两个关注点拆开：`sched_can_stop_tick()` 只负责武装 server（RT+CFS 共存且有 runtime 时 `dl_server_start()`），deferred 状态下不强制 tick；`inc_dl_tasks()/dec_dl_tasks()` 为 dl server 维护 tick 需求。

## 版本演进与当前进展

v1（10-05）→ 今日（10-12）Juri 认可并要 v3（含 SCX 支持）+ 重基 tip/sched/core。

## Maintainer 意见与讨论焦点

Juri Lelli（SCHED_DEADLINE 维护者）认可方向、无 NAK，但要求补 SCX 支持并以 tip/sched/core 为基。

## 合入评估

*likelihood=medium*。方向获维护者认可，仍需 v3 补齐 SCX 支持。*blocking_issues*：v3（SCX 支持）+ 重基。*next_action*：作者发 v3。

## 效果评估

无性能数字（nohz 行为修复，未见 benchmark）。

## 我可以参与的点

- `testing`：在 nohz_full + RT/CFS 共存场景验证 deferred 状态下 tick 是否真的保持 tickless。
- `review`：核对 v3 的 SCX 支持路径。

## 参考链接

- lore（RFC v1）: https://lore.kernel.org/all/20261005132038.353661-1-ionut.nechita@windriver.com/
- lore（Juri 认可并要 v3）: https://lore.kernel.org/all/aszViUxPLBuH0h7L@jlelli-thinkpadt14gen4.remote.csb/

---
id: sched-20261012-019
date: '2026-10-12'
subject: 'sched/deadline: keep nohz_full tickless while the fair server is deferred'
subsystem: sched
type: fix
status: rfc
severity: low
thread_root_msgid: <20261005132038.353661-1-ionut.nechita@windriver.com>
lore_url: https://lore.kernel.org/all/20261005132038.353661-1-ionut.nechita@windriver.com/
authors:
- Ionut Nechita
maintainers_involved:
- Juri Lelli
current_version: v1
patch_series:
- version: v1
  msgid: <20261005132038.353661-1-ionut.nechita@windriver.com>
  date: '2026-10-05'
  summary: 拆开「武装 fair server」与「为 server 保 tick」，deferred 状态下不强制 tick
  review_outcome: Juri Lelli 认可方向，要求发 v3（含 SCX 支持）基于 tip/sched/core
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 需重发 v3（含 SCX 支持）并基于 tip/sched/core
  next_action: 作者按 Juri 要求发 v3
contribution_opportunities:
- kind: testing
  description: 在 nohz_full 核上验证 deferred fair server 下 tick 是否保持 tickless
- kind: review
  description: 核对 v3 需补的 SCX 支持路径与现有 dl_server 逻辑的衔接
generated_at: '2026-10-13T01:40:00'
source_email_count: 1
related_articles:
- sched-20261005-004
tags:
- deadline
- dl_server
- nohz
---
