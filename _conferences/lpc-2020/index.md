---
title: "LPC 2020 议题总览（调度 / 内存 / 性能 / Android / 体系结构）"
conf: LPC
year: "2020"
overview: true
direction: mixed
permalink: /conferences/lpc-2020/
date: 2026-09-22
tags: [lpc]
tldr: "LPC 2020（线上）五大方向：core scheduling 上游冲刺、PREEMPT_RT 入主线前夜、DAMON 首秀、Android GKI 与 pKVM 首次公开、RISC-V 向量支持。"
---

> 2020-08-24~28 · 纯线上举办（因疫情，免费直播），吸收被取消的 GNU Tools Cauldron。
> 相关 MC：Scheduler、Real-Time、Android、PM & Thermal、RISC-V、linux/arch、VFIO/IOMMU/PCI、Networking & BPF Summit（当年无 MM 专场）。

## 调度

- **Core Scheduling feature Upstreaming Plans** — Desfossez/Pillai/Fernandes (DigitalOcean)：core scheduling v6 合入前收尾（最终随 5.14 上游）。
- **The Thing that was Latency Nice** — Bellasi/Hyser/Shah 等：latency-nice 与多个同类 per-task 参数能否统一成一个接口（uclamp 之外的旋钮之争）。
- **Looking forward on proxy execution** — Schneider (Arm)：proxy execution 首次系统亮相 LPC。
- **CFS flat runqueue v2** — Riel (Facebook)：扁平化 cgroup CFS 层级 runqueue。
- **scheduler fairness** — Guittot (Linaro)：系统不可完全均衡时（8 CPU 跑 9 任务）的公平性。
- **NUMA topology limitations** — Schneider (Arm)。
- Real-Time MC：**PREEMPT_RT status and Q&A** — Gleixner（当时预期随 5.10 入主线，实际全量合入发生在 2024/6.12）；**futex2 新接口** — Almeida (Collabora)；RT-stable 维护、CI-RT、OS noise 定位 — Williams/Lelli (Red Hat)；RT 调度延迟定理与测量工具 — Bristot (Red Hat, Refereed)。

## 内存（无 MM 专场，散布）

- **DAMON: Data Access Monitoring Framework** — Park (Amazon, Kernel Summit)：DAMON 首秀。
- **Recent changes in the kernel memory accounting** — Gushchin (Facebook, Refereed)：memcg 记账改 objcg，内核内存占用约 -40%。
- **Restricted kernel address spaces** — Rapoport (IBM)；**Kernel Address Space Isolation** — Chartre (Oracle)。
- **Memory management bits in arch/** — Rapoport：DISCONTIGMEM→SPARSEMEM 退役。

## 性能

- BPF & Net Summit（19 题）：**BPF LSM** — Singh (Google)；**BPF JIT 形式化验证** — Nelson (UW)；**单接口多 XDP** — Høiland-Jørgensen；**tail call 开销实测** — Cloudflare；**可动态扩缩 BPF map** — Fastabend (Isovalent)。
- **Exploring PGO of the Linux Kernel** — Bearman (Microsoft)；**LTO, PGO, and AutoFDO** — Tolvanen 等 (Google)。
- **Data-race detection (KCSAN)** — Elver (Google, Refereed)。

## Android / 手机

- **GKI 复盘与 GKI 2.0（Android S）规划** — Kjos/Stultz 等；**GKI KMI/ABI 监控** — Männich (Google)。
- **Protected KVM: Memory protection of KVM guests in Android** — Perret (Google)：pKVM 首次公开。
- **State of Android on Mainline Kernels** — Semwal/Tangirala；**ION→DMA-BUF heaps** — Stultz (Linaro)；**Incremental FS** — Lawrence；**Android Automotive 虚拟化 (trout)** — Granata/Delva (Google)。
- PM & Thermal MC：**Energy Model 扩展到 GPU/Devfreq** — Luba（EAS 基础设施外延）；**CPU/GPU 共享功耗预算** — Wysocki/Jerez (Intel)；**低温「加热」设备** — Gopinath/Lezcano。

## 体系结构

- RISC-V MC：**RVV 向量支持** — Hu/Chen (SiFive)；**hypervisor 扩展与 KVM** — Patel (WD)；**EBBR/UEFI 兼容** — Patra；**RISC-V tracing** — Guo Ren。
- linux/arch MC：**跨架构统一 vDSO** — Frascino；**syscall/trap 入出口通用化** — Gleixner；**4G/4G 替代 highmem（32 位）** — Walleij/Bergmann。
- VFIO/IOMMU/PCI：**guest SVA**、**Intel Scalable IOV**、**PCI movable BAR**。
- **Morello/CHERI 能力架构 ABI** — Brodsky (Arm, Refereed)。

## 当年亮点

- 疫情首次全程线上，吸收被取消的 GNU Tools Cauldron 形成 GNU Tools track。
- 最大主线是 PREEMPT_RT 的「最后一公里」：讨论焦点从能否合入转向合入之后（stable 维护、CI-RT、安全认证）。
- core scheduling 进入上游冲刺；latency-nice、proxy execution、CFS 扁平 runqueue 同场交锋。
- 内存方向无 MM 专场，DAMON 与 memcg objcg 重构（内核内存约 -40%）借 Kernel Summit/Refereed 登场。
- Android MC 以 GKI 为主线并首次公开 pKVM 设想。

> 数据来源：[lpc.events/event/7](https://lpc.events/event/7/)（官方 Indico 议程），经 LWN 报道交叉核验。
