---
title: "LPC 2024 议题总览（调度 / 内存 / 性能 / Android / 体系结构）"
conf: LPC
year: "2024"
overview: true
direction: mixed
permalink: /conferences/lpc-2024/
date: 2026-09-22
tags: [lpc]
tldr: "LPC 2024（维也纳）五大方向：sched_ext 与 PREEMPT_RT 双双随 6.12 合入、mTHP 与 MGLRU 生产化、验证器工具链成熟、OPPO mTHP 量产、x86 MC 首设。"
---

> 2024-09-18~20 · 奥地利维也纳。
> 相关 MC：Sched、**Sched-Ext（新）**、Real-time、Kernel MM、Android、PM & Thermal、**x86（新）**、RISC-V、CXL、Tracing/Perf、eBPF。

## 调度

- Sched-Ext MC（8 题）：**The current status and future potential of sched_ext** — Vernet (Meta)（LWN: [Sched_ext at LPC 2024](https://lwn.net/Articles/991205/)）；**scx_rustland 用户态框架** — Righi (NVIDIA)；**SteamDeck 帧率优化（scx_lavd）** — Min (Igalia)；**Optimizing Google Search and beyond with pluggable scheduling** — Rhoden/Don (Google)；**发行版上船圆桌** — Gherdovich (SUSE) 等。
- ★ **The wakeup path is not enough anymore for EAS** — Guittot (Linaro)。
- **There's a blackhole in the scheduler** — Yousef (Google)：DVFS 时间膨胀恶化响应。
- **Priority Inheritance for CFS Bandwidth Control** — Xi Wang：带宽限流致优先级反转。
- **Improve scheduler debuggability** — Yousef (Google)。
- **Challenges in scheduling virtual CPUs** — Huschle (IBM/s390)。
- Real-Time MC：**Current overview of PREEMPT_RT** — Siewior（会期官宣 6.12 全量合入，二十年长跑收官）；**IPI deferral** — Schneider (Red Hat)；**Demystifying Proxy Execution** — Stultz (Google)；**DL servers for FIFO starvation avoidance** — Cascardo (Igalia)；**QPW 隔离并行策略** — Bras (Red Hat)。

## 内存（Kernel MM MC 回归，12 题）

- mTHP 三连：**mTHP and swap allocator** — Li (Google)/Song (Tencent)；★ **mTHP swap-out and swap-in** — Barry Song 等 (OPPO)；**TAO: THP Allocator Optimizations** — Yu Zhao (Google)。
- **Multi-Gen LRU updates** — Rasmussen 等 (Google)：生产落地、NUMA/CXL 页表扫描。
- **Memory Allocation Profiling deployment results** — Baghdasaryan/Tatashin (Google)。
- **Ongoing Challenges of Large Page Sizes** — Yescas/Singh (Google)：16KB 迁移持续问题。
- **Poison & remedy of vmas instead of guards** — Howlett/Stoakes (Oracle)；**Madvise lazy free** — Riel (Meta)。
- **Policy zones: memory partitioning for fun and profit** — Yu Zhao (Google)。
- 散见：**LUF (Lazy Unmap Flush)** — Byungchul Park (Refereed)；**Towards Programmable Memory Management with eBPF** (CMU, eBPF Track)。

## 性能

- 验证器工具链：**State of eBPF Fuzzing / Lessons from the Buzz (buzzer)** — Chaignon；**Agni 形式化验证 range analysis** — Chaignon。
- **Making Sense of tnum** — Yu (SUSE)；**bpftrace 现代化** — Xu (Meta)/Malik (Red Hat)。
- **Improving the Perf event subsystem after 15 years** — Rogers (Google)；**perf 数据类型剖析** — Kim (Google)。
- **Kernel func tracing in the face of compiler optimization** — Song (Meta)/Maguire (Oracle)。
- **BOLT 内核二进制优化** — Panchenko (Meta)；**AutoFDO + ThinLTO + Propeller** — Shen/Xu (Google)（LWN 专文×2）。
- **SIDE 统一用户态插桩规范** — Desnoyers (EfficiOS)；**Runtime Verification 展望** — Rostedt。

## Android / 手机

- ★ **Product practices of large folios on millions of OPPO Android phones** — Barry Song/Kalesh Singh/Yu Zhao：mTHP 国产量产实践。
- **memcg developments for Android** — Mercier (Google)：Android 15 侧启用 memcg v2。
- **Bringup devices with 16kb support** — Yescas/Singh (Google)；**Android Kernel Support for Device Longevity** — Kjos (Google)。
- **Android Generic Boot Loader (GBL)** — Merkurev/Muthiah (Google)；**ublk zero copy I/O** — Kailash。
- PM & Thermal 大重构：**thermal 子系统重构** — Wysocki (Intel)；**Userspace trip points、PID/timer governor、统一 Power/Thermal/Performance 接口** — Lezcano (Linaro)；**Wattson（trace 功耗评估）** — Wu/Kannan (Google)。

## 体系结构

- x86 MC 设立（8 题）：**State of CPU side-channel vulnerabilities and mitigations** — Gupta (Intel)；**Attack vector controls（简化十几项 cmdline）** — Kaplan (AMD)；**FRED 新进出机制** — Anvin/Li；**Address Space Isolation** — Jackman (Google)；**Future of Memory Protection Keys** — Hansen (Intel)。
- CXL MC：**DCD status** — Weiny/Singh (Intel)/Cameron (Huawei)；**Unification of RAS feature control - Enhancing EDAC** — Shiju Jose 等 (Huawei)；**Type-2 (CXL.cache)** — Lucero (AMD)；**Shared Memory 进展** — Groves (Micron)；**libcxlmi** — Bueso (Samsung)。
- RISC-V：**Unified Discovery 争议**（社区反对进内核）、**异构系统 ISA 扩展管理**、**atomic code patching/ftrace**。
- **Accelerating Linux Kernel Boot-Up for Large Multi-Core Systems（~1792 CPU）** — Sengar/Bhat (Microsoft)。
- **ACPI fast handover for kexec live-update** — Zheng (Refereed)。

## 当年亮点

- 最大事件是历经约 20 年的 PREEMPT_RT 在会期前后随 Linux 6.12 全量进入主线，Real-time MC 转向收尾与延迟质量（RCU in KVM、IPI deferral、DL server）。
- sched_ext 首设独立 MC 并同窗口合入 6.12：Google 百万级机器运行 scx_layered、scx_lavd 登陆 Steam Deck、CachyOS 等发行版积极跟进。
- MM 焦点从 folio 基建转向 mTHP（swap 双向化、防碎片）与 MGLRU 生产化，并与 Android 16KB 页、OPPO mTHP 量产在 Android MC 形成联动。
- 热管理子系统处于 Lezcano/Wysocki 主导的大重构期。
- CXL 进入 DCD、RAS/EDAC 统一、共享内存等深水区，x86 MC 聚焦侧信道缓解收敛与 FRED/ASI/XSAVE 等新特性落地。

> 数据来源：[lpc.events/event/18](https://lpc.events/event/18/)（官方 Indico 议程），经 LWN 报道交叉核验。
