---
id: sched-20260916-015
date: '2026-09-16'
subject: 'sched/fair: Randomize equally shallow idle CPU picks'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260916100116.701206-1-christian.loehle@arm.com>
lore_url: https://lore.kernel.org/all/20260916100116.701206-1-christian.loehle@arm.com/
authors:
- Christian Loehle
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260916100116.701206-1-christian.loehle@arm.com>
  date: '2026-09-16'
  summary: 去掉 idle-recency 偏好并用 reservoir sampling 随机化等 latency 候选
  review_outcome: Kayra / Sashiko 关切已回应，设计分歧待收敛
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 小核数系统收益与随机不可预测性的设计分歧待收敛
  - 缺调度维护者评审
  next_action: 维护者评审，回应剩余关切
contribution_opportunities:
- kind: testing
  description: 在 8~32 核小系统复测 stress-ng fork 验证收益与回归
- kind: discussion
  description: 评估确定性与随机化方案的取舍与小核数替代思路
generated_at: '2026-09-17T09:00:00'
source_email_count: 7
related_articles: []
tags:
- load_balance
- idle
title: 'sched/fair: Randomize equally shallow idle CPU picks'
layout: article
---

## TL;DR
Christian Loehle（ARM）的两枚新 patch：慢路径 CPU 选择存在扫描顺序偏差，并发的 wakeup 选择器可能收敛到同一个 idle CPU。方案是去掉 idle-recency 偏好、对等 latency 候选用 reservoir sampling 单趟随机化。在 160 核 Altra 上 stress-ng fork 中位数吞吐最多 +4.13%、stale-pick 率近乎减半。Kayra/Sashiko 提出小核数系统与随机不可预测性两个关切，作者已回应。合入可能性中等。

## 背景与问题
慢路径的 idle CPU 选择器（`sched_balance_find_dst_group_cpu()`）按扫描顺序取第一个满足条件者，并用「最近进入 idle」的时间戳作为 cache 温暖的代理来做 tie-break。问题有二：①并发慢路径选择器会在任务 enqueue 前收敛到同一个 idle CPU；②「更新 idle 戳」偏好可能反而选中唤醒成本最高的 CPU（进入无法中止时需完成进入再退出）。作者测试平台（160 核双插槽 Altra）NUMA 层有 80 核的大候选组，尤其容易命中 stale idle pick。

## 技术方案
两枚补丁：patch 1 删除 idle 时间戳 tie-break（若非更低退出延迟，保留第一个 idle 候选）；patch 2 用 per-CPU PRNG + `reciprocal_scale()` 在等延迟分支做 reservoir sampling，重置候选计数（找到更低 exit latency 时），避免可变除法或二次扫描，在不预留选中 CPU 的前提下降低确定性收敛。

## 版本演进与当前进展
- v1（本日 106770，`<20260916100116.701206-1-christian.loehle@arm.com>`）：本日发出后 Kayra Cizmeci 与 Sashiko 立即回复，作者逐一回应。

## Maintainer 意见与讨论焦点
- **Kayra Cizmeci**：担心随机化在小核数系统上效果差——8 核系统 4 空闲时随机选到同一 CPU 的概率比 80 核高，问题只是「更难复现」，未完全消除；并认为随机不可预测、其它方案可预测。作者回应：该问题在 8 核域基本不存在（并发慢路径更少、窗口更小），完全消除需要同步，数字（本已不大）不支持增加慢路径开销。
- **Sashiko（转述）**：担心 `!idle || idle->exit_latency == min_exit_latency` 分支会让后扫描到的 non-idle CPU 以 1/nr_candidates 概率覆盖已选中的最优 idle CPU。作者回应：该分支在 `available_idle_cpu(i)` 的 if 块内，除开原代码也刻意接受的竞态外不成立。
- 无 NAK；设计取舍（随机化 vs 可预测 fallback）仍在讨论。

## 合入评估
likelihood=medium。有扎实的 benchmark 与 stale-pick 数据支撑，方向无反对；但尚无 sched 维护者表态，且随机化在小核数/可预测性上的设计分歧尚未完全闭合。blocking_issues：小核数系统收益与随机不可预测性的设计分歧待收敛；缺维护者评审。next_action：等待 Vincent/Peter 等维护者评审，回应 Kayra/Sashiko 的剩余关切。

## 效果评估
160 核双插槽 Altra，stress-ng 中位数吞吐（bogo ops/s）：`--fork 1/1` +4.13%、`8/1` +0.06%、`16/1` +3.48%、`16/4` +1.81%、`32/1` -0.22%、`64/1` +1.82%。stale-pick 率（最终返回时候选仍忙）：fork 32 creators 0.771%→0.407%，64 creators 1.242%→0.672%。

## 我可以参与的点
- kind=testing：在 8~32 核小系统上复测 stress-ng fork，验证小核数下的收益与潜在回归（作者主要测 160 核）。
- kind=discussion：评估「预留选中 CPU」等确定性方案与随机化的取舍，给出小核数下的替代思路。

## 参考链接
- cover：https://lore.kernel.org/all/20260916100116.701206-1-christian.loehle@arm.com/
- Kayra 的小核数关切：https://lore.kernel.org/all/20260916110603.24230-1-kayracizmeci@gmail.com/
