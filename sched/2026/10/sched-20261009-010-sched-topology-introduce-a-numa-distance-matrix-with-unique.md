# sched/topology: Introduce a NUMA distance matrix with unique distance values

## TL;DR

本文为增量更新，完整脉络见 related_articles。这是 Jianyong Wu（海光）23 补丁 RFC（NUMA/LLC 两级亲和性打分负载均衡）的持续评审。

- sched-20260923-006：Tim Chen 提 `llc_next` 数组替代人造 LLC 距离矩阵，路线未收敛。
- sched-20260924-008：分歧收敛到「去重矩阵必要性」——Tim 主张 raw distance + 平局决胜即可，Jianyong 坚持去重是为强制对称性。
- sched-20260928-009：Jianyong 在对称性上让步，提出三元组 `(distance, abs(node_id_i - node_id_j), min(i, j))` 全序即可保证对称与去重，并给出不依赖距离幅度的 affinity 打分式。
- sched-20261008-010：Jianyong 澄清「bias 不是为打破 affinity 平分、而是让 score 反映聚合机会」，接受 Tim 对距离幅度的关切，提出「距离差权重 + 亲和顺序 eligibility」的新打分式。
- sched-20261009-010（今天）：Chen Yu（Intel）从「LLC 对称性」切入——距离比较的动机是 NUMA 节点非对称，但 LLC 是对称的，可直接把 preferred LLC 的「range 个兄弟」加入 preferred_mask、无需距离矩阵；主张至少在 LLC 层去掉距离比较。

## 背景与问题

（承接 sched-20260928-009 / sched-20261008-010）上游 cache-aware 负载均衡只在 LLC 粒度决策，跨 NUMA 节点放置交给独立的 NUMA balancing，二者互不知情。该系列给拓扑加一张去重后的 NUMA 距离矩阵，供负载均衡按「任务数 × 距离差」算 affinity 得分；海光这类非全对称互连平台节点间距离非单值，需要区分度。今天的增量是 Chen Yu 对「距离比较是否真的必要」提出分层质疑。

## 技术方案

（承接 + 今日更新）Tim Chen 前几轮主张排序用确定性全序、打分用真实幅度（raw distance）；昨天 Jianyong 给出「距离差权重 + 亲和顺序 eligibility」的新打分式。今天 Chen Yu 提出**分层简化**：

- 作者方案对 multi-LLC/node 聚合都采用 best-effort 策略，向 preferred mask 迁移，mask 大小即 `task_cache_work()` 里算的「range」。
- 以 LLC 为例：6 个 LLC、range=3，策略允许负载均衡以任意顺序往 preferred LLC mask/range 里迁（例如 LLC4→LLC1 OK、LLC4→LLC0 OK、LLC0→LLC1 no）。
- Chen Yu 的观点：距离比较之所以被引入，是因为 NUMA 节点彼此**非对称**，需要真实顺序去饱和节点；但 LLC 是对称的——可以从 preferred CPU 出发、按 LLC id 顺序拿到下一个 LLC，`dist(LLC1,LLC2)=(rank1+rank2)%k+1` 并非必需。何不直接把 preferred LLC 的「range 个兄弟」加进 `preferred_mask`、负载均衡直接用该 mask？这样至少 LLC 层可以去掉距离比较。

## 版本演进与当前进展

*current_version: v2*（仍无新版）。今日进展：Chen Yu 提出 LLC 层可去掉距离比较、直接构造 preferred_mask；这是对「去重距离矩阵必要性」争论的新一层分解（Node 层保留、LLC 层简化）。

## Maintainer 意见与讨论焦点

- **Chen Yu（Intel，本日新加入）**：承认作者引入距离比较的动机成立（NUMA 节点非对称），但指出该动机对 LLC 不成立（LLC 对称、可按 id 序取兄弟）；建议 LLC 层直接用 preferred_mask、丢掉距离比较，降低复杂度。这实质上呼应了 Tim Chen 更早的「llc_next 数组替代人造 LLC 距离矩阵」主张。
- **Tim Chen（Intel）**：此前关切「人造节点距离幅度不应决定聚合机会权重」，昨天 Jianyong 已接受。
- **Jianyong Wu（作者）**：昨天的「距离差权重 + 亲和顺序 eligibility」新打分式尚未对 Chen Yu 的 LLC 分层简化作出回应。
- 分歧从「去重矩阵是否必要」进一步细化为「Node 层保留距离比较、LLC 层可否去掉」。

## 合入评估

*likelihood=unknown*。23 枚架构性 RFC 仍处早期评审；Chen Yu 本日的 LLC 分层简化尚未得到作者回应，若成立将进一步缩小编排规模、但也要求重写 LLC 层聚合逻辑。*blocking_issues*：① Chen Yu 的 LLC 层简化提议待作者回应；② 新打分式（距离差权重 + 亲和顺序 eligibility）未经 Tim/Peter 最终确认；③ 系列缺跨平台收益数据与 v3。*next_action*：作者回应 Chen Yu 的 LLC 分层简化，据此收敛 v3。

## 效果评估

本日无性能数据；属设计论证层的进一步细化（LLC 对称性 → 可去距离比较），无实测。

## 我可以参与的点

- `discussion`：分析「LLC 对称、Node 非对称」这一分层是否成立，以及 preferred_mask 直构方案在 range>1 时的负载均衡正确性。
- `testing`：若手上有 Hygon 多节点机型，给出开启/关闭该系列的 NUMA 亲和收益对比——整个系列最缺的仍是跨平台收益背书。

## 参考链接

- Chen Yu 今日回复: https://lore.kernel.org/all/asfGTaJjCGMLW6fp@chenyu-dev/
- Jianyong 前日回复: https://lore.kernel.org/all/4d2b5dede1f64350ac17ea9d0a5428a1@hygon.cn/
- v2 封面: https://lore.kernel.org/all/20260827122816.756234-1-wujianyong@hygon.cn/

---
id: sched-20261009-010
date: '2026-10-09'
subject: 'sched/topology: Introduce a NUMA distance matrix with unique distance values'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: '<4d2b5dede1f64350ac17ea9d0a5428a1@hygon.cn>'
lore_url: 'https://lore.kernel.org/all/asfGTaJjCGMLW6fp@chenyu-dev/'
authors:
  - 'Jianyong Wu'
maintainers_involved:
  - 'Tim Chen'
  - 'Chen Yu'
current_version: v2
patch_series:
  - version: v2
    msgid: '<20260827122816.756234-1-wujianyong@hygon.cn>'
    date: '2026-08-27'
    summary: '23 枚：NUMA 距离矩阵 + LLC 距离小矩阵 + affinity 打分'
    review_outcome: 'Chen Yu 提出 LLC 层可去距离比较、直接构造 preferred_mask'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - 'Chen Yu 的 LLC 分层简化待作者回应'
    - '新打分式未经 Tim/Peter 最终确认'
    - '系列缺跨平台收益与 v3'
  next_action: '作者回应 LLC 分层简化并收敛 v3'
contribution_opportunities:
  - kind: discussion
    description: '分析 LLC 对称/Node 非对称分层与 preferred_mask 直构的正确性'
  - kind: testing
    description: 'Hygon 多节点机型给出 NUMA 亲和收益对比'
generated_at: '2026-10-10T01:30:00'
source_email_count: 1
related_articles:
  - sched-20260923-006
  - sched-20260924-008
  - sched-20260928-009
  - sched-20261008-010
tags:
  - topology
  - numa_balancing
  - load_balance
---