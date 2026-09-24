# sched: Fix incorrect sched_stat_wait statistics for rt and dl

## TL;DR
Liang Luo 提交修复：rt/dl 调度类的 `sched_stat_wait` 统计在 schedstats 运行时才开启的场景下会输出"自开机以来"的虚假等待时间（wait_max/wait_sum 被永久污染）。修复是把 fair 类既有的"零 wait_start 跳过"检查下沉到公共的 `__update_stats_wait_end()`，让所有调度类共享。值得注意的是：该补丁明确指出等价修复早在 2024 年由 Zhang Qiao 提出过、但未合入。

## 背景与问题
`update_stats_wait_start_*()` 仅在 `schedstat_enabled()` 时才记录 `wait_start`。schedstats 默认关闭，运行时才开启时，之前就已入队的任务 `wait_start==0`，其下一次 `__update_stats_wait_end()` 会算出 `rq_clock(rq) - 0`（等于开机时长）的虚假 delta，并累进 `wait_max`/`wait_sum` 传给 `trace_sched_stat_wait()`。二者只增不减，一次虚假样本就永久污染任务统计直至退出。作者在 mainline 用 SCHED_RR 任务复现：开机约 1058 s 的机器上 `wait_max` 读出 `1058533.555050`（ms）。
fair 类自 commit b9c88f752268 起已免疫（在 fair 包装器里跳过零 wait_start），但 rt/dl 包装器直接调 `__update_stats_wait_end()`，从未继承该检查。

## 技术方案
把零 `wait_start` 的跳过检查下沉到 `__update_stats_wait_end()`（`kernel/sched/stats.c`），使所有调度类与调用点共享；同时删除 fair 包装器里现已冗余的检查（`kernel/sched/fair.c` 删 9 行）。

## 版本演进与当前进展
- v1（09-18，`<20260918094848.2518338-1-luoliang@kylinos.cn>`）：首版，本日无回复。

## Maintainer 意见与讨论焦点
- 本日无维护者回复。补丁自带 Fixes 与清晰的复现说明，并指出 2024 年 Zhang Qiao 的等价修复（https://lore.kernel.org/r/20240322081521.2687856-1-zhangqiao22@huawei.com）未合入，暗示此问题长期存在。

## 合入评估
*likelihood=medium*。修复小、逻辑清晰、带 Fixes 与 mainline 复现，且与既有 fair 类免疫方式完全同构；但本日尚无人 review。*blocking_issues*：无阻塞；等待维护者 review（fair 类类似检查早已合入，阻力应小）。*next_action*：等待 sched 维护者 review 即可；若无人响应可 ping 或对比 Zhang Qiao 2024 版本补充差异说明。

## 效果评估
作者复现：开机 ~1058 s 时 SCHED_RR 任务 `wait_max` 显示 `1058533.555050`（恰为 uptime 量级，即虚假值）。修复后该统计应回到真实等待时间（作者未附修复前后对比数据）。

## 我可以参与的点
- kind=review：该修复与 2024 年 Zhang Qiao 的等价补丁几乎同构——可对比两者的差异（下沉位置、RT/DL 覆盖面），并向维护者确认收敛方案。
- kind=testing：在 schedstats 运行时开启的时序下复现并验证 rt/dl 的 wait_max/wait_sum 不再被污染。

## 参考链接
- lore（patch）: https://lore.kernel.org/all/20260918094848.2518338-1-luoliang@kylinos.cn/
- 2024 年 Zhang Qiao 等价修复: https://lore.kernel.org/r/20240322081521.2687856-1-zhangqiao22@huawei.com

---
id: sched-20260918-017
date: '2026-09-18'
subject: 'sched: Fix incorrect sched_stat_wait statistics for rt and dl'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20260918094848.2518338-1-luoliang@kylinos.cn>'
lore_url: 'https://lore.kernel.org/all/20260918094848.2518338-1-luoliang@kylinos.cn/'
authors:
  - 'Liang Luo'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260918094848.2518338-1-luoliang@kylinos.cn>'
    date: '2026-09-18'
    summary: '零 wait_start 检查下沉到 __update_stats_wait_end()，覆盖 rt/dl'
    review_outcome: '本日无回复'
upstream_commit: null
fixes_commit: '57a5c2dafca8'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: '等待 sched 维护者 review'
contribution_opportunities:
  - kind: review
    description: '对比 Zhang Qiao 2024 等价补丁，确认收敛方案'
  - kind: testing
    description: '在 schedstats 运行时开启时序下验证 rt/dl 统计不再污染'
generated_at: '2026-09-19T09:00:00'
source_email_count: 1
related_articles: []
tags:
  - rt
  - deadline
  - sched_debug
---