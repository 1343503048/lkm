---
id: sched-20261029-003
date: 2026-10-29
subject: 'sched: Scale cache-aware aggregation at LLC granularity'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20261029022036.4002331-1-wujianyong@hygon.cn>
lore_url: https://lore.kernel.org/all/20261029022036.4002331-1-wujianyong@hygon.cn/
authors:
- Jianyong Wu
maintainers_involved:
- Peter Zijlstra
current_version: v3
patch_series:
- version: v1
  msgid: null
  date: 2026-06-25
  summary: 23 片 RFC，按 sched domain 边界扩展 cache-aware 聚合
  review_outcome: 首版，方向性问题较多
- version: v2
  msgid: null
  date: 2026-08-27
  summary: 改按 LLC 粒度铺开；新增 node/LLC 距离矩阵、affinity gain、NUMA 迁移 tunable
  review_outcome: Peter Zijlstra 逐片跟读，判掉 numa_counts[]、反对 NUMA/LLC 迁移可分别开关
- version: v3
  msgid: <20261029022036.4002331-1-wujianyong@hygon.cn>
  date: 2026-10-29
  summary: 17 片：三角数亲和序列替代距离矩阵，简化迁移决策，删利用率估算与 NUMA tunable
  review_outcome: RFC v3 刚发，尚无当日回帖
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - NUMA balancing 与 cache-aware 迁移的优先级/协同未定型（作者自述 issue not completely resolved）
  - hackbench/schbench 多处可复现回退待归因
  next_action: 解决 NUMA balancing 协同与回退归因后，期望 Peter Zijlstra 下一轮 review
contribution_opportunities:
- kind: review
  description: 逐片核对 fair.c 里 affinity gain 与 can_migrate_llcs() 实现、三角数序列在非对称拓扑上的正确性
- kind: testing
  description: 在自有 NUMA 多 LLC 机型复跑 hackbench/schbench，验证 48fds 与 128 线程回退可复现性
- kind: discussion
  description: 就 NUMA balancing 与 cache-aware 迁移的优先级排布给出建议
generated_at: '2026-10-30T09:30:00'
source_email_count: 18
related_articles:
- sched-20260827-002
- sched-20260901-015
tags:
- load_balance
- numa_balancing
title: 'sched: Scale cache-aware aggregation at LLC granularity'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/08/27/sched-20260827-002-sched-scale-cache-aware-aggregation-at-llc-granularity.html">sched-20260827-002</a>（v1）：Jianyong Wu（海光）发 23 片 RFC，把 cache-aware 调度的聚合域从「固定单个 LLC」扩展为「按 LLC 粒度有序铺开」，解决多 NUMA 节点/多 LLC 系统上单 LLC 聚合容量到顶后放置退化的问题。
- <a class="article-ref" href="/lkm/2026/09/01/sched-20260901-015-sched-scale-cache-aware-aggregation-at-llc-granularity.html">sched-20260901-015</a>（v2）：当天该系列 24 封邮件（Peter Zijlstra 12 / 作者 12），PZ 逐片跟读；patch 08 的 `numa_counts[]` 被要求改为按需累加 LLC 计数，patch 17 的「NUMA 与 LLC 迁移可分别开关」被 PZ 明确反对（NUMA 迁移永远优先于 LLC），并给出「把 LLC 的最小前缀铺开原样搬到 node 维度」的方向。
- <a class="article-ref" href="/lkm/2026/10/29/sched-20261029-003-sched-scale-cache-aware-aggregation-at-llc-granularity.html">sched-20261029-003</a>（今天）：作者发 **RFC v3**（收束为 17 片），按 PZ 建议改用**三角数**构建 LLC 亲和序列（废弃人造的 node/LLC 距离矩阵），简化迁移决策、去掉 v2 的负载利用率估算与 NUMA tunable；给出 Hygon + Intel 两套平台的 hackbench/schbench 数据（schbench p99 多档最高 -80%，但 128 线程 Intel 上 -18.48% 回退、hackbench 48fds 上亦有倒退，作者承认需进一步调查）。

## 背景与问题
（承接 v1/v2）现有 cache-aware 实现是 **LLC 中心的聚合模型**：任务聚到 preferred LLC，装不下才外溢，聚合范围固定、无法跨 LLC 扩展。在多 NUMA/多 LLC 系统上单 LLC 可能只有 4 核，聚到单个 LLC 收益有限。把线程组跨 LLC/NUMA 聚合可降低 cache-to-cache 通信延迟；若内存跟随线程放置，还能降低远端内存访问延迟、提升有效带宽。Peter Zijlstra 给出「按 LLC 粒度扩展资源」的方向，本系列即其实现。

## 技术方案
（承接 v2，v3 变化）核心问题有二：preferred LLC 饱和后往哪个 LLC 摊负载？线程组沿这个顺序铺多远？v3 的做法：

- **亲和序列用三角数决胜**（v3 相对 v2 的关键变化）：node 层按节点距离排序、用三角数破平；LLC 层 cache-preferred node 内用三角数、跨 node 用 LLC ID。序列在系统初始化时预生成、拓扑不变则固定。**废弃 v2 的人造 node 距离矩阵与 LLC 距离矩阵**，affinity gain 改为只用原始 node 距离作权重（否则权重为 1）。
- **两步迁移**：① 找能给最大 affinity gain 的 source rq/group（新增 rq 亲和增益计算）；② 用 `can_migrate_llcs()` 替换 `can_migrate_llc()` 支持跨 LLC 迁移判定。
- **简化**：去掉 v2 的整线程组利用率估算（聚合范围推导）、去掉 v2 的 NUMA 迁移 tunable、不再限制 NUMA balancing 的任务迁移。
- **与 NUMA balancing 的协同仍是难点（作者明说未完全解决）**：改为在组内所有有效 preferred NUMA node 之间选 preferred LLC 以降争用、稳定 preferred LLC，并放宽部分绑定 preferred NUMA node 的迁移限制——但 preferred NUMA node 落在聚合范围外的任务仍可能「游走」。

## 版本演进与当前进展
*current_version: v3 (RFC)*（2026-10-29，cover `<20261029022036.4002331-1-wujianyong@hygon.cn>`）。17 片（1–5 拓扑基础设施、6–16 sched/cache 迁移决策、17 debug 展示 preferred LLC），diffstat `1400 insertions(+), 176 deletions(-)`，base-commit `0f23d56f17fd`。

- **v3 相对 v2**：三角数亲和序列替代人工距离矩阵；简化迁移决策；去掉利用率估算；不再限制 NUMA balancing 迁移并删 v2 tunable；吸收 v2 其余 review。
- **v2 相对 v1**：不再按 sched domain 边界摊（改为 LLC）；新增无重复值的 node 距离矩阵与 node 内 LLC 距离矩阵（本版被三角数替代）；改 affinity gain 与迁移许可算法；修 schbench 饱和bug；按 Chen Yu 建议加 NUMA 迁移开关（本版删除）。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra（维护者）**：方向是他定的（「按 LLC 粒度扩展资源」）；v2 阶段明确反对 patch 17 的「NUMA task/page 迁移可分别开关」——「无论何时 NUMA 迁移都应优先于 LLC，远端 node 代价远大于 other-LLC；单独禁用 page 或 task 迁移会把事情搞乱，还不如直接关 NUMA balancing」，并给替代方向「若进程跨多 node，则按本系列对 LLC 做的同样方式，在最小可容纳 node 集合上 spread/interleave」。v3 已据此删除该 tunable。
- 作者在封面明确承认 NUMA balancing 协同「issue is not completely resolved yet」——这是当前最大的开放分歧。
- 今日 RFC v3 刚发，尚无当日回帖。

## 合入评估
*likelihood=low*。方向获 PZ 背书是最大加分项，但系列属大体量 RFC（17 片、+1400 行、动 `kernel/sched/fair.c` 883 行），且作者自述 NUMA balancing 协同未解决、两组测试均有可复现回退。*blocking_issues*：NUMA balancing 与 cache-aware 迁移的优先级/协同未定型；hackbench（Hygon 48fds 2组 -2.01%/-6.90%，Intel 24fds 1组 -7.94%、48fds 2组 -2.62%）与 schbench（Intel 128线程 -18.48%）回退待解释；RFC 无正式 Ack。*next_action*：作者先解决 NUMA balancing 协同与回退归因，再期望 PZ 下一轮 review。

## 效果评估
作者给出两套平台数据（baseline `0f23d56f17fd`，NUMA balancing 关闭，均 10 次取均值，括号内标准差占均值百分比）：

- **Hygon（2 socket × 4 NUMA × 4 LLC × 4 core × 2 SMT）**：hackbench 大部分档位提升（4fds/2groups -38.92%、8fds/1group -41.87%、12fds/1group -34.24%），但 48fds 两档 -2.01%/-6.90%；schbench p99 wakeup 延迟 11 档全提升，32/48 线程约 -80%，且 7/11 档 run-to-run 方差更低。
- **Intel Xeon Platinum 8592+（2 socket，每 socket 2 sub-NUMA，1 LLC/socket）**：hackbench 15/18 档提升（最高 fds=20/groups=2 -26.12%），回退在 fds=24/groups=1（-7.94%）等处；schbench 128 线程 -18.48% 回退且方差变大。
- 作者自评：两组回退「需要进一步调查」，且 baseline 在部分测试中并未稳定把线程聚在单 LLC，可能放大其延迟——归因仍是开放问题。

## 我可以参与的点
- **review**：这个系列正好与你关心的 cache-aware 负载均衡方向强相关，可逐片核对 `kernel/sched/fair.c` 里 affinity gain 计算与 `can_migrate_llcs()` 的实现是否正确（尤其三角数序列在非对称拓扑上的正确性）。
- **testing**：在自有 NUMA 多 LLC 机型上复跑 hackbench/schbench，重点验证 48fds 与 128 线程的回退是否可复现，回帖作者。
- **discussion**：NUMA balancing 协同是作者点名的开放问题，可结合 pghot/现有 tiering 讨论给出「二者优先级如何排布」的建议。

## 参考链接
- lore thread（RFC v3 cover）: https://lore.kernel.org/all/20261029022036.4002331-1-wujianyong@hygon.cn/
- v2: https://lore.kernel.org/all/20260827122816.756234-1-wujianyong@hygon.cn/
- v1: https://lore.kernel.org/all/20260625030759.25928-1-wujianyong@hygon.cn/
