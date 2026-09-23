---
title: "OSDI 2016–2026：OS 调度 / 性能 / 体系结构相关论文整理"
conf: OSDI
year: "2016-2026"
overview: true
direction: mixed
permalink: /conferences/osdi-2016-2026/
date: 2026-09-22
tags: [osdi]
tldr: "OSDI 2016–2026 共 9 届 541 篇论文中筛出的 262 篇调度/性能/体系结构相关论文整理：OS/内核级调度、集群级调度（数据中心/ML 系统）与体系结构三条主线。"
---


> 整理日期：2026-09-22。数据来源：USENIX 官网各届 Technical Sessions 页面（文末附链接），与公开报道交叉核对。
> 覆盖范围：OSDI 2016–2026 共 9 届（OSDI 自 2021 年起改为一年一届），总论文 541 篇，筛出三主题相关 262 篇。
> 分类说明：第一~三节为 OS/内核视角；第四节为集群级调度（数据中心/ML 系统），单列以便区分。★ = 该方向标杆/获奖论文。

## 总览

| 届次 | 论文总数 | 相关入选 | 地点 |
|---|---|---|---|
| OSDI '16 | 47 | 20 | Savannah |
| OSDI '18 | 47 | 19 | Carlsbad |
| OSDI '20 | 70 | 30 | 线上 |
| OSDI '21 | 31 | 15 | 线上（首届一年一届制） |
| OSDI '22 | 49 | 23 | Carlsbad |
| OSDI '23 | 55 | 24 | Boston |
| OSDI '24 | 53 | 32 | Santa Cruz |
| OSDI '25 | 53 | 29 | — |
| OSDI '26 | 136 | 70 | Seattle（大幅扩容） |

---

## 一、OS / 内核级调度

### OSDI '16
- [**Light-Weight Contexts: An OS Abstraction for Safety and Performance**](https://www.usenix.org/conference/osdi16/technical-sessions/presentation/litton) — James Litton（UMD/MPI-SWS）：跨隔离域的微秒级轻量上下文切换抽象。

### OSDI '18
- [**Arachne: Core-Aware Thread Management**](https://www.usenix.org/conference/osdi18/presentation/qin) — Henry Qin（Stanford）：用户态线程库，应用自管核数、微秒级调度，绕开内核调度器。
- [**Principled Schedulability Analysis for Distributed Storage Systems using Thread Architecture Models**](https://www.usenix.org/conference/osdi18/presentation/yang) — Suli Yang（UW–Madison/Ant）：用线程架构模型系统化分析存储系统的可调度性。
- [**µTune: Auto-Tuned Threading for OLDI Microservices**](https://www.usenix.org/conference/osdi18/presentation/sriraman) — Akshitha Sriraman（Michigan）：自动调优微服务线程/核配比，保毫秒级尾延迟。
- [**Adaptive Dynamic Checkpointing for Safe Efficient Intermittent Computing**](https://www.usenix.org/conference/osdi18/presentation/maeng) — Kiwan Maeng（CMU）：能量采集设备间歇计算的自适应检查点调度。

### OSDI '20
- [**Caladan: Mitigating Interference at Microsecond Timescales**](https://www.usenix.org/conference/osdi20/presentation/fried) — Joshua Fried（MIT）：微秒级核仲裁调度器，动态分配核消除共享资源干扰，免静态分区。★微秒级调度标杆
- [**RackSched: A Microsecond-Scale Scheduler for Rack-Scale Computers**](https://www.usenix.org/conference/osdi20/presentation/zhu) — Hang Zhu（JHU）：基于跨节点共享内存的机架级微秒级两级调度器。
- [**Overload Control for µs-scale RPCs with Breakwater**](https://www.usenix.org/conference/osdi20/presentation/cho) — Inho Cho（MIT）：微秒级 RPC 的自适应准入控制，过载时保尾延迟。
- [**Serving DNNs like Clockwork: Performance Predictability from the Bottom Up**](https://www.usenix.org/conference/osdi20/presentation/gujarati) — Arpan Gujarati（MPI-SWS）：自底向上时间感知调度，DNN 推理延迟可预测。
- [**Thunderbolt: Throughput-Optimized, QoS-Aware Power Capping at Scale**](https://www.usenix.org/conference/osdi20/presentation/li-shaohong) — Shaohong Li（Google）：QoS 感知的分布式功率封顶调度。
- [**Providing SLOs for Resource-Harvesting VMs in Cloud Platforms**](https://www.usenix.org/conference/osdi20/presentation/ambati) — Pradeep Ambati（MSR）：Azure 收割型（低优先级）VM 的弹性 SLO 供给，混部方向的代表工作。

### OSDI '21
- [**Optimizing Storage Performance with Calibrated Interrupts**](https://www.usenix.org/conference/osdi21/presentation/tai) — Amy Tai（VMware）：软硬协同校准中断合并策略，兼顾延迟与吞吐。
- [**Privacy Budget Scheduling**](https://www.usenix.org/conference/osdi21/presentation/luo) — Tao Luo（Columbia）：把差分隐私预算当稀缺资源统一调度（调度对象的扩展）。

### OSDI '22
- [**Immortal Threads: Multithreaded Event-driven Intermittent Computing**](https://www.usenix.org/conference/osdi22/presentation/yildiz) — Eren Yıldız（Ege）：间歇供电 MCU 上的多线程运行时与公平调度。
- [**Microsecond-scale Preemption for Concurrent GPU-accelerated DNN Inferences（REEF）**](https://www.usenix.org/conference/osdi22/presentation/han) — Mingcong Han（上交 IPADS）：微秒级 GPU kernel 抢占，实时任务可抢占尽力而为任务。

### OSDI '23
- [**Core slicing: closing the gap between leaky confidential VMs and bare-metal cloud**](https://www.usenix.org/conference/osdi23/presentation/zhou-ziqiao) — Ziqiao Zhou（MSR）：静态核划分消除机密 VM 侧信道并抹平性能差距——cpuset 式隔离思想用于机密计算。
- [**BWoS: Formally Verified Block-based Work Stealing**](https://www.usenix.org/conference/osdi23/presentation/wang-jiawei) — Jiawei Wang（Huawei Dresden/TU Dresden）：块式工作窃取，有界窃取开销，附形式化验证。

### OSDI '24
- [**Harvesting Memory-bound CPU Stall Cycles in Software with MSH**](https://www.usenix.org/conference/osdi24/presentation/luo) — Zhihong Luo（UC Berkeley）：微架构感知调度——软件收割内存阻塞的 stall 周期执行其他工作。
- [**Data-flow Availability: Achieving Timing Assurance in Autonomous Systems**](https://www.usenix.org/conference/osdi24/presentation/li) — Ao Li（WashU）：数据流可用性模型，自动驾驶类系统的端到端时序保障（实时调度视角）。

### OSDI '25
- [**XSched: Preemptive Scheduling for Diverse XPUs**](https://www.usenix.org/conference/osdi25/presentation/shen) — Weihang Shen（上交 IPADS）：可抢占命令队列抽象，CPU/GPU/NPU 等 XPU 统一抢占调度。
- [**Quantum Virtual Machines**](https://www.usenix.org/conference/osdi25/presentation/tao) — Runzhou Tao（Maryland）：量子计算机虚拟机——多路复用与隔离。
- [**QOS: Quantum Operating System**](https://www.usenix.org/conference/osdi25/presentation/giortamis) — Emmanouil Giortamis（TUM）：噪声与硬件异构感知的量子程序调度 OS。

### OSDI '26（Seattle）
- [**kSTEP: Characterization and Deterministic Testing of Linux CPU Scheduler Bugs**](https://www.usenix.org/conference/osdi26/presentation/cao) — Tingjia Cao（UW–Madison）：系统刻画 Linux CPU 调度器缺陷并做确定性测试——直接以主线调度器为研究对象。★
- [**What Are You (M)Waiting For: The Hidden Cost of Idle in the Hyperscale Cloud**](https://www.usenix.org/conference/osdi26/presentation/wang-yun) — Yun Wang（上交）：超售云中 mwait 直通的空闲代价与规模化治理。
- [**Xkernel: Principled Performance Tunability of Operating System Kernels**](https://www.usenix.org/conference/osdi26/presentation/chen-zhongjie) — Zhongjie Chen（清华/MSR）：内核性能相关常量（含调度参数）的在线、安全、可调。
- [**SBB: Eliminating Centralized Bottlenecks in Userspace Network Runtime**](https://www.usenix.org/conference/osdi26/presentation/hu-kang) — Kang Hu（北大）：去中心化实现请求抢占、CPU 分配与负载均衡。
- [**Rakaia: Scalable In-Kernel Scheduling for TCP-Based RPCs**](https://www.usenix.org/conference/osdi26/presentation/yang-rui) — Rui Yang（EPFL）：内核内 work-conserving 调度，消除 TCP RPC 队头阻塞。
- [**PeeR: First-Class Scheduling for Latency-Critical eBPF Applications**](https://www.usenix.org/conference/osdi26/presentation/carin) — Jeremy Carin（MIT）：延迟敏感 eBPF 程序可抢占、纳入调度器统一管理。★
- [**vBOIDs: Taming Chaos via Coarse-Grained Scheduling Abstraction for Containers**](https://www.usenix.org/conference/osdi26/presentation/manakkal) — Kaesi Manakkal（UT–Arlington）：BOID 粗粒度分组 + 两级负载均衡的容器调度抽象。
- [**Surviving the Impossible Trinity: Revisiting CPU Scheduling Problem on Modern COTS Mobile Devices**](https://www.usenix.org/conference/osdi26/presentation/xiao) — Jun Xiao（荣耀终端）：用户交互上下文感知的移动端 CPU 调度，权衡性能/功耗/流畅。★
- [**Unleash All Cores: Asymmetry-Aware Scalable DNN Inference on Mobile CPUs**](https://www.usenix.org/conference/osdi26/presentation/sang) — Qianlong Sang（武大）：大小核感知的移动端推理调度，防"塌陷"到大核争抢。
- [**Stop Pretending to Be Busy: A Case for Serverless Paradigms in Co-Located Batch Workloads**](https://www.usenix.org/conference/osdi26/presentation/chai) — Xiaohu Chai（清华/蚂蚁）：serverless 化混部批处理，榨空闲 CPU 同时保 SLO。
- [**LiteSwitch: Harvesting Sub-Microsecond CXL Memory Stalls**](https://www.usenix.org/conference/osdi26/presentation/li-nanqinqin) — Nanqinqin Li（Princeton）：软硬件协同收割亚微秒 CXL 访存停顿周期（MSH 思想的 CXL 版）。

---

## 二、性能

### 2.1 性能隔离 / QoS / 尾延迟 / 过载控制
- [**Kraken: Leveraging Live Traffic Tests to Identify and Resolve Resource Utilization Bottlenecks**](https://www.usenix.org/conference/osdi16/technical-sessions/presentation/veeraraghavan)（'16）— Kaushik Veeraraghavan（Facebook）：常态化注入真实流量定位资源瓶颈。
- [**RobinHood: Tail Latency Aware Caching**](https://www.usenix.org/conference/osdi18/presentation/berger)（'18）— Daniel Berger（CMU）：尾延迟感知的缓存资源动态"劫富济贫"。
- [**Splinter: Bare-Metal Extensions for Multi-Tenant Low-Latency Storage**](https://www.usenix.org/conference/osdi18/presentation/kulkarni)（'18）— Chinmay Kulkarni（Utah）：函数下推共享 KV，裸金属级多租户性能隔离。
- [**Taming Performance Variability**](https://www.usenix.org/conference/osdi18/presentation/maricq)（'18）— Aleksander Maricq（Utah）：大规模实测性能漂移模式，自动调参收敛。
- [**LinnOS: Predictability on Unpredictable Flash Storage with a Light Neural Network**](https://www.usenix.org/conference/osdi20/presentation/hao)（'20）— Mingzhe Hao（Chicago）：轻量 NN 逐 IO 预测 SSD 延迟。
- [**Metastable Failures in the Wild**](https://www.usenix.org/conference/osdi22/presentation/huang-lexiang)（'22）— Lexiang Huang（Penn State/Twitter）：实证云系统自持性过载故障的模式。
- [**XRP: In-Kernel Storage Functions with eBPF**](https://www.usenix.org/conference/osdi22/presentation/zhong)（'22）— Yuhong Zhong（Columbia）：eBPF 挂钩 NVMe 轮询路径在内核执行用户函数，削尾延迟。
- [**Svalinn: Overload Control in Large-Scale Servers with Multiple Resource Bottlenecks**](https://www.usenix.org/conference/osdi26/presentation/pardeshi)（'26）— Bhaskar Pardeshi（Georgia Tech）：多资源瓶颈下的过载控制，破"单队列谬误"。
- [**Shaving the Peaks: Taming Tail Latency for Managed Workloads via Disaggregated Garbage Collection**](https://www.usenix.org/conference/osdi26/presentation/lyu)（'26）— Hongtao Lyu（上交 IPADS）：共享资源池的分解式并发 GC 削平尾延迟。
- [**Sereno: Taming Memory Bandwidth Contention in Mobile LLM Inference**](https://www.usenix.org/conference/osdi26/presentation/xin)（'26）— Tong Xin（上交 IPADS）：移动端 LLM 推理与前台应用的内存带宽干扰治理。

### 2.2 内核可扩展性 / 同步 / 系统调用路径
- [**Machine-Aware Atomic Broadcast Trees for Multicores**](https://www.usenix.org/conference/osdi16/technical-sessions/presentation/kaestle)（'16）— Stefan Kaestle（ETH）：自动生成缓存/NUMA 感知的多核广播树。
- [**To Waffinity and Beyond: A Scalable Architecture for Incremental Parallelization of File System Code**](https://www.usenix.org/conference/osdi16/technical-sessions/presentation/curtis-maury)（'16）— Matthew Curtis-Maury（NetApp）：写亲和域增量并行化遗留文件系统代码。
- [**RedLeaf: Isolation and Communication in a Safe Operating System**](https://www.usenix.org/conference/osdi20/presentation/narayanan-vikram)（'20）— Vikram Narayanan（UC Irvine）：Rust 语言级隔离驱动 + 低开销通信/中断路径。
- [**NrOS: Effective Replication and Sharing in an Operating System**](https://www.usenix.org/conference/osdi21/presentation/bhardwaj)（'21）— Ankit Bhardwaj（Utah）：复制内核状态消除跨核共享，提升 OS 可扩展性。
- [**Occualizer: Optimistic Concurrent Search Trees From Sequential Code**](https://www.usenix.org/conference/osdi22/presentation/shanny)（'22）— Tomer Shanny（TAU）：为顺序搜索树自动注入乐观并发。
- [**KSplit: Automating Device Driver Isolation**](https://www.usenix.org/conference/osdi22/presentation/huang-yongzhe)（'22）— Yongzhe Huang（Penn State）：静态分析内核-驱动共享状态，自动化驱动隔离。
- [**Operating System Support for Safe and Efficient Auxiliary Execution**](https://www.usenix.org/conference/osdi22/presentation/jing)（'22）— Yuzhuo Jing（JHU）：OS 原语支撑应用内辅助任务，兼顾隔离与低开销。
- [**Application-Informed Kernel Synchronization Primitives（SynCord）**](https://www.usenix.org/conference/osdi22/presentation/park)（'22）— Sujin Park（Georgia Tech）：用户态定制内核锁策略，免重编译免重启。
- [**Ship your Critical Section, Not Your Data: TCLOCKS**](https://www.usenix.org/conference/osdi23/presentation/gupta)（'23）— Vishal Gupta（EPFL）：临界区"委托"到数据所在核执行，透明免改应用。
- [**RON: One-Way Circular Shortest Routing Spinlocks**](https://www.usenix.org/conference/osdi23/presentation/lo)（'23）— Shiwu Lo（中正大学）：单向环形最短路由自旋锁，高效且有界等待。
- [**Userspace Bypass: Accelerating Syscall-intensive Applications**](https://www.usenix.org/conference/osdi23/presentation/zhou-zhe)（'23）— Zhe Zhou（复旦）：SFI 将系统调用间的用户代码移入内核执行。
- [**Fast and Scalable In-network Lock Management Using Lock Fission**](https://www.usenix.org/conference/osdi24/presentation/zhang-hanze)（'24）— Hanze Zhang（上交 IPADS）：交换机侧锁分片管理，消除锁排队瓶颈。
- [**Disentangling the Dual Role of NIC Receive Rings**](https://www.usenix.org/conference/osdi25/presentation/pismenny)（'25）— Boris Pismenny（EPFL/NVIDIA）：解耦 NIC 接收环双重角色，缩小 per-CPU 缓存工作集。
- [**Arctic: A Practical Lock-Free Adaptive Radix Tree**](https://www.usenix.org/conference/osdi26/presentation/ni)（'26）— Newton Ni（UT Austin）：无锁自适应基数树 + 新的安全内存回收方案。
- [**Efficient and Scalable Synchronization via Generalized Cache Coherence**](https://www.usenix.org/conference/osdi26/presentation/yu-yanpeng)（'26）— Yanpeng Yu（Yale）：广义缓存一致性原语支撑分解式内存同步。
- [**DeLFS: A Decentralized Log-Structured File System for Manycores**](https://www.usenix.org/conference/osdi26/presentation/ahn)（'26）— Taehwan Ahn（韩国中央大学）：去中心化锁与元数据，消众核文件系统争用。

### 2.3 剖析 / 追踪 / 调试工具
- [**Non-Intrusive Performance Profiling for Entire Software Stacks**](https://www.usenix.org/conference/osdi16/technical-sessions/presentation/zhao)（'16）— Xu Zhao（Toronto）：流重构原理无侵入剖析全栈请求流。
- [**JetStream: Cluster-Scale Parallelization of Information Flow Queries**](https://www.usenix.org/conference/osdi16/technical-sessions/presentation/quinn)（'16）— Andi Quinn（Michigan）：集群并行执行 DIFT 信息流追踪。
- [**wPerf: Generic Off-CPU Analysis to Identify Bottleneck Waiting Events**](https://www.usenix.org/conference/osdi18/presentation/zhou)（'18）— Fang Zhou（OSU）：等待图 + 级联分摊定位 off-CPU 瓶颈。
- [**Differential Energy Profiling**](https://www.usenix.org/conference/osdi18/presentation/jindal)（'18）— Abhilash Jindal（Purdue）：差分相似应用能耗定位优化空间。
- [**DMon: Efficient Detection and Correction of Data Locality Problems Using Selective Profiling**](https://www.usenix.org/conference/osdi21/presentation/khan)（'21）— Tanvir Ahmed Khan（Michigan）：选择性剖析低开销定位 NUMA 局部性问题。
- [**Hubble: Performance Debugging with In-Production, Just-In-Time Method Tracing on Android**](https://www.usenix.org/conference/osdi22/presentation/luo)（'22）— Yu Luo（Toronto）：生产环境 Android 环形缓冲区 JIT 方法追踪。
- [**Triangulating Python Performance Issues with SCALENE**](https://www.usenix.org/conference/osdi23/presentation/berger)（'23）— Emery Berger（UMass）：低开销同时剖析 Python 的 CPU/内存/GPU。
- [**Relational Debugging — Pinpointing Root Causes of Performance Problems**](https://www.usenix.org/conference/osdi23/presentation/ren)（'23）— Jenny Ren（Toronto）：关联组件间性能症状自动定位根因。
- [**ServiceLab: Preventing Tiny Performance Regressions at Hyperscale**](https://www.usenix.org/conference/osdi24/presentation/chow)（'24）— Mike Chow（Meta）：预生产测试平台拦截微小性能回归。
- [**μSlope: High Compression and Fast Search on Semi-Structured Logs**](https://www.usenix.org/conference/osdi24/presentation/wang-rui)（'24）— Rui Wang（YScope）：半结构化日志高压缩比 + 快速检索。
- [**Identifying On-/Off-CPU Bottlenecks Together with Blocked Samples**](https://www.usenix.org/conference/osdi24/presentation/ahn)（'24）— Minwoo Ahn（成均馆大学）：阻塞样本统一剖析 on-/off-CPU 瓶颈。
- [**Tintin: A Unified Hardware Performance Profiling Infrastructure**](https://www.usenix.org/conference/osdi25/presentation/li)（'25）— Ao Li（WashU）：统一硬件计数器剖析，高保真测量与归因。
- [**KRR: Efficient and Scalable Kernel Record Replay**](https://www.usenix.org/conference/osdi25/presentation/zhang-tianren)（'25）— Tianren Zhang（SmartX）：高效可扩展的内核记录重放。
- [**Principles and Methodologies for Serial Performance Optimization**](https://www.usenix.org/conference/osdi25/presentation/park-sujin)（'25）— Sujin Park（Georgia Tech）：串行程序性能优化的系统化方法论。
- [**When Sampling Lies: Trustworthy Performance Profiling for Flat Workloads with Blink**](https://www.usenix.org/conference/osdi26/presentation/devsot)（'26）— Rishikesh Devsot（YScope）：扁平负载下可信剖析，纠正采样失真。
- [**StriaTrace: Efficient Tracing and Diagnosis for Online LLM Inference**](https://www.usenix.org/conference/osdi26/presentation/wu-haonan)（'26）— Haonan Wu（上交/阿里）：低开销在线 LLM 推理追踪与 SLO 异常归因。
- [**Diagnosing Performance Issues in Application-Defined Resources**](https://www.usenix.org/conference/osdi26/presentation/hu-yigong)（'26）— Yigong Hu（BU）：让剖析器理解应用自定义资源语义。
- [**TypeCraft: A Lightweight Data Type Profiler with High Resolution**](https://www.usenix.org/conference/osdi26/presentation/li-zecheng)（'26）— Zecheng Li（NCSU）：数据类型级高分辨率剖析器（含内核）。
- [**DiTing: Achieving the Trinity of Observability in Cloud**](https://www.usenix.org/conference/osdi26/presentation/ren)（'26）— Zhenyu Ren（阿里）：统一日志/指标/链路的云观测框架。
- [**CLP: Efficient and Scalable Search on Compressed Text Logs**](https://www.usenix.org/conference/osdi21/presentation/rodrigues)（'21）— Kirk Rodrigues（Toronto）：无损压缩日志上直接高效搜索。

### 2.4 内存管理性能
- [**Yak: A High-Performance Big-Data-Friendly Garbage Collector**](https://www.usenix.org/conference/osdi16/technical-sessions/presentation/nguyen)（'16）— Khanh Nguyen（UC Irvine）：大数据应用显式管堆绕开 GC 停顿。
- [**The benefits and costs of writing a POSIX kernel in a high-level language（Biscuit）**](https://www.usenix.org/conference/osdi18/presentation/cutler)（'18）— Cody Cutler（MIT）：Go 写完整 POSIX 内核，量化 GC/运行时代价。
- [**Beyond malloc efficiency to fleet efficiency: a hugepage-aware memory allocator**](https://www.usenix.org/conference/osdi21/presentation/hunter)（'21）— A.H. Hunter（Jane Street）：hugepage 感知分配器缓解 TLB miss 与整机内存浪费。
- [**RESIN: A Holistic Service for Dealing with Memory Leaks in Production Cloud Infrastructure**](https://www.usenix.org/conference/osdi22/presentation/lou-resin)（'22）— Chang Lou（JHU）：内存泄漏检测、定位与在线缓解一体化。
- [**ORC: Increasing Cloud Memory Density via Object Reuse with Capabilities**](https://www.usenix.org/conference/osdi23/presentation/sartakov)（'23）— Vasily Sartakov（Imperial）：能力机制下二进制对象复用，提升云内存密度。
- [**MDK: Rethinking the Data Center Memory Reclamation Problem**](https://www.usenix.org/conference/osdi26/presentation/patel)（'26）— Shaurya Patel（Google/UBC）：SLO 约束下主动回收内存提升主机装箱率。
- [**Finding NEMO: Nimble and Expressive Memory Observability**](https://www.usenix.org/conference/osdi26/presentation/li-shihang)（'26）— Shihang Li（华盛顿大学）：多级异构内存的细粒度低开销用量观测。
- [**Ichnaea: A Framework for Precise Tracking of Memory Objects**](https://www.usenix.org/conference/osdi26/presentation/haque)（'26）— Samad Haque（GWU）：低开销精确追踪内存对象访问历史。
- [**LifeLine: An Object-Page Lifetime Alignment GC Enabling Minimal Memory Copying for Mobile Devices**](https://www.usenix.org/conference/osdi26/presentation/huang-jiacheng)（'26）— Jiacheng Huang（香港城大）：对象-页生命周期对齐 GC，移动端免拷贝整理。
- [**jwmalloc: A Verified Memory Allocator for Mobile Devices**](https://www.usenix.org/conference/osdi26/presentation/wang-jiawei)（'26）— Jiawei Wang（华为）：移动软实时场景的形式化验证分配器。

### 2.5 存储 / IO / 应用与运行时性能
- [**Don't Get Caught in the Cold, Warm-up Your JVM**](https://www.usenix.org/conference/osdi16/technical-sessions/presentation/lion)（'16）— David Lion（Toronto）：剖析 JVM 冷启动根源，快照复用消除预热。
- [**NetBricks: Taking the V out of NFV**](https://www.usenix.org/conference/osdi16/technical-sessions/presentation/panda)（'16）— Aurojit Panda（Berkeley）：Rust 类型安全 NFV，核绑定零拷贝提速。
- [**Flare: Optimizing Apache Spark with Native Compilation for Scale-Up Architectures**](https://www.usenix.org/conference/osdi18/presentation/essertel)（'18）— Gregory Essertel（Purdue）：原生编译 Spark 适配大内存多核单机。
- [**Rearchitecting Linux Storage Stack for µs Latency and High Throughput**](https://www.usenix.org/conference/osdi21/presentation/hwang)（'21）— Jaehyun Hwang（Cornell）：重构 Linux 块层调度路径，内核态微秒级 IO。
- [**zIO: Accelerating IO-Intensive Applications with Transparent Zero-Copy IO**](https://www.usenix.org/conference/osdi22/presentation/stamler)（'22）— Timothy Stamler（UT Austin）：追踪 IO 数据流转，透明消除应用-内核冗余拷贝。
- [**A Simpler and Faster NIC Driver Model for Network Functions**](https://www.usenix.org/conference/osdi20/presentation/pirelli)（'20）— Solal Pirelli（EPFL）：极简网卡驱动模型，批量描述符高吞吐。
- [**Microkernel Goes General: Performance and Compatibility in the HongMeng Production Microkernel**](https://www.usenix.org/conference/osdi24/presentation/chen-haibo)（'24）— Haibo Chen（华为/上交）：鸿蒙生产级微内核的通用化性能与兼容。
- [**Fork in the Road: Reflections and Optimizations for Cold Start Latency in Production Serverless Systems**](https://www.usenix.org/conference/osdi25/presentation/chai-xiaohu)（'25）— Xiaohu Chai（清华/蚂蚁）：生产 serverless 冷启动延迟剖析与优化。
- [**Extending Applications Safely and Efficiently**](https://www.usenix.org/conference/osdi25/presentation/zheng-yusheng)（'25）— Yusheng Zheng（UCSC）：资源化扩展接口模型与用户态 eBPF。
- [**OS Rendering Service Made Parallel with Out-of-Order Execution and In-Order Commit**](https://www.usenix.org/conference/osdi25/presentation/wu-yuanpei)（'25）— Yuanpei Wu（上交 IPADS）：乱序执行 + 顺序提交并行化 OS 渲染服务。
- [**Rethinking Process Snapshots for Near-Warm Serverless Cold Starts**](https://www.usenix.org/conference/osdi26/presentation/holmes)（'26）— Ben Holmes（MIT）：进程快照近热恢复消冷启动。

---

## 三、体系结构

### 3.1 CXL / 分层内存 / 远端与分离式内存
- [**Network Requirements for Resource Disaggregation**](https://www.usenix.org/conference/osdi16/technical-sessions/presentation/gao)（'16）— Peter Gao（Berkeley）：量化内存/盘解耦所需的网络吞吐与延迟。
- [**LegoOS: A Disseminated, Distributed OS for Hardware Resource Disaggregation**](https://www.usenix.org/conference/osdi18/presentation/shan)（'18）— Yizhou Shan（Purdue）：分布式 OS 管理全网解耦的处理器/内存/存储。★资源解耦 OS 形态开创者
- [**Write-Optimized and High-Performance Hashing Index Scheme for Persistent Memory**](https://www.usenix.org/conference/osdi18/presentation/zuo)（'18）— Pengfei Zuo（HUST）：持久内存写优化哈希索引。
- [**AIFM: High-Performance, Application-Integrated Far Memory**](https://www.usenix.org/conference/osdi20/presentation/ruan)（'20）— Zhenyuan Ruan（MIT）：应用集成远端内存，页迁移内核协同降开销。
- [**Semeru: A Memory-Disaggregated Managed Runtime**](https://www.usenix.org/conference/osdi20/presentation/wang)（'20）— Chenxi Wang（UCLA）：内存分解环境下的 JVM，GC 与远端内存协同。
- [**Assise: Performance and Availability via Client-local NVM in a Distributed File System**](https://www.usenix.org/conference/osdi20/presentation/anderson)（'20）— Thomas Anderson（UW）：计算与持久内存同置的分布式文件系统。
- [**AGAMOTTO: How Persistent is your Persistent Memory Application?**](https://www.usenix.org/conference/osdi20/presentation/neal)（'20）— Ian Neal（Michigan）：无干扰记录重放检测 PM 应用持久性与性能 bug。
- [**Nap: A Black-Box Approach to NUMA-Aware Persistent Memory Indexes**](https://www.usenix.org/conference/osdi21/presentation/wang-qing)（'21）— Qing Wang（清华）：黑盒叠加 NUMA 感知层，热数据节点本地化。
- [**MemLiner: Lining up Tracing and Application for a Far-Memory-Friendly Runtime**](https://www.usenix.org/conference/osdi22/presentation/wang)（'22）— Chenxi Wang（UCLA）：对齐 GC/追踪与应用执行，减少远端内存缺页。
- [**Carbink: Fault-Tolerant Far Memory**](https://www.usenix.org/conference/osdi22/presentation/zhou-yang)（'22）— Yang Zhou（Harvard）：纠删码 + 单边 RMA 的高效容错远端内存。
- [**ODINFS: Scaling PM Performance with Opportunistic Delegation**](https://www.usenix.org/conference/osdi22/presentation/zhou-diyu)（'22）— Diyu Zhou（EPFL）：争用与 NUMA 感知的机会性委派扩展 PM 文件系统。
- [**Johnny Cache: the End of DRAM Cache Conflicts (in Tiered Main Memory Systems)**](https://www.usenix.org/conference/osdi23/presentation/lepers)（'23）— Baptiste Lepers（Neuchâtel）：硬件管理分层内存，细粒度 DRAM 缓存免冲突。★CXL 分层内存前奏
- [**SMART: A High-Performance Adaptive Radix Tree for Disaggregated Memory**](https://www.usenix.org/conference/osdi23/presentation/luo)（'23）— Xuchuan Luo（复旦）：分离式内存上的自适应基数树。
- [**Nomad: Non-Exclusive Memory Tiering via Transactional Page Migration**](https://www.usenix.org/conference/osdi24/presentation/xiang)（'24）— Lingfeng Xiang（UT–Arlington）：事务式页面迁移实现非独占内存分层。
- [**Managing Memory Tiers with CXL in Virtualized Environments**](https://www.usenix.org/conference/osdi24/presentation/zhong-yuhong)（'24）— Yuhong Zhong（Columbia/Azure）：虚拟化环境低开销 CXL 分层内存管理。
- [**A Tale of Two Paths: Toward a Hybrid Data Plane for Efficient Far-Memory Applications**](https://www.usenix.org/conference/osdi24/presentation/chen-lei)（'24）— Lei Chen（中科院软件所）：混合内核分页与内核旁路的远内存数据面。
- [**DRust: Language-Guided Distributed Shared Memory**](https://www.usenix.org/conference/osdi24/presentation/ma-haoran)（'24）— Haoran Ma（UCLA）：借 Rust 所有权约束同步，实用化细粒度 DSM。
- [**Motor: Multi-Versioning for Distributed Transactions on Disaggregated Memory**](https://www.usenix.org/conference/osdi24/presentation/zhang-ming)（'24）— Ming Zhang（HUST）：内存解耦池上的多版本分布式事务。
- [**FineMem: Breaking the Allocation Overhead vs. Memory Waste Dilemma in Fine-Grained Disaggregated Memory Management**](https://www.usenix.org/conference/osdi25/presentation/wang-xiaoyang)（'25）— Xiaoyang Wang（中科大）：细粒度远端内存分配，兼顾开销与浪费。
- [**Tigon: A Distributed Database for a CXL Pod**](https://www.usenix.org/conference/osdi25/presentation/huang-yibo)（'25）— Yibo Huang（UT Austin）：CXL Pod 上免网络消息的分布式事务库。
- [**Tiered Memory Management Beyond Hotness**](https://www.usenix.org/conference/osdi25/presentation/liu)（'25）— Jinshu Liu（Virginia Tech）：AOL 指标取代热度，指导分层内存放置。
- [**RamRyder: Pooling Memory Elastically**](https://www.usenix.org/conference/osdi26/presentation/zhou-yanbo)（'26）— Yanbo Zhou（UCSD）：CXL 内存池化，容量与带宽脱离 vCPU 比例弹性分配。
- [**MAC: Metadata Acceleration for Sustainable Performance in Big-Data Systems with CXL DRAM**](https://www.usenix.org/conference/osdi26/presentation/lee)（'26）— Dusol Lee（首尔大学）：CXL 大容量内存下的元数据分层加速。
- [**OBASE: Object-Based Address-Space Engineering to Improve Memory Tiering**](https://www.usenix.org/conference/osdi26/presentation/banakar)（'26）— Vinay Banakar（UW–Madison/Google）：按对象热度重构地址空间治分层内存碎片。
- [**Blowfish: Elastic Virtual Machine Memory for Disaggregated Memory**](https://www.usenix.org/conference/osdi26/presentation/zhang-yulong)（'26）— Yulong Zhang（中科院计算所）：微秒级冷内存回收，避开 THP 页表重映射。
- [**Duhu: Shared Disaggregated Memory for Distributed Data Processing Frameworks**](https://www.usenix.org/conference/osdi26/presentation/men)（'26）— Qiutong Men（NYU）：共享分解内存支撑分布式框架免拷贝处理。
- [**FORGE: Mitigating Synchronization Amplification for Memory-Disaggregated Caching**](https://www.usenix.org/conference/osdi26/presentation/yang-zhijun)（'26）— Zhijun Yang（HUST）：分组摊销同步 + RDMA 网卡内存卸载。
- [**MEGALON: Efficient Data Sharing for Partly Coherent CXL Memory**](https://www.usenix.org/conference/osdi26/presentation/hu-jiyu)（'26）— Jiyu Hu（UIUC）：部分一致 CXL 内存的跨机数据共享。

### 3.2 虚拟化 / 机密计算 / TEE
- [**SCONE: Secure Linux Containers with Intel SGX**](https://www.usenix.org/conference/osdi16/technical-sessions/presentation/arnautov)（'16）— Sergei Arnautov（TU Dresden）：SGX 容器运行时，异步 syscall + 用户级调度。
- [**Graviton: Trusted Execution Environments on GPUs**](https://www.usenix.org/conference/osdi18/presentation/volos)（'18）— Stavros Volos（MSR）：GPU 可信执行环境，命令处理器级隔离。
- [**FVM: FPGA-assisted Virtual Device Emulation for Storage Virtualization**](https://www.usenix.org/conference/osdi20/presentation/kwon)（'20）— Dongup Kwon（首尔大学/三星）：FPGA 卸载虚拟设备仿真。
- [**Efficiently Mitigating Transient Execution Attacks using the Unmapped Speculation Contract**](https://www.usenix.org/conference/osdi20/presentation/behrens)（'20）— Jonathan Behrens（MIT）：取消映射高危页阻断瞬态执行攻击。
- [**Scalable Memory Protection in the PENGLAI Enclave**](https://www.usenix.org/conference/osdi21/presentation/feng)（'21）— Erhu Feng（上交 IPADS）：RISC-V PMP+EPT 拼接实现可扩展 enclave。
- [**MAGE: Nearly Zero-Cost Virtual Memory for Secure Computation**](https://www.usenix.org/conference/osdi21/presentation/kumar)（'21）— Sam Kumar（Berkeley）：内存密钥保护替代换页，安全计算虚存近零开销。★Best Paper
- [**Design and Verification of the Arm Confidential Compute Architecture**](https://www.usenix.org/conference/osdi22/presentation/li)（'22）— Xupeng Li（Columbia）：Arm CCA Realm 的设计与验证。
- [**CAP-VMs: Capability-Based Isolation and Sharing in the Cloud**](https://www.usenix.org/conference/osdi22/presentation/sartakov)（'22）— Vasily Sartakov（Imperial）：硬件能力实现细粒度 VM 隔离与高效共享。
- [**Security and Performance in the Delegated User-level Virtualization（iVirt）**](https://www.usenix.org/conference/osdi23/presentation/chen)（'23）— Jiahao Chen（上交 IPADS）：hypervisor 拆分控制面与用户级 VM 面。
- [**Sabre: Hardware-Accelerated Snapshot Compression for Serverless MicroVMs**](https://www.usenix.org/conference/osdi24/presentation/lazarev)（'24）— Nikita Lazarev（MIT）：硬件加速快照压缩与页预取，降 microVM 冷启动。
- [**To PRI or Not To PRI, That's the question**](https://www.usenix.org/conference/osdi25/presentation/wang-yun)（'25）— Yun Wang（上交）：动态切换直通与 virtio，免 I/O 页故障（IOMMU）。
- [**MettEagle: Costs and Benefits of Implementing Containers on Microkernels**](https://www.usenix.org/conference/osdi25/presentation/miemietz)（'25）— Till Miemietz（Barkhausen Institut）：微内核实现容器的代价与收益实测。
- [**JANUS: Cross-World, Cooperative Nested Virtualization for Secure Containers**](https://www.usenix.org/conference/osdi26/presentation/lai)（'26）— Jiangshan Lai（蚂蚁）：跨世界协作嵌套虚拟化，降三级页表开销。
- [**Nested SEV: Secure and Generic SEV Support for Nested Virtualization**](https://www.usenix.org/conference/osdi26/presentation/takiguchi)（'26）— Kazuki Takiguchi（九工大）：嵌套虚拟化下 SEV 直通/虚拟化双机制。
- [**Osprey: Transparent and Efficient Virtual Memory for Secure Computation**](https://www.usenix.org/conference/osdi26/presentation/liu-yicheng)（'26）— Yicheng Liu（UCLA）：密态计算放大内存开销的透明虚拟内存。
- [**Accelerating Confidential Databases with Crypto-Free Mappings**](https://www.usenix.org/conference/osdi26/presentation/huang-wenxuan)（'26）— Wenxuan Huang（中科院软件所）：免加密页映射消除机密库密码开销。
- [**μUSB: Practical and Safe USB Driver Reuse for Arm TrustZone**](https://www.usenix.org/conference/osdi26/presentation/zhang-xuankai)（'26）— Xuankai Zhang（电子科大）：安全复用 Linux USB 驱动进 TrustZone。
- [**M3U: Scalable Kernel Memory Management for Efficient Post-Copy Live Migration of High-End VMs**](https://www.usenix.org/conference/osdi26/presentation/xu-yizhe)（'26）— Yizhe Xu（上交）：可扩展内核内存管理加速 post-copy 热迁移。
- [**Compaction-Free Memory Defragmentation for Virtualization via Infinite Guest Physical Address Space**](https://www.usenix.org/conference/osdi26/presentation/zeng)（'26）— Peixin Zeng（哈工大深圳）：无限客户物理地址空间免压缩整理大页碎片。
- [**Virtualizing eBPF with Late-Binding**](https://www.usenix.org/conference/osdi26/presentation/zhang-jing)（'26）— Jing Zhang（上交 IPADS）：eBPF 晚绑定实现多租户共享内核。

### 3.3 加速器 / DPU / SmartNIC / FPGA
- [**AmorphOS: Sharing, Protection, and Compatibility for Reconfigurable Fabric**](https://www.usenix.org/conference/osdi18/presentation/khawaja)（'18）— Ahmed Khawaja（UT Austin）：FPGA 多租户动态分区共享与保护。
- [**Floem: A Programming System for NIC-Accelerated Network Applications**](https://www.usenix.org/conference/osdi18/presentation/phothilimthana)（'18）— Mangpo Phothilimthana（Berkeley）：SmartNIC 卸载编程系统。
- [**PANIC: A High-Performance Programmable NIC for Multi-tenant Networks**](https://www.usenix.org/conference/osdi20/presentation/lin)（'20）— Jiaxin Lin（UW–Madison）：可编程 NIC 多基底卸载，多租户性能隔离。
- [**hXDP: Efficient Software Packet Processing on FPGA NICs**](https://www.usenix.org/conference/osdi20/presentation/brunella)（'20）— Marco Spaziani Brunella（罗马二大）：eBPF/XDP 编译到 FPGA 网卡线性速包处理。★Best Paper
- [**Do OS abstractions make sense on FPGAs?**](https://www.usenix.org/conference/osdi20/presentation/roscoe)（'20）— Dario Korolija（ETH）：分析 OS 抽象映射 FPGA 混合系统的收益与代价。
- [**PipeSwitch: Fast Pipelined Context Switching for Deep Learning Applications**](https://www.usenix.org/conference/osdi20/presentation/bai)（'20）— Zhihao Bai（JHU）：流水线化上下文切换，GPU 训练推理秒级复用。
- [**Rammer: Enabling Holistic DL Compiler Optimizations with rTasks**](https://www.usenix.org/conference/osdi20/presentation/ma)（'20）— Lingxiao Ma（北大/MSR）：rTasks 抽象统一编排 GPU 算子并发。
- [**GNNAdvisor: An Adaptive and Efficient Runtime System for GNN Acceleration on GPUs**](https://www.usenix.org/conference/osdi21/presentation/wang-yuke)（'21）— Yuke Wang（UCSB）：按图与算子特征自适应优化 GPU 执行。
- [**FAERY: An FPGA-accelerated Embedding-based Retrieval System**](https://www.usenix.org/conference/osdi22/presentation/zeng)（'22）— Chaoliang Zeng（HKUST）：FPGA 卸载嵌入检索，高吞吐低尾延迟。
- [**Efficient and Scalable Graph Pattern Mining on GPUs**](https://www.usenix.org/conference/osdi22/presentation/chen)（'22）— Xuhao Chen（MIT）：GPU 图模式挖掘，细粒度并行。
- [**Characterizing Off-path SmartNIC for Accelerating Distributed Systems**](https://www.usenix.org/conference/osdi23/presentation/wei-smartnic)（'23）— Xingda Wei（上交 IPADS）：系统刻画 BlueField-2 多通信路径卸载特性。
- [**Ensō: A Streaming Interface for NIC-Application Communication**](https://www.usenix.org/conference/osdi23/presentation/sadok)（'23）— Hugo Sadok（CMU）：NIC 内环形流式接口，免拷贝免中断收发。
- [**No Provisioned Concurrency: Fast RDMA-codesigned Remote Fork for Serverless Computing（MITOSIS）**](https://www.usenix.org/conference/osdi23/presentation/wei-rdma)（'23）— Xingda Wei（上交 IPADS）：RDMA 协同远程 fork，秒级起万级容器。
- [**Welder: Scheduling Deep Learning Memory Access via Tile-graph**](https://www.usenix.org/conference/osdi23/presentation/shi)（'23）— Yining Shi（北大/MSR）：tile 图统一调度 DNN 访存缓解带宽瓶颈。
- [**MGG: Fine-Grained Intra-Kernel Communication-Computation Pipelining on Multi-GPU**](https://www.usenix.org/conference/osdi23/presentation/wang-yuke)（'23）— Yuke Wang（UCSB）：内核级通信-计算流水线，多 GPU 加速 GNN。
- [**Effectively Scheduling Computational Graphs of DNNs toward Their Domain-Specific Accelerators**](https://www.usenix.org/conference/osdi23/presentation/zhao)（'23）— Jie Zhao（信息工程大学）：硬件感知切分计算图调度至专用加速器。
- [**ACCL+: an FPGA-Based Collective Engine for Distributed Applications**](https://www.usenix.org/conference/osdi24/presentation/he)（'24）— Zhenhao He（ETH）：FPGA 集合通信引擎。
- [**Burstable Cloud Block Storage with Data Processing Units**](https://www.usenix.org/conference/osdi24/presentation/shu)（'24）— Junyi Shu（北大/阿里云）：DPU 卸载实现可突发云块存储。
- [**Performance Interfaces for Hardware Accelerators**](https://www.usenix.org/conference/osdi24/presentation/ma-jiacheng)（'24）— Jiacheng Ma（EPFL）：声明加速器性能接口，预测收益再选用。
- [**MonoNN: Enabling a New Monolithic Optimization Space for NN Inference**](https://www.usenix.org/conference/osdi24/presentation/zhuang)（'24）— Donglin Zhuang（悉尼大学）：算子单体化融合消 GPU 非计算开销。
- [**High-throughput and Flexible Host Networking for Accelerated Computing**](https://www.usenix.org/conference/osdi24/presentation/skiadopoulos)（'24）— Athinagoras Skiadopoulos（Stanford）：GPU 主机网络高吞吐可定制。
- [**InfiniGen: Efficient Generative Inference of LLMs with Dynamic KV Cache Management**](https://www.usenix.org/conference/osdi24/presentation/lee)（'24）— Wonbeom Lee（首尔大学）：预测注意力热键，KV cache 卸载至 CPU 内存。
- [**FuseLink: Enabling Efficient GPU Communication over Multiple NICs**](https://www.usenix.org/conference/osdi25/presentation/ren)（'25）— Zhenghang Ren（HKUST）：GPU 中继流量至空闲网卡榨满多 NIC。
- [**WaferLLM: Large Language Model Inference at Wafer Scale**](https://www.usenix.org/conference/osdi25/presentation/he)（'25）— Congjie He（爱丁堡）：适配晶圆级片上网格的 LLM 推理。
- [**Scalio: Scaling up DPU-based JBOF Key-value Store with NVMe-oF Target Offload**](https://www.usenix.org/conference/osdi25/presentation/sun)（'25）— Xun Sun（清华）：NVMe-oF target 卸载 DPU 扩展 JBOF。
- [**KPerfIR: Towards an Open and Compiler-centric Ecosystem for GPU Kernel Performance Tooling**](https://www.usenix.org/conference/osdi25/presentation/guan)（'25）— Yue Guan（UCSD）：编译器 pass 生态构建 GPU 剖析工具。
- [**Neutrino: Fine-grained GPU Kernel Profiling via Programmable Probing**](https://www.usenix.org/conference/osdi25/presentation/huang-songlin)（'25）— Songlin Huang（香港大学）：汇编级可编程探针细粒度 GPU 剖析。
- [**PipeThreader: Software-Defined Pipelining for Efficient DNN Execution**](https://www.usenix.org/conference/osdi25/presentation/cheng)（'25）— Yu Cheng（北大）：软件接管流水调度用满 GPU 异构单元。
- [**Prism: Cost-Efficient Multi-LLM Serving via GPU Memory Ballooning**](https://www.usenix.org/conference/osdi26/presentation/yu-shan)（'26）— Shan Yu（UCLA）：GPU 内存"气球"弹性分配，统一多模型空/时共享。
- [**MoonBright: A GPU Memory Allocator with Device-Side Page Table Materialization and Deferred TLB Coherence**](https://www.usenix.org/conference/osdi26/presentation/zhang-yangyu)（'26）— Yangyu Zhang（中科院计算所）：GPU 侧页表构建 + 延迟 TLB 一致性。
- [**Nixie: Efficient, Transparent Temporal Multiplexing for Consumer GPUs**](https://www.usenix.org/conference/osdi26/presentation/xu-yechen)（'26）— Yechen Xu（Duke）：消费级 GPU 透明时间复用多进程共享。
- [**CoPilotIO: CPU as a Co-Pilot for GPU I/O to Free GPU Compute**](https://www.usenix.org/conference/osdi26/presentation/chen-guanyi)（'26）— Guanyi Chen（港科大广州）：CPU 代 GPU 轮询按需 I/O 释放算力。
- [**RoCE BALBOA: Service-Enhanced RDMA Offload Engine for Data Center SmartNICs**](https://www.usenix.org/conference/osdi26/presentation/heer)（'26）— Maximilian Heer（ETH）：FPGA SmartNIC 百 G 开源 RDMA 卸载引擎。
- [**μShell: A Microkernel-based FPGA Shell Architecture**](https://www.usenix.org/conference/osdi26/presentation/chen-jiyang)（'26）— Jiyang Chen（TUM）：微内核式 FPGA shell 支撑多租户组合。
- [**FARLock: Asymmetric RDMA Locking Made Fair**](https://www.usenix.org/conference/osdi26/presentation/hu-yuehao)（'26）— Yuehao Hu（SFU）：修复非对称 RDMA 锁的 FCFS 公平性。

### 3.4 微架构 / 缓存 / 页表 / 硬件协同
- [**Coordinated and Efficient Huge Page Management with Ingens**](https://www.usenix.org/conference/osdi16/technical-sessions/presentation/kwon)（'16）— Youngjin Kwon（UT Austin）：大页协调管理，按需晋升防 THP 浪费。
- [**EbbRT: A Framework for Building Per-Application Library Operating Systems**](https://www.usenix.org/conference/osdi16/technical-sessions/presentation/schatzberg)（'16）— Dan Schatzberg（BU）：per-app 库 OS，事件驱动跨节点可扩展。
- [**The nanoPU: A Nanosecond Network Stack for Datacenters**](https://www.usenix.org/conference/osdi21/presentation/ibanez)（'21）— Stephen Ibanez（Stanford）：消息直达寄存器的 NIC-CPU 协同网络栈。
- [**Automatically Reasoning About How Systems Code Uses the CPU Cache**](https://www.usenix.org/conference/osdi24/presentation/iyer)（'24）— Rishabh Iyer（EPFL）：自动蒸馏代码缓存访问行为精确推理。
- [**EMT: An OS Framework for New Memory Translation Architectures**](https://www.usenix.org/conference/osdi25/presentation/chai-siyuan)（'25）— Siyuan Chai（UIUC）：可扩展内存管理框架，实验新内存翻译硬件（页表/MMU）。
- [**When DDIO Meets Page Coloring: Revisiting DDIO Performance with Sepia**](https://www.usenix.org/conference/osdi26/presentation/song)（'26）— Changwoo Song（成均馆大学）：页着色隔离 DDIO 的 LLC，治 DMA 缓存泄漏。

---

## 四、集群级调度（数据中心 / ML 系统）

### OSDI '16
- [Altruistic Scheduling in Multi-Resource Clusters](https://www.usenix.org/conference/osdi16/technical-sessions/presentation/grandl_altruistic) — Robert Grandl（UW–Madison）：利他式调度，短期让渡公平换集群效率。
- [GRAPHENE: Packing and Dependency-Aware Scheduling for Data-Parallel Clusters](https://www.usenix.org/conference/osdi16/technical-sessions/presentation/grandl_graphene) — Robert Grandl：依赖与资源感知打包，容器共置提效。
- [Firmament: Fast, Centralized Cluster Scheduling at Scale](https://www.usenix.org/conference/osdi16/technical-sessions/presentation/gog) — Ionel Gog（Cambridge）：基于最大流的中心式调度，兼顾质量与规模。
- [Morpheus: Towards Automated SLOs for Enterprise Clusters](https://www.usenix.org/conference/osdi16/technical-sessions/presentation/jyothi) — Sangeetha Abdu Jyothi：自动推导 SLO 的滚动调度。
- [History-Based Harvesting of Spare Cycles and Storage in Large-Scale Datacenters](https://www.usenix.org/conference/osdi16/technical-sessions/presentation/zhang-yunqi) — Yunqi Zhang（Michigan/MSR）：依历史负载预测安全收割空闲资源共置。
- [TensorFlow: A System for Large-Scale Machine Learning](https://www.usenix.org/conference/osdi16/technical-sessions/presentation/abadi) — Martín Abadi（Google）：数据流图引擎自动设备放置，大规模训练奠基系统。

### OSDI '18
- [Gandiva: Introspective Cluster Scheduling for Deep Learning](https://www.usenix.org/conference/osdi18/presentation/xiao) — Wencong Xiao（北航/MSR）：利用 DL 作业特性做 GPU 时分复用与迁移。★DL 集群调度开创
- [Ray: A Distributed Framework for Emerging AI Applications](https://www.usenix.org/conference/osdi18/presentation/moritz) — Philipp Moritz（Berkeley）：统一 task/actor 抽象的动态任务引擎。
- [Three steps is all you need: fast, accurate, automatic scaling decisions for distributed streaming dataflows](https://www.usenix.org/conference/osdi18/presentation/kalavri) — Vasiliki Kalavri（ETH）：三步自动决策流式负载扩缩容。

### OSDI '20
- [Heterogeneity-Aware Cluster Scheduling Policies for Deep Learning Workloads（Tiresias）](https://www.usenix.org/conference/osdi20/presentation/narayanan-deepak) — Deepak Narayanan（Stanford/MSR）：感知加速器与互联异构性的训练调度。
- [HiveD: Sharing a GPU Cluster for Deep Learning with Guarantees](https://www.usenix.org/conference/osdi20/presentation/zhao-hanyu) — Hanyu Zhao（北大/MSR）：GPU 集群多租户共享，配额与拓扑双保证。
- [AntMan: Dynamic Scaling on GPU Clusters for Deep Learning](https://www.usenix.org/conference/osdi20/presentation/xiao) — Wencong Xiao（阿里）：生产 GPU 集群弹性调度，训练在线混部。
- [A Unified Architecture for Accelerating Distributed DNN Training in Heterogeneous GPU/CPU Clusters（BytePS）](https://www.usenix.org/conference/osdi20/presentation/jiang) — Yimin Jiang（清华/字节）：调动 CPU 与带宽参与梯度同步。
- [KungFu: Making Training in Distributed Machine Learning Adaptive](https://www.usenix.org/conference/osdi20/presentation/mai) — Luo Mai（Imperial）：依梯度统计自适应调整 worker 规模。
- [Twine: A Unified Cluster Management System for Shared Infrastructure](https://www.usenix.org/conference/osdi20/presentation/tang) — Chunqiang Tang（Facebook）：Facebook 十年生产统一集群管理。
- [Protean: VM Allocation Service at Scale](https://www.usenix.org/conference/osdi20/presentation/hadary) — Ori Hadary（Azure）：Azure 可用区级 VM 分配放置服务。
- [FIRM: An Intelligent Fine-grained Resource Management Framework for SLO-Oriented Microservices](https://www.usenix.org/conference/osdi20/presentation/qiu) — Haoran Qiu（UIUC）：学习干扰模型，微服务细粒度分配保 SLO。
- [Building Scalable and Flexible Cluster Managers Using Declarative Programming](https://www.usenix.org/conference/osdi20/presentation/suresh) — Lalith Suresh（VMware）：声明式描述集群优化问题自动求解。
- [Unearthing inter-job dependencies for better cluster scheduling](https://www.usenix.org/conference/osdi20/presentation/chung) — Andrew Chung（CMU）：挖掘生产作业间依赖改进调度。

### OSDI '21
- [Pollux: Co-adaptive Cluster Scheduling for Goodput-Optimized Deep Learning](https://www.usenix.org/conference/osdi21/presentation/qiao) — Aurick Qiao（Petuum/CMU）：作业与集群协同自适应，goodput 最优分配。★Best Paper
- [Oort: Efficient Federated Learning via Guided Participant Selection](https://www.usenix.org/conference/osdi21/presentation/lai) — Fan Lai（Michigan）：兼顾速度与数据贡献挑选联邦学习设备。
- [Dorylus: Affordable, Scalable, and Accurate GNN Training with Distributed CPU Servers and Serverless Threads](https://www.usenix.org/conference/osdi21/presentation/thorpe) — John Thorpe（UCLA）：serverless 线程弹性扩展 CPU 集群 GNN 训练。

### OSDI '22
- [Orca: A Distributed Serving System for Transformer-Based Generative Models](https://www.usenix.org/conference/osdi22/presentation/yu) — Gyeong-In Yu（首尔大学）：迭代级调度与连续批处理。★影响 vLLM 等推理引擎
- [Alpa: Automating Inter- and Intra-Operator Parallelism for Distributed Deep Learning](https://www.usenix.org/conference/osdi22/presentation/zheng-lianmin) — Lianmin Zheng（Berkeley）：分层自动化算子间/算子内并行规划。
- [Unity: Accelerating DNN Training Through Joint Optimization](https://www.usenix.org/conference/osdi22/presentation/unger) — Colin Unger（Stanford）：统一计算图联合优化代数变换与并行。
- [Synergy: Looking Beyond GPUs for DNN Scheduling on Multi-Tenant Clusters](https://www.usenix.org/conference/osdi22/presentation/mohan) — Jayashree Mohan（MSR）：按训练对 CPU/内存敏感度做多资源调度。
- [ORION and the Three Rights: Sizing, Bundling, and Prewarming for Serverless DAGs](https://www.usenix.org/conference/osdi22/presentation/mahgoub) — Ashraf Mahgoub（Purdue）：统计推断函数时延，优化 serverless DAG 资源配置。

### OSDI '23
- [Global Capacity Management With Flux](https://www.usenix.org/conference/osdi23/presentation/eriksen) — Marius Eriksen（Meta）：跨地域数据中心的全局服务容量调配。
- [Kerveros: Efficient and Scalable Cloud Admission Control](https://www.usenix.org/conference/osdi23/presentation/sajal) — Sultan Mahmud Sajal（MSR/Penn State）：动态供需下的分布式准入控制。
- [Defcon: Preventing Overload with Graceful Feature Degradation](https://www.usenix.org/conference/osdi23/presentation/meza) — Justin Meza（Meta）：过载时优雅降级产品功能保容量。
- [Cilantro: Performance-Aware Resource Allocation for General Objectives via Online Feedback](https://www.usenix.org/conference/osdi23/presentation/bhardwaj) — Romil Bhardwaj（Berkeley）：在线性能反馈驱动的通用目标资源分配。
- [Karma: Resource Allocation for Dynamic Demands](https://www.usenix.org/conference/osdi23/presentation/vuppalapati) — Midhul Vuppalapati（Cornell）：动态需求下兼顾公平与效率。
- [AlpaServe: Statistical Multiplexing with Model Parallelism for Deep Learning Serving](https://www.usenix.org/conference/osdi23/presentation/li-zhouhan) — Zhuohan Li（Berkeley）：模型并行实现多模型 GPU 统计复用。
- [Hydro: Surrogate-Based Hyperparameter Tuning Service in Datacenters](https://www.usenix.org/conference/osdi23/presentation/hu) — Qinghao Hu（NTU S-Lab）：代理模型优化调参作业的调度。

### OSDI '24（LLM serving 爆发）
- [Sarathi-Serve: Taming Throughput-Latency Tradeoff in LLM Inference](https://www.usenix.org/conference/osdi24/presentation/agrawal) — Amey Agrawal（Georgia Tech）：分块 prefill 无停顿批调度，保时延 SLO。
- [DistServe: Disaggregating Prefill and Decoding for Goodput-optimized LLM Serving](https://www.usenix.org/conference/osdi24/presentation/zhong-yinmin) — Yinmin Zhong（北大）：prefill/decode 算力解耦部署。
- [Llumnix: Dynamic Scheduling for Large Language Model Serving](https://www.usenix.org/conference/osdi24/presentation/sun-biao) — Biao Sun（阿里）：跨实例动态迁移请求，均载降尾延迟。
- [ServerlessLLM: Low-Latency Serverless Inference for Large Language Models](https://www.usenix.org/conference/osdi24/presentation/fu) — Yao Fu（爱丁堡）：加载感知调度配近 GPU 存储。
- [Fairness in Serving Large Language Models](https://www.usenix.org/conference/osdi24/presentation/sheng) — Ying Sheng（Berkeley/Stanford）：虚拟令牌计数实现 LLM 服务公平调度。
- [Parrot: Efficient Serving of LLM-based Applications with Semantic Variable](https://www.usenix.org/conference/osdi24/presentation/lin-chaofan) — Chaofan Lin（上交）：语义变量打通 LLM 请求间数据流复用。
- [dLoRA: Dynamically Orchestrating Requests and Adapters for LoRA LLM Serving](https://www.usenix.org/conference/osdi24/presentation/wu-bingyang) — Bingyang Wu（北大）：动态合并/拆分 LoRA 适配器编排请求。
- [USHER: Holistic Interference Avoidance for Resource Optimized ML Inference](https://www.usenix.org/conference/osdi24/presentation/shubha) — Sudipta Saha Shubha（UVA）：干扰感知 GPU 空间复用最大化 goodput。
- [When will my ML Job finish? Predictability-Centric Scheduling](https://www.usenix.org/conference/osdi24/presentation/bin-faisal) — Abdullah Bin Faisal（Tufts）：以完成时间可预测为中心的 GPU 调度。
- [MAST: Global Scheduling of ML Training across Geo-Distributed Datacenters](https://www.usenix.org/conference/osdi24/presentation/choudhury) — Arnab Choudhury（Meta）：跨地域 ML 训练全局调度。
- [Optimizing Resource Allocation in Hyperscale Datacenters](https://www.usenix.org/conference/osdi24/presentation/kumar) — Neeraj Kumar（Meta）：超大规模资源分配优化实践。
- [nnScaler: Constraint-Guided Parallelization Plan Generation for DL Training](https://www.usenix.org/conference/osdi24/presentation/lin-zhiqi) — Zhiqi Lin（中科大）：约束引导生成训练并行化计划。

### OSDI '25
- [BlitzScale: Fast and Live Large Model Autoscaling with O(1) Host Caching](https://www.usenix.org/conference/osdi25/presentation/zhang-dingyan) — Dingyan Zhang（上交）：O(1) 主机缓存实现大模型活体扩缩容。
- [NanoFlow: Towards Optimal Large Language Model Serving Throughput](https://www.usenix.org/conference/osdi25/presentation/zhu-kan) — Kan Zhu（UW）：设备内纳批次流水复用逼近最优吞吐。
- [WLB-LLM: Workload-Balanced 4D Parallelism for LLM Training](https://www.usenix.org/conference/osdi25/presentation/wang-zheng) — Zheng Wang（UCSD/Meta）：负载均衡的 4D 并行训练配置。
- [Decouple and Decompose: Scaling Resource Allocation with DeDe](https://www.usenix.org/conference/osdi25/presentation/xu) — Zhiying Xu（Harvard）：解耦与分解加速云资源分配求解。
- [Understanding Stragglers in Large Model Training Using What-if Analysis](https://www.usenix.org/conference/osdi25/presentation/lin-jinkun) — Jinkun Lin（NYU/字节）：what-if 分析定位训练掉队根因。
- [Söze: Per-flow Weighted Bandwidth Allocation at Scale](https://www.usenix.org/conference/osdi25/presentation/wang-weitao) — Weitao Wang（Rice）：遥测驱动去中心化加权带宽分配。
- [Kamino: Efficient VM Allocation at Scale with Latency-Driven Cache-Aware Scheduling](https://www.usenix.org/conference/osdi25/presentation/domingo) — David Domingo（Rutgers）：时延驱动缓存感知的大规模 VM 分配。

### OSDI '26（LLM/RL 调度占主导）
LLM 推理/请求调度：
- [Simple Is Better: Multiplication May Be All You Need for LLM Request Scheduling](https://www.usenix.org/conference/osdi26/presentation/zhang-dingyan) — Dingyan Zhang（上交 IPADS）：用乘法合成 KV 命中与均衡分做请求调度。
- [Tessera: A Holistic Pipeline Parallelism Framework for Trillion-Parameter Heterogeneous MoE Training](https://www.usenix.org/conference/osdi26/presentation/hu-weifang) — Weifang Hu（HUST）：异构 MoE 万亿模型流水线划分与调度。★
- [Hetu v2: Hierarchical and Heterogeneous SPMD Annotations](https://www.usenix.org/conference/osdi26/presentation/li-haoyang) — Haoyang Li（北大）：层次化异构 SPMD 标注自动推导切分与通信。
- [Teaching the Old Dog New Tricks: Efficient Data Pipelines for Large-Scale LLM Pre-Training](https://www.usenix.org/conference/osdi26/presentation/chen-luofan) — Luofan Chen（中科大/字节 Seed）：预测性复制 + 预处理卸载消万卡数据瓶颈。★‡Best Paper（大陆机构首次第一单位获奖）
- [TrainMover: An Interruption-Resilient Runtime for ML Training](https://www.usenix.org/conference/osdi26/presentation/lao) — ChonLam Lao（Harvard/阿里）：弹性/备用机近零停机接管中断训练。
RL 训练调度：[Weave](https://www.usenix.org/conference/osdi26/presentation/wu-tianyuan)（HKUST，回放-训练分解协同调度）、[RLinf](https://www.usenix.org/conference/osdi26/presentation/yu-chao)（清华，宏到微流变换）、[DynaRL](https://www.usenix.org/conference/osdi26/presentation/wang-yuanqing)（北大，动态重配置）、[RollArt](https://www.usenix.org/conference/osdi26/presentation/gao)（HKUST，多任务智能体 RL）、[Seer](https://www.usenix.org/conference/osdi26/presentation/qin)（月之暗面/清华，同提示输出相似性预测）。
生产系统/能耗：
- [DVLA: Dynamic VM Lifetime Aware Scheduling](https://www.usenix.org/conference/osdi26/presentation/zhang-zhengtong) — Zhengtong Zhang（阿里云）：VM 生命周期漂移感知调度消"放置债"。★
- [PIMS: Fleet-Wide Datacenter Maintenance with Minimal Capacity Buffer](https://www.usenix.org/conference/osdi26/presentation/leonhardi) — Benjamin Leonhardi（Meta）：百万服务器舰队维护调度。★
- [Heterogeneity at Hyperscale: Characterization and Scheduling of Large Production AI Clusters at Alibaba](https://www.usenix.org/conference/osdi26/presentation/li-suyi) — Suyi Li（HKUST/阿里）：15.5 万 GPU 异构集群 6 个月刻画与调度。★
- [Hardware Lifecycle-Aware Power Planning in Commercial Hyperscale Datacenters](https://www.usenix.org/conference/osdi26/presentation/li-ruihao) — Ruihao Li（Meta/UT Austin）：硬件生命周期感知的电力规划。
- [Kareus: Joint Reduction of Dynamic and Static Energy in Large Model Training](https://www.usenix.org/conference/osdi26/presentation/wu-ruofan) — Ruofan Wu（Michigan）：联合优化训练动态与静态能耗。
- [SPADE: Signal-Aware DAG Scheduling and Dynamic Provisioning](https://www.usenix.org/conference/osdi26/presentation/lechowicz) — Adam Lechowicz（UMass）：电价/碳排信号感知的 DAG 调度。
- [Quota Marketplace: Dynamic Pricing for ML Training Resources](https://www.usenix.org/conference/osdi26/presentation/sivan) — Balasubramanian Sivan（Google）：动态定价分配训练配额。
- [Mimesys: Generating Realistic Executable Testing Environments from Resource Usage Traces](https://www.usenix.org/conference/osdi26/presentation/kim-donghyun) — Donghyun Kim（UT Austin）：从资源痕迹合成可执行混部测试环境。
- [SDCs in the Wild: Characterizing and Diagnosing SDC-Defective GPUs](https://www.usenix.org/conference/osdi26/presentation/zheng) — Wenxin Zheng（上交/字节 Seed）：生产集群静默数据损坏坏卡定位。★

---

## 五、十年趋势

1. **微秒级调度成为主线**：Caladan（'20）确立微秒级核仲裁范式 → RackSched（机架级，'20）→ GPU 抢占 REEF（'22）/XSched（'25）→ '26 的 SBB/Rakaia/PeeR 把抢占推进用户态网络运行时、内核 RPC 路径和 eBPF 程序。调度决策点从内核调度器外移至用户态 runtime，"内核调度器管什么、runtime 管什么"是贯穿十年的分工议题。
2. **Linux 内核重新成为研究对象**：'21 重构存储栈、'22 XRP（eBPF 进内核 IO 路径）与 SynCord（用户态定制内核锁）、'26 kSTEP（系统研究 Linux CPU 调度器 bug）、Xkernel（内核性能常量在线可调）、(M)Waiting（超售云 idle 治理）。eBPF 已成内核可编程性标准载体（XRP → PeeR → Virtualizing eBPF）。
3. **CXL/分层内存浪潮**：'23 Johnny Cache 起 CXL 成为主线议题，'24–'26 每届 6–10 篇（页迁移、TLB、地址空间重构、跨机共享、stall 收割）。页面放置/迁移与 NUMA balancing、内存 cgroup 的交互对内核内存管理是直接输入。
4. **集群调度重心迁移**：DL 训练调度（Gandiva '18 → Pollux '21）→ 推理 serving（Orca '22 起 continuous batching）→ LLM/RL（'24–'26 占比最大）。OSDI '26 论文数暴涨至 136 与此直接相关。
5. **混部（harvesting/colocation）贯穿十年**：'16 spare cycles → '20 Azure harvesting VMs → '26 serverless 混部。核心问题始终是干扰隔离与 SLO——正是 cgroup/调度器的主场。
6. **国产力量崛起**：上交 IPADS 持续产出（REEF/XSched/MITOSIS/StriaTrace/kSTEP 合作等）；华为三篇（BWoS '23、HongMeng '24、jwmalloc '26）；'26 最佳论文首次由大陆机构第一单位获得（中科大/字节）。

## 六、内核调度方向推荐阅读 Top 12

1. **kSTEP**（'26）— Linux CPU 调度器 bug 的系统刻画与确定性测试，最直接以主线调度器为对象。
2. **Caladan**（'20）— 微秒级核仲裁与干扰消除的标杆，直接对标内核调度器能力边界。
3. **Arachne**（'18）— 用户态核管理，与内核调度器的职责之争。
4. **What Are You (M)Waiting For**（'26）— 超售云 idle/C-state 的代价与治理。
5. **Xkernel**（'26）— 内核性能参数（含调度参数）的在线安全调优。
6. **Core Slicing**（'23）— 核划分隔离，cpuset 思想在机密计算的应用。
7. **vBOIDs**（'26）— 容器粗粒度调度抽象与两级均衡。
8. **MSH**（'24）+ **LiteSwitch**（'26）— 微架构感知：软件收割内存 stall 周期。
9. **Surviving the Impossible Trinity**（'26）— 移动端大小核 + 交互感知调度。
10. **XSched**（'25）— 异构 XPU 统一抢占调度。
11. **PeeR**（'26）— eBPF 程序纳入调度器一等公民。
12. **Breakwater**（'20）— 过载控制即调度：准入控制保尾延迟。

## 数据来源

- [OSDI '16 Technical Sessions](https://www.usenix.org/conference/osdi16/technical-sessions) / [OSDI '18](https://www.usenix.org/conference/osdi18/technical-sessions) / [OSDI '20](https://www.usenix.org/conference/osdi20/technical-sessions) / [OSDI '21](https://www.usenix.org/conference/osdi21/technical-sessions) / [OSDI '22](https://www.usenix.org/conference/osdi22/technical-sessions) / [OSDI '23](https://www.usenix.org/conference/osdi23/technical-sessions) / [OSDI '24](https://www.usenix.org/conference/osdi24/technical-sessions) / [OSDI '25](https://www.usenix.org/conference/osdi25/technical-sessions) / [OSDI '26](https://www.usenix.org/conference/osdi26/technical-sessions)
- 录用数交叉验证：[北大 OSDI '20 接收新闻（70/398）](https://eecs.pku.edu.cn/xxkxjsxy/info/1023/10686.htm)、[USTC OSDI '26 最佳论文新闻](http://news.ustc.edu.cn/info/1055/95731.htm)、[IPADS OSDI '26 接收新闻](https://ipads.sjtu.edu.cn/zh/news/)
