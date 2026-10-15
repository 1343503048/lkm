# x86, sched, mm: Speed up CPU hotplug on large systems

## TL;DR
Pasha Tatashin 发 v1 八补丁系列（x86 + sched + mm），针对 live update 场景需要快速 CPU online/offline 的需求，系统性地消除大规模 x86 服务器上顺序热插拔的软硬件瓶颈。其中调度侧两处改动：缓存 `sched_group_capacity` 的 group_weight/cores/asym_prefer_cpu、按需惰性分配 domain 结构（5/8），以及去掉 root_domain 重建时的 O(N^2) dl_server 带宽遍历（6/8）。整体在 480 核 Intel Xeon 上热插拔总耗时 106.23s→5.07s（快 21 倍），在 512 核 AMD EPYC 上 8.41s→3.38s（快 2.5 倍）。当日无 review，合入前景待维护者评估。

## 背景与问题
live update 要求快速的 CPU online/offline 能力。在现代高核数 x86 服务器上顺序 offlining/onlining 所有应用处理器，会依次暴露 arch/x86、调度拓扑构建器、deadline 带宽记账、vmstat 四个层面的硬件与算法瓶颈。封面信给出的基准是逐核 `echo 0/1 > .../online` 循环（`rcu_expedited=1`，每步 10 次取均值）。

调度侧的两个瓶颈（5/8、6/8）：
- **拓扑构建 O(N^3)**：顺序热插拔中每步都调 `build_sched_domains()`。非重叠层级上所有共享同一 domain span 的 CPU 共享同一 `sched_group` 环，但 `init_sched_groups_capacity()` 对域内每个 CPU 都重走整个环、反复重算 group_weight/cores/asym_prefer_cpu；`__sdt_alloc()/__sds_alloc()` 又为每个 CPU 预分配一堆立即被释放的结构。
- **dl_server 带宽记账 O(N^2)**：每个 rq 默认带 fair_server（可选 ext_server）。root_domain 重建时 `partition_sched_domains_locked()` 做三次 O(N^2) 的远端 rq 带宽更新（`detach_destroy_domains()`、`build_sched_domains()` 各一次 `__dl_server_attach_root()`，加上 `dl_clear_root_domain()` 里嵌套 O(N^2) 且关中断的循环）。

## 技术方案
**Patch 5/8（sched/topology，kernel/sched/sched.h + topology.c，+117/−75）**：
- 在 `struct sched_group_capacity` 上缓存 `group_weight/cores/asym_prefer_cpu`，`init_sched_groups_capacity()` 每个共享 group capacity 只算一次；`init_overlap_sched_group()` 复用已初始化的 sgc，不再重算 `build_balance_mask()` 与 `cpumask_weight(sg_span)`。
- `sdd->sg/sgc` 与 `d->sds` 改为按需惰性分配（原来 `__sdt_alloc()/__sds_alloc()` 为 cpu_map 里每个 CPU 在每个层级都预分配，绝大多数随即被 `__free_domain_allocs()` 释放）。

**Patch 6/8（sched/deadline, topology，kernel/sched/deadline.c 等，+89）**：
- 从 `rq_attach_root()` 移除冗余的 `__dl_server_attach_root()` 调用（`partition_sched_domains_locked()` 在 domain attach 完成后本就通过 `dl_rebuild_rd_accounting()` 重建记账）。
- 把 `dl_clear_root_domain()` 的嵌套 O(N^2) 循环替换为一次 O(N) 累加 + 一次 O(N) `extra_bw` 更新。
- 补上 `!CONFIG_CPUSETS` 下 `dl_rebuild_rd_accounting()` 的缺失实现（此前是 no-op stub，root_domain 重建完全没有 SCHED_DEADLINE 带宽记账，且 `rq_attach_root()` 里用不完整的 active CPU 数算出了不一致的 per-CPU extra_bw）。

封面信中 1–4/8 为 x86（移除 trampoline 的过时 WBINVD、跳过 mwait_play_dead 前的冗余 WBINVD、CMCI 重发现、MTRR rendezvous），7–8/8 为 mm/vmstat——不在本简报调度范围内。

## 版本演进与当前进展
v1 刚发出（封面 <20261015153331.1872641-1-pasha.tatashin@soleen.com>），尚无任何 review 意见。

## Maintainer 意见与讨论焦点
暂无维护者表态。潜在的争议点（作者在封面信自己标注）：1–3/8 对 AMD 无效（AMD 无大 L3 WBINVD 负担、acpi_idle 而非 mwait_play_dead、无 Intel CMCI）；以及移除 1990 年代遗留 WBINVD 这类 x86 改动需要 x86 维护者确认，调度侧 6/8 改动了 deadline 带宽记账的核心路径，需要 Juri Lelli 等 deadline 维护者 review。

## 合入评估
*likelihood=unknown*。系列刚发、无任何维护者回应；跨 x86/sched/mm 三个子系统，合入前需要多方 review 且可能被要求按子系统拆开。*blocking_issues*：暂无 review；跨子系统改动可能被要求拆分。*next_action*：等 x86/sched/deadline/mm 各维护者 review，确认 dl_server 记账重构与拓扑构建改动无回归。

## 效果评估
系列整体（封面信，10 次均值）：
- 2-socket 480 核 Intel Xeon 6985P-C（N=479）：Offline 40.40s→3.09s（−92.4%）、Online 65.83s→1.98s（−97.0%）、Total 106.23s→5.07s（−95.2%，21.0x）。
- 2-socket 512 核 AMD EPYC 9B45（N=511）：Offline 4.53s→2.30s、Online 3.88s→1.08s、Total 8.41s→3.38s（−59.8%，2.5x）。

调度侧单独（5/8 与 6/8 叠加）：
- Intel：5/8 使 build_sched_domains() 35.65ms→10.39ms（offline，−70.9%）；6/8 使 dl_clear_root_domain() 5,537µs→58.1µs（−99.0%）。
- AMD：6/8 使 dl_clear_root_domain() 1,880.5µs→27.5µs（−98.5%）。

数据均为作者自测，未见独立第三方验证。

## 我可以参与的点
- *review*：重点审视 6/8 对 deadline 带宽记账（`extra_bw`、`total_bw`）重构的正确性，以及 5/8 惰性分配与 sgc 缓存是否与 `sched_update_asym_prefer_cpu()` 等后续路径一致。
- *testing*：在非 x86 架构（如 arm64/riscv）上验证热插拔路径无回归；以及在 CONFIG_CPUSETS=n 配置下验证 6/8 补上的 dl 记账实现。

## 参考链接
- 封面信（0/8）：https://lore.kernel.org/all/20261015153331.1872641-1-pasha.tatashin@soleen.com/
- 5/8 sched/topology：https://lore.kernel.org/all/20261015153331.1872641-6-pasha.tatashin@soleen.com/
- 6/8 sched/deadline, topology：https://lore.kernel.org/all/20261015153331.1872641-7-pasha.tatashin@soleen.com/

---
id: sched-20261015-002
date: 2026-10-15
subject: "x86, sched, mm: Speed up CPU hotplug on large systems"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261015153331.1872641-1-pasha.tatashin@soleen.com>"
lore_url: "https://lore.kernel.org/all/20261015153331.1872641-1-pasha.tatashin@soleen.com/"
authors: ["Pasha Tatashin"]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261015153331.1872641-1-pasha.tatashin@soleen.com>"
    date: 2026-10-15
    summary: "8 补丁系列消除大规模 x86 CPU 热插拔瓶颈；调度侧为 5/8（sgc 缓存 + 惰性分配）与 6/8（dl_server O(N^2)→O(N) 记账重构）"
    review_outcome: "暂无 review"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["跨 x86/sched/mm 三子系统，暂无任何 review"]
  next_action: "等 x86/sched/deadline/mm 维护者 review；可能需要按子系统拆分"
contribution_opportunities:
  - kind: review
    description: "审视 6/8 deadline 带宽记账重构与 5/8 惰性分配/sgc 缓存的正确性"
  - kind: testing
    description: "在非 x86 架构与 CONFIG_CPUSETS=n 配置下验证热插拔无回归"
generated_at: "2026-10-16T01:05:00"
source_email_count: 3
related_articles: []
tags: [topology, dl_server, deadline]
---