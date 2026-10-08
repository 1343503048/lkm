# sched/topology: Introduce a NUMA distance matrix with unique distance values

## TL;DR

本文为增量更新，完整脉络见 related_articles。这是 Jianyong Wu（海光）23 补丁 RFC（NUMA/LLC 两级亲和性打分负载均衡）的持续评审。

- sched-20260923-006：Tim Chen 提 `llc_next` 数组替代人造 LLC 距离矩阵，路线未收敛。
- sched-20260924-008：分歧收敛到「去重矩阵必要性」——Tim 主张 raw distance + 平局决胜即可，Jianyong 坚持去重是为强制对称性。
- sched-20260928-009：Jianyong 在对称性上让步，提出三元组 `(distance, abs(node_id_i - node_id_j), min(i, j))` 全序即可保证对称与去重、无需发明新距离值，并给出不依赖距离幅度的 affinity 打分式。
- sched-20261008-010（今天）：Jianyong 澄清「bias 不是为打破 affinity 平分、而是让 score 本身反映聚合机会」，接受 Tim 对人造距离幅度的关切，提出新打分式——源/目的对某 preferred 节点 raw distance 不同时用距离差作权重（目的更近时），距离相等时用固定亲和顺序定 eligibility（目的更靠前则权重 1，否则不计）。

## 背景与问题

（承接 sched-20260928-009）上游 cache-aware 负载均衡只在 LLC 粒度决策，跨 NUMA 节点放置交给独立的 NUMA balancing，二者互不知情。该系列给拓扑加一张去重后的 NUMA 距离矩阵，供负载均衡按「任务数 × 距离差」算 affinity 得分；海光这类非全对称互连平台节点间距离非单值，需要区分度。今天背景无新增，焦点是 02/23 中 affinity 打分式里「人造距离/bias」的语义与幅度。

## 技术方案

（承接 + 今日更新）Tim Chen 前几轮主张排序用确定性全序、打分用真实幅度（raw distance）。今天 Jianyong 明确 bias 的意图——不是打破 affinity 平分，而是让 score 反映「聚合机会」（包括 raw NUMA 距离不变但遵循固定节点亲和顺序的迁移），并**接受 Tim 对人造距离幅度的关切**：人造距离/rank 差的幅度不应决定聚合机会的权重。据此提出新打分式（对每个 preferred 节点）：

```
delta = node_distance(src, pref) - node_distance(dst, pref)
if (delta > 0)          weight = delta
else if (delta == 0 && affi_rank(pref, dst) < affi_rank(pref, src)) weight = 1
else                    continue
score += numa_counts[pref] * weight
```

即：源/目的对 preferred 节点 raw distance 不同且目的更近时，用距离差作权重；距离相等时，用固定节点亲和顺序决定是否 eligible，eligible 者贡献权重 1。`numa_counts[pref]` 为该节点上的任务数。

## 版本演进与当前进展

*current_version: v2*（仍无新版）。本日继续收敛 02/23 的 affinity 打分细节：作者澄清 bias 语义、接受「人造距离幅度不应定权重」、给出「距离差权重 + 亲和顺序 eligibility」的新式。

## Maintainer 意见与讨论焦点

- **Tim Chen（Intel）**：关切「在打分里使用人造节点距离」——人造距离/rank 差的幅度不应决定聚合机会权重（本日 Jianyong 明确同意该关切）。
- **Jianyong Wu（作者）**：澄清 bias 意图，提出新打分式以同时满足「真实幅度定权重」与「等距时用亲和顺序定 eligibility」。
- 无 Peter Zijlstra 本日新表态。分歧从「去重矩阵是否必要」进一步收敛到「新打分式的 eligibility 规则是否经 Tim/Peter 确认」。

## 合入评估

*likelihood=unknown*。23 枚架构性 RFC 仍处早期评审，02/23 的打分式持续收敛但尚未出 v3；三元组全序 + 新打分式尚未经 Tim/Peter 最终确认，系列整体仍缺跨平台收益数据。*blocking_issues*：新打分式（距离差权重 + 亲和顺序 eligibility）未经确认；系列缺跨平台收益与 v3。*next_action*：作者按今日收敛方向改出 v3，并补跨平台收益背书。

## 效果评估

本日无性能数据；属设计论证层面的进一步收敛（打分式从「三元组全序 + affinity_bias」细化为「距离差权重 + 亲和顺序 eligibility」），无实测。

## 我可以参与的点

- `discussion`：就「距离差权重 + 亲和顺序 eligibility」是否等价/优于「三元组全序 + affinity_bias」，以及对负载均衡正确性与可预测性的影响给出分析，帮助双方在 v3 前对齐。
- `testing`：若手上有 Hygon 多节点机型，给出开启/关闭该系列的 NUMA 亲和收益对比——整个系列最缺的仍是跨平台收益背书。

## 参考链接

- Jianyong 今日回复: https://lore.kernel.org/all/4d2b5dede1f64350ac17ea9d0a5428a1@hygon.cn/
- v2 封面: https://lore.kernel.org/all/20260827122816.756234-1-wujianyong@hygon.cn/

---
id: sched-20261008-010
subject: 'sched/topology: Introduce a NUMA distance matrix with unique distance values'
date: '2026-10-08'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: '<4d2b5dede1f64350ac17ea9d0a5428a1@hygon.cn>'
lore_url: 'https://lore.kernel.org/all/4d2b5dede1f64350ac17ea9d0a5428a1@hygon.cn/'
authors:
  - 'Jianyong Wu'
maintainers_involved:
  - 'Tim Chen'
current_version: v2
patch_series:
  - version: v2
    msgid: '<20260827122816.756234-1-wujianyong@hygon.cn>'
    date: '2026-08-27'
    summary: '23 枚：NUMA 距离矩阵 + LLC 距离小矩阵 + affinity 打分'
    review_outcome: '02/23 打分式向「距离差权重 + 亲和顺序 eligibility」收敛'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - '新打分式尚未经 Tim/Peter 最终确认'
    - '系列整体缺跨平台收益数据与 v3'
  next_action: '作者按今日收敛方向改出 v3 并补跨平台收益'
contribution_opportunities:
  - kind: discussion
    description: '分析距离差权重+亲和顺序 eligibility 对负载均衡正确性的影响'
  - kind: testing
    description: 'Hygon 多节点机型给出 NUMA 亲和收益对比数据'
generated_at: '2026-10-09T01:00:00'
source_email_count: 1
related_articles:
  - sched-20260923-006
  - sched-20260924-008
  - sched-20260928-009
tags:
  - topology
  - numa_balancing
  - load_balance
---