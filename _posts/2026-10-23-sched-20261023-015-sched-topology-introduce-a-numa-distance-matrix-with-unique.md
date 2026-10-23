---
id: sched-20261023-015
date: 2026-10-23
subject: 'sched/topology: Introduce a NUMA distance matrix with unique distance values'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <8a0c239b5bdf40c99b645087dec8fd18@hygon.cn>
lore_url: https://lore.kernel.org/all/8a0c239b5bdf40c99b645087dec8fd18@hygon.cn/
authors:
- Jianyong Wu
maintainers_involved:
- Tim Chen
- Chen Yu
current_version: v2
patch_series:
- version: v2
  msgid: <854b5714024b4d5b97be916b740ce003@hygon.cn>
  date: 2026-10-23
  summary: v3 预告：node/LLC 两级均无人造距离值，三角数破平
  review_outcome: Tim 减法主张收敛；Chen Yu 的 LLC 简化问尚未最终回应
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 23 补丁大系列无维护者整体表态
  - v3 尚未发出
  next_action: Jianyong 发 v3 并回应 Chen Yu 的 LLC 层简化建议
contribution_opportunities:
- kind: discussion
  description: 就 LLC 层是否需要距离比较给出拓扑/缓存行为依据
- kind: review
  description: v3 发出后复核三角数破平的全序确定性/对称性
generated_at: '2026-10-24T09:14:00'
source_email_count: 1
related_articles:
- sched-20261002-009
- sched-20261008-010
- sched-20261009-010
tags:
- topology
- numa
- load_balance
title: 'sched/topology: Introduce a NUMA distance matrix with unique distance values'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见下（Jianyong Wu（海光）23 补丁 RFC「NUMA/LLC 两级亲和性打分负载均衡」的持续评审）。

- <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-009-sched-topology-introduce-a-numa-distance-matrix-with-unique.html">sched-20261002-009</a>：Tim Chen 继续做减法——质疑打分式里新加的 `affinity_bias_i`：「Do we really need an affinity bias?」其用途只是打破平局，直接用位置差（position diff）做 tie-break 即可；作者回复接受，bias 项将从打分式中移除。
- <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-010-sched-topology-introduce-a-numa-distance-matrix-with-unique.html">sched-20261008-010</a>：Jianyong 澄清「bias 不是为打破 affinity 平分、而是让 score 本身反映聚合机会」，接受 Tim 对人造距离幅度的关切，提出新打分式——源/目的对某 preferred 节点 raw distance 不同时用距离差作权重、距离相等时用固定亲和顺序定 eligibility。
- <a class="article-ref" href="/lkm/2026/10/09/sched-20261009-010-sched-topology-introduce-a-numa-distance-matrix-with-unique.html">sched-20261009-010</a>：Chen Yu（Intel）从「LLC 对称性」切入——距离比较的动机是 NUMA 节点非对称，但 LLC 是对称的，可直接把 preferred LLC 的兄弟加入 preferred_mask、无需距离矩阵；主张至少在 LLC 层去掉距离比较。
- <a class="article-ref" href="/lkm/2026/10/23/sched-20261023-015-sched-topology-introduce-a-numa-distance-matrix-with-unique.html">sched-20261023-015</a>（今天）：Jianyong 回应 Chen Yu——**v3 不再在 node 层或 LLC 层引入任何人造距离值**，平局改用三角数（triangular numbers）打破，从而简化排序。这是继 Tim 多轮「去人造成分」主张后的实质性收敛。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/09/28/sched-20260928-009-sched-topology-introduce-a-numa-distance-matrix-with-unique.html">sched-20260928-009</a> → <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-009-sched-topology-introduce-a-numa-distance-matrix-with-unique.html">sched-20261002-009</a> → <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-010-sched-topology-introduce-a-numa-distance-matrix-with-unique.html">sched-20261008-010</a> → <a class="article-ref" href="/lkm/2026/10/09/sched-20261009-010-sched-topology-introduce-a-numa-distance-matrix-with-unique.html">sched-20261009-010</a>）上游 cache-aware 负载均衡只在 LLC 粒度决策，跨 NUMA 节点放置交给独立的 NUMA balancing，二者互不知情；海光这类非全对称互连平台节点间距离非单值，需要区分度。该系列给拓扑加一张去重后的 NUMA 距离矩阵，供负载均衡按「任务数 × 距离差」算 affinity 得分。今日的收敛点是：Chen Yu 上轮质疑「LLC 层根本无需距离比较」，作者以「v3 全部去掉人造距离值、用三角数打破平局」回应。

## 技术方案
（承接 + 今日更新）历史主线：Tim Chen 一贯主张排序用确定性全序、打分用真实幅度（raw distance），反对任何人造距离/rank 幅度决定聚合机会权重；Jianyong 多轮让步，先后去掉 `affinity_bias`、人造 node 距离。今天的最终答复：**v3 在 node 层与 LLC 层都不再引入人造距离值**，平局用三角数（triangular numbers）决胜、简化排序——即「raw distance 优先、拓扑位置仅用于确定性决胜」原则在 node 与 LLC 两级都落地。

## 版本演进与当前进展
*current_version: v2（RFC 02/23，`<854b5714024b4d5b97be916b740ce003@hygon.cn>` 为今日回帖）*。作者预告 v3 的改动方向（去掉人造距离值、三角数破平），v3 尚未在当日缓存中发出。

## Maintainer 意见与讨论焦点
Tim Chen（贯穿）：坚持 raw distance + 确定性全序，多次要求去掉 bias/人造距离。Chen Yu（上轮）：进一步从 LLC 对称性主张「LLC 层无需距离矩阵」。Jianyong（今日）：接受并归纳为「v3 两个层级都无人造距离、三角数破平」。当前无明确反对意见，方向趋于「最小化人造成分」，但系列规模大（23 补丁）、仍在 RFC 阶段，距离合入尚远。

## 合入评估
*likelihood=unknown*。RFC 早期、23 补丁大系列，核心打分/排序原则多轮收敛良好（已满足 Tim 的减法主张），但尚无维护者明确认可整体方案；LLC 层是否还需矩阵（Chen Yu 之问）尚未见作者最终回应是否简化。*blocking_issues*：系列规模大、无维护者整体表态；v3 尚未发出。*next_action*：Jianyong 发 v3 并回应 Chen Yu 的 LLC 层简化建议。

## 效果评估
无性能数据。讨论聚焦设计原则（人造距离/排序一致性），未涉及 benchmark。

## 我可以参与的点
- *kind: discussion*：就「LLC 层是否需要距离比较、能否直接用 preferred_mask 兄弟」这一 Chen Yu 之问给出拓扑学/缓存行为依据。
- *kind: review*：v3 发出后复核三角数破平的全序性质（确定性/对称性）。

## 参考链接
- Jianyong 回帖: https://lore.kernel.org/all/854b5714024b4d5b97be916b740ce003@hygon.cn/
- 前文: <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-009-sched-topology-introduce-a-numa-distance-matrix-with-unique.html">sched-20261002-009</a> / <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-010-sched-topology-introduce-a-numa-distance-matrix-with-unique.html">sched-20261008-010</a> / <a class="article-ref" href="/lkm/2026/10/09/sched-20261009-010-sched-topology-introduce-a-numa-distance-matrix-with-unique.html">sched-20261009-010</a>
