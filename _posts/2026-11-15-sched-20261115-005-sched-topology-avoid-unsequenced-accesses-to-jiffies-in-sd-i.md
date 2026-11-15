---
id: sched-20261115-005
date: '2026-11-15'
subject: 'sched/topology: Avoid unsequenced accesses to jiffies in sd_init()'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261114-topology-wunsequenced-v1-1-686a36fe61f5@kernel.org>
lore_url: https://lore.kernel.org/all/20261114-topology-wunsequenced-v1-1-686a36fe61f5@kernel.org/
authors:
- Nathan Chancellor
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261114-topology-wunsequenced-v1-1-686a36fe61f5@kernel.org>
  date: '2026-11-15'
  summary: 把两处 jiffies 初始化移出 designated initializer，插入序列点
  review_outcome: 暂无 review
upstream_commit: null
fixes_commit: 2b4cfe64dee0
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: '等待 sched 维护者 ack 并决定 stable 回合（Cc: stable）'
contribution_opportunities:
- kind: testing
  description: 用新版 clang 在 CONFIG_WERROR=y 下验证 sd_init() 告警消失，并排查同类 volatile 访问
generated_at: '2026-11-16T09:00:00+08:00'
source_email_count: 1
related_articles: []
tags:
- topology
title: 'sched/topology: Avoid unsequenced accesses to jiffies in sd_init()'
layout: article
---

## TL;DR

Nathan Chancellor 修 clang 新告警导致的构建破坏：`sd_init()` 的 designated initializer 里两处 `= jiffies`（`.last_balance`、`.last_decay_max_lb_cost`）对 volatile 变量构成未定序访问，`CONFIG_WERROR=y` / `W=1` 下 `-Wunsequenced` 报错。补丁把这两次初始化移到 initializer 之外插入序列点，消除 UB 与告警（Fixes: 2b4cfe64dee0，Cc: stable）。

## 背景与问题

clang 近期改进对 volatile 变量未定序访问的告警后（llvm commit 955715460eaf），`sd_init()` 出现新实例（kernel/sched/topology.c:2008）：`.last_decay_max_lb_cost = jiffies` 与另一处 `.last_balance = jiffies` 位于同一 designated initializer。按 C11 6.7.9.23，initializer list 各表达式求值顺序 indeterminately sequenced，两处对 volatile `jiffies` 的访问构成未定序的 side effect（UB），且访问 volatile 对象本身即 side effect——`CONFIG_WERROR=y` / `W=1` 下直接构建失败（Closes: ClangBuiltLinux/linux#2190）。回溯 `Fixes: 2b4cfe64dee0`（该 commit 把 newidle 统计初始化迁进 sd_numa_init() 的 designated initializer）。

## 技术方案

从 designated initializer 移除 `.last_balance = jiffies` 和 `.last_decay_max_lb_cost = jiffies` 两行，改为 initializer 之后独立赋值 `sd->last_balance = jiffies; sd->last_decay_max_lb_cost = jiffies;`，从而在两次 jiffies 访问之间放置序列点。kernel/sched/topology.c +2/-2，语义不变。

## 版本演进与当前进展

*current_version: v1（2026-11-15，`<20261114-topology-wunsequenced-v1-1-686a36fe61f5@kernel.org>`）*。当日发出，暂无 review。

## Maintainer 意见与讨论焦点

当日无维护者回帖。作者为 ClangBuiltLinux 维护者，附 Cc: stable 与完整 C11 条款逐条论证。

## 合入评估

*likelihood=high*。极简、纯编译器告警修复、语义不变、附 Cc: stable，属典型快速合入的 trivial fix。*blocking_issues*：暂无实质分歧，等待 sched 维护者 ack。*next_action*：等待维护者 ack 并决定 stable 回合范围。

## 效果评估

无运行时数据；修复的是构建期告警/错误（消除 `-Wunsequenced`）。作者给出 C11 5.1.2.3.2 / 6.5 / 6.7.9.23 条款论证 UB 性质。

## 我可以参与的点

- **testing**：用新版 clang 在 CONFIG_WERROR=y 下验证 sd_init() 不再报 -Wunsequenced；并排查内核其余 designated initializer 是否还有同类对 jiffies/volatile 变量的未定序访问。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261114-topology-wunsequenced-v1-1-686a36fe61f5@kernel.org/
- ClangBuiltLinux issue: https://github.com/ClangBuiltLinux/linux/issues/2190
