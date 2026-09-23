---
title: "LPC 2023 议题总览（调度 / 内存 / 性能 / Android / 体系结构）"
conf: LPC
year: "2023"
overview: true
direction: mixed
permalink: /conferences/lpc-2023/
date: 2026-09-22
tags: [lpc]
tldr: "LPC 2023（里士满）五大方向：CPU isolation 深化与 RT end game、MM MC 缺位（分流 KSM/DAMON/16KB page）、验证器可验证化、Pixel 6 上游与去 vendor hooks、CXL 深水区。"
---

> 2023-11-13~15 · 美国弗吉尼亚州里士满。
> 相关 MC：Real-time and Scheduling、Android、PM & Thermal、CXL、RISC-V、Tracing、VFIO/IOMMU/PCI、eBPF & Net（当年无 MM 专场，系统性 MM 讨论移至 LSFMM+BPF）。

## 调度

- **Welcome message and DL Server** — Bristot (Red Hat)：用 SCHED_DEADLINE「server」防 CFS 被 SCHED_FIFO 饿死。
- ★ **CPU Isolation state of the art** — Weisbecker (SUSE)：年度盘点（vmstat、IPI 延迟、cpuset v2、osnoise）。
- **Improving CPU Isolation with per-cpu spinlocks** — Bras (Red Hat)。
- **system pressure on CPUs capacity and feedback to scheduler** — Guittot (Linaro)。
- **Do nothing fast: How to scale idle cpus?** — Desnoyers (EfficiOS)：192 核 EPYC idle 循环扩展性。
- **How to reduce complexity in Proxy Execution** — Stultz (Google)：拆成可渐进上游的小补丁（LWN 专文）。
- **Adaptive userspace spinlocks with rseq** — Almeida (Igalia)/Desnoyers (EfficiOS)。
- **Optimizing Chromium Low-Power Workloads on Intel Notebooks** — Brown (Intel)：EQOS。
- PM MC 侧：**uclamp in CFS: Fairness, latency, and energy efficiency** — Eggemann/Rasmussen (Arm)。
- LWN: [The real realtime preemption end game](https://lwn.net/Articles/951337/)。

## 内存（无 MM 专场，分流 Kernel Summit / Android / CXL）

- **Kernel Samepage Merging (KSM) at Meta and Future Improvements** — Roesch (Meta)（LWN: [An overview of KSM](https://lwn.net/Articles/953141/)）。
- **DAMON: Current Status and Future Plans** — Park。
- **16KB Page Size Support** — Yescas/Singh (Google, Android MC)：起步。
- **Using hardware hints for optimal page placement** — Rao (AMD, Refereed)。

## 性能

- 验证器可验证化：**Verifier range analysis verification**；**bpftime 用户态 BPF 运行时** — Zheng (PLCT)；**xprobes 混合探针** — Castanheira (CMU)。
- ★ **Function parameters with BTF** — Hiramatsu/Rostedt：函数图跟踪打印参数。
- ★ **Performance Monitor Control Unit** — Zhan (Huawei)：鲲鹏 PMCU 硬件卸载 PMU 访问。
- **Developing Continuous eBPF Profiler** — Priyadarsini (Polar Signals)。
- ★ **Graphing tools for scheduler tracing** — Lawall (Inria)：调度 trace 图形化分析。
- **Linux perf tool metrics** — Rogers (Google, Refereed)。

## Android / 手机

- 主线化最强年：**Pixel 6 support on android-mainline** — Griffin (Linaro)/McVicker (Google)；**Can mainline Linux run on Android without vendor hooks?** — Yousef (Google)。
- **16KB Page Size Support** — Yescas/Singh (Google)。
- **A Rust implementation of Android's Binder** — Ryhl (Google)（LWN 专文：[A Rust implementation of Android's Binder](https://lwn.net/Articles/953116/)）。
- **Adding Third-Party Hypervisor (Gunyah) to Android Virtualization Framework** — Berman (Qualcomm)。
- PM & Thermal：★ **uclamp in CFS**（见调度节）；**New thermal trip types** — Lezcano (Linaro)；**DDR segments on demand** — Rajagopalan (Qualcomm)；**Intel Low Power Mode Daemon on Hybrid CPUs**；**Improving suspend/resume on Android** — Kannan (Google)。

## 体系结构

- CXL MC（7 题）：**CXL Memory Tiering** — Gummaluri；**Plumbing challenges in Dynamic capacity device** — Weiny/Cameron (Huawei)/Singh (Intel)；**Type-2 core support** — Weiny；**Shared CXL 3 memory** — Groves (Micron)；**move_pages() equivalent for physical memory** — Price (MemVerge)；**RAS for CXL ports** — Bowman (AMD)。
- RISC-V：**Control Flow Integrity** — Gupta；**Vector 现状** — Chiu；**ILP32 on RV64** — Guo Ren；**SBI events** — Léger (Rivos)；**irqbypass+KVM** — Jones (Ventana)。
- **iommufd** — Gunthorpe (NVIDIA)/Tian (Intel)。
- **Standardizing CPUID data for open-source x86** — Darwish (Linutronix, Refereed)。
- **resctrl filesystem BoF** — Newman (Google)。

## 当年亮点

- 首次未设 MM MC，内存议题分流到 Kernel Summit（KSM、DAMON）、Android（16KB 页）与 CXL MC；系统性 MM 讨论当年已移至 LSFMM+BPF。
- 调度主题是「隔离与实时」：CPU isolation 两场加 DL Server、proxy execution 拆分，PREEMPT_RT 被 LWN 称为进入 end game。
- Android 主线化是最强旋律——Pixel 6 上游、去 vendor hooks、DDK v2 与 Rust Binder。
- eBPF 走向成熟与标准化（exceptions、内存模型、ISA 一致性测试、用户态运行时 bpftime）。
- CXL MC 议题密度极高，tiering、动态容量与共享内存成为内存与体系结构的共同焦点。

> 数据来源：[lpc.events/event/17](https://lpc.events/event/17/)（官方 Indico 议程），经 LWN 报道交叉核验。
