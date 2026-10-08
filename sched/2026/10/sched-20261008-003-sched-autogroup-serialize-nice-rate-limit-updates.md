# sched/autogroup: Serialize nice rate-limit updates

## TL;DR

Hui Su 修掉 `proc_sched_autogroup_set_nice()` 里一个经典的 check-then-act 竞态：用函数级静态时间戳做 100ms 限流的检查和更新不是原子的，两个并发非特权写者可同时看到过期时间戳、都进入 `sched_group_set_shares()`，击穿限流。补丁用一个专用 spinlock 串行化时间戳的查/改，能力检查移出临界区、重活保持锁外。带 `Fixes: 5091faa449ee` 与 KCSAN 复现证据；autogroup 原作者 Mike Galbraith 回帖认可（「by all means lock it up」）。

## 背景与问题

`proc_sched_autogroup_set_nice()` 用 `static unsigned long next` 函数级时间戳来限制昂贵的 `sched_group_set_shares()` 调用频率（100ms）。但「检查时间戳是否过期」与「更新时间戳」两步之间没有同步：两个并发写者（unprivileged 用户写 `/proc/<pid>/autogroup`）都能观察到过期的时间戳、各自推进并继续执行 `sched_group_set_shares()`，从而击穿限流。作者用 x86_64 KVM 的 KCSAN forced-overlap 复现器观测到了 CPU0/1 对共享时间戳的并发写，并用 rate-limit oracle 测得修复前两次写入间隔 <20ms、修复后 100ms 窗口内不再成对出现。

## 技术方案

新增 `DEFINE_SPINLOCK(autogroup_nice_lock)`，把时间戳的检查与更新放进锁内做原子「查-改」，`sched_group_set_shares()` 这一重活保持在临界区之外（只保护时间戳本身，不把昂贵操作压在锁下）。能力检查（`capable(CAP_SYS_NICE)`）放到进锁之前，避免在持锁状态下做权限判定。

## 版本演进与当前进展

v1 首发（`<20261008064440.240528-1-sh_def@163.com>`）。当日 Mike Galbraith（autogroup 功能的原作者）回帖认可，无反对意见。

## Maintainer 意见与讨论焦点

- **Mike Galbraith**（autogroup 原作者）：「The intent was to make it slow enough to prevent users from annoying admins. If it doesn't do that well enough, by all means lock it up.」——既有限流的本意是防扰民而非强语义保证，认可加锁堵住竞态。
- 无分歧、无 NAK。硬要说观察点：限流只是「软」保护（作者与 Mike 都清楚其无法提供强隔离），加锁的收益是消除并发写竞态，代价是极小的锁开销（仅覆盖时间戳查改）。

## 合入评估

*likelihood=high*。自包含的单点竞态修复、带 `Fixes:` 与 KCSAN 复现证据、改动面 13 行，且得到该代码原作者的明确认可。无实质争议；主要等一位正式 sched 维护者给出 R-b/A-b 即可进入 tip 的 fix 路径。*next_action*：等维护者（Peter/Ingo/Vincent）审阅合并。

## 效果评估

作者提供 KCSAN 复现证据（并发写 to 共享时间戳）与 rate-limit oracle 数据（修复前两次写入 <20ms、修复后无 <100ms 成对写入）。无性能基准，但改动本身只在限流路径加一次 spinlock 查改，热点可忽略。

## 我可以参与的点

- `review`：确认把能力检查移到锁外是否引入 TOCTOU 面（`capable()` 语义不依赖时间戳、且 nice 值最终写入仍走既有权限路径，理论上无影响），以及 spinlock 是否需要在非 PROC_FS 配置下显式排除。
- 当前阶段整体参与空间不大：补丁小、方向明确、原作者的认可已拿到，主要动作是等维护者合并。

## 参考链接

- 补丁: https://lore.kernel.org/all/20261008064440.240528-1-sh_def@163.com/
- Mike Galbraith 回复: https://lore.kernel.org/all/828fe52d7514cabf240f354268f7cfb541516f15.camel@gmx.de/

---
id: sched-20261008-003
subject: 'sched/autogroup: Serialize nice rate-limit updates'
date: '2026-10-08'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20261008064440.240528-1-sh_def@163.com>'
lore_url: 'https://lore.kernel.org/all/20261008064440.240528-1-sh_def@163.com/'
authors:
  - 'Hui Su'
maintainers_involved:
  - 'Mike Galbraith'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20261008064440.240528-1-sh_def@163.com>'
    date: '2026-10-08'
    summary: '用 spinlock 串行化 nice rate-limit 时间戳查改，重活锁外'
    review_outcome: 'Mike Galbraith 认可（by all means lock it up）'
upstream_commit: null
fixes_commit: '5091faa449ee'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: '等维护者给出 R-b/A-b 并收进 tip fix 路径'
contribution_opportunities:
  - kind: review
    description: '确认能力检查移出锁外无 TOCTOU 面及非 PROC_FS 配置下的锁排除'
generated_at: '2026-10-09T01:00:00'
source_email_count: 2
related_articles: []
tags:
  - autogroup
  - cgroup
---