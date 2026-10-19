# x86, sched, mm: Speed up CPU hotplug on large systems

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261015-002：Pasha Tatashin 发 v1 八补丁系列（x86+sched+mm）加速大规模 x86 服务器顺序热插拔，调度侧为 5/8（sgc 缓存 + 惰性分配）与 6/8（dl_server O(N^2)→O(N) 记账）；480 核 Intel 总耗时 106.23s→5.07s（21x）。
- sched-20261016-014：Tony Luck 实测离线 4.833s→3.17s、在线 6.157s→3.796s，提示反向离线可再省；Prateek 对 5/8 提 `find_group_balance_cpu()` 重构；Tim Chen 指出 7/8 的 free 不受 `sched_domains_mutex` 保护、要求补 `lockdep_assert_cpus_held()` 与惰性分配不变量。
- sched-20261019-004（今天）：Pasha 发 v2（8 补丁）折入各方意见；Borislav Petkov 回帖援引 submitting-patches「至少等一周再重发/ping」+ merge window 刚开，要求「stop the spamming please」——流程提醒，非内容 NAK。

## 背景与问题

（承接 20261015-002 → 016-014 → 018-010）live update 要求快速 CPU online/offline；系列消除大规模 x86 服务器顺序热插拔在 arch/x86（WBINVD/CMCI/MTRR rendezvous）、调度拓扑构建器、deadline 带宽记账、vmstat 四层的瓶颈。v2 今日发出，继续以 480 核 Intel Xeon 6985P-C 与 512 核 AMD EPYC 9B45 为基准。

## 技术方案

v2 共 8 补丁，调度侧三处：

- **5/8 sched/topology**：`init_sched_groups_capacity()` 反复算 `group_weight`/`cores`/`asym_prefer_cpu`（O(N^3)）；改为在 `sched_group_capacity` 上缓存，重叠 NUMA 层级复用已初始化的 sgc，并惰性分配 `sdd->sg/sgc/d->sds`。（离线 9.85→5.15s，-47.7%；在线 8.69→4.05s，-53.4%）
- **6/8 sched/deadline, topology**：root_domain 重建时 `__dl_server_attach_root()` 反复走 O(N^2) dl_server 带宽遍历；移除 `rq_attach_root()` 里冗余调用，`dl_clear_root_domain()` 换成单次 O(N) 累加 + 单次 O(N) extra_bw 更新。
- **7/8 sched/topology**：`build_sched_domains()` 里 percpu 指针数组反复 alloc/free、`cpumask_weight` 重复计算；跨重建复用 percpu 数组、`sd_init()` 直接初始化 span_weight、LLC sibling 复用 llc_bytes。（离线 3.88→3.37s，-13.1%）

x86 侧（1-4）：移除 1990s 遗留的 trampoline WBINVD（单此一项把 Intel 在线 65.83→11.14s）、跳过 MWAIT 前冗余 WBINVD、`cmci_rediscover()` 改单拓扑 peer 探测、MTRR 匹配时跳过 stop_machine rendezvous。另 8/8 为 vmstat。总体：Intel 总耗时 106.23→5.07s（-95.2%，21x）；AMD 8.41→3.38s（-59.8%，2.5x）。

## 版本演进与当前进展

*current_version: v2*（今日 `<20261019011446.834487-1-pasha.tatashin@soleen.com>`）。v1（20261015-002）→ 三方 review（Tony 实测、Prateek、Tim Chen，20261016-014）→ 作者逐条回应确认折入（20261018-010）→ 今日 v2 发出。

## Maintainer 意见与讨论焦点

Borislav Petkov（x86 维护者）今日回帖仅作流程提醒：援引 submitting-patches「patches 发出后至少等一周再重发或 ping（merge window 期间可能更久）」+「merge window just opened」，要求停止频繁重发。非对内容的 NAK，但说明 v2 短期不会进入评审焦点；此前 Tony Luck/Prateek/Tim Chen 的技术意见已在 v2 中折入。

## 合入评估

*likelihood=unknown*。方向（快速热插拔）有实质三方验证与具体数据，但处于 merge window、x86 维护者明确要求作者等待，sched 侧维护者（Peter/Juri/Vincent）尚未对 sched 补丁 5-7 正式表态。*blocking_issues*：merge window 期间暂停、sched 侧补丁无正式 review。*next_action*：作者按 Borislav 建议等待 merge window 后再推进，争取调度维护者对 5-7/8 的 review。

## 效果评估

作者给出 10 次均值：Intel 480 核 offline 40.40→3.09s（-92.4%，13.1x）、online 65.83→1.98s（-97.0%，33.2x）、total 106.23→5.07s（-95.2%，21x）；AMD 512 核 offline 4.53→2.30s、online 3.88→1.08s、total 8.41→3.38s（-59.8%，2.5x）。各 sched 补丁也附单项收益（见技术方案）。无 rcu_expedited 时全序列 10 次均值：Intel 12.04s、AMD 15.99s。

## 我可以参与的点

- `testing`：在其它大核数平台（arm64、更多 socket/CCD 拓扑）复测离线/在线耗时，验证 5-7/8 的拓扑/带宽优化在非 x86 拓扑下无回退。
- `review`：sched 侧（5-7/8）的 `sched_group_capacity` 缓存、dl_server O(N) 记账、跨重建 percpu 复用涉及锁与生命周期不变量，值得调度维护者之外的人复核。

## 参考链接

- v2 封面信：https://lore.kernel.org/all/20261019011446.834487-1-pasha.tatashin@soleen.com/
- Borislav 回帖：https://lore.kernel.org/all/20261019041420.GCatWZHINJx7DIhXSP@fat_crate.local/

---
id: sched-20261019-004
subject: "x86, sched, mm: Speed up CPU hotplug on large systems"
date: 2026-10-19
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261019011446.834487-1-pasha.tatashin@soleen.com>"
lore_url: "https://lore.kernel.org/all/20261019011446.834487-1-pasha.tatashin@soleen.com/"
authors: ["Pasha Tatashin"]
maintainers_involved: ["Borislav Petkov"]
current_version: v2
patch_series:
  - version: v1
    msgid: "<20261015153331.1872641-1-pasha.tatashin@soleen.com>"
    date: 2026-10-15
    summary: "八补丁 v1：x86 WBINVD/CMCI/MTRR + sched 拓扑 O(N^3)/dl_server O(N^2) + vmstat"
    review_outcome: "Tony Luck 实测认可；Prateek/Tim Chen 给 5/8、7/8 具体改动意见（见 016-014）"
  - version: v2
    msgid: "<20261019011446.834487-1-pasha.tatashin@soleen.com>"
    date: 2026-10-19
    summary: "折入 Tony/Prateek/Tim 意见，8 补丁重发，附带逐项 benchmark"
    review_outcome: "Borislav 指 merge window 期间应等待、停止频繁重发"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["merge window 期间维护者要求等待", "sched 侧补丁 5-7/8 无正式 review"]
  next_action: "作者等待 merge window 结束，推进调度维护者对 5-7/8 的 review"
contribution_opportunities:
  - kind: testing
    description: "在 arm64/更多拓扑大核数平台复测离线/在线耗时，验证非 x86 无回退"
  - kind: review
    description: "复核 sched 侧 sgc 缓存、dl_server O(N) 记账、跨重建 percpu 复用的锁与生命周期不变量"
generated_at: "2026-10-20T01:30:00"
source_email_count: 5
related_articles: ["sched-20261015-002", "sched-20261016-014", "sched-20261018-010"]
tags: [topology, deadline, load_balance]
---