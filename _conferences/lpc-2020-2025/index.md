---
title: "LPC 2020–2025 五年议题纵览（调度 / 内存 / 性能 / Android / 体系结构）"
conf: LPC
year: "2020-2025"
overview: true
direction: mixed
permalink: /conferences/lpc-2020-2025/
date: 2026-09-22
tags: [lpc]
tldr: "LPC 六届（2020–2025）全景：MC 生态变迁、五大方向跨年趋势，以及与调度/cpuset/cgroup 方向最相关的 12 条议题精选。各届明细见同目录年度总览。"
---

> 数据来源：lpc.events 官方议程（Indico，event/7、11、16、17、18、19），经 LWN.net 各年 LPC 报道交叉核验。各届明细见本文侧栏「LPC 各届总览」。

## 六届概览

| 年份 | 时间 / 地点 | 相关 MC |
|---|---|---|
| 2020 | 08-24~28，线上 | Scheduler、Real-Time、Android、PM & Thermal、RISC-V、linux/arch、VFIO/IOMMU/PCI、Net & BPF（无 MM 专场） |
| 2021 | 09-20~24，线上 | Scheduler、Real-time、Android、Tracing、Performance & Scalability、RISC-V、Confidential Computing、VFIO/IOMMU/PCI（无 MM、无独立 PM&Thermal） |
| 2022 | 09-12~14，都柏林 | Real-time and Scheduling、**CPU Isolation（新）**、**Kernel Memory Management（新）**、**CXL（新）**、Android、PM & Thermal、RISC-V、linux/arch |
| 2023 | 11-13~15，里士满 | Real-time and Scheduling、Android、PM & Thermal、CXL、RISC-V、Tracing、VFIO/IOMMU/PCI（无 MM 专场） |
| 2024 | 09-18~20，维也纳 | Sched、**Sched-Ext（新）**、Real-time、Kernel MM、Android、PM & Thermal、**x86（新）**、RISC-V、CXL、Tracing/Perf |
| 2025 | 12-11~13，东京 | Scheduler & Real-time、sched_ext、Kernel MM、**Device & Specific Purpose Memory（新）**、Android、Power & Thermal、RISC-V、x86、**Observability（新）**、Devicetree（新） |

MC 生态观察：

- **调度线**：Scheduler 与 RT 分立（2020–21）→ 合并为 Real-time and Scheduling（2022–23）→ 三分 Sched / Sched-Ext / Real-time（2024）→ 二分 + sched_ext 独立（2025）。CPU Isolation 于 2022 独立成 MC，之后并回调度/RT 议题。
- **内存线**：MM MC 2022 首设，2023 缺位（系统性讨论移至 LSFMM+BPF），2024/2025 回归，2025 又拆出 Device & Specific Purpose Memory MC。
- **性能线**：eBPF & Networking 每年最大 track；Tracing MC 时有时无；2025 新设 Observability MC。
- **Android/PM**：Android MC 每年常设；PM & Thermal 2021 一度并入 Android MC，2022 起恢复，2024–25 处于结构性重构期（另有独立 OSPM workshop 承接深入专题）。
- **体系结构线**：RISC-V 常设；Confidential Computing 2021 设立；CXL 2022 设立；x86 2024 设立；Devicetree 2025 设立。

## 五年趋势

### 调度

1. **可编程调度是最大主线**：ghOSt（2021）→ SCX/ghOSt BoF（2022）→ sched_ext 随 6.12 合入（2024）→ Meta AI 训练集群、Google CCX 生产部署（2025）。EEVDF（6.6）+ sched_ext（6.12）构成新基线。
2. **PREEMPT_RT 二十年收官**：2020 预期「5.10 见」→ 2023 "end game" → 2024 官宣 6.12 全量合入 → 2025 转入维护与运行时验证。
3. **混合架构与 chiplet 拓扑**：EAS 上 x86（2022）、split-LLC（2022）、cache-aware/CCX（2025）。
4. **CPU isolation 从边缘到主线**：2022 独立成 MC；核心是 IPI/噪声治理，配置面明确向 cpuset 收敛（2022 tuning through cpuset → 2023 cpuset v2 盘点 → 2025 IPI interference）。
5. **proxy execution 五年长线**：2020 亮相 → 2023/2024 拆分与「祛魅」 → 2025 与 sched_ext 的融合之问。
6. **per-task QoS 接口之争未收敛**：latency-nice（2020）→ Scheduler QOS API（2022）→ EQOS（2023）→ Sched QoS（2025）。
7. **均衡模型被重新审视**：idle CPU 选择（2021）→ EAS 唤醒路径不足（2024）→ push-based balancing（2025）。

### 内存

1. **folio 从争论到解耦**：2021 大争论 → 2023–24 默认基建 → 2025 Decoupling Large Folios from THP；mTHP 是 2024 年度词（OPPO 量产）。
2. **LRU/回收革新**：MGLRU 2022 冲刺 → 2024 生产化+NUMA 扩展；KSM、DAMON 常青（DAMON 2025 扩展到异构 {C,G,X}PU NUMA 迁移）。
3. **cgroup 内存语义持续演进**：objcg（2020）→ memcg v2 进 Android 15（2024）→ 僵尸 memcg 修复、per-cgroup swap 控制（2025）。
4. **内存分层是 MM 与体系结构的交汇点**：tiered memory（2021）→ CXL MC（2022–）→ DCD/共享内存（2023–24）→ HBM for AI + 页热度统一（2025）。
5. **扩展性成果落地**：maple tree、per-VMA lock（2021–22）上游后，2025 转向 mm_struct 生命周期、anon_vma 等存量结构重构。
6. **LPC 与 LSFMM 分工**：MM MC 时设时废，系统性回收/THP 讨论部分依赖 LSFMM+BPF；16KB page 由 Android MC 长期承载。

### 性能

1. **BPF 常青最大 track**：从「能力扩张」（2020–22）转向「安全可信」——verifier 形式化、fuzzing、签名、ISA 标准化（2022–25）。
2. **验证器本身成为研究对象**：proof-carrying（2021）→ range analysis 验证（2023）→ buzzer/Agni（2024）→ visualizer/state pruning（2025）。
3. **观测平台化**：Meta/Google 生产级实践、continuous profiler、AI flame graph（2025）；2025 新设 Observability MC。
4. **perf/ftrace 体系大修**：function args、BTF 参数打印、perf 子系统 15 年重构、紧凑调试格式。
5. **性能工程进入构建链**：PGO（2020）→ BOLT/AutoFDO/Propeller（2024）。
6. **与调度/内存交叉**：BPF 调度（2021–25）、可编程 MM（2024）、memcg stats 观测（2025）。

### Android / 手机

1. **与主线加速融合**：GKI（2020–21）→ Pixel 6 上游（2023）→ 设备长寿（2024–25）；vendor hooks 退场是明确方向。
2. **EAS 生态在内核与产品间迭代**：uclamp 产品化负反馈（2021）→ 与上游对齐（2023）→ EM 按热态动态更新（2025）。
3. **16KB page 贯穿 2023–2025**：起步（2023）→ 设备适配+内存代价（2024）→ ELF/软硬设计（2025）。
4. **内存技术下放**：MGLRU 验证（2022）→ mTHP 量产（2024，OPPO）。
5. **虚拟化三步走**：pKVM 设想（2020）→ Android 13 虚拟化 API（2022）→ AVF/Gunyah/trusted VM（2023–25）。
6. **中国厂商话语权上升**：OPPO（mTHP 量产）、Tencent（mTHP swap、内核网络观测）、ByteDance（调度）。

### 体系结构

1. **CXL 五年走完「愿景→子系统→深水区」**：单场（2021）→ MC 设立（2022）→ DCD/共享内存（2023–24）→ HBM/页热度统一（2025）；华为（Cameron、Jose）在 CXL 议程持续高频出现。
2. **机密计算从新 MC（2021）到常态化**：TDX/SEV/s390 → pKVM → ASI（2024 推进、2025 "ready"）。
3. **RISC-V 上游化主线**：服务器化（2020–23）→ 规范收敛争议（2024）→ RVA23 与 RV32/RV64 分家（2025）。
4. **x86 从无专门场到独立 MC（2024）**：侧信道缓解收敛与 FRED/APX/新 CPUID API。
5. **固件/启动链持续统一**：UEFI Capsule、LinuxBoot、GBL、UKI、DRTM on Arm、kexec live-update。
6. **IOMMU/VFIO 收敛为 iommufd 统一框架**。

## 与调度/cpuset/cgroup 方向最相关的 12 条

1. **CPU isolation tuning through cpuset**（2022，Weisbecker）+ **CPU Isolation state of the art**（2023）+ **CPU Isolation and IPI interference**（2025，Schneider）——隔离配置面向 cpuset 收敛的完整脉络。
2. **Mempolicy is dead, long live memory policy!**（2025，Price/Meta）——mempolicy 与 cpuset 交互重构。
3. **Taming Zombie Cgroups**（2025，Oracle）——memcg 卸载后页滞留。
4. **Per-cgroup Swap Device Control**（2025，Google/LG）。
5. **Uclamp cgroup usage challenges in Android**（2021）→ **uclamp in CFS**（2023）——uclamp/cgroup CPU 接口的产品反馈与上游对齐全过程。
6. **Remote charging in the CPU controller**（2021，Jordan）——kthread 代劳工作的 cgroup CPU 记账语义。
7. **sched_ext 系列**（2024 MC 全场 + 2025 生产化：Meta AI 集群、Google CCX）——EEVDF 之后调度器演进主战场。
8. **The wakeup path is not enough anymore for EAS**（2024，Guittot）+ **Push based load-balancing**（2025，Nayak/Guittot）——EAS 与负载均衡模型新方向。
9. **Rethinking Android's Priority Inheritance**（2025，Llamas）——binder PI，RT+cgroup 语义交汇。
10. **Graphing tools for scheduler tracing**（2023，Lawall/Inria）。
11. **Paravirt Scheduling**（2024–25）——vCPU capacity/steal time 语义。
12. **PREEMPT_RT 收官与维护**（2024–25，Siewior）——RT 合入后的生态。

## LPC 2026 展望

- 2026-10-05~07，布拉格 Prague Congress Centre，混合模式；CFP 已开放。
- 按 2024–25 走势可预期：sched_ext 生产案例继续扩容、调度器新接口（Sched QoS / push balancing）落地进展、CXL/HBM 内存分层与 AI 负载、RISC-V RVA23、16KB page 收尾。

> 官方议程：[2020](https://lpc.events/event/7/) · [2021](https://lpc.events/event/11/) · [2022](https://lpc.events/event/16/) · [2023](https://lpc.events/event/17/) · [2024](https://lpc.events/event/18/) · [2025](https://lpc.events/event/19/) · [2026](https://lpc.events/event/20/) · [LWN 会议索引](https://lwn.net/Archives/ConferenceIndex/)
