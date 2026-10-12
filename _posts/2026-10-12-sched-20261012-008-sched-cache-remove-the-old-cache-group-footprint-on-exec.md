---
id: sched-20261012-008
date: '2026-10-12'
subject: 'sched/cache: Remove the old cache group footprint on exec'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261010111612.31345-1-jemmywong512@gmail.com>
lore_url: https://lore.kernel.org/all/20261010111612.31345-1-jemmywong512@gmail.com/
authors:
- Jemmy Wong
maintainers_involved:
- Chen Yu
current_version: v2
patch_series:
- version: v2
  msgid: <20261010111612.31345-1-jemmywong512@gmail.com>
  date: '2026-10-10'
  summary: exec 路径也 drop 旧 cache group footprint，抽成 helper 与 exit 共用
  review_outcome: Chen Yu 指出竞态；Jemmy 吸收进本地树并做 try_cmpxchg_relaxed/带符号 diff 等改进
merge_assessment:
  likelihood: medium
  blocking_issues:
  - footprint 更新 clamp 的「贡献应平衡」疑问未解
  - 需确认 atomic_long_add 是否能替代 CAS 循环
  next_action: 回应 Chen Yu 关于 clamp 是否会掩盖记账 bug 的疑问后发 v3
contribution_opportunities:
- kind: review
  description: 评估 footprint 是否可用 atomic_long_add(diff) 替代 try_cmpxchg 循环，及是否需 clamp
generated_at: '2026-10-13T01:40:00'
source_email_count: 1
related_articles:
- sched-20261009-007
- sched-20261010-003
tags:
- load_balance
- numa_balancing
title: 'sched/cache: Remove the old cache group footprint on exec'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/09/sched-20261009-007-sched-cache-remove-the-old-cache-group-footprint-on-exec.html">sched-20261009-007</a> / 20261010-003：Jemmy Wong 修 `sched_cache_exec_mmap()` 记账遗漏——exec 换掉 cache group 后旧 group 的 footprint 只在 exit 路径被减，共享 mm 任务 exec 后旧贡献残留；v2 抽成 helper 让 exec 与 exit 两处都 drop。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-008-sched-cache-remove-the-old-cache-group-footprint-on-exec.html">sched-20261012-008</a>（今天）：Chen Yu 指出一处竞态；Jemmy 感谢并吸收进本地树，做了 `try_cmpxchg_relaxed()`（替代全序 `try_cmpxchg()`）、带符号 `diff` 等改进，同时反问 clamp 是否会掩盖「贡献不平衡」的记账 bug。

## 背景与问题

（承接 20261009-007/20261010-003）`grp->footprint` 记录每个任务对该 cache group 的 NUMA fault 贡献，退出/exec 时应减掉。v2 让 exec 与 exit 共用 drop 逻辑；但今日 Chen Yu 提醒存在竞态：`grp->footprint` 仅由 `READ_ONCE()/WRITE_ONCE()` 更新（无锁），exec 与 exit、task_numa_placement 可能并发读写。

## 技术方案

（承接 v2）Jemmy 把 Chen Yu 的意见吸收进本地树并做三点改进：`sched_cache_footprint_drop()` 里用 `try_cmpxchg_relaxed()` 替代 `try_cmpxchg()`（exec_mmap 上方对 `tsk->mm`/`active_mm` 的写无需与 `grp->footprint` 定序，全序 CAS 的 acquire/release 两半都多余）；`@diff` 改为带符号（减法仍在无符号算术里 clamp，保持单一类型）；helper 提前定义避免前置声明、`CONFIG_NUMA_BALANCING` 关闭时给空 stub。同时反问 Chen Yu：原子更新是否该让每个任务的 placement diff 与其 exit/exec 减法平衡——若不平衡则 clamp 掩盖了记账 bug，也许该换 `atomic_long_add()`（无序）替代 CAS 循环。

## 版本演进与当前进展

v2（10-10）→ 今日（10-12）Chen Yu 提竞态 + Jemmy 折入改进，尚未定稿 v3。

## Maintainer 意见与讨论焦点

Chen Yu 指出 footprint 无锁读写的竞态；Jemmy 认可方向并做 memory-ordering 层面的精化，但抛出「clamp 是否掩盖记账 bug / 是否该用 atomic_long_add」的开放问题，尚未收敛。

## 合入评估

*likelihood=medium*。方向稳定、reviewer 参与度高，但 clamp 语义与是否用原子加减仍有开放问题。*blocking_issues*：clamp 平衡疑问、atomic_long_add 取舍未定。*next_action*：回应 Chen Yu 的 clamp 疑问后发 v3。

## 效果评估

无性能数字；作者提到「生成代码里 `sched_cache_footprint_drop()` 被内联进 exec/exit，early-out 测试仍落在调用点」，属编译层验证。

## 我可以参与的点

- `review`：评估 `grp->footprint` 是否真能保证 placement/exit/exec 三处贡献严格平衡，从而用 `atomic_long_add()` 替代 CAS 循环并去掉 clamp。

## 参考链接

- lore（v2）: https://lore.kernel.org/all/20261010111612.31345-1-jemmywong512@gmail.com/
- lore（Jemmy 折入 Chen Yu 意见）: https://lore.kernel.org/all/CEF1F3DC-07E5-44DA-9602-56A5B5810F09@gmail.com/
