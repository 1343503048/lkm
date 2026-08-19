# sched/fair: Allow load balancing between CPUs of identical capacity

# sched/fair: 允许相同容量 CPU 间负载均衡

## TL;DR
`sched_balance_find_src_rq()` 的「~5% 额外容量」阈值无意中阻止了相同容量 CPU 间的迁移；Ricardo Neri 改为用 `get_actual_cpu_capacity()` 并经 `sched_cluster_active` 静态键保护，使 `CONFIG_SCHED_CLUSTER` 下能跨相同容量 cluster 均衡。v6 已两枚 Tested-by，合入可能性 high。

## 背景与问题
选 busiest runqueue 时，原函数用「目标 CPU 容量低于源 <5% 则不选」的规则避免迁到低容量 CPU，但该规则**也阻止了相同容量 CPU 之间**的迁移。当 `CONFIG_SCHED_CLUSTER` 开启时，本应在相同容量的 cluster 间均衡负载，原逻辑与此目标冲突。

## 技术方案
改用 `get_actual_cpu_capacity()` 反映架构容量及因硬件/cpufreq 压力而降低的容量；用 `sched_cluster_active` 静态键保护该检查，使无 cluster 拓扑的系统不受影响。v6 据 Vincent 意见切换API并据 Andrea 意见重命名变量，且加了两枚 Tested-by。

## 版本演进与当前进展
当前 v6（2026-08-04）。历经 v2→v6 多轮：v3 修正反转容量检查，v4 加静态键保护，v5/v6 切换 API + 重命名。Christian Loehle、Andrea Righi 均 Tested-by。

## Maintainer 意见与讨论焦点
Vincent Guittot 在 08-04 给出 review 讨论（推动 API 切换与命名）。Christian Loehle、Andrea Righi 提供 Tested-by。无方向反对。

## 合入评估
合入可能性 high。已有两枚 Tested-by + maintainer review 收敛，无架构障碍。

## 效果评估
邮件附多轮 Tested-by（含 cluster 拓扑实测），属「有实证」的均衡修正。

## 我可以参与的点
- 在开启 CONFIG_SCHED_CLUSTER 的机型上验证相同容量 CPU 间均衡行为，回帖实测确认（已有 Tested-by，可补更广覆盖）。

## 参考链接
- lore thread: 未获取到

---
subject: "sched/fair: Allow load balancing between CPUs of identical capacity"
id: sched-20260804-011
date: 2026-08-04
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<unknown>"
lore_url: "unknown"
authors: [Ricardo Neri]
maintainers_involved: [Peter Zijlstra, Vincent Guittot, Christian Loehle]
current_version: v6
patch_series:
  - version: v6
    msgid: "<unknown>"
    date: 2026-08-04
    summary: "sched_balance_find_src_rq() 原用『~5% 额外容量』阈值避免迁到低容量 CPU，但无意中也阻止了相同容量 CPU 间的迁移；当 CONFIG_SCHED_CLUSTER 开启时应允许跨相同容量 cluster 均衡。改用 get_actual_cpu_capacity() 并经 sched_cluster_active 静态键保护。"
    review_outcome: "Christian Loehle Tested-by，Andrea Righi Tested-by，Vincent Guittot 在 08-04 给出 review 讨论。v6 已多轮迭代。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待 Vincent 对 v6 调整的认可；已有两枚 Tested-by，阻力小。"
contribution_opportunities:
  - kind: testing
    description: "可在开启 CONFIG_SCHED_CLUSTER 的异构/同构机型上验证相同容量 CPU 间负载均衡是否如预期工作，回帖实测确认。"
generated_at: "2026-08-05T00:25:00"
source_email_count: 1
related_articles: []
tags: [cfs, load_balance, topology, capacity]
---
