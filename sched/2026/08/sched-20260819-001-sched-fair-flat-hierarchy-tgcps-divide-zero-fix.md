# tip `sched/core` 的 flat-hierarchy rework 在 enqueue 路径触发 `#DE` 除零 panic（group ...


## TL;DR
tip `sched/core` 的 flat-hierarchy rework 在 enqueue 路径触发 `#DE` 除零 panic（group se 的 `load.weight==0`，`__calc_prop_weight()` 除 `cfs_rq->load.weight`），由 `tg_cpus()` 未对 0 做下限导致；同日配套补丁把 `tg_cpus()` 下限取到 1。critical 级崩溃，但仅影响尚未进主线、由发行版（CachyOS）带入的 tip 系列。

## 背景与问题
报告者在 CachyOS 发行内核（携带 flat-hierarchy rework 系列）上，7.2-rc7 / 7.2.0，机器空闲、合盖 11.66h 后 `bash` fork 新任务、`wake_up_new_task()` → `enqueue_task_fair()` 触发 `divide error`：

```
RIP: 0010:enqueue_task_fair ...
weight *= se->load.weight;
if (parent_entity(se))
    weight /= cfs_rq->load.weight;   /* #DE: cfs_rq->load.weight == 0 */
```

`panic_on_oops=0` 下第一次 #DE 后 oops 恢复路径（kill task → schedule()）在 rq 锁仍持有、enqueue 未完成时再次进入同一 enqueue，寄存器完全一致，第二次 fault 升级为 panic。RCX=`cfs_rq->load.weight=0` 且 R13=`se->load.weight=0`，即一个携带零权重的 group sched_entity。

根因链条（报告者已确认部分）：`tg_cpus()` 直接返回 `cpuset_num_cpus()` 未做下限，而其姊妹函数 `tg_tasks()` 已经 `max(...,1)`。`calc_concur_shares()` 取 `nr = min(tg_tasks(tg), tg_cpus(tg))` 作为 `shares_max` 喂给 `__calc_smp_shares()`；`nr==0` 时 `clamp_t(long, shares, MIN_SHARES, 0)` 因 `hi<lo` 返回 hi=0，绕过了注释明确要求的 MIN_SHARES 下限，留下 `load.weight==0` 的 group se，进而除零。

## 技术方案
配套补丁将 `tg_cpus()` 下限取到 1，与 `tg_tasks()` 对称，保证 `shares_max >= tg_shares`，使 `__calc_smp_shares()` 的 MIN_SHARES 下限不再被绕过。补丁作者明确说明：该修复只消除除法危险；`cpuset_num_cpus()` 能否合法返回 0（v2 cpuset 在 hotplug/suspend 路径瞬时空窗，或 RCU 竞态）是另一个独立问题，未在本补丁处理。

## 版本演进与当前进展
同日（2026-08-19）bug 报告 + 修复补丁 v1 一起发出，暂无 reviewer 回复。`se->on_rq` 守卫（已合入 85570f10a4c6）只覆盖了 5 月报告的 `task_tick_fair()` 变体；`enqueue_hierarchy()`/`dequeue_hierarchy()` 没有等效检查，所以本次是 enqueue 路径的新变体。

## Maintainer 意见与讨论焦点
暂无 maintainer 正式回复。需 Peter/Vincent 判定修复点：是在 `tg_cpus()` 做下限（简单、与 `tg_tasks()` 一致），还是在 `cpuset_num_cpus()` 的 hotplug/suspend 空窗口处处理（更治本但改动面更大）。

## 合入评估
合入可能性 high：这是一个清晰、局部、无功能副作用的除零修复，且配套了完整根因分析。卡点仅是该系列本身尚未进 Linus 树（属于 tip 实验性 rework），需该 rework 作者确认修复落点。

## 效果评估
报告者给出复现数据：50% 配额场景无关，纯属零权重 group se 触发；panic 在合盖空闲 11.66h 后由一次 clone 触发，oops 恢复路径 476ms 内二次 fault 升级为 panic。补丁暂无独立 benchmark，属正确性修复。

## 我可以参与的点
- 在 tip flat-hierarchy rework 内核 + cgroup v2 cpuset 上复现并验证补丁消除 #DE。
- 帮忙分析 `cpuset_num_cpus()` 在 hotplug/suspend 下返回 0 是否合法，给维护者提供根因落点建议。

## 参考链接
- lore thread: 未获取到（邮件正文可见完整 oops/commit 引用 85570f10a4c6）
- tip-bot commit: 未获取到

---
id: sched-20260819-001
date: 2026-08-19
subsystem: sched
type: bug
status: under_review
severity: critical
thread_root_msgid: "<unknown>"
lore_url: "未获取到"
authors: [reporter (unknown), kernel dev]
maintainers_involved: [Peter Zijlstra, Vincent Guittot, Ingo Molnar]
current_version: v1
patch_series:
  - version: v1
    msgid: "<unknown>"
    date: 2026-08-19
    summary: "配套修复补丁 tg_cpus() 在 cpuset 为空时返回 0，使 shares_max 归零绕过 MIN_SHARES 下限，导致 group se 的 load.weight==0，__calc_prop_weight() 除零崩溃；补丁将 tg_cpus() 下限取到 1，与 tg_tasks() 对称。"
    review_outcome: "补丁随 bug 报告同日发出，暂无 maintainer 正式回复。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["问题仅存在于 tip sched/core 的 flat-hierarchy rework，尚未进 Linus 树，需该系列作者/维护者确认根因修复点"]
  next_action: "等待 Peter/Vincent 确认修复点是否应在 tg_cpus() 还是在 cpuset_num_cpus() 的 hotplug/suspend 空窗口处处理。"
contribution_opportunities:
  - kind: testing
    description: "在启用 flat-hierarchy rework 的 tip 内核 + cgroup v2 cpuset 上复现（关闭某 cpuset 所有 CPU 后 fork 新任务），验证补丁消除 #DE。"
  - kind: discussion
    description: "cpuset_num_cpus() 在 cpu hotplug/suspend 路径下能否合法返回 0（v2 cpuset 瞬时空窗或 RCU 竞态）仍是开放问题，可帮忙分析。"
generated_at: "2026-08-20T00:30:00"
source_email_count: 2
related_articles: ["sched-20260814-001", "sched-20260815-001"]
tags: [sched/fair, cgroup, crash, regression]
---
