# mm, sched, cgroup: LRU Cache never drains when isolcpus are used with spinning SCHED_FIFO tasks causing page migration stalls

## TL;DR

Canonical 的 Caron Wills / Matthew Ruffell 报告一起生产环境 bug：isolcpus 大系统上 SCHED_FIFO 忙循环任务导致 systemd/PID 1 卡 D 状态最长 10 分钟、ssh 登录失败。根因是 nohz_full CPU 的 per-CPU work 永不执行、`flush_work()` 挂起。6 补丁系列修复 `cpu_is_isolated()` 对 nohz_full 的判定退化（patch 1）并让隔离 CPU 清空 per-CPU LRU batch（patch 4）。首版刚发出，社区仍在争论方案走向。

## 背景与问题

用户在用 192 CPU（2× AMD EPYC 9R45）且 `isolcpus=nohz,18-95,108-178 nohz_full=18-95,108-178 rcu_nocbs=...` 隔离大段 CPU，隔离 CPU 上跑 100% SCHED_FIFO（prio 80）忙循环。当约 50GB 页面跨 NUMA 迁移时，systemd 卡 D 状态（`wait_for_completion → __flush_workqueue → flush_migrate_mm_task_workfn`）3-10 分钟。根因一半来自 commit `1c3329df409b`（"sched/isolation: Remove HK_TYPE_TICK test from cpu_is_isolated()"）：它把 `cpu_is_isolated()` 退化为只测 HK_TYPE_DOMAIN，使 nohz_full（但仍留在调度域内）的 CPU 被误判为「非隔离」，于是 `bh_lru_install()`、`vmstat_shepherd()`、memcg stock drain、blk-mq 又重新往这些 CPU 排队 per-CPU work；这些 CPU 忙于 SCHED_FIFO 永不清空，`flush_work()` 随之挂起。下游 bug：LP #2165410。

## 技术方案

patch 1（sched/isolation）让 `cpu_is_isolated()` 额外测试 HK_TYPE_KERNEL_NOISE（HK_TYPE_TICK 的别名，由 nohz_full=/isolcpus=nohz 设置），并用 `housekeeping_cpu()` 包装使无隔离系统仍只付出静态分支。patch 4 在 `housekeeping_update()` 更新完 HK_TYPE_DOMAIN mask 后、紧挨 vmstat/memcg flush 处调用 `lru_add_drain_all()`，让运行时被隔离（cpuset 分区）的 CPU 以空 batch 起步。sched 缓存只含 1/6 与 4/6 两封 sched/isolation 补丁，系列其余为 mm/cgroup 侧改动。

## 版本演进与当前进展

*current_version: v1（2026-11-03 发出，msgid 20261103075940.110308-1-matthew.ruffell@canonical.com）*。当日即有 Michal Hocko、Tejun Heo、Frederic Weisbecker 回帖。

## Maintainer 意见与讨论焦点

Michal Hocko 质疑方向，提出「在返回用户态时 flush pcp 页面」的底层方案并追问其进展，「这才是解决底层问题、避免引入锁竞争的方向」。Tejun Heo 更直接：「应该彻底去掉细粒度隔离控制，这是 footgun，把实现细节绑死到接口上」，并问作者是否关了 fair deadline server。Frederic Weisbecker 指向已有的 Leonardo Bras 系列（lore 20260519012754.240804-1-leobras.c@gmail.com），问其是否计划 v5。方案层面尚未收敛。

## 合入评估

*likelihood=unknown*。跨 mm/sched/cgroup 三子系统的系列，且方案仍有根本分歧（底层 pcp flush vs 逐个 work 队列修补；是否值得保留细粒度隔离）。*next_action*：作者需回应 Michal 与 Tejun 的方向性质疑，或与 Leonardo Bras 系列对齐。

## 效果评估

报告附带生产的可复现数据（systemd 卡 3-5 分钟、生产最长 10 分钟、50GB 迁移即可触发）；修复本身未见 benchmark。属可复现生产 bug，非纯理论。

## 我可以参与的点

- review：审阅 patch 1 的判定退化修复是否完整覆盖所有 `cpu_is_isolated()` 调用方的影响。
- discussion：参与「细粒度隔离 vs 底层 pcp flush」的方案取舍，提供隔离场景实测依据。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261103075940.110308-1-matthew.ruffell@canonical.com/
- downstream bug: https://bugs.launchpad.net/ubuntu/+source/linux-aws/+bug/2165410

---
id: sched-20261103-002
date: 2026-11-03
subject: "mm, sched, cgroup: LRU Cache never drains when isolcpus are used with spinning SCHED_FIFO tasks causing page migration stalls"
subsystem: sched
type: bug
status: rfc
severity: high
thread_root_msgid: "<20261103075940.110308-1-matthew.ruffell@canonical.com>"
lore_url: "https://lore.kernel.org/all/20261103075940.110308-1-matthew.ruffell@canonical.com/"
authors: [Caron Wills, Matthew Ruffell]
maintainers_involved: [Michal Hocko, Tejun Heo, Frederic Weisbecker]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261103075940.110308-1-matthew.ruffell@canonical.com>"
    date: 2026-11-03
    summary: "6 补丁：修复 cpu_is_isolated() 判定退化 + 隔离时清空 per-CPU LRU batch（含 mm/cgroup 侧）。"
    review_outcome: "Michal 提底层 pcp flush 方案；Tejun 质疑细粒度隔离；Frederic 指向 Leonardo Bras 系列。"
upstream_commit: null
fixes_commit: "1c3329df409b"
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["方案层面分歧：底层 pcp flush vs 逐个 work 队列修补"]
  next_action: "回应 Michal/Tejun 方向性质疑，或与 Leonardo Bras 系列对齐。"
contribution_opportunities:
  - kind: review
    description: "审阅 patch 1 判定退化修复是否完整覆盖 cpu_is_isolated() 所有调用方。"
  - kind: discussion
    description: "参与细粒度隔离 vs 底层 pcp flush 的方案取舍。"
generated_at: "2026-11-04T09:00:00+08:00"
source_email_count: 6
related_articles: []
tags: [cgroup, numa_balancing]
---