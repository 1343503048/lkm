# sched: Restart hrtick after same-task repicks

## TL;DR
增量更新，v2 全貌见 sched-20260912-004。09-14 作者 Shubhang Kaushik 自报 v2 的 DL 部分有缺陷：非 tick 重调度且 same-task repick SCHED_DEADLINE 时 `next == prev` 跳过 put_prev_task_dl()，update_curr_dl() 可能未对 exec_start 后的执行记账，SNT_REPICK 用陈旧 dl_se->runtime 武装 hrtick 过晚、延迟 DL runtime 强制。作者表示若无 DL 情形需要该 rearm，下版将删除 DL 部分，请社区先忽略 v2 的 DL 部分。

## 背景与问题
hrtick 到期 → task_tick 触发 resched_curr() → schedule() 里 pick 再次选中当前任务 → `next == prev` 路径跳过 set_next_task()/start_hrtick_*()，下一个抢占点未被武装。v2 用 SNT_NORMAL/SNT_PICK/SNT_REPICK 枚举修复 fair 与 DL（承 sched-20260912-004）。今日作者发现 DL 分支引入新缺陷。

## 技术方案
今日无新代码，是对 v2 DL 分支的自我否定：作者将删除 DL 的 SNT_REPICK rearm。缺陷机理（作者自述）：

- 非 tick 重调度 repick 当前 SCHED_DEADLINE 任务时，`next == prev` 跳过 put_prev_task_dl()；
- 因此 update_curr_dl() 可能未对 exec_start 之后的执行记账；
- v2 的 SNT_REPICK 路径用陈旧的 dl_se->runtime 调 start_hrtick_dl()，可能把下一次 hrtick 武装得太晚，延迟 DL runtime 强制。

## 版本演进与当前进展
- v1（08-13）→ v2（09-11，SNT_REPICK 枚举 + 首份量化数据）见 sched-20260912-004。
- 09-14（本文窗口）：作者自报 v2 DL 分支缺陷，预告 v3 删除 DL 部分。

## Maintainer 意见与讨论焦点
- **作者 Shubhang Kaushik（自我评审）**：识别 DL rearm 记账缺陷，主动撤回 DL 部分（"please disregard the DL portion of v2 for review"）。
- **Peter Zijlstra / Vincent Guittot**（承 sched-20260912-004）：v2 尚无复核。
- 分歧/未闭合处：DL 场景是否确有「same-task repick 需重新武装 hrtick」的用例尚未定论，作者倾向删除。

## 合入评估
*likelihood=medium*（承 sched-20260912-004）：fair 部分方向已获维护者认可，DL 部分回退使系列更聚焦。*blocking_issues*：DL 部分待删除；v2 维护者复核仍待。*next_action*：作者发 v3（删除 DL 部分），等 PeterZ 复核。

## 效果评估
承 sched-20260912-004 的 fair 量化数据（CPU-bound fair 任务最大运行时长 5.227ms → 3.386ms、>4ms 样本 6 → 0）；DL 部分无数据且将被删除。

## 我可以参与的点
- kind=review：确认 DL 场景是否确有「same-task repick 需重新武装 hrtick」的用例，帮助作者决定删除还是修正 DL 分支。
- kind=testing：复测 v3（删 DL 后）的 fair 场景量化数据是否保持。

## 参考链接
- 作者 DL 缺陷回帖：https://lore.kernel.org/all/79a14c31-b4ed-4ff2-0551-8b31b86b91cb@gentwo.org/

---
id: sched-20260914-009
date: '2026-09-14'
subject: 'sched: Restart hrtick after same-task repicks'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20260911-sched-fair-hrtick-restart-v2-1-0d34db26ecd1@gentwo.org>'
lore_url: 'https://lore.kernel.org/all/79a14c31-b4ed-4ff2-0551-8b31b86b91cb@gentwo.org/'
authors:
  - 'Shubhang Kaushik'
maintainers_involved: []
current_version: v2
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'DL 部分待删除'
    - 'v2 维护者复核仍待'
  next_action: '作者发 v3（删除 DL 部分），等 PeterZ 复核'
contribution_opportunities:
  - kind: review
    description: '确认 DL 场景是否需要 same-task repick 重新武装 hrtick'
  - kind: testing
    description: '复测 v3 的 fair 场景量化数据是否保持'
generated_at: '2026-09-15T09:30:00'
source_email_count: 1
related_articles:
  - 'sched-20260912-004'
tags:
  - cfs
  - sched_clock
---