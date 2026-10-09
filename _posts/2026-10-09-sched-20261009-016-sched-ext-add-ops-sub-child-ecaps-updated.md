---
id: sched-20261009-016
date: '2026-10-09'
subject: 'sched_ext: Add ops.sub_child_ecaps_updated()'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261008093228.2015427-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/asjNO0ggCPcfIP7Y@gpd4/
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
- Andrea Righi
current_version: v2
patch_series:
- version: v1
  msgid: <20261008000352.1689057-1-tj@kernel.org>
  date: '2026-10-08'
  summary: 新增 ops.sub_child_ecaps_updated()；disable 报告在 dispatch 外运行并持 sleep lock
  review_outcome: self-review 后砍掉 disable 报告
- version: v2
  msgid: <20261008093228.2015427-1-tj@kernel.org>
  date: '2026-10-08'
  summary: 砍掉 disable 报告与 sleep lock，父级从 sub_detach 恢复
  review_outcome: 10-09 Andrea 提出 bypass 上报与 detach 复位边界问题
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - Andrea 的两个边界问题待 Tejun 回应
  - 尚缺第二人独立测试
  next_action: Tejun 回应 bypass/复位边界，必要时出 v3
contribution_opportunities:
- kind: review
  description: 审 bypass 上报时机与 detach 复位误伤的修复方向
- kind: testing
  description: shared pool 多 holder 轮流 + 中途 detach 场景测试
generated_at: '2026-10-10T01:30:00'
source_email_count: 2
related_articles:
- sched-20261004-004
- sched-20261006-006
- sched-20261007-003
- sched-20261007-004
- sched-20261008-004
tags:
- sched_ext
- cgroup
title: 'sched_ext: Add ops.sub_child_ecaps_updated()'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-004-sched-ext-add-ops-sub-child-ecaps-updated.html">sched-20261008-004</a>：Tejun Heo 为 sched_ext sub-scheduler 补上「父级何时得知 grant/revoke 生效」的缺口——新增 `ops.sub_child_ecaps_updated()` 回调，v1→v2 快速迭代（v2 砍掉 disable 报告与 sleep lock），并吸收 Tao Cui 实测与 Tejun 的 last-writer-wins 裁决。
- <a class="article-ref" href="/lkm/2026/10/09/sched-20261009-016-sched-ext-add-ops-sub-child-ecaps-updated.html">sched-20261009-016</a>（今天）：**Andrea Righi（sched_ext 联合维护者）首次 review，抛出两个边界问题**——① 子级 bypassing 但父级不 bypass 时，revoke 生效是否还应通知父级（否则父级在 `sub_detach()` 之前无从得知 revoke 生效时刻）；② `qa.rr_cids` 覆盖整个 shared pool，若 child A 在 child B 的回合 detach，会误把仍持有 PERF 的 B 写下的 cpuperf target 复位。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-004-sched-ext-add-ops-sub-child-ecaps-updated.html">sched-20261008-004</a>）grant/revoke 只记录目标值、真正生效要等 cid 下一次 dispatch，父调度器此前无从得知生效时刻。v2 的方案是新增 `ops.sub_child_ecaps_updated()`、砍掉 disable 报告、父级从 `ops.sub_detach()` 恢复。今天的增量是 Andrea 对这套「生效时刻上报」语义的两处边界提出质疑。

## 技术方案

（承接）v2 方案：`ops.sub_child_ecaps_updated()` 在子级 `sub_ecaps_updated()` 之后投递给直接父级；子级 bypass 期间投递被抑制、bypass 解除后重放；disabled 子级不报告、由父级在 `sub_detach()` 恢复。今天的两个边界问题：

1. **bypassing 子级的 revoke 上报（Andrea，patch 1 相关）**：`ops.sub_child_ecaps_updated()` 在「子级 bypassing 但父级不 bypass」时是否仍应投递给父级？场景：shared pool 可能转离一个 bypassing 的子级，其 PERF revoke 要到下一次 dispatch 才生效，而子级 bypass 状态同时抑制了对父级的通知；若子级正被 disable、永不离开 bypass，父级只会收到 `ops.sub_detach()`，无法得知 revoke 何时生效。Andrea 建议：revoke 生效时即使子级 bypassing 也通知父级，只推迟子级自身的通知到离开 bypass 之后。
2. **detach 复位误伤当前 holder（Andrea，patch 2 相关）**：`qa.rr_cids` 覆盖整个 shared pool、不管当前 holder 是谁。若 child A 在 child B 的回合 detach，会把 pool 的 cpuperf target 复位，即使 B 仍持有 PERF 且已写下自己的 target。Andrea 建议避免复位当前 holder 的 target。

## 版本演进与当前进展

- v1/v2（10-08）：见 related_articles。
- 10-09（今天）：Andrea 提出两处边界问题（bypassing 子级 revoke 上报、detach 复位误伤 holder），Tejun 尚未回应。

## Maintainer 意见与讨论焦点

- **Andrea Righi（sched_ext 联合维护者，今天首次 review）**：聚焦「生效时刻上报」的语义完整性——父级在子级 bypassing/disabled 时对 revoke 生效时刻的可见性，以及 scx_qmap 复位逻辑对 shared pool 当前 holder 的误伤。这是 v2 收敛后迎来的第一轮外部 review。
- **Tejun Heo**（作者/维护者）：尚未回应。
- 无 NAK；分歧点是「上报时机与复位范围」的边界语义，需 v3 或澄清回应。

## 合入评估

*likelihood=high*。仍是 Tejun 自维护的 for-7.4 特性、前身补丁有独立实测背书；Andrea 的边界问题属可修复的语义补强，不构成方向性阻塞。*blocking_issues*：① Andrea 的两个边界问题待 Tejun 回应/修复；② `ops.sub_child_ecaps_updated()` 尚缺第二人独立测试。*next_action*：Tejun 回应 Andrea 的 bypass/复位边界，必要时出 v3。

## 效果评估

无性能数据（API/正确性补全）。前身 caps-clear 补丁已有 Tao Cui 的 Tested-by/Reviewed-by 与 lockdep 干净背书；今天无新量化数据。

## 我可以参与的点

- `review`：审「bypassing 子级 revoke 上报」的时机语义与「detach 复位误伤 holder」的修复方向，评估是否会影响 last-writer-wins 契约。
- `testing`：跑 sub-scheduler caps/cpuperf 全流程，含 shared pool 多 holder 轮流 + 中途 detach 场景。

## 参考链接

- Andrea 对 1/2 回复: https://lore.kernel.org/all/asjNO0ggCPcfIP7Y@gpd4/
- Andrea 对 2/2 回复: https://lore.kernel.org/all/asjNo3JmkmeTK8dr@gpd4/
- v2 封面: https://lore.kernel.org/all/20261008093228.2015427-1-tj@kernel.org/
