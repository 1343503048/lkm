---
title: "LPC 2021 议题总览（调度 / 内存 / 性能 / Android / 体系结构）"
conf: LPC
year: "2021"
overview: true
direction: mixed
permalink: /conferences/lpc-2021/
date: 2026-09-22
tags: [lpc]
tldr: "LPC 2021（线上）五大方向：唤醒路径与 EAS 微调、folio 之争、uclamp 产品化负反馈、ghOSt、机密计算 MC 设立与 CXL 首秀。"
---

> 2021-09-20~24 · 纯线上举办。
> 相关 MC：Scheduler、Real-time、Android、Tracing、Performance & Scalability、RISC-V、Confidential Computing、VFIO/IOMMU/PCI、BPF & Net Summit（当年无 MM、无独立 PM&Thermal 专场）。

## 调度

- **Challenge of selecting an idle CPU** — Song/Li/Dronamraju/Guittot：唤醒路径 idle CPU 选择多方案。
- **New challenges in using LLC sched domain on wakeup path** — Chen (Oracle)：AMD/ARM 服务器 LLC 调度域。
- **Overeager pulling from wake_wide() in interrupt heavy workloads** — Chen (Oracle)。
- **Improving responsiveness of interactive CFS tasks using util_est** — Donnefort (Arm)。
- **Per-task I/O boost tracking** — Michalska/Eggemann (Arm)。
- ★ **Remote charging in the CPU controller** — Jordan (Oracle)：kthread 代用户组完成的工作记账进 cgroup CPU 控制器。
- **Use of eBPF in cpu scheduler** — Luo/Rhoden (Google)：ghOSt，eBPF 驱动调度策略。
- Real-Time MC：**printk 重构（kthread+原子控制台）收官** — Ogness (Linutronix)；**rtla（osnoise/timerlat）** — Bristot (Red Hat)；RT 维护模式化 — Siewior (Linutronix)。

## 内存（无 MM 专场，散布）

- **Efficient buffered I/O** — Wilcox (Oracle, FS MC)：folio 之争主战场（LWN: [A discussion on folios](https://lwn.net/Articles/869942/)）。
- **Design discussion and performance characteristics of Maple Tree** — Howlett (Oracle)。
- **Optimize Page Placement in Tiered Memory System** — Ying Huang 等：HBM/PMEM/CXL 分层。
- **Overview of memory reclaim in the current upstream kernel** — Babka (SUSE, Refereed)。
- **systemd-oomd: PSI-based OOM kills** — Zhang (Refereed)。
- Kernel Summit：**DAMON/DAMOS 实战** — Park；**物理内存表示统一** — Rapoport (IBM)。
- BoF：**VMA life cycle and MM locking** — Howlett；**Direct map management** — Rapoport/Babka。

## 性能

- Tracing MC 重启：**用户态 trace_event/dyn_event** — Belgrave (Microsoft)；**LTTng 上游化** — Desnoyers (EfficiOS)；**Function tracing with arguments** — Rostedt/Olsa；**统一 return caller 基础设施** — Rostedt。
- BPF：**BPF Memory Model** — McKenney (Facebook)；**proof-carrying verifier** — Nelson (UW)；**BPF map 热更新** — Burton (Google)。
- **Adding features to perf using BPF** — Melo/Kim (Red Hat, Refereed)。
- **Compact NUMA-aware Locks** — Kogan/Dice (Oracle, Perf&Scal MC)。

## Android / 手机

- ★ **Uclamp cgroup usage challenges in Android** — Wang/Perret (Google)：产品化负反馈——uclamp.max 被共调度任务整体抬走、跨过 EAS 过利用阈值导致耗电。
- **Thermal core usage challenges in Android** — Wang (Google)：thermal core 与各厂商 DVFS 整合难。
- **Speculative page faults 上游重启** — Lespinasse (Facebook)/Dufour。
- **Android drivers in Rust（Binder 重写样例）** — Almeida Filho/Ojeda。
- **FS stacking with FUSE 性能** — Balsini/Lawrence (Google)；**dm-snapshot in userspace** — Akilesh/Anderson。
- **GKI update** — Kjos (Google)。

## 体系结构

- Confidential Computing MC 设立：**TDX guest** — Kleen 等 (Intel)；**AMD SEV 热迁移** — Kalra；**s390 Secure Execution** — Naucke (IBM)；**远程证明与密钥注入** — Cadden/Bottomley (IBM)。
- RISC-V：**平台规范** — Patra (WD) 等；**ACPI for RISC-V** — Sunil V L；**AIA/ACLINT 新中断架构** — Patel (WD)；**全志 D1 上游化** — Guo Ren 等。
- **Compute Express Link + Linux + QEMU = Yes** — Widawsky (Refereed)：CXL 首秀。
- **User Interrupts** — Mehta (Intel, Kernel Summit)；**PBHA on arm64** — Deacon (Arm)。
- VFIO/IOMMU：**DOE/CMA/SPDM** — Cameron (Huawei)；**统一 I/O 页表管理** — Tian/Lu (Intel)。

## 当年亮点

- 结构性变化：Memory Management 与 mobile 功耗热控都没有独立 MC，MM 内容散布于 Perf&Scal、File Systems（folio 之争）、Kernel Summit 与 BoF，移动功耗并入 Android MC。
- 调度焦点是唤醒路径选核、LLC 调度域与 cgroup CPU 控制器记账，并首次系统收集到 uclamp 在 Android 产品化中的负反馈。
- Real-time MC 主旋律已是 PREEMPT_RT 合入主线后的维护模式。
- 体系结构由机密计算（TDX/SEV/s390）、RISC-V 平台规范/ACPI/AIA、CXL 与 User Interrupts 主导；Rust for Linux 横跨多个会场。

> 数据来源：[lpc.events/event/11](https://lpc.events/event/11/)（官方 Indico 议程），经 LWN 报道交叉核验。
