# sched/fair: Allow load balancing between CPUs of identical capacity

# sched/fair: 允许相同 capacity 的 CPU 间负载均衡（v6）

## 摘要

Ricardo Neri（Intel）的系列推进到 **v6**：放宽 `load_balance()` 的「异构 capacity 才均衡」限制，允许**相同 capacity 的 CPU 之间**也做负载均衡，以解决 Hybrid（大小核）/非对称平台上的负载粘滞问题。

要点：
- **v6 变化（来自 review）**：Vincent 要求把「相同 capacity 才允许均衡」的判断收敛到 `sd->flags` 与 `sd_llc` 的既有容量比较逻辑，避免新增独立分支；Christian 建议补充「仅当 LLC 内存在 capacity 差异时才启用」的 gate，防止在纯对称平台上引入多余均衡开销。
- 背景：当某域所有 CPU capacity 相同（或差异被 `SD_ASYM_CPUCAPACITY` 标记排除）时，当前 `load_balance` 会跳过该域的均衡，导致任务在 busy 核上粘滞、不被搬到同 capacity 的 idle 核。
- v6 还包含对 `update_sd_lb_stats()` 的 `group_has_spare` 判定微调，使其在对称子域也正确识别 spare capacity。

## 技术细节

v6 思路（示意）：
```
// 在 load_balance 入口放宽
if (!sd_has_asym_capacity(sd) && !sd_flag_test(SD_BALANCE_IDENTICAL))
    goto out_balanced;     // 旧：直接跳过
// 新：允许相同 capacity 子域均衡
```

Vincent 的收敛建议：复用 `sd->flags & SD_ASYM_CPUCAPACITY` 判断，而非新增 `identical_capacity` 概念，保持逻辑统一。

## 影响与风险

- 影响面：`load_balance()` 在对称/异构混合拓扑上的均衡行为；Hybrid 平台上把任务从 busy 同-capacity 核搬到 idle 同-capacity 核，改善利用率。
- 风险：中。放宽均衡可能在某些对称平台上增加均衡扫描频率（微小开销）；需 `SD_BALANCE_IDENTICAL` 之类 gate 避免回退。
- 收益：消除「同 capacity 核间任务粘滞」，在大小核平台上更均衡。

## 评价

方向合理（解决真实 Hybrid 粘滞），reviewer（Vincent/Christian）已给出收敛建议。合入可能性中等，建议落实 Vincent 的「复用既有 flag」与 Christian 的「对称平台 gate」后推进。属 feature，仍处 review。

---
subject: "sched/fair: Allow load balancing between CPUs of identical capacity"
id: sched-20260806-013
date: "2026-08-06"
title: "sched/fair: 允许相同 capacity 的 CPU 间负载均衡（v6）"
series: "sched/fair: Allow load balancing between CPUs of identical capacity"
type: feature
status: under_review
severity: none
merge_likelihood: medium
tags: [cfs, load_balance, topology]
authors: ["Ricardo Neri <ricardo.neri-calderon@linux.intel.com>", "Vincent Guittot <vincent.guittot@linaro.org>", "Christian Loehle <christian.loehle@arm.com>"]
reviewers: ["Vincent Guittot <vincent.guittot@linaro.org>", "Christian Loehle <christian.loehle@arm.com>"]
related_articles: []
emails: ["uid-23679@qq-imap"]
---
