---
id: sched-20261112-003
date: '2026-11-12'
subject: 'sched/fair: Cut per-group work from sched domain rebuilds'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261111-bug-sched-fair-offline-active-v1-0-4f54523c5a70@linux.dev>
lore_url: https://lore.kernel.org/all/20261111-bug-sched-fair-offline-active-v1-0-4f54523c5a70@linux.dev/
authors:
- Qiliang Yuan
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <20261111-bug-sched-fair-offline-active-v1-0-4f54523c5a70@linux.dev>
  date: '2026-11-11'
  summary: active 短路 rq_offline_fair 两段遍历；per-rq flag 跳过 runtime_enabled 重同步
  review_outcome: Peter 质疑慢路径加成员变量的必要性并给 boolean 参数方向；作者用数据回应
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Peter 倾向用 boolean 参数取代 per-rq 成员
  next_action: 按 Peter 的 boolean 参数建议重构 patch 2 并回应场景正当性质疑
contribution_opportunities:
- kind: review
  description: 评估 boolean 参数方案在 rq_attach_root 三场景下能否替代 per-rq 成员
- kind: testing
  description: 在 RT_GROUP_SCHED 启用配置下测两补丁的 rt 侧记账副作用
generated_at: '2026-11-13T09:00:00+08:00'
source_email_count: 6
related_articles: []
tags:
- cfs
- load_balance
- topology
- perf
title: 'sched/fair: Cut per-group work from sched domain rebuilds'
layout: article
---

## TL;DR

Qiliang Yuan 发两补丁削掉 sched domain rebuild（CPU hotplug / cpuset partition 变更触发）里按「CPU 数 × task group 数」膨胀的逐组清理：rebuild 时 `rq_attach_root()` 会对每个 active CPU 跑一遍 `rq_offline_fair()`/`rq_online_fair()` 的全 task group 遍历。作者给出 4000 cpu cgroups / 32 核实测——partition 切换 -91%、cpu offline -70%、cpu online -65%，且补丁后耗时不再随 group 数增长。Peter Zijlstra 质疑「hotplug 本就是慢路径，为『从不发生』的事加成员变量」的必要性，并给出「加 boolean 参数」的替代实现方向。

## 背景与问题

sched domain rebuild 会把每个 active CPU 经 `rq_attach_root()` 移到新 root domain。其中 `rq_offline_fair()` 与 `rq_online_fair()` 在持 rq 锁、关中断的情况下遍历所有 task group，rebuild 成本为 `O(nr_cpus * nr_task_groups)`。此前 commit `af98d8a36a96` 已让 `unthrottle_offline_cfs_rqs()` 对 active CPU 提前返回，但 `f60a631ab9ed` 引入的 `clear_tg_offline_cfs_rqs()` 仍会遍历每个 group 并扣掉 `tg->load_avg` 贡献（随后 `update_tg_load_avg()` 又加回来）。作者在 AI agent harness 场景（每个容器/pod 一个带 cpu controller 的 cgroup，单机轻松上千 task group）下确证该成本真实存在，核上 KubeVirt 等 hot-add/remove vCPU 的负载会反复触发 rebuild。

## 技术方案

两补丁（`kernel/sched/fair.c` +20/-3、`kernel/sched/sched.h` +2）：

1. `Skip rq_offline_fair() work for CPUs that stay active`——把 active 判断收进 `rq_offline_fair()`，让 `unthrottle_offline_cfs_rqs()` 与 `clear_tg_offline_cfs_rqs()` 两段遍历都只对真正下线的 CPU 运行。
2. `Avoid re-syncing runtime_enabled on root domain changes`——`rq_online_fair()` 的 `update_runtime_enabled()` 会遍历所有 group 并各拿一次 `cfs_bandwidth` 锁；缓存状态只在 CPU 从未上线、或 `unthrottle_offline_cfs_rqs()` 背后清掉时才会过期。用 per-rq flag 记录「walk 已做完」，`update_runtime_enabled()` 在 flag 置起时跳过遍历，`unthrottle_offline_cfs_rqs()` 清 flag。

## 版本演进与当前进展

*current_version: v1（2026-11-11，cover `<20261111-bug-sched-fair-offline-active-v1-0-4f54523c5a70@linux.dev>`，11-12 北京时间收到）*。无版本演进。基准 `067c5c24cef23`。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**：对 patch 2 提出三点质疑——(a)「CPU hotplug 是慢路径，没什么『修复』可言；如果它疼，就是那种你需要停止去做的事」；(b) 对 4k cgroups 表示「wild」，追问「为什么在乎 rebuild 性能？为『从不』发生的事加数据我不确定是否说得通，真的需要新成员变量吗？」(c) 给出方向性替代：hotplug 代码本身显然知道 CPU 是「正在下线」还是「只是 rebuild」，可以给 `rq_offline_fair()`/`rq_online_fair()` 各加一个 boolean 参数、在 `rq_attach_root()` 与 `sched_set_rq_{on,off}line()` 里传对的值，而不用引入 per-rq 状态变量。
- **Qiliang Yuan（作者）**：回应 hotplug 非罕见——agent harness / KubeVirt 场景在运行时 hot-add/remove vCPU 很常见；补充实测（见效果评估）证明 rebuild 代价随 group 数可长到亚毫秒级关中断。并解释成员变量存在的理由：`rq_online_fair()` 无法区分「rebuild」与「CPU 首次上线」（两者 CPU 都是 active），只有后者在 `unthrottle_offline_cfs_rqs()` 后 runtime_enabled 才可能过期。

## 合入评估

*likelihood=medium*。方向（削减 rebuild 逐组遍历）明确、作者有量化数据支撑并用真实场景回应了 Peter 的「慢路径」质疑，但 Peter 倾向用「传 boolean 参数」而非「新增 per-rq 成员」实现，需作者调整实现方式。*blocking_issues*：Peter 质疑为慢路径加成员变量的必要性，倾向 boolean 参数方案。*next_action*：作者按 Peter 的 boolean 参数建议重构 patch 2（去成员变量），回复其对 4k cgroups 场景正当性的疑问。

## 效果评估

4000 cpu cgroups、32 核 VM（rt_group_sched=0，20 次 partition 切换 + 16 次 hotplug 中位数，三个内核同一轮测出）：partition root 13.28ms→1.21ms（-91%）、cpu offline 44.95ms→13.44ms（-70%）、cpu online 36.84ms→12.82ms（-65%），补丁后耗时不再随 group 数增长。作者另给单次 `rq_attach_root()`：median 188us、最坏 938us（4000 cgroups / 32 核，1280 次调用），打两个补丁后降到 2us。RT_GROUP_SCHED 启用时 rt.c 的 runtime 遍历仍保留。

## 我可以参与的点

- **review**：评估 Peter 的 boolean 参数方案是否真的能取代 per-rq 成员（尤其 `rq_attach_root()` 在三种调用场景下如何无误传参），这是 patch 2 能否按维护者预期形态落地的关键。
- **testing**：在 RT_GROUP_SCHED 启用的配置下测两补丁，确认 patch 1 的 active 短路对 rt.c 侧 runtime 记账无副作用（作者仅测了 rt_group_sched=0）。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261111-bug-sched-fair-offline-active-v1-0-4f54523c5a70@linux.dev/
- Peter 对 patch 2 的质疑: https://lore.kernel.org/all/20261112105624.GM2668804@noisy.programming.kicks-ass.net/
- 作者对 4k cgroups 场景的回应: https://lore.kernel.org/all/20261112111055.400697-1-qiliang.yuan@linux.dev/
