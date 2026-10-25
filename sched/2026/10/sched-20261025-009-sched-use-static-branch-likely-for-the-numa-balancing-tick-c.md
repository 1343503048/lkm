# sched: use static_branch_likely() for the NUMA balancing tick check

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261021-018：Yafang Shao 的 bpf-next RFC v3 系列中的 2/5 补丁——把 NUMA balancing tick 检查改用 `static_branch_likely()` 微优化；当日 Gregory Price 给 Acked-by 并要求「请单独提交」。
- sched-20261024-010：作者拆出单独重发（`[PATCH 2/2]`），Gregory Price 复审后撤回其 Ack 判断——「probably just drop this patch」，理由单节点系统该 static key 默认关闭、收益不大。
- sched-20261025-009（今天）：Vincent Guittot 质疑「其它 static key 也用 `static_branch_unlikely()`、numa 为何要例外」；作者 Yafang 逐条回应——其余 `sched_numa_balancing` 使用点都在 likely() 侧或 disabled 时也运行，且 `sched_numa_balancing` 是唯一带显式默认开启策略的 key；同时承认 Gregory 说得对：单节点系统会为此每次 tick 多付一次预测跳转。

## 背景与问题
（承接 20261021-018）`task_tick_fair()` 每个 tick 检查 `sched_numa_balancing`，`static_branch_unlikely()` 把 nop 留给 disabled 分支，导致默认配置（`NUMA_BALANCING_DEFAULT_ENABLED=y`）每次 tick 多付一次 taken jump；拟翻成 `static_branch_likely()` 使快路径匹配默认。今日背景新增：Vincent 质疑为何 numa 与 `sched_cluster_active`/`sched_cache_active` 等其它 key 不一致。

## 技术方案
（承接 20261021-018）单补丁：`task_tick_fair()` 里 `static_branch_unlikely(&sched_numa_balancing)` 改 `static_branch_likely(&sched_numa_balancing)`。今日无代码变更，为作者对维护者质疑的逐条回应。

## 版本演进与当前进展
*current_version: v3*（所在系列原为 bpf-next RFC v3；拆出的单独提交为 `[PATCH 2/2]`）。当日无新版本，为讨论推进。

## Maintainer 意见与讨论焦点
- **Vincent Guittot**（sched maintainer）：`static_branch_unlikely` 是其它 static key（`sched_cluster_active`、`sched_cache_active`、`__sched_core_enabled`、`sched_asym_cpucapacity` 等）的默认选择，「有些地方可能被别的 key 挡在后面，但否则就应 unlikely()」。
- **Gregory Price**（复审）：其它 `sched_numa_balancing` 检查点都走 likely()，这一处是例外；numa balancing 默认开启。
- **作者 Yafang** 回应：枚举了其它 `sched_numa_balancing` 使用点（`exceed_llc_capacity`、`get_pref_llc`、`get_scan_cpumasks`、`update_scan_period`、`migrate_degrades_locality`）——都不被别的 key 挡、且除 `task_numa_fault()` 外都在 key disabled 时也运行；`sched_cluster_active` 等虽是 `DEFINE_STATIC_KEY_FALSE()`，但都**没有默认开启的 config**，而 `sched_numa_balancing` 是唯一带 `NUMA_BALANCING_DEFAULT_ENABLED=y` 默认策略的。同时承认 Gregory 对单节点情况的指正：单节点系统为此每次 tick 多付一次预测跳转。

## 合入评估
*likelihood=low*。作者在尽力辩护，但 Vincent（维护者）与 Gregory 均倾向维持 `unlikely()`，分歧点（默认开启策略是否足以成为例外）尚未被维护者接受。*blocking_issues*：Vincent 与 Gregory 的质疑未化解；单节点系统存在可测量的负收益。*next_action*：作者若能提供多节点 NUMA 热路径实测收益、或接受维护者的 unlikely() 口径，方可继续。

## 效果评估
无 benchmark。属分支预测/静态 key 语义微优化；今日作者承认单节点系统会因此每次 tick 多付一次预测跳转（负收益），多节点侧收益仍无数据支撑。

## 我可以参与的点
- *kind: discussion*：在多节点 NUMA 系统上实测 `task_tick_fair()` 该检查点的分支走向与收益，为「默认开启策略是否值得例外」提供数据。
- *kind: review*：核对作者对其它 `sched_numa_balancing` 使用点「disabled 时也运行」的枚举是否准确。

## 参考链接
- 作者今日回帖: https://lore.kernel.org/all/CALOAHbAgUdVvvtdEjcP6otQgVmptsred+xZSLtDd9zj-bMmM1Q@mail.gmail.com/
- 前文: sched-20261024-010 / sched-20261021-018

---
id: sched-20261025-009
date: 2026-10-25
subject: 'sched: use static_branch_likely() for the NUMA balancing tick check'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20261019064157.29885-3-laoar.shao@gmail.com>'
lore_url: 'https://lore.kernel.org/all/20261019064157.29885-3-laoar.shao@gmail.com/'
authors:
  - 'Yafang Shao'
maintainers_involved:
  - 'Vincent Guittot'
current_version: v3
patch_series:
  - version: v3
    msgid: '<20261019064157.29885-3-laoar.shao@gmail.com>'
    date: 2026-10-19
    summary: 'NUMA balancing tick 检查改用 static_branch_likely()'
    review_outcome: 'Vincent 质疑例外、Gregory 建议 drop，作者逐条辩护'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - 'Vincent 与 Gregory 的质疑未化解，单节点系统有可测负收益'
  next_action: '作者提供多节点热路径实测收益或接受 unlikely() 口径'
contribution_opportunities:
  - kind: discussion
    description: '多节点 NUMA 系统实测该检查点分支走向与收益，为「默认开启策略是否值得例外」提供数据'
  - kind: review
    description: '核对作者对其它 sched_numa_balancing 使用点枚举的准确性'
generated_at: '2026-10-26T09:00:00'
source_email_count: 1
related_articles:
  - sched-20261024-010
  - sched-20261021-018
tags:
  - numa_balancing
  - cfs
---