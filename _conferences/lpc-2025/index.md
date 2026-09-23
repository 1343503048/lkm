---
title: "LPC 2025 议题总览（调度 / 内存 / 性能 / Android / 体系结构）"
conf: LPC
year: "2025"
overview: true
direction: mixed
permalink: /conferences/lpc-2025/
date: 2026-09-22
tags: [lpc]
tldr: "LPC 2025（东京，12 月）五大方向：sched_ext 生产化（Meta AI 集群）、mempolicy 重构与僵尸 memcg、Observability MC 新设、Android 16KB 全面押注、RISC-V RVA23 与分家。"
---

> 2025-12-11~13 · 日本东京 Toranomon Hills Forum（首次落地日本，与 Kernel Summit Japan 12/07~09、Maintainers Summit 12/10 同周）。
> 相关 MC：Scheduler & Real-time、sched_ext、Kernel MM、**Device & Specific Purpose Memory（新）**、Android、Power & Thermal、RISC-V、x86、eBPF、**System Monitoring & Observability（新）**、Devicetree（新）。

## 调度

- sched_ext MC（11 题，Meta 主场）：**Accelerating AI training fleets with sched_ext** — Lu 等 (Meta)：AI 训练集群首批大规模部署；**Taming the Chiplet: High Performance CCX scheduling via BPF** — Gattani/Don (Google)；**Automated Workload-Aware Scheduling with SCX** — Kumar (Meta)；**The Current Status and Future Direction of the LAVD Scheduler** — Min (Igalia)；**Can ProxyExec and sched_ext get along?** — Stultz (Google)；**scx_chaos 故意乱调度压测** — Hillion (Meta)。
- ★ **Push based load-balancing for fair tasks** — Nayak (AMD)：推送式均衡替代 idle/newidle balance 原型。
- ★ **Enabling Push call back in Fair class** — Guittot (Linaro)：fair class push 回调，EAS 直接受益。
- **Cache Aware Scheduling** — Chen/Chen (Intel)：按 LLC 域聚拢线程。
- ★ **CPU Isolation and IPI interference** — Schneider (Red Hat)：静态键更新、TLB 刷新等 IPI 破坏隔离。
- **Paravirt Scheduling: Framework for better physical CPU utilization** — Leoshkevich/Hegde。
- ★ **Rethinking Android's Priority Inheritance** — Llamas：重审 binder PI 设计。
- **Userspace Assisted Scheduling via Sched QoS** — Stultz/Yousef/Guittot 等 (Refereed)。
- **Steps Towards a Gaming-Optimized Scheduler** — Min (Igalia)（Gaming MC，LWN 专文）。
- **Adaptive futexes / Enforcing PI locks by default** — Rostedt/Yousef；**News from PREEMPT_RT** — Siewior（合入后维护态）；RT runtime verification — Monaco/Cao。

## 内存（Kernel MM MC 12 题 + Device & Specific Purpose Memory MC 新设）

- ★ **Taming Zombie Cgroups: Should Reparenting Be Simple or Smart?** — Yoo/Babulal (Oracle)：memcg 卸载后共享文件页滞留 LRU。
- ★ **Mempolicy is dead, long live memory policy!** — Price (Meta)：NUMA mempolicy 重构及与 cpuset 的交互。
- **Decoupling Large Folios from Transparent Huge Pages** — Raghav (Samsung)。
- **The Past, Present & Future of the Anonymous Reverse Mapping** — Stoakes (Oracle)：anon_vma 锁竞争。
- **The life cycle of the mm_struct** — Howlett (Oracle)。
- ★ **Per-cgroup Swap Device Control** — Li (Google)/Park (LG)。
- **Memory Allocation Profiling upcoming features** — Panda/Baghdasaryan (Google)；**type-based slab allocation: kmalloc_obj** — Cook (Google)。
- Device Memory MC：**DAMON-based Pages Migration for {C,G,X}PU NUMA nodes** — Park；**Parallel Paths to High-Bandwidth Memory for ML/AI** — Bhardwaj (AMD)；**Unifying sources of page hotness information** — Rao (AMD)；**CXL HDM-DB** — Bueso (Samsung)。
- **Highmem deprecation planning** — Bergmann (Linaro, Kernel Summit)（LWN 专文）。

## 性能

- **AI flame graphs with eBPF** — Gregg/Olson (Intel)；**Advanced BPF profiling techniques** — Nakryiko (Meta)。
- **BPF Verifier Visualizer** — Solodrai (Meta)；**State Pruning 优化** — Tardy/Chaignon（各配 LWN 专文）；**Fuzzing the Verifier with a Test Oracle** — Chaignon。
- **Extending eBPF to GPU** — Zheng 等；**eBPF Load-Acquire/Store-Release（arm64 弱内存序）** — Ye (Google)。
- Observability MC（新设）：**Scaling Kernel Production Monitoring @ Meta** — Poenaru；**Reading memcg stats more efficiently** — Kobryn (Meta)；**bpftrace→ToolBox**；**Actionable DAMON Output** — Park；**Improving page_owner** — Oliveira (Igalia)。
- **Perf tools updates** — Kim (Google)；**Linux Tracing updates** — Hiramatsu (Google)；**Compact Debuginfo** — Brennan (Oracle)（LWN 专文）。

## Android / 手机

- 16KB 全面押注：**The Challenge of Loading 4kB-Aligned ELFs on 16kB Systems**、**Memory optimizations for 16kb kernel / HW/SW design recommendations** — Yescas/Singh (Google)。
- **BPF Based Telemetry, Metrics, and Accounting on Android** — Mercier (Google)。
- **A Linux VM on Android via AVF** — Cha (Google)；**Ramdump for Trusted VMs（pVM 调试）** — Zhang。
- **Pixel 6 support upstream** — McVicker (Google)；**AOSP on taped-out RISC-V SoC** — Tsai (Andes)。
- **Cooperation between CPU and system level cache by using MPAM** — Huang。
- Power & Thermal 移动相关：★ **Updating Energy Model from Thermal** — Luba：按发热/漏电动态更新 EAS 能耗模型；**Thermal framework issues and limitations** — Lezcano (Linaro)；**flash 存储低功耗态选择（UFS/eMMC/NVMe）** — Hansson (Linaro)。

## 体系结构

- RISC-V：**Preparing RISC-V Linux for RVA23** — Jenkins (Rivos)；**Schism: Splitting RV32 from arch/riscv** — Tsai (Andes)/Shu (SiFive)；**RISC-V QoS: CBQRI, RQSC and resctrl** — Fustini (Tenstorrent)；**Finer-grained CFI** — Gupta；**pre-silicon upstream first** — Liang (DeepComputing)。
- x86：**Address Space Isolation is ready** — Jackman (Google)；**Dynamic mitigations（运行时 sysfs 重选）** — Kaplan (AMD)；**APX 新通用寄存器** — Bae (Intel)；**新内核 CPUID API** — Darwish (Linutronix)。
- Devicetree MC 新设：**EFI 版 DT 加载、DT metadata** — Tsai 等 (Google)。
- **iommu page table consolidation / iommufd** — Gunthorpe (NVIDIA)；**Turning PCIe Hints into Cache Hits** — Huang。
- **Oak stage0 极简 VM 固件** (Google/Meta)；**Android Boot: Next Steps（GBL/FIT/UKI）** — Merkurev (Google)。

## 当年亮点

- 首次移师日本东京，与 Maintainers Summit 同周举办。
- 调度方向最热：sched_ext 独立 MC，Meta 报告 AI 训练集群与机群默认调度器的生产级部署，配合 Intel 缓存感知调度、push-based 均衡与 Sched QoS，预示 EEVDF 之后的新一轮演进。
- 内存主线是僵尸 memcg、mempolicy 重构（直接关系 cpuset/cgroup 语义）与大 folio/THP 解耦；CXL 已讨论到 3.0 HDM-DB 与页热度信息统一。
- eBPF Track 保持 25 题体量，验证器工具链与 AI flame graphs 成为新热点。
- Android 全面押注 16KB 页、BPF 遥测与 AVF 虚拟化；RISC-V 聚焦 RVA23 与 RV32/RV64 分家，x86 推进 ASI、APX 与动态缓解。

> 数据来源：[lpc.events/event/19](https://lpc.events/event/19/)（官方 Indico 议程），经 LWN 报道交叉核验。
