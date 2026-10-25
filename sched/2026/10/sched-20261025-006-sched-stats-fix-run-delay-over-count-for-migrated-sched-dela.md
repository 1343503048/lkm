# sched/stats: Fix run_delay over-count for migrated sched_delayed tasks

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261012-027（及更早 20260923-007/20260921-006/20260922-015）：Wei Yang 的 run_delay 多计数修复——`sched_delayed` 任务跨 CPU 迁移时 `run_delay` 重复累计；v2 获 K Prateek Nayak Reviewed-by + Tested-by，v3 已收集 tags；作者 10-12 向 Peter 补充「为何不能与 proxy exec 耦合」的论证并等拍板。
- sched-20261024-006（v4）：Wei Yang 发 v4（`Fixes: 152e11f6df29`），**无代码改动**，仅重发浮出补丁；新增 Kayra Cizmeci、Chen Yu 的 Reviewed-by 与 K Prateek 的 Tested-by。作者重申 proxy exec 的同类 re-arm 问题另议、保持本补丁仅 delayed dequeue、以便回移植 v6.12.y..v6.16.y。
- sched-20261025-006（今天）：作者回 Peter，用内核 mutex 测试模块**复现了 proxy 场景**并给出数据——同 ~170ms 阻塞，cross-cpu 下 v4 仍计 ~167ms、加 `!task_is_blocked()` 后降到 0.01ms，证明 proxy 与 delayed dequeue 是两个独立 bug、v4 不覆盖 proxy；并说明 proxy 侧将单独发补丁。

## 背景与问题
（承接 20261012-027/20261024-006）`DELAY_DEQUEUE` 下 blocked 任务留在 runqueue 且 `sched_info.last_queued` 被清，睡眠不计入 run_delay；但 sched_delayed 任务经普通迁移路径跨 CPU 时 `activate_task(dst, 0)` 不带 `ENQUEUE_RESTORE` 地 re-arm last_queued，抑制后续真实唤醒的 re-arm，`sched_info_arrive()` 把迁移到唤醒的睡眠时长折进 run_delay。今日新进展：作者用内核 mutex 测试模块复现了**proxy exec 下的同类问题**——userspace futex mutex 从不设 `blocked_on`，需要暴露内核 mutex 的测试模块才能让 donor 成为真 proxy donor（`on_rq=1`、`is_blocked=1`、`blocked_on=1`），并观察其被迁到 owner 的 CPU（cpu_before=0 → cpu_now=1）。

## 技术方案
（承接 20261012-027/20261024-006）单补丁：`sched_info_enqueue()` 不再为 sched_delayed 任务重装 last_queued。今日作者进一步论证 proxy 侧门控：`t->is_blocked` 不能作为门控（`ttwu_runnable()` 的真实唤醒 enqueue 在 `if (p->is_blocked)` 分支内、`is_blocked` 之后才在 `ttwu_do_wakeup()` 中清除，`!is_blocked` 会压掉本补丁依赖的 re-arm）；`task_is_blocked()` 可作为**附加条件**（`!sched_delayed && !task_is_blocked()`），delayed sleeper 没有 `blocked_on`、delayed dequeue 修复不受影响。因 proxy migration 仅 v7.1 合入、delayed dequeue bug 自 v6.12 存在，耦合二者会破坏 v6.12.y..v6.16.y（无 proxy exec）的回移植或加死依赖，故 proxy 侧单独发补丁（见 sched-20261025-002）。

## 版本演进与当前进展
*current_version: v4*（`<20261024042753.2276779-1-albin_yang@163.com>`）。今日作者回帖 msgid `<20261025130329.3322194-1-albin_yang@163.com>` 提供 proxy 复现数据，未发新版。

## Maintainer 意见与讨论焦点
Peter Zijlstra 此前在 v3 线程追问 `t->is_blocked` 是否可作门控；今日作者用数据回应：v4（仅 `!sched_delayed`）对 proxy 场景无效（167.1ms 不变），`!sched_delayed && !task_is_blocked()` 才降到 0.01ms，并说明为何 proxy 侧需单独补丁。Peter 仍未在当日缓存内对拆分口径拍板。

## 合入评估
*likelihood=high*。作者补齐了 Peter 要的 proxy 复现证据，v4 的 delayed-dequeue 修复方向仍稳；今日未改变合入判断。*blocking_issues*：Peter 是否接受「仅 delayed dequeue、proxy 侧单独修」的拆分未定。*next_action*：Peter 拍板收原样（delayed-dequeue only，v4）+ 单独 proxy 补丁。

## 效果评估
今日新增实测数据（2 CPU VM，5 次迭代，run_delay 为 schedstat 第 2 字段）：cross-cpu unfixed 169.9ms 计 167.1ms、v4 169.9ms 计 167.1ms、加 `!task_is_blocked()` 169.8ms 计 0.01ms；同 CPU 对照 167.3ms 计 0.00ms。门控健全性：donor runnable 争 CPU 时 80ms 窗口 run_delay 仍增 ~39ms（5/5）。

## 我可以参与的点
- *kind: testing*：在启用代理执行的构建上复现跨 CPU mutex 阻塞场景，为拆分口径提供独立验证。
- *kind: review*：核对 `task_is_blocked()` 附加条件与 `se.sched_delayed` 检查的组合语义。

## 参考链接
- v4: https://lore.kernel.org/all/20261024042753.2276779-1-albin_yang@163.com/
- 今日回帖（proxy 复现）: https://lore.kernel.org/all/20261025130329.3322194-1-albin_yang@163.com/
- 前文: sched-20261024-006 / sched-20261012-027

---
id: sched-20261025-006
date: 2026-10-25
subject: 'sched/stats: Fix run_delay over-count for migrated sched_delayed tasks'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20261024042753.2276779-1-albin_yang@163.com>'
lore_url: 'https://lore.kernel.org/all/20261024042753.2276779-1-albin_yang@163.com/'
authors:
  - 'Wei Yang'
maintainers_involved:
  - 'Peter Zijlstra'
current_version: v4
patch_series:
  - version: v3
    msgid: '<20260922082432.2987855-1-albin_yang@163.com>'
    date: 2026-09-22
    summary: '修 sched_delayed 任务跨 CPU 迁移时 run_delay 重复累计'
    review_outcome: 'K Prateek Reviewed-by + Tested-by'
  - version: v4
    msgid: '<20261024042753.2276779-1-albin_yang@163.com>'
    date: 2026-10-24
    summary: '无代码改动，重发浮出补丁 + 补 Chen Yu/Kayra R-b 与 K Prateek T-b'
    review_outcome: '多 R-b/T-b；Peter 未拍板'
upstream_commit: null
fixes_commit: '152e11f6df29'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - 'Peter 是否接受「仅 delayed dequeue、proxy 侧单独修」的拆分未定'
  next_action: 'Peter 拍板收原样 v4 + 单独 proxy 补丁'
contribution_opportunities:
  - kind: testing
    description: '启用代理执行的构建上复现跨 CPU mutex 阻塞场景，独立验证拆分口径'
  - kind: review
    description: '核对 task_is_blocked() 附加条件与 se.sched_delayed 的组合语义'
generated_at: '2026-10-26T09:00:00'
source_email_count: 1
related_articles:
  - sched-20261012-027
  - sched-20261024-006
tags:
  - cfs
  - sched_debug
---