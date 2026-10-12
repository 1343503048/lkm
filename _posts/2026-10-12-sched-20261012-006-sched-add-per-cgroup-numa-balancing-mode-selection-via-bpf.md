---
id: sched-20261012-006
date: '2026-10-12'
subject: 'sched: add per-cgroup NUMA balancing mode selection via BPF'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20261012120438.52849-1-laoar.shao@gmail.com>
lore_url: https://lore.kernel.org/all/20261012120438.52849-1-laoar.shao@gmail.com/
authors:
- Yafang Shao
maintainers_involved: []
current_version: v2
patch_series:
- version: v2
  msgid: <20261012120438.52849-2-laoar.shao@gmail.com>
  date: '2026-10-12'
  summary: 1/3 引入 task_numab_enabled()/numab_mode_tiering() helper，替换散落的静态键/位掩码访问
  review_outcome: 当日新发，暂无 review
- version: v2
  msgid: <20261012120438.52849-3-laoar.shao@gmail.com>
  date: '2026-10-12'
  summary: 2/3 新增 bpf_numab_ops struct_ops，按 cgroup 选 NUMA balancing 模式
  review_outcome: 当日新发，暂无 review
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - RFC 阶段无人表态
  - BPF 内核侧接口与 cgroup 语义需 BPF/调度维护者确认
  next_action: 等 NUMA balancing / BPF struct_ops 维护者（Peter、Tejun、Andrew Morton 等）表态
contribution_opportunities:
- kind: review
  description: 评估 bpf_numab_ops 与现有 memcg/struct_ops 的 cgroup 生命周期、热路径开销是否符合预期
- kind: discussion
  description: 就「任务面 vs 内存面」两套策略钩子与全局 sysctl 的组合语义提设计问题
generated_at: '2026-10-13T01:40:00'
source_email_count: 2
related_articles: []
tags:
- numa_balancing
- cgroup
title: 'sched: add per-cgroup NUMA balancing mode selection via BPF'
layout: article
---

## TL;DR

Yafang Shao 发 RFC v2：全局 `kernel.numa_balancing[_mode]` 是 all-or-nothing，无法同时满足「延迟敏感服务只要调度统计不要 tiering 提升」与「批处理要 PMEM 内存被热提升」；引入 `bpf_numab_ops` struct_ops，把 NUMA balancing 模式选择下放到 per-cgroup BPF 策略。当日新发，RFC 阶段尚无 review。

## 背景与问题

全局 NUMA balancing 开关对每个 workload 一视同仁：`kernel.numa_balancing` 与 `kernel.numa_balancing_mode` 决定是否启用 + 用 normal 还是 tiering 模式。但不同服务诉求冲突——延迟敏感服务想要调度器的 NUMA 统计却不想要 tiering 的 promotion 机制，批处理服务则希望 PMEM 常驻内存变热时被提升、同时不想为调度器驱动的迁移买单。单一全局开关无法两全。

## 技术方案

系列 3 个补丁（今日缓存含 1/3、2/3）：

- **1/3**（`sched: add helpers for numa balancing`）：抽出 `task_numab_enabled()` 与 `numab_mode_tiering()` 两个 helper，替换 `fair.c`/`memory-tiers.c`/`migrate.c`/`vmscan.c`/`mempolicy.c` 里散落的 `sched_numa_balancing` 静态键与 `sysctl_numa_balancing_mode` 位掩码访问，无功能变化。
- **2/3**（`sched: add per-cgroup NUMA balancing mode selection via BPF`）：新增 `bpf_numab_ops` struct_ops，挂在 cgroup 上；内核跑「该 cgroup 及其所有祖先」的策略并把返回值做 OR 合并。一条策略问题两个表面：task 面（scanner/fault 统计）传 `task_struct*`、内存面（cpupid vs access-time、扫描豁免）传 `folio*`，二者恰有一个非空。语义：`DISABLED beats NORMAL beats TIERING`——策略总能 opt-out，不会被更强机制强行拉入。demotion 与迁移 fallback 保持全局（按节点级 reclaim 状态，不按 cgroup 策略）；root 链上无策略时退化为全局 sysctl（系列默认 no-op）。

## 版本演进与当前进展

v2 当日新发（作者自述 v1 后重组）；封面信详述动机与「保守选择优先」的组合规则。暂无回帖。

## Maintainer 意见与讨论焦点

当日无维护者表态。潜在焦点（据转述推断，未见正文）：BPF struct_ops 热路径（hinting fault/scanner/load balance）不可睡眠约束已在 `check_member` 落实（reject sleepable prog）；cgroup 生命周期与 struct_ops 析构、以及「空实现策略仍付静态键代价」用 `bpf_numab_validate()` 拒绝。

## 合入评估

*likelihood=unknown*。RFC 阶段无人表态，且 BPF/cgroup 交叉改动需多方确认。*blocking_issues*：无任何 review。*next_action*：等 NUMA balancing 与 BPF 维护者回应后再评估。

## 效果评估

无性能数据；作者强调「无策略挂载时系列是 no-op」，但未附 benchmark。

## 我可以参与的点

- `review`：核对 `bpf_numab_ops` 在 cgroup 销毁/迁移时与 `cgroup_bpf_release()` 的生命周期一致性，以及热路径（fault/scanner/load balance 持 rq 锁）下 `rcu_read_lock` + `percpu_ref_tryget_live_rcu` 的开销是否可接受。
- `discussion`：就任务面/内存面双表面与全局 sysctl 的组合语义、以及「祖先链 OR 合并」是否满足真实隔离诉求提设计问题。

## 参考链接

- lore（1/3）: https://lore.kernel.org/all/20261012120438.52849-2-laoar.shao@gmail.com/
- lore（2/3）: https://lore.kernel.org/all/20261012120438.52849-3-laoar.shao@gmail.com/
