# sched/fair: Reject misfit pulls onto busy SMT siblings on asym-capacity

## TL;DR
09-15 Matthieu Baerts 回复 Sasha Levin 的 AUTOSEL（6.18-6.1）回合通知，指出该补丁在 v6.1 上编译失败：`update_sd_lb_stats()` 里用到 `is_core_idle()`，但该函数在 6.1 尚未声明（implicit declaration of function 'is_core_idle'）。这解释了为何 6.1 的自动检测没发现问题——补丁在 6.1 上根本无法编译，需要 Sasha 检查该 stable 回合。

## 背景与问题
`[PATCH AUTOSEL 6.18-6.1]` 表明 Sasha Levin 的自动 stable 选择机制把主线补丁「sched/fair: Reject misfit pulls onto busy SMT siblings on asym-capacity」纳入了 6.18 到 6.1 的 stable 候选。Matthieu Baerts（net/MPTCP 维护者，常审 stable backport）在验证 v6.1 构建时发现编译错误，并据此反推：6.1 上 CI 未报问题是编译没过、并非真的没问题。

## 技术方案
无代码补丁。Matthieu 给出具体报错定位：

```
kernel/sched/fair.c:9912:53: error: implicit declaration of function 'is_core_idle'
 9912 | env->dst_core_idle = !sched_smt_active() || is_core_idle(env->dst_cpu);
```

即补丁依赖的 `is_core_idle()` 辅助函数在 6.1 分支尚不存在，需要额外 backport 依赖函数或对该 stable 版本做适配。

## 版本演进与当前进展
本日为 single 回帖，无新版。待 Sasha/stable 侧确认：是否丢弃 6.1 的候选、或补依赖后再回。尚无 Sasha 回复。

## Maintainer 意见与讨论焦点
- **Matthieu Baerts**：点出 v6.1 构建失败（`is_core_idle` 未声明）并暗示之前的自动检测因编译失败而未真正生效，"you might need to check this"。
- 未决问题：该 stable 候选在 6.1 上应被 drop 还是补依赖 backport，尚无结论。

## 合入评估
*likelihood=unknown*。这是 stable 回合内部的正确性提示，不涉及 mainline 合入；v6.1 候选大概率需修正或丢弃。*blocking_issues*：补丁依赖 `is_core_idle()`，6.1 缺失该函数。*next_action*：Sasha/stable 维护者确认 6.1 候选处理方式（drop 或 backport 依赖函数）。

## 效果评估
无性能数据。核心证据是 6.1 上的编译报错（`implicit declaration of function 'is_core_idle'`），属构建层面问题。

## 我可以参与的点
- kind=review：核对 `is_core_idle()` 在主线是何时、以哪个 commit 引入，判断 6.1 最优是 drop 还是连带 backport 依赖。
- kind=testing：在 v6.1 分支应用该候选后尝试构建，确认报错与所需的最小依赖集合。

## 参考链接
- Matthieu Baerts 回帖：https://lore.kernel.org/all/599fd878-e670-4ee7-8ded-4299c19c085c@kernel.org/
- AUTOSEL 6.1 候选：https://lore.kernel.org/all/20260831133314.4125787-171-sashal@kernel.org/

---
id: sched-20260915-008
date: '2026-09-15'
subject: 'sched/fair: Reject misfit pulls onto busy SMT siblings on asym-capacity'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20260831133314.4125787-171-sashal@kernel.org>'
lore_url: 'https://lore.kernel.org/all/599fd878-e670-4ee7-8ded-4299c19c085c@kernel.org/'
authors: []
maintainers_involved:
  - 'Matthieu Baerts'
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - '补丁依赖 is_core_idle()，6.1 分支缺失该函数导致编译失败'
  next_action: 'Sasha/stable 维护者确认 6.1 候选处理方式（drop 或 backport 依赖函数）'
contribution_opportunities:
  - kind: review
    description: '核对 is_core_idle() 主线的引入 commit，判断 6.1 最优是 drop 还是连带 backport 依赖'
  - kind: testing
    description: '在 v6.1 分支应用候选后尝试构建，确认报错与所需最小依赖集合'
generated_at: '2026-09-16T01:05:00'
source_email_count: 1
related_articles: []
tags:
  - load_balance
  - topology
  - hyperthreading
---