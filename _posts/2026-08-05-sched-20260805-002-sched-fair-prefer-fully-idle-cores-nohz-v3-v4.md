---
subject: 'sched/fair: Prefer fully idle cores for NOHZ balancing'
id: sched-20260805-002
date: '2026-08-05'
title: 'sched/fair: Prefer fully idle cores for NOHZ balancing'
series: Prefer fully idle cores for NOHZ balancing
type: feature
status: under_review
severity: none
merge_likelihood: high
tags:
- cfs
- load_balance
- nohz
- topology
- hyperthreading
authors:
- Andrea Righi <arighi@nvidia.com>
- Gautham R. Shenoy <gautham.shenoy@amd.com>
- K Prateek Nayak <kprateeknayak@amd.com>
- Peter Zijlstra <peterz@infradead.org>
reviewers:
- Peter Zijlstra <peterz@infradead.org>
- Vincent Guittot <vincent.guittot@linaro.org>
related_articles:
- sched-20260804-005
- sched-20260801-005
- sched-20260730-008
emails:
- uid-22123@qq-imap
- uid-21934@qq-imap
- uid-20997@qq-imap
- uid-20678@qq-imap
layout: article
---

# sched/fair: NOHZ 负载均衡优先 fully idle core（v3/v4 收尾讨论）

## 摘要

Andrea Righi（NVIDIA）的「NOHZ idle load balancer 优先挑选整核全 idle 的 CPU」系列在 08-05 继续推进，收到 v3 → v4 的多方 review 往返。核心诉求不变：**选 ILB（idle load balancer）CPU 时优先选 SMT 兄弟线程都空闲的物理核**，避免 ILB 跑在繁忙 SMT core 的空闲兄弟上而挤占其算力。

本日讨论要点：
- **Peter 对 `cpumask_andnot()` 用法的质疑**：在 `nohz_balancer_kick()` 里选 ILB 时，Peter 质疑把「已运行 task 的 core」从候选集里 `cpumask_andnot` 掉是否必要，担心它改变了 ILB 选择的既有语义（例如 tick 停了的忙碌 CPU 是否仍应被考虑）。
- **Vincent 关注 `sched_smt_active` 的判定时机**：`update_sd_lb_stats()` 里依赖 `sched_smt_active()` 来决定是否调用 `is_core_idle()`，但 `sched_smt_active` 是运行期全局开关，可能在负载均衡过程中变化，需确认判定时点一致。
- **Gautham / Prateek（AMD）确认语义等价**：AMD 侧验证 v3 在 Zen 平台上与既有 `is_core_idle()` 行为一致，没有引入新的 core 选择偏差。
- **`is_core_idle()` 的 SMT 遍历边界**：延续此前 Mete（s390）提出的「`is_core_idle()` 不检查目标 CPU 自身 sibling」的隐患，本日再次被提醒需在 `for_each_cpu` 内正确跳过关心的 CPU本身。

## 技术细节

ILB 选择逻辑（简化）：
```
候选 = housekeeping + nohz
if (sched_smt_active())           // 依赖运行期开关
    去掉「有兄弟在跑 task」的 core
选剩余候选里 idle 等级最高的 CPU 作为 ilb_cpu
```

争议点：
1. `cpumask_andnot()` 是否过度裁剪了候选——Peter 担心把「忙 core 的空闲兄弟」完全排除后，某些本可做 ILB 的 CPU 不再被考虑，可能影响 tickless 场景的均衡及时性。
2. `sched_smt_active()` 在 `update_sd_lb_stats()` 调用路径上的稳定性——它非 per-RQ 快照，存在与其它 CPU 状态不一致的窗口。

实测数据状态：**与之前多版本一样，本日仍未补上新的效果数据**。已知历史数据：无调频噪声下 GEMM 6.2 → 9.4 TFLOP/s（+51%），但加 ibs 噪声后提升消失。

## 影响与风险

- 影响面：仅 NOHZ idle load balancing 的 ILB 选择，单线程/轻线程性能敏感（尤其 SMT 同核上有忙线程时）。
- 风险：中。逻辑改动小，但 `cpumask_andnot` 的语义变更需 maintainer 拍板，否则可能出现「ILB 不选最合适 CPU」的回退。
- 关键短板：**长期缺稳定复现的效果数据**，是当前唯一的明显阻碍。

## 评价

方案本身简单合理、已过多轮打磨、获 Vincent R-b（历史），合入可能性高。本日主要是 maintainer 对边界语义的把关，建议作者在 v4 里直接回应 Peter 的 `cpumask_andnot` 质疑并补一个对比数据（哪怕只在某台固定机器上）。

## 衔接

- 直接延续 08-04-005（v3 已获 Vincent R-b）/ 08-01-005（v3 主线）/ 07-30-008（v2 背景）。
- 与本系列历史归档：`sched/by-tag/nohz` 已累计 10 篇。
