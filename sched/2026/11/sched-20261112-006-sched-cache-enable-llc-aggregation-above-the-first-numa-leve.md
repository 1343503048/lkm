# sched/cache: Enable LLC aggregation above the first NUMA level

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261105-008：Jianyong Wu（Hygon）的 v1 修复 cache-aware 调度里 `group_llc_balance` 在第一层 NUMA 之上不可达的缺陷——任务一旦落到第一层 NUMA 之外就不会再被拉回首选 LLC。Intel 的 Tim Chen 给 busiest_llc_balance 重构、Chen Yu 质疑「fix vs 增强」定位并要求补 benchmark。
- sched-20261112-006（今天）：**v2 发出**——采纳 Tim Chen 的重构（条件拆成两个显式测试并把 llc_balance 检查收进 `sched_cache_enabled()` 门控的 `busiest_llc_balance()` helper）、按 Chen Yu 要求补了 NUMA balancing 开/关的 schbench/hackbench 数据、并把标题从「Fix」改为「Enable」并 drop `Fixes:` 标签。schbench p99 唤醒延迟 3/4 线程下单 LLC 聚合率从 53-80% 提到 97-100%，延迟改善 15.5%-26.7%。

## 背景与问题

（承接 sched-20261105-008）`sched_balance_find_src_group()` 只有在 `sds.prefer_sibling` 置起时才考虑 `group_llc_balance`，而 `prefer_sibling` 镜像的是 busiest group 子调度域的 `SD_PREFER_SIBLING`，`sd_init()` 在每个 SD_NUMA 域上清掉该标志。于是任何「子域本身是 NUMA 域」的多层 NUMA 系统（如每 socket 多 NUMA node）上，被 `llc_balance()` 打上 `group_llc_balance` 标记的 group 永远走不到 `force_balance` 路径，落在第一层 NUMA 之外的任务不会被拉回首选 LLC。此为「增强」而非「修复」：此前 NUMA 层任务聚合被禁用。作者同事 Yibin Liu 发现并报告（Reported-by）。

## 技术方案

v2 关键变化（采纳 Tim Chen / Peter 早期意见）：「只对 `sibling_imbalance()` 情形要求 `sds.prefer_sibling`（这是它最初引入的目的）」，把条件拆成两个显式测试，`llc_balance` 那条 gate 在 `sched_cache_enabled()` 之后（helper `busiest_llc_balance()`），使非 cache-aware 场景不读 group type，`CONFIG_SCHED_CACHE` 关闭时该检查在编译期消失。相比 v1 单条件判断，更清晰也更便宜。

## 版本演进与当前进展

*current_version: v2（2026-11-12，`<20261112065445.592968-1-wujianyong@hygon.cn>`）*。v1→v2：① 条件拆两测试、llc_balance 收进 `sched_cache_enabled()` 门控的 `busiest_llc_balance()`（Tim Chen）；② 补 NUMA balancing 开/关的 schbench/hackbench（Chen Yu）；③ 标题 From「Fix」改「Enable」、drop `Fixes:`（Chen Yu）。`Reported-by: Yibin Liu`、`Suggested-by: Tim Chen`。

## Maintainer 意见与讨论焦点

无调度维护者当日直接表态。前一轮（20261105-008）两位 Intel 调度工程师的评审已全部落实：Tim Chen 的 `busiest_llc_balance()` 重构被采纳；Chen Yu 要求的 benchmark 与定位改写（drop Fixes、标题改 Enable）已补齐。当前无未解决分歧，等待 cache-aware 维护者（Peter/Ingo）对 v2 的正式评审。

## 合入评估

*likelihood=medium*。v2 已回应上一轮全部评审意见并带完整 benchmark，方向获 Intel 侧积极背书；但 patch 触及负载均衡核心路径的判断条件，尚需调度维护者确认。*blocking_issues*：无硬阻塞；待维护者对 v2 评审。*next_action*：等待调度维护者评审 v2；作者已给出多层 NUMA 系统上的收益与无回归数据作为支撑。

## 效果评估

Hygon 2 socket / 每 socket 4 NUMA node / 每 node 4 LLC / 每 LLC 4 core / SMT-2 机器（baseline fb7bd3a2aad7，aggr_tolerance 调为 2、C2 关闭以凸显差异，schbench `-m 1 -t 3/4 -r 30 -i 100` 各 30 跑）。p99 唤醒延迟（相对 baseline）：NUMA balancing 开时 3 线程 -21.9%、4 线程 -25.8%；关时 -15.5%、-26.7%。所有线程同处一个 LLC 的聚合率：开时 80%→97%（3t）/60%→97%（4t）、关时 80%→100%（3t）/53%→100%（4t）。hackbench 与其余 schbench 配置（默认 aggr_tolerance=1、C2 开）显示无显著回归（个别配置 ±3% 以内噪声）。

## 我可以参与的点

- **testing**：在 Intel SNC 或 AMD NPS 等多层 NUMA 系统上复测 v2，重点验证 `busiest_llc_balance()` 门控后非 cache-aware 配置的行为无变化、且多层 NUMA 下任务能被拉回首选 LLC。
- **review**：核对「只对 sibling_imbalance 要求 prefer_sibling」的语义拆分是否与原 `force_balance` 判定严格等价（在单层 NUMA / SNC 系统上无行为改变）。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261112065445.592968-1-wujianyong@hygon.cn/
- v1: https://lore.kernel.org/all/20261104141313.185433-1-wujianyong@hygon.cn/

---
id: sched-20261112-006
date: '2026-11-12'
subject: "sched/cache: Enable LLC aggregation above the first NUMA level"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261112065445.592968-1-wujianyong@hygon.cn>"
lore_url: "https://lore.kernel.org/all/20261112065445.592968-1-wujianyong@hygon.cn/"
authors: [Jianyong Wu]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v1
    msgid: "<20261104141313.185433-1-wujianyong@hygon.cn>"
    date: '2026-11-04'
    summary: "让 group_llc_balance 在第一层 NUMA 之上可达"
    review_outcome: "Tim Chen 给重构、Chen Yu 要求 benchmark 与定位改写"
  - version: v2
    msgid: "<20261112065445.592968-1-wujianyong@hygon.cn>"
    date: '2026-11-12'
    summary: "采纳 busiest_llc_balance 重构、补 benchmark、标题改 Enable 并 drop Fixes"
    review_outcome: "上一轮意见全部落实，待维护者评审"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: "等待调度维护者评审 v2"
contribution_opportunities:
  - kind: testing
    description: "在 SNC/NPS 多层 NUMA 系统复测 v2 并验证非 cache-aware 配置行为不变"
  - kind: review
    description: "核对 prefer_sibling 拆分与 force_balance 判定是否在单层 NUMA/SNC 系统上等价"
generated_at: "2026-11-13T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261105-008]
tags: [load_balance, numa_balancing, topology]
---