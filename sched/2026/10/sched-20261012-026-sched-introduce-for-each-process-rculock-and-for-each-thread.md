# sched: introduce for_each_process_rculock and for_each_thread_rculock

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260907-004 / 20260911-012 / 20260921-002：Ye Liu 的进程/线程遍历 RCU 化系列发到 v4（15 补丁）——新增 `for_each_process_rculock()`/`for_each_thread_rculock()`/`for_each_process_thread_rculock()`，用 `scoped_guard(rcu)` 收敛 RCU 读锁作用域，并批量转换 mm/kernel/fs/lib/security 调用点；v3 已落实 Peter/Rostedt 的拆分要求。
- sched-20261012-026（今天）：作者发「友好 ping」——v4 已发三周、之前 Peter 要求的按子系统拆分已在 v4 完成，请 Peter 确认是否在关注清单里。

## 背景与问题

（承接 20260907-004 等）用 `scoped_guard(rcu)` 的迭代宏替换手写 `rcu_read_lock()/rcu_read_unlock()`，让 break/goto/return 退出时自动释放锁，降低泄漏风险并提升可读性。

## 技术方案

（承接 20260921-002）方案不变；v4 已完成按子系统拆分（Peter 此前要求）。

## 版本演进与当前进展

v4（09-21）→ 今日（10-12）作者 ping；无新 review 或版本。

## Maintainer 意见与讨论焦点

Peter Zijlstra 此前要求按子系统拆分（已在 v4 落实）；今日作者友好 ping，未获回应。sched 部分已带 mhocko Acked-by 与若干 R-b。

## 合入评估

*likelihood=medium*。拆分要求已落实、部分 Acked/R-b，但主 review（Peter）仍待推进。*blocking_issues*：等待 Peter review。*next_action*：等 Peter 看 v4。

## 效果评估

无性能数字（无功能变化的 RCU 宏重构）。

## 我可以参与的点

已发 v4 等 review，当前阶段暂无明显参与空间。

## 参考链接

- lore（v4 cover）: https://lore.kernel.org/all/20260921092101.89285-1-ye.liu@linux.dev/
- lore（作者 ping）: https://lore.kernel.org/all/7842535e-ae71-4de3-b16d-14d55b514df5@linux.dev/

---
id: sched-20261012-026
date: '2026-10-12'
subject: 'sched: introduce for_each_process_rculock and for_each_thread_rculock'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260921092101.89285-1-ye.liu@linux.dev>
lore_url: https://lore.kernel.org/all/20260921092101.89285-1-ye.liu@linux.dev/
authors:
- Ye Liu
maintainers_involved:
- Peter Zijlstra
current_version: v4
patch_series:
- version: v4
  msgid: <20260921092101.89285-1-ye.liu@linux.dev>
  date: '2026-09-21'
  summary: 新增 for_each_process_rculock()/for_each_thread_rculock() 宏并批量转换调用点
  review_outcome: 已按 Peter 要求拆分子系统补丁；今日作者友好 ping
merge_assessment:
  likelihood: medium
  blocking_issues:
  - v4 已发三周、等待 Peter review
  next_action: 等 Peter 看 v4（作者已 ping）
contribution_opportunities: []
generated_at: '2026-10-13T01:40:00'
source_email_count: 1
related_articles:
- sched-20260907-004
- sched-20260911-012
- sched-20260921-002
tags:
- cfs
---
