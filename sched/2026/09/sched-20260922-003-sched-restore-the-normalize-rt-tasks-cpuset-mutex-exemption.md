# sched: Restore the normalize_rt_tasks() cpuset_mutex exemption

## TL;DR
Donggeun Yoo 修复 sysrq-n（Nice All RT Tasks）在存在 SCHED_DEADLINE 任务时于原子上下文睡眠的死锁/挂起：`normalize_rt_tasks()` 持 `tasklist_lock` 走 `__sched_setscheduler()`，而后者对 deadline 策略会取 `cpuset_mutex`（普通 `mutex_lock`），导致原子上下文 sleep splat 甚至 sysrq-n 挂死。补丁让 `__sched_setscheduler()` 只在 `pi == true` 时取锁，恢复此前被 `111cd11bbc54` 移除的豁免。Juri Lelli 已 Acked。

## 背景与问题
sysrq-n 触发 `normalize_rt_tasks()`，在 `read_lock(&tasklist_lock)` 下遍历任务表，把每个用户 RT/deadline 任务交给 `__sched_setscheduler()`（`pi == false`）。`__sched_setscheduler()` 在新旧策略为 deadline 时取 `cpuset_mutex`（`cpuset_lock()` 即普通 `mutex_lock()`），于是只要有 SCHED_DEADLINE 用户任务，sysrq 处理路径就在原子上下文 sleep：

```
sysrq: Nice All RT Tasks
BUG: sleeping function called from invalid context at kernel/locking/mutex.c:623
...
locks held by init/1: ... tasklist_lock ... at: normalize_rt_tasks
```

`Fixes: 111cd11bbc54 ("sched/cpuset: Bring back cpuset_mutex")`。

## 技术方案
在 `__sched_setscheduler()` 中把 `pi` 与策略一起检查——仅 `pi == false` 的调用者是 `normalize_rt_tasks()`，此时放弃取锁，因为 sysrq 紧急路径本就放弃了 deadline 保证。改动仅 3 行（`kernel/sched/syscalls.c`）。

## 版本演进与当前进展
v1 当日发出，附带 qemu-x86_64 复现与修复前后对照表。Juri Lelli 回帖 `Acked-by`。

## Maintainer 意见与讨论焦点
- **Juri Lelli**：确认问题成立，回帖「Ah, yes indeed. Acked-by: Juri Lelli」。无反对意见。

## 合入评估
likelihood=high。已获 deadline/cpuset 相关维护者 Acked，改动极小且带完整复现，无争议点。blocking_issues 无；next_action 等待被收取进 tip（或作者跟进催合）。

## 效果评估
作者给出修复前后对照（qemu-x86_64, -smp 2, tip/sched/core `e81ee0630837`）：
- 0 个 deadline + 1 RT：无 splat，RT 正常归一化（修复前后相同）
- 1 blocked deadline：修复前 splat，修复后无 splat 且归一化
- 2 blocked + 1 RT：修复前 splat 且 sysrq-n 挂死，修复后无 splat、全部归一化
- 1 spinning / 2 spinning：修复前 splat，修复后无 splat 且归一化

## 我可以参与的点
- **testing**：在带 CPUSETS+MAGIC_SYSRQ+DEBUG_ATOMIC_SLEEP 的内核上复现 sysrq-n，验证修复并补 Tested-by。
- **review**：核查 `pi == false` 是否还有其它调用者会因放弃 cpuset_mutex 引入新问题。

## 参考链接
- lore thread: https://lore.kernel.org/all/20260922030738.1613919-1-donggeunyoo.kernel@gmail.com/

---
id: sched-20260922-003
date: '2026-09-22'
subject: 'sched: Restore the normalize_rt_tasks() cpuset_mutex exemption'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: '<20260922030738.1613919-1-donggeunyoo.kernel@gmail.com>'
lore_url: 'https://lore.kernel.org/all/20260922030738.1613919-1-donggeunyoo.kernel@gmail.com/'
authors:
  - 'Donggeun Yoo'
maintainers_involved:
  - 'Juri Lelli'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260922030738.1613919-1-donggeunyoo.kernel@gmail.com>'
    date: '2026-09-22'
    summary: '仅在 pi==true 时取 cpuset_mutex，恢复 normalize_rt_tasks 豁免'
    review_outcome: 'Juri Lelli Acked-by'
upstream_commit: null
fixes_commit: '111cd11bbc54'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: '等待被收取进 tip，或作者跟进催合'
contribution_opportunities:
  - kind: testing
    description: '在 CPUSETS+MAGIC_SYSRQ+DEBUG_ATOMIC_SLEEP 配置下复现 sysrq-n 并补 Tested-by'
  - kind: review
    description: '核查 pi==false 是否还有其它调用者会因放弃 cpuset_mutex 引入新问题'
generated_at: '2026-09-23T00:00:00'
source_email_count: 2
related_articles: []
tags:
  - cgroup
  - deadline
---