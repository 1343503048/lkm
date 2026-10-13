# sched: add helpers for numa balancing

> **subject**：sched: add helpers for numa balancing

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261012-006：Yafang Shao 发 RFC v2「sched: add per-cgroup NUMA balancing mode selection via BPF」——全局 `kernel.numa_balancing[_mode]` 是 all-or-nothing，无法同时满足延迟敏感服务（只要统计不要 tiering 提升）与批处理（要 PMEM 热提升）两类诉求；引入 `bpf_numab_ops` struct_ops 把模式选择下放到 per-cgroup。系列 3 补丁，1/3 抽出 `task_numab_enabled()` 与 `numab_mode_tiering()` 两个 helper。当日新发、无 review。
- sched-20261013-005（今天）：David Hildenbrand（mm 维护者）对 1/3 的两个新 helper 给出针对性 review——函数命名（`numab_in_tiering_mode()`/`numab_tiering_enabled()` 更直观）、kerneldoc 里不该引用后续补丁、返回表达式应直接压成一行；Yafang 逐条接受并承诺更新。

## 背景与问题
（承接 sched-20261012-006）全局 NUMA balancing 开关对每个 workload 一视同仁，而不同服务诉求冲突（延迟敏感服务想要调度器的 NUMA 统计但不要 tiering promotion；批处理希望 PMEM 常驻内存变热被提升、又不想为调度器驱动迁移买单）。系列 1/3 把 `fair.c`/`memory-tiers.c`/`migrate.c`/`vmscan.c`/`mempolicy.c` 里散落的 `sched_numa_balancing` 静态键与 `sysctl_numa_balancing_mode` 位掩码访问抽出成 helper，为后续 per-cgroup 策略铺路，本身无功能变化。今天的新进展是这一 helper 补丁得到 mm 维护者的具体 review。

## 技术方案
（承接 sched-20261012-006）1/3 抽出两个 helper：
- `task_numab_enabled()`：封装 `sched_numa_balancing` 静态键判断
- `numab_mode_tiering()`：封装 `sysctl_numa_balancing_mode & NUMA_BALANCING_MEMORY_TIERING` 判断

今天 David 的 review 意见：
- 函数名 `numab_mode_tiering()` 不直观，建议 `numab_in_tiering_mode()` / `numab_tiering_enabled()` 一类，语义为「是否处于 tiering 模式」。
- 返回表达式可直接压成一行 `return sysctl_numa_balancing_mode & NUMA_BALANCING_MEMORY_TIERING;`。
- 两个函数既然要文档化，就应写规范 kerneldoc；当前函数文档里「谈论后续补丁」是错误的，且后半段在本文上下文中不通。
- （正面）「Some of these might make sense even without the bigger series」——这些 helper 独立亦有价值。

Yafang 逐一回应：会改名 `numab_in_tiering_mode()`、会按建议简化、会更新文档。

## 版本演进与当前进展
RFC v2（系列 3 补丁，1/3 为 helper）。当日无新版本，1/3 得到 David 的首次 review，作者承诺按意见更新（改名、简化、kerneldoc），v3 待发。

## Maintainer 意见与讨论焦点
- **David Hildenbrand**（mm 维护者）：只就新暴露的 helper 提意见——命名、kerneldoc、化简；认为部分 helper 甚至可脱离大系列独立有价值。
- 无 NAK；方向获建设性 review，作者全部接受。

## 合入评估
*likelihood=medium*。RFC 阶段获 mm 维护者正向 review、反馈具体可执行，作者已承诺更新，但尚未见 Ack 或 v3。*blocking_issues*：helper 命名/文档需按 review 修订，整个 struct_ops 大系列仍在 RFC。*next_action*：Yafang 发 v3（helper 改名+化简），继续等 sched/mm 维护者评整个系列。

## 效果评估
暂无效果数据（1/3 为无功能变化的预重构 helper，无 benchmark）。

## 我可以参与的点
当前阶段暂无明显参与空间：1/3 是纯重构、review 反馈已明确、作者已认领；可持续观察 v3 及整个 BPF-cgroup 系列在 sched 维护者侧的走向。

## 参考链接
- 1/3 补丁 lore：https://lore.kernel.org/all/20261012120438.52849-2-laoar.shao@gmail.com/
- 系列 cover（20261012-006）：https://lore.kernel.org/all/20261012120438.52849-1-laoar.shao@gmail.com/

---
id: sched-20261013-005
subject: 'sched: add helpers for numa balancing'
date: 2026-10-13
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: '<20261012120438.52849-2-laoar.shao@gmail.com>'
lore_url: 'https://lore.kernel.org/all/20261012120438.52849-2-laoar.shao@gmail.com/'
authors:
  - 'Yafang Shao'
maintainers_involved:
  - 'David Hildenbrand'
current_version: v2
patch_series:
  - version: v2
    msgid: '<20261012120438.52849-2-laoar.shao@gmail.com>'
    date: 2026-10-12
    summary: '抽出 task_numab_enabled()/numab_mode_tiering() helper，为 per-cgroup BPF 策略铺路'
    review_outcome: 'David 建议改名 numab_in_tiering_mode()、写规范 kerneldoc、化简，作者全部接受'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'helper 命名/文档需按 David 意见修订，整个 bpf_numab_ops 系列仍在 RFC'
  next_action: 'Yafang 发 v3 并入改名/化简，继续推进整个 BPF-cgroup 系列'
contribution_opportunities: []
generated_at: '2026-10-14T01:00:00+08:00'
source_email_count: 2
related_articles:
  - sched-20261012-006
tags: [numa_balancing, cgroup]
---