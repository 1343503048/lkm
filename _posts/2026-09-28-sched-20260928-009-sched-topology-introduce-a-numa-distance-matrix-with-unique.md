---
id: sched-20260928-009
date: '2026-09-28'
subject: 'sched/topology: Introduce a NUMA distance matrix with unique distance values'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20260827122816.756234-1-wujianyong@hygon.cn>
lore_url: https://lore.kernel.org/all/8a0c239b5bdf40c99b645087dec8fd18@hygon.cn/
authors:
- Jianyong Wu
maintainers_involved:
- Tim Chen
current_version: v2
patch_series:
- version: v2
  msgid: <20260827122816.756234-1-wujianyong@hygon.cn>
  date: '2026-08-27'
  summary: 23 枚：NUMA 距离矩阵 + LLC 距离小矩阵 + affinity 打分
  review_outcome: 02/23 去重矩阵向三元组全序收敛，作者拟移除人造距离
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 三元组全序 + 新打分式尚未经 Tim/Peter 确认
  - 系列整体仍缺跨平台收益数据与 v3
  next_action: 作者按三元组全序方向改出 v3 并补跨平台收益
contribution_opportunities:
- kind: discussion
  description: 分析三元组全序与顺序打分对负载均衡正确性的影响
- kind: testing
  description: Hygon 多节点机型上给出该系列 NUMA 亲和收益对比数据
generated_at: '2026-09-29T01:00:00'
source_email_count: 1
related_articles:
- sched-20260924-008
- sched-20260923-006
tags:
- topology
- numa_balancing
- load_balance
title: 'sched/topology: Introduce a NUMA distance matrix with unique distance values'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。这是 Jianyong Wu（海光）23 补丁 RFC（NUMA/LLC 两级亲和性打分负载均衡）的持续评审。

- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-006-sched-topology-introduce-a-numa-distance-matrix-with-unique.html">sched-20260923-006</a>：Tim Chen 提 `llc_next` 数组替代人造 LLC 距离矩阵，路线未收敛。
- <a class="article-ref" href="/lkm/2026/09/24/sched-20260924-008-sched-topology-introduce-a-numa-distance-matrix-with-unique.html">sched-20260924-008</a>：分歧收敛到「去重矩阵必要性」——Tim 主张 raw distance + 平局决胜即可，Jianyong 坚持去重是为强制对称性，唯一 open 点是「对称是否必需」。
- <a class="article-ref" href="/lkm/2026/09/28/sched-20260928-009-sched-topology-introduce-a-numa-distance-matrix-with-unique.html">sched-20260928-009</a>（今天）：Jianyong 在对称性问题上做出实质让步——提出用三元组 `(distance, abs(node_id_i - node_id_j), min(i, j))` 构造全序即可保证对称与去重、无需发明新距离值，并表示「let me try to remove this artificial node distance」，同时给出不依赖距离幅度的 affinity 打分式（`Di + affinity_bias_i`）。路线向 Tim 方案收敛。

## 背景与问题

（承接）上游 cache-aware 负载均衡只在 LLC 粒度决策，跨 NUMA 节点放置交给独立的 NUMA balancing，二者互不知情。该系列给拓扑加一张去重后的 NUMA 距离矩阵，让每个节点距离值互不相同，供负载均衡按「任务数 × 距离差」算 affinity 得分。海光这类非全对称互连平台节点间距离非单值，需要区分度。今天背景无新增，焦点仍是 02/23 去重矩阵的必要性与对称性。

## 技术方案

（承接 + 今日更新）Tim Chen 前几轮主张：排序只需确定性全序（raw distance + node_id 决胜）、打分需要真实幅度（raw distance），二者都可用未修改的 distance 完成。今天 Jianyong 部分接受：
- 排序：用三元组 `(distance, abs(node_id_i - node_id_j), min(i, j))` 构造全序，第三分量保证确定性，从而「无需发明新距离值」即可去重与对称。
- 打分：affinity 得分用 `p = Σ numa_counts[i] × (Di + affinity_bias_i)`（仅保留 `Di + affinity_bias_i > 0` 项），其中 `Di = raw_dist(src,i) - raw_dist(dst,i)`、`affinity_bias_i` 为 src 与 dst 在节点 i 亲和序列中同距离分组内的位置差；并倾向固定顺序而非让负载决定（避免负载波动导致任务被反复拉回）。

## 版本演进与当前进展

*current_version: v2*（仍无新版）。本日为 02/23 去重矩阵「对称性」路线讨论的收敛——作者明确「let me try to remove this artificial node distance」，朝简化方向让步。

## Maintainer 意见与讨论焦点

- **Tim Chen（Intel）**：核心反对人造去重距离（只在等距对上制造虚假偏置），主张 raw distance + 平局决胜、偏置单独施加（前几轮观点，本轮被部分采纳）。
- **Jianyong Wu（作者）**：今日让步，接受用三元组全序替代去重矩阵，并解释 affinity 打分可用顺序（而非距离幅度）驱动。
- 无 Peter Zijlstra 本日新表态。分歧从「是否去重」收敛为「三元组 + 打分式」的细节确认。

## 合入评估

*likelihood=unknown*。23 枚架构性 RFC 仍处早期评审，02/23 已朝简化收敛但尚未出 v3；此前 Peter 的 `__build_all_zonelists()` 联动、着色上界等 open 项依旧未决。*blocking_issues*：三元组全序 + 新打分式尚未经 Tim/Peter 确认；系列整体仍缺跨平台收益数据与 v3。*next_action*：作者按今日收敛的方向（去除人造距离、三元组全序）改出 v3，并补充跨平台收益背书。

## 效果评估

本日无性能数据；属设计论证层面的收敛（三元组全序 + 打分式），无实测。

## 我可以参与的点

- `discussion`：就「三元组全序是否等价替代去重矩阵」与「affinity 打分式用顺序 vs 距离幅度」是否影响负载均衡正确性给出分析，帮助双方在 v3 前对齐。
- `testing`：若手上有 Hygon 多节点机型，给出开启/关闭该系列的 NUMA 亲和收益对比——整个系列最缺的仍是跨平台收益背书。

## 参考链接

- Jianyong 今日回复: https://lore.kernel.org/all/8a0c239b5bdf40c99b645087dec8fd18@hygon.cn/
- v2 封面: https://lore.kernel.org/all/20260827122816.756234-1-wujianyong@hygon.cn/
