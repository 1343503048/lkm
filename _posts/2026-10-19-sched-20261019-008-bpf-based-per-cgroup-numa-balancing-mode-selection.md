---
id: sched-20261019-008
subject: BPF-based per-cgroup NUMA balancing mode selection
date: 2026-10-19
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20261019064157.29885-1-laoar.shao@gmail.com>
lore_url: https://lore.kernel.org/all/20261019064157.29885-1-laoar.shao@gmail.com/
authors:
- Yafang Shao
maintainers_involved: []
current_version: v3
patch_series:
- version: v3
  msgid: <20261019064157.29885-1-laoar.shao@gmail.com>
  date: 2026-10-19
  summary: RFC v3 五补丁：get_pref_llc stub 修复 + static_branch 极性 + numa helpers + 每 cgroup
    模式选择的 BPF kfunc 与热路径组合
  review_outcome: bpf-ci bot 仅 nit（多余括号、注释方向），无维护者表态
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - RFC 无维护者 review
  - per-cgroup 模式 vs 全局 sysctl 语义待确认
  next_action: 等 sched/numa 与 bpf 维护者 review，先清 bot nit
contribution_opportunities:
- kind: review
  description: challenge per-cgroup 模式与全局 sysctl 的优先级及 DISABLED 沿链继承语义
- kind: testing
  description: 混合负载（延迟敏感 + PMEM 分层）下验证按 cgroup 开关 NUMA balancing 的正确性
- kind: discussion
  description: 讨论调度参数 per-cgroup/BPF 化的社区接受度
generated_at: '2026-10-20T01:30:00'
source_email_count: 6
related_articles: []
tags:
- numa_balancing
- bpf
title: BPF-based per-cgroup NUMA balancing mode selection
layout: article
---

## TL;DR

Yafang Shao 发往 bpf-next 的 RFC v3 五补丁系列：给 NUMA balancing 加**每 cgroup 的模式选择**——latency-sensitive 服务想关掉 NUMA balancing、batch 服务想让 PMEM-resident 内存热晋升，全局 `kernel.numa_balancing` 单一 sysctl 无法同时满足。方案新增 `cgroup::numab_mode` + 两个 BPF kfunc，热路径组合 cgroup 链上请求。bpf-ci bot 只给了几处 nit（多余括号、注释方向存疑）。当日新发，暂无维护者表态。

## 背景与问题

`kernel.numa_balancing` 是系统级单一 sysctl：0 关机制、置位选普通平衡/内存分层/两者皆可，对所有 workload 一视同仁。但不同 workload 诉求冲突：latency-sensitive 服务要关、batch 服务希望 PMEM 内存热晋升而不付调度迁移代价。无单全局设置可同时满足——需要 per-cgroup 粒度。

## 技术方案

RFC v3（bpf-next）五补丁：

- **1/5** `sched: fix stale get_pref_llc() stub for !CONFIG_SCHED_CACHE`（`Fixes: b636fef85bda`）：`get_pref_llc()` 改签名后，!CONFIG_SCHED_CACHE 分支的 stub 仍是旧 `mm_struct *` 形参。
- **2/5** `sched: use static_branch_likely() for the NUMA balancing tick check`：默认 `NUMA_BALANCING_DEFAULT_ENABLED=y` 下 `task_tick_fair()` 每 tick 的 `static_branch_unlikely()` 走 taken jump，翻转为 `likely` 让快路径与默认一致。
- **3/5** `sched: add helpers for numa balancing`：新增 `task_numab_enabled()`/`numab_in_tiering_mode()`/`numab_in_normal_mode()` 取代散落的 static key 与 `sysctl_numa_balancing_mode` 位掩码直接访问（无功能变化）。
- **4/5** `sched: add BPF-based per-cgroup NUMA balancing mode selection`（核心）：`cgroup::numab_mode` 存每 cgroup 请求（`NUMAB_FOLLOW_SYSTEM=-1` 回退全局，否则是 `NUMA_BALANCING_*` 位掩码，创建时初始 -1）；两个 kfunc `bpf_numab_set_mode()`/`bpf_numab_get_mode()` 读写。热路径组合「匹配 cgroup 与所有祖先」的请求：task 侧走 task cgroup 链、folio 侧走其 memcg 链；DISABLED 在链上任一处即整体 opt-out、不可被下层重新开启；demotion 与 misplaced-migration 回退保持全局。
- **5/5**：selftest（不在 sched 缓存内）。

## 版本演进与当前进展

*current_version: v3*（RFC）。当日 bpf-ci AI bot 对 3/5、4/5 评论：`!(numab_in_tiering_mode())` 的多余括号可去；`task_numab_in_tiering_mode()` 注释方向可能写反（真值让 `task_numa_fault()` 跳过非 top-tier 统计）。暂无作者回复与维护者表态。

## Maintainer 意见与讨论焦点

无维护者/资深 member 表态。仅 bpf-ci AI bot 的 nit 级反馈（括号与注释措辞），不构成方向性异议。核心待决点（无人提出）：per-cgroup 模式与全局 sysctl 的语义优先级、DISABLED 的继承/传播规则是否被社区接受。

## 合入评估

*likelihood=unknown*。属 RFC、跨 sched/bpf/mm 三域，方案实质（per-cgroup NUMA balancing）此前少见先例，且当日只收到 AI bot nit、无任何维护者（sched/bpf/numa）表态。*blocking_issues*：RFC 无维护者 review、跨域语义待确认。*next_action*：等 sched/numa（Inabu/Mel Gorman 等）与 bpf 维护者 review；先按 bot 意见清 nit。

## 效果评估

无 benchmark 数据。2/5 是静态 branch 极性的微优化（作者称「消除默认配置下每 tick 的 taken jump」，主观判断、未见量化数据）；4/5 属功能扩展，无性能数字。

## 我可以参与的点

- `review`：per-cgroup 模式与全局 sysctl 的优先级、DISABLED 沿 cgroup 链的继承与传播语义值得 challenge。
- `testing`：在真实混合负载（延迟敏感 + PMEM 分层）上验证按 cgroup 开关 NUMA balancing 的行为正确性。
- `discussion`：4/5 里 kfunc 暴露的 per-cgroup 模式选择是否符合社区对「调度参数 BPF 化」的预期。

## 参考链接

- 封面信：https://lore.kernel.org/all/20261019064157.29885-1-laoar.shao@gmail.com/
- bpf-ci 对 4/5 的评论：https://lore.kernel.org/all/737a8f07246a2cd31950ffcdb2a98b9ee81824c27a362dd17e0ba94e2281b00e@mail.kernel.org/
