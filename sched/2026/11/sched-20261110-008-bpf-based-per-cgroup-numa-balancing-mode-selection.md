# BPF-based per-cgroup NUMA balancing mode selection

## TL;DR

Yafang Shao 发 RFC v4（4 补丁），把 NUMA balancing 的开关从「单一系统级 sysctl `kernel.numa_balancing`」下放到 per-memcg，并通过 BPF kfunc（`bpf_numab_set_mode()`/`bpf_numab_get_mode()`）读写：延迟敏感负载可关、NUMA 感知负载可开，不再靠一个全局开关。设计按 Tejun 的建议把 mode 存进 cgroup 的 memcg。patch 1 是纯 helper 清理（`task_numab_enabled()` 等），已获 Zi Yan 与 Gregory Price 双 Acked-by 且「可单独收取」；核心 BPF 机制（patch 2/3/4）仍待 bpf 与 mm/numa 维护者评审。

## 背景与问题

作者在 Kubernetes 大规模服务器集群里，NUMA balancing 历来是每台机器全局关闭的；随着多 socket AMD EPYC 部署增多，跨 NUMA 访问成了关键性能问题，又需要重新考虑开启。`kernel.numa_balancing` 是单一系统级 sysctl：延迟敏感负载要关、NUMA 感知负载要开，没有任何全局设置能同时满足。于是需要 per-cgroup 的 NUMA balancing 模式。

## 技术方案

按 Tejun 的建议，把现有 NUMA balancing 模式位存进 cgroup 的 memcg，用 BPF kfunc 暴露：`bpf_numab_set_mode()`（对特定 memcg 设置模式，cgroup 无可见在线 memcg 时 -EOPNOTSUPP，取值 NUMAB_* 枚举或 `NUMAB_FOLLOW_SYSTEM(-1)` 回落到全局 sysctl）、`bpf_numab_get_mode()`（返回该 cgroup 生效 memcg 及所有祖先的组合任务侧请求，无请求时返回 FOLLOW_SYSTEM）。两个 kfunc 注册为 `BPF_PROG_TYPE_SYSCALL`，set 是 KF_SLEEPABLE。

patch 1 `sched: add helpers for numa balancing` 引入 `task_numab_enabled()`/`numab_in_normal_mode()`/`numab_in_tiering_mode()` 替换对 `sched_numa_balancing` static key 与 `sysctl_numa_balancing_mode` 的直接访问（无功能变化）；patch 2 `sched: sample NUMA balancing mode once per path` 每个路径取一次快照下传（无功能变化）；patch 3 `sched: add BPF-based per-cgroup NUMA balancing mode selection` 为核心机制（新增 `kernel/sched/bpf_numab.c`，mode 存 `mem_cgroup::numab_mode`）；patch 4 `selftests/bpf: add tests for the numab kfuncs`。

## 版本演进与当前进展

*current_version: v4（2026-11-10，`<20261110032913.71974-1-laoar.shao@gmail.com>`）*。v4 已按此前评审演进到 memcg 存储 + kfunc 形态。当日新评审：Zi Yan 对 patch 1 给 Acked-by（「nice cleanup，可单独收取」）并在 cover 上 ping Ying Huang；Gregory Price 对 patch 1 给 Acked-by。

## Maintainer 意见与讨论焦点

- **Zi Yan（mm maintainer）**：Acked patch 1，并 ping Ying Huang（NUMA balancing 主要贡献者）看整体方案。
- **Gregory Price（Meta）**：Acked patch 1。
- 核心 BPF 机制（patch 3）尚无维护者（bpf / mm / sched）明确表态。无 NAK。

## 合入评估

*likelihood=unknown*。patch 1（纯 helper 清理）已获双 Ack 可先单独收取；但「per-cgroup NUMA balancing 用 BPF kfunc 控制」本身是新颖机制，需 bpf 与 mm/numa 维护者认可（Ying Huang 尚未表态），当日证据不足以判合入前景。*blocking_issues*：① patch 3 的 memcg 存储 + kfunc 设计待 bpf/mm 维护者评审；② Ying Huang 对整体方向的意见未回。*next_action*：patch 1 可先收；整体方案等 Ying 与 bpf 维护者评审。

## 效果评估

无性能数据。价值诉求是运维灵活性（按负载类型分控 NUMA balancing），cover 未给 benchmark。

## 我可以参与的点

- **review**：评估 patch 3 里「DISABLED 绑定整棵子树、其余按位 OR」的合并语义（作者明示了「最近请求优先会被后裔反悔祖先 opt-out」的设计取舍，值得验证其正确性）。
- **discussion**：若有混合负载集群（延迟敏感 + NUMA 感知共存）的真实需求，向作者提供场景输入有助于方案落地。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261110032913.71974-1-laoar.shao@gmail.com/

---
id: sched-20261110-008
date: '2026-11-10'
subject: "BPF-based per-cgroup NUMA balancing mode selection"
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: "<20261110032913.71974-1-laoar.shao@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261110032913.71974-1-laoar.shao@gmail.com/"
authors: [Yafang Shao]
maintainers_involved: [Zi Yan]
current_version: v4
patch_series:
  - version: v4
    msgid: "<20261110032913.71974-1-laoar.shao@gmail.com>"
    date: '2026-11-10'
    summary: "per-memcg NUMA balancing 模式 + BPF kfunc 读写"
    review_outcome: "patch 1 获 Zi Yan 与 Gregory Price 双 Acked-by，可单独收取"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - "patch 3 memcg 存储 + kfunc 设计待 bpf/mm 维护者评审"
    - "Ying Huang 对整体方向的意见未回"
  next_action: "patch 1 可先收；整体方案等 Ying 与 bpf 维护者评审"
contribution_opportunities:
  - kind: review
    description: "评估 patch 3 DISABLED 绑定子树/其余按位 OR 的合并语义正确性"
  - kind: discussion
    description: "提供混合负载集群（延迟敏感 + NUMA 感知共存）的真实需求场景"
generated_at: "2026-11-11T09:00:00+08:00"
source_email_count: 3
related_articles: []
tags: [numa_balancing, cgroup]
---