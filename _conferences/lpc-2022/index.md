---
title: "LPC 2022 议题总览（调度 / 内存 / 性能 / Android / 体系结构）"
conf: LPC
year: "2022"
overview: true
direction: mixed
permalink: /conferences/lpc-2022/
date: 2026-09-22
tags: [lpc]
tldr: "LPC 2022（都柏林）五大方向：EAS 上 x86、CPU Isolation MC 新设与 cpuset 化、MM MC 设立与 MGLRU 冲刺、CXL MC 首设、SCX/ghOSt BoF 预热。"
---

> 2022-09-12~14 · 爱尔兰都柏林 Clayton Hotel Burlington Road。
> 相关 MC：Real-time and Scheduling、**CPU Isolation（新）**、**Kernel Memory Management（新）**、**CXL（新）**、Android、PM & Thermal、RISC-V、linux/arch、eBPF & Net。

## 调度

- **Bringing Energy-Aware Scheduling to x86** — Brown/Neri (Intel)：x86 混合架构启用 EAS 的难点（LWN: [Hybrid scheduling gets more complicated](https://lwn.net/Articles/909611/)）。
- **Linux Kernel Scheduling and split-LLC architectures** — Shenoy/Nayak (AMD)：chiplet/split-LLC。
- **Latency hints for CFS task** — Guittot (Linaro)。
- **Linux needs a Scheduler QOS API -- and it isn't nice(2)** — Brown (Intel)。
- **Limit the idle CPU search depth … during task wake up** — Chen Yu/Wu (ByteDance)。
- ★ **CPU isolation tuning through cpuset** — Weisbecker (SUSE)：用 cpuset 统一开关 nohz_full、RCU nocb 等隔离特性。
- ★ **CPU isolation vs jailbreaking IPIs** — Schneider (Red Hat)：IPI 路径未充分检查隔离 cpumask。
- **Execution Context Aware IPIs** — Saenz Julienne (Red Hat)；**Isolation aware smp_call_function/queue_work_on** — Tosatti (Red Hat)。
- **PREEMPT_RT Q&A** — Gleixner（合入前夕）；**rtla: what is next?** — Bristot (Red Hat)。
- BOF：**Pluggable scheduling: SCX and ghOSt** — Vernet (Meta)：sched_ext 定名前夜；另 eBPF Track 有 **eBPF Kernel Scheduling with Ghost** — Rhoden (Google)。

## 内存（Kernel MM MC 设立，7 题）

- **Multi-Gen LRU: Current Status & Next Steps** — Barnes/Lemarchand (Google)。
- **Scalability solutions for the mmap_lock - Maple Tree and per-VMA locks** — Howlett/Baghdasaryan/Lespinasse。
- **Copy On Write, Get User Pages, and Mysterious Counters** — Hildenbrand (Red Hat)。
- **The slab allocators of past, present, and future** — Babka (SUSE)：SLAB/SLOB 收敛到 SLUB。
- **Memory tiering** — Glisse (Google)；**Preserving guest memory across kexec** — Gowans (Amazon)；**Low-overhead memory allocation tracking** — Overstreet/Baghdasaryan。
- Kernel Summit：MGLRU、**Zettalinux** — Wilcox (Oracle)；DAMON BoF。

## 性能

- eBPF & Net（30 题）：**BPF 语言规范化** — Starovoitov (Meta)；**eBPF Standardization** — Thaler (Microsoft)；**BPF Signing + IMA** — Singh (Google)。
- **CO-RE 抗编译优化** — Maguire (Oracle)；**eBPF profiler for polyglot apps** — Thakkar/Honduvilla Coto。
- **Percpu hashtab traversal（200+ CPU）** — Vazquez (Google)；**Profiling data structures** — Melo (Red Hat)。
- **Runtime Verification: where are we?** — Bristot (Red Hat)。

## Android / 手机

- **MGLRU results on Android** — Singh (Google)。
- **Dynamic Energy Model to handle leakage power** — Luba：运行时 EM 应对漏电。
- **(Impact of) Recent CPU topology changes** — Eggemann/Voinescu (Arm)。
- **EROFS as a replacement for EXT4 and Squashfs** — Anderson (Google)；**eBPF-based FUSE** — Lawrence (Google)；**io_uring in Android** — Kailash。
- **Virtualization in Android（pKVM/Android 13 API）** — Brazdil (Google)。
- PM & Thermal MC：**频率不变性缺口** — Zhang；**Energy model accuracy** — Rasmussen (Arm)；**AMD P-State/CPPC** — Huang；**DTPM 并入温控框架** — Lezcano (Linaro)；**per-cpu idle injection** — Pandruvada (Intel)。

## 体系结构

- CXL MC 设立（8 题）：**CXL 3.0 DCD 动态容量内存** — Cameron (Huawei)/Singh (Intel)；**CXL hotplug 规范 vs 现实** — Waskiewicz；**QEMU 仿真路线** — Cameron (Huawei)；**CXL SSD autocaching** — Park (Samsung)；**错误上报通用化** — Richter/Ghannam (AMD)。
- RISC-V：**ACPI/UEFI 服务器化** — Sunil V L；**ftrace×抢占指令序列** — Chiu；**HWCAP 演化** — Tsai (SiFive)。
- **LoongArch: What we will do next** — Chen (Loongson)/Wang。
- **ASI（地址空间隔离）上游推进** — Shahid/Weisse (Google)（LWN: [A call to reconsider address-space isolation](https://lwn.net/Articles/909469/)）。
- **物理内存表示统一** — Rapoport (IBM)；**HIGHMEM API 现代化** — Weiny。

## 当年亮点

- 调度主线是混合架构 EAS 落地 x86（Intel）与 chiplet/split-LLC 调度（AMD），PREEMPT_RT 合入进入收官阶段。
- CPU Isolation 首次独立成 MC，聚焦 IPI 治理与「cpuset 化配置」。
- 内存侧 MGLRU 冲刺默认化并在 Android 得到验证，mmap_lock 扩展性（maple tree/per-VMA lock）与 CXL 内存分层成为新焦点。
- BPF Track 规模最大（30 题），核心争论是语言规范化、标准化与程序签名安全；可插拔调度以 SCX/ghOSt BoF 形式预热。
- CXL MC 首设（3.0 DCD、QEMU 仿真、错误上报），RISC-V 主攻 ACPI/UEFI 服务器化，LoongArch 进入 arch MC 议程。

> 数据来源：[lpc.events/event/16](https://lpc.events/event/16/)（官方 Indico 议程），经 LWN 报道交叉核验。
