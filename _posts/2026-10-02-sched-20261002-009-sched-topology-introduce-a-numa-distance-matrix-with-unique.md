---
id: sched-20261002-009
date: '2026-10-02'
subject: 'sched/topology: Introduce a NUMA distance matrix with unique distance values'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <8a0c239b5bdf40c99b645087dec8fd18@hygon.cn>
lore_url: https://lore.kernel.org/all/2a120db1b0c052eb88dcbc2ed1de6027a16542b4.camel@linux.intel.com/
authors:
- Jianyong Wu
maintainers_involved: []
current_version: v2
patch_series:
- version: v2
  msgid: <8a0c239b5bdf40c99b645087dec8fd18@hygon.cn>
  date: '2026-10-02'
  summary: 23 补丁 RFC v2 的 02/23：NUMA 距离矩阵（讨论线）
  review_outcome: 10-02 Tim 质疑 affinity bias 扭曲得分，作者接受移除、改用位置差平局决胜
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - v3 未发出
  - 系列整体缺跨平台收益数据
  next_action: 按三元组全序+无 bias 打分发 v3 并补数据
contribution_opportunities:
- kind: discussion
  description: 分析位置差决胜是否引入系统性节点 id 偏好
- kind: testing
  description: 海光多节点机型收益对比
generated_at: '2026-10-03T01:00:00'
source_email_count: 1
related_articles:
- sched-20260901-004
- sched-20260923-006
- sched-20260924-008
- sched-20260928-009
tags:
- numa
- topology
- load_balance
title: 'sched/topology: Introduce a NUMA distance matrix with unique distance values'
layout: article
---

> **subject**：`sched/topology: Introduce a NUMA distance matrix with unique distance values`

## TL;DR

本文为增量更新，完整脉络见 related_articles（Jianyong Wu（海光）23 补丁 RFC「NUMA/LLC 两级亲和性打分负载均衡」的持续评审）。

- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-006-sched-topology-introduce-a-numa-distance-matrix-with-unique.html">sched-20260923-006</a>：Tim Chen 提 `llc_next` 数组替代人造 LLC 距离矩阵，路线未收敛。
- <a class="article-ref" href="/lkm/2026/09/24/sched-20260924-008-sched-topology-introduce-a-numa-distance-matrix-with-unique.html">sched-20260924-008</a>：分歧收敛到「去重矩阵必要性」——Tim 主张 raw distance + 平局决胜即可，Jianyong 坚持去重是为强制对称性。
- <a class="article-ref" href="/lkm/2026/09/28/sched-20260928-009-sched-topology-introduce-a-numa-distance-matrix-with-unique.html">sched-20260928-009</a>：Jianyong 让步——提出 `(distance, abs(node_id_i - node_id_j), min(i, j))` 三元组构造全序、无需发明新距离值，并表示「let me try to remove this artificial node distance」。
- <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-009-sched-topology-introduce-a-numa-distance-matrix-with-unique.html">sched-20261002-009</a>（今天）：Tim Chen 继续做减法——质疑打分式里新加的 `affinity_bias_i`：「Do we really need an affinity bias?」其用途只是打破平局，直接用位置差（position diff）做 tie-break 即可，「Having a bias distorts the affinity score」；作者回复接受（Tim 的回帖引用了作者的「That's fine.」），bias 项将从打分式中移除。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/28/sched-20260928-009-sched-topology-introduce-a-numa-distance-matrix-with-unique.html">sched-20260928-009</a>）上游 cache-aware 负载均衡只在 LLC 粒度决策，跨 NUMA 节点放置交给独立的 NUMA balancing，二者互不知情；海光这类非全对称互连平台节点间距离非单值，需要区分度。系列 02/23 的去重距离矩阵经三轮收敛已确定改用「三元组全序 + raw distance」；今天讨论的是打分公式的最后一处人造成分：`affinity_bias_i`（src 与 dst 在节点 i 亲和序列中同距离分组内的位置差）被加进 `Di + affinity_bias_i` 打分式，Tim 认为它扭曲了 affinity 得分本身。

## 技术方案

（承接）v2 02/23 的打分式：`p = Σ numa_counts[i] × (Di + affinity_bias_i)`，其中 `Di = raw_dist(src,i) - raw_dist(dst,i)`。今天的收敛：Tim 建议「If there is a tie in affinity score (without injecting bias), just use the position diff to break the tie」——affinity 得分保持纯净（只用 raw distance 差），平局时才用位置差决胜；作者接受（「That's fine.」）。至此打分式与排序两个组件都回到「raw distance 优先、拓扑位置只用于确定性决胜」的统一原则，与 Tim 自 09-23 以来的主张完全一致。

## 版本演进与当前进展

- v1/v2 历史（<a class="article-ref" href="/lkm/2026/09/01/sched-20260901-004-sched-topology-introduce-a-numa-distance-matrix-with-unique.html">sched-20260901-004</a> 起，23 补丁 RFC v2 于 09 月中发出）。
- 09-23 Tim 提 llc_next；09-24 分歧「是否去重」；09-28 Jianyong 让步（三元组全序、去除人造距离）（<a class="article-ref" href="/lkm/2026/09/28/sched-20260928-009-sched-topology-introduce-a-numa-distance-matrix-with-unique.html">sched-20260928-009</a>）。
- 10-02（今天）：Tim（06:04，`<2a120db1b0c052eb88dcbc2ed1de6027a16542b4.camel@linux.intel.com>`，回复 v2 02/23 `<8a0c239b5bdf40c99b645087dec8fd18@hygon.cn>`）质疑 affinity bias；作者同意移除（其回复未进当日缓存，由 Tim 的引用可得）。v3 尚未发出。

## Maintainer 意见与讨论焦点

- **Tim Chen**（Intel，评审者）：连续第四轮做减法——从 llc_next → raw distance + tie-break → 三元组全序 → 去掉 affinity bias，一致性原则始终是「不注入人造偏置，保序靠确定性决胜」。
- **Jianyong Wu**（海光，作者）：逐轮接受简化，打分式与排序设计均已向 Tim 方案收敛。
- **Peter Zijlstra**：当日无表态；此前的 `__build_all_zonelists()` 联动、着色上界等 open 项仍未决。
- 焦点几乎收敛完毕：剩 v3 落地与系列整体（23 补丁）的跨平台收益背书。

## 合入评估

*likelihood=unknown*。02/23 的设计争论基本收束（今天移除最后一个偏置项），但 v3 未发、23 补丁架构性 RFC 的其余部分（着色上界、zonelists 联动）与跨平台数据缺口依旧。*blocking_issues*：v3 未发出；系列整体缺跨平台收益数据。*next_action*：作者按「三元组全序 + 无 bias 打分式」发 v3，补跨平台数据。

## 效果评估

本日无性能数据；属设计论证收尾（移除 bias 项），无实测。

## 我可以参与的点

- `discussion`：评估移除 `affinity_bias_i` 后「平局 + 位置差决胜」在非对称互连上的行为——位置差是否会在等距节点间引入系统性的节点 id 偏好（小 id 恒胜），给出分析帮助 v3 前定案。
- `testing`：海光多节点机型上开/关系列的 NUMA 亲和收益对比——系列最缺的仍是跨平台收益背书。

## 参考链接

- Tim 质疑 affinity bias: https://lore.kernel.org/all/2a120db1b0c052eb88dcbc2ed1de6027a16542b4.camel@linux.intel.com/
- v2 02/23（被回复的补丁）: https://lore.kernel.org/all/8a0c239b5bdf40c99b645087dec8fd18@hygon.cn/
