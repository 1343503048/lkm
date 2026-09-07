---
id: sched-20260902-009
date: '2026-09-02'
subject: 'sched/cache: Introduce helpers for task migration decisions'
subsystem: sched
type: feature
status: under_review
severity: medium
thread_root_msgid: null
lore_url: null
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: null
authors:
- Jianyong Wu
- Tim Chen
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: low
  blocking_issues:
  - Peter Zijlstra 对 02/23、11/23、17/23 的意见仍在答复循环，未见认可
  - 23 补丁的 RFC 体量未拆分，无法单独评审
  - 热路径开销与 NUMA 均衡收益均无实测数据
  next_action: 在多 NUMA 机器上给出 11/23 helper 的开销数据与 17/23 的均衡效果，并回答 Peter 的建模质疑
contribution_opportunities:
- 在 4P/8P 或 Hygon 多 NUMA 平台跑 NUMA balancing 回归并回报独立测试结果
- 量化 RFC v2 11/23 迁移决策 helper 的热路径开销
- 跟进 nr_pref_llc_running 比较对象的未决问题（72353 线程），与 003/009 交叉
source_email_count: 4
related_articles: []
tags:
- sched/cache
- load_balance
title: 'sched/cache: Introduce helpers for task migration decisions'
layout: article
---

## TL;DR

23 补丁的 RFC v2（Jianyong Wu, Hygon），把 cache-aware 调度与细粒度 NUMA 均衡合成一套「唯一化 NUMA
距离矩阵 + 迁移决策 helper」框架。9/1~9/2 由 Peter Zijlstra 逐子补丁质疑、作者批量答复，9/3 Tim Chen
加入。离收口还远，但方向上有维护者在认真看。

## 背景与问题

这是一个较大的 RFC 系列（v2，共 23 个补丁），方向是 **NUMA 细粒度均衡** 与
**sched/cache 任务迁移决策辅助**。邮件中可见的子补丁讨论：02/23 引入具有唯一距离值的
NUMA distance matrix（UID 73108）、11/23 引入任务迁移决策的辅助函数（72903/72950）、
17/23 细粒度 NUMA 均衡（73045）。

## 技术方案

- 02/23 `sched/topology: Introduce a NUMA distance matrix with unique distance values`
- 11/23 `sched/cache: Introduce helpers for task migration decisions`
- 17/23 `sched/fair: Fine-granularity NUMA balancing`
- （其余补丁构成 NUMA 距离建模 + 迁移决策 + 细粒度均衡的完整框架）

## 版本演进与当前进展

- 当前状态：**under_review / RFC 阶段**（v2，体量很大，需多轮评审）。
- 合入可能性 low/medium（大 RFC，方向上与 cache-aware 调度、NUMA balancing 演进一致，
  但需解决建模与开销争议）。
- 与 003（sched/cache use-after-free）、007（task_h_load）同属调度核心演进。

## Maintainer 意见与讨论焦点

- Peter Zijlstra 在 9/1 就 02/23、11/23、17/23 分别提了意见（作者回帖引用的 Sent 时间戳：16:48、17:09、
  19:32、20:48），Jianyong Wu 9/2 连发 4 封 RE: 逐条答复（73106 02/23、72902+72942 11/23、73048 17/23）。
  这种「一位评审者密集开炮、作者密集解释」的形态说明分歧是真实的，但缓存里看不到 Peter 的原文意见。
- Tim Chen 9/3 05:11 也回 11/23（75293），作者 9/3 10:04 再答（75677）。
- 作者对现状的自我定位（75293 所引）："Cache-aware scheduling makes migration decisions purely based on
  LLC affinity, allowing moves only toward a task's preferred LLC. This rigid…"（截断）——承认现有实现过于
  刚性，这既是本系列的动机，也是被质疑的起点。无 NAK，也无 Reviewed-by。

## 合入评估

**低（短期）**。这是 RFC，v2 就已经 23 个补丁且仍在膨胀方向。需要先满足：(1) 「唯一距离值 NUMA 距离矩阵」
的建模被 Peter 认可；(2) helper 在热路径上的开销有数字；(3) 系列拆分到可评审粒度。当日无任何 ack 类信号。

## 效果评估

缓存内无数据。RFC v2 的迁移决策 helper 与细粒度 NUMA 均衡都没有给出吞吐/NUMA hint fault 对比。
暂无效果数据。

## 我可以参与的点

- 在 4P/8P 或 Hygon 多 NUMA 机器上跑 NUMA balancing 回归并回报——大 RFC 最缺独立测试者。
- 直接量 11/23 的 helper 开销：Peter 反复问的通常就是热路径成本，目前没人给数字。
- 关注同族问题线程 "sched/fair: which tasks should nr_pref_llc_running be compared against?"
  （Chen Yu 发起，Tim Chen 9/2 04:42 回帖 72353，涉及 Zhan Xusheng）——那条线目前也没人给结论。

## 参考链接

- 003 sched/cache use-after-free mm 访问
- 007 sched/fair 重做 task_h_load
