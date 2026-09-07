# sched/fair: Rework/fix task_h_load()

## TL;DR

Peter Zijlstra 亲自重做/修 `task_h_load()`（8/28 发的 4 补丁系列），9/2 由 Chen Yu、Vincent Guittot
与他在 `set_next_task_fair()`/`__calc_prop_weight()` 附近来回。当天状态是「维护者还在复现」，没有结论。

## 背景与问题

`task_h_load()` 用于负载均衡时估算任务在层级 cgroup 下的「层级负载」，其计算在
cgroup 权重/层级变化后存在不一致或错误，影响 load balance 的迁移决策。本期对其做
重做/修复（作为某 4/4 或 7/7 系列的一部分，UID 72914 为 4/4）。

## 技术方案

- `[PATCH 4/4] sched/fair: Rework/fix task_h_load()`（UID 72914），配套 Re: 讨论
  （73218、73259、73677、73678、73685）。
- 修正层级负载的累加/缩放逻辑，使其在 cgroup 权重调整后给出一致结果。

## 版本演进与当前进展

- 当前状态：**under_review**（作为多补丁系列的一部分推进）。
- 合入可能性 medium；影响 load balance 准确性，需维护者确认语义正确性。

## Maintainer 意见与讨论焦点

- 顺序：Chen Yu（Intel）13:26 首先回帖（72936），Vincent Guittot 15:55 / 18:37 / 18:39 三次跟进
  （73238/73683/73685），Peter Zijlstra 16:13 表态（73257）后 18:36 回报（73704）："Different physical
  machine.. *splat*, virtual machine it lives. Argh I hate computers. Anyway, confir…"（缓存中截断）。
  也就是说换机器验证时先撞到一个崩溃、随后退回虚拟机，连作者本人当天都还没稳定复现问题。
- 没有 NAK，也没有 ack；焦点是 `__calc_prop_weight()` 在 `set_next_task_fair()` 路径上算出的 weight
  与层级负载是否自洽。

## 合入评估

**中**。层级负载直接决定 load balance 的迁移判断，作者又是要合的人，方向上没人反对；卡点是复现与
语义确认——Peter 当天还在追 repro，说明这个 bug 的触发条件本身没讲清楚。4/4 的其余 3 个补丁当天没有讨论。

## 效果评估

线程内无 benchmark 数字，无人给出「修复前后迁移次数/负载均衡质量」的对比。争议全部停留在代码语义层面。
暂无效果数据。

## 我可以参与的点

- 最有价值的是给一个确定性 repro：cgroup 权重/层级热调整 + 跨组迁移的组合，Peter 当天在找的东西。
- 若手上有机器，可以替他验证那个 "*splat*"——换物理机后出现的崩溃是什么，和本 bug 是否同源。
- 顺带 review 4/4 系列的其余 3 个补丁，它们在 09-02 完全没有被讨论。

## 参考链接

- 009 RFC v2 NUMA 细粒度均衡 + sched/cache 迁移辅助
- 015 sched：Remove sched_class::balance()

---
id: sched-20260902-007
date: '2026-09-02'
subject: 'sched/fair: Rework/fix task_h_load()'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: null
lore_url: null
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: null
authors:
- Vincent Guittot
- Peter Zijlstra
- Chen Yu
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: medium
  blocking_issues:
  - "Peter Zijlstra 当天仍在尝试复现，故障触发条件未定义清楚"
  - "__calc_prop_weight() 与 set_next_task_fair() 路径的负载/权重自洽性未获 Chen Yu / Vincent Guittot 认可"
  - "系列其余 3 个补丁当日无人讨论"
  next_action: "提供确定性复现脚本，并确认换机后出现的崩溃是否与本问题同源"
contribution_opportunities:
- "构造 cgroup 权重热调 + 跨组迁移的确定性 repro，帮 Peter Zijlstra 结束复现阶段"
- "验证 task_h_load() 在层级权重调整后与 __calc_prop_weight() 的结果一致性"
- "review 该 4 补丁系列中当日无人讨论的另外 3 个补丁"
source_email_count: 6
related_articles: []
tags:
- sched/fair
---
