# sched/topology: Introduce a NUMA distance matrix with unique distance values

## TL;DR
本文为增量更新，完整背景见 sched-20260901-004。Jianyong Wu（海光）的 NUMA/LLC 两级亲和性负载均衡系列（RFC v2）今日继续 02/23 的距离矩阵去重讨论：Tim Chen 提出用 `llc_next` 数组替代「人造 LLC 距离矩阵」这一更省存储、更直白的方案，并质疑去重算法会耗尽可用距离槽；Jianyong 逐条回应，澄清系列目标（系统级 LLC 亲和排序）与去重只作用于节点层、不涉及 LLC 数。分歧未收敛，属设计路线讨论。

## 背景与问题
背景见 sched-20260901-004：上游 cache-aware 负载均衡只在 LLC 粒度决策，跨 NUMA 节点放置交给独立的 NUMA balancing，二者互不知情。该系列给拓扑加「去重后的 NUMA 距离矩阵」，让每个节点的距离值互不相同，供 load balance 按「任务数 × 距离差」算 affinity 得分。海光这类非全对称互连平台节点间距离非单值，需要去重矩阵才有区分度。

## 技术方案
本日讨论聚焦 02/23 的去重矩阵设计，出现一条替代路线：

- **Tim Chen**：真正想要的是「同一 NUMA 节点内 cache 的排序」——cache 满时按顺序取下一个。提议 `llc_next` 数组（如 `[1 0 3 2 5 4 7 6]`），回到起始 LLC 即跳到次近节点，比「人造 cache 距离矩阵」更省存储、更直白。他厌恶人造矩阵的另一理由：两个距离层级之间的可用「距离槽」个数没有保证——例如 NODE1 有 16 个 LLC 但两级距离间只有 10 个槽可去重，会耗尽槽位。
- **Jianyong Wu（作者）**：澄清系列目标是「系统级 LLC 亲和排序」（而非仅单节点内 LLC 排序）；单张系统级 LLC 排序代价大，故分层表示——节点级亲和排序 + 节点内 LLC 排序，此 patch 只管节点级。针对「等距节点的次近选择」歧义，正是本 patch 要消解的：为每个源节点去重等距离、产出唯一节点级排序，`llc_next` 数组描述不了「该访问哪个等距节点」。系列无系统级 LLC 距离矩阵，去重只作用于节点矩阵，故 NODE1 的 LLC 数不影响所需距离值个数。算法还会预留距离空间（不为每个重复插一个值），故不会耗尽可用距离。

## 版本演进与当前进展
- v2（08-27，23 枚）以来持续逐片评审。本日为 02/23 去重矩阵的路线分歧延续，无新版。

## Maintainer 意见与讨论焦点
本日无 Peter Zijlstra 新表态，参与者为 Tim Chen（Intel）与作者 Jianyong Wu。分歧点：`llc_next` 数组（节点内 cache 排序）是否足以表达作者要的「系统级 LLC 亲和排序」。Tim 的方案更省存储、更直白且无「距离槽耗尽」风险；作者的方案针对跨节点等距消歧，二者解决的不是完全同一层问题。路线未收敛。

## 合入评估
likelihood=unknown。仍是 23 枚架构性 RFC 的早期评审，去重矩阵的数据结构路线（节点级去重矩阵 vs `llc_next`）尚未与 Tim 的方案对齐；且此前 Peter 提出的 `__build_all_zonelists()` mm 侧联动、着色算法上界等 open 项依旧未决。blocking_issues：去重矩阵 vs `llc_next` 路线未定；系列整体仍缺跨平台收益数据与 v3。next_action：作者与 Tim 就「节点级去重矩阵」与「节点内 cache 排序」的职责边界对齐，再决定 02/23 采用哪种结构。

## 效果评估
本日无性能数据。设计层面的静态论点为：`llc_next` 存储效率与无「槽耗尽」风险 vs 节点级去重矩阵的跨节点等距消歧能力；均属设计论证，无实测。

## 我可以参与的点
- kind=discussion：对「节点级去重矩阵 vs `llc_next`」给出折中判断——例如可否两层并用（节点级去重矩阵 + 节点内 `llc_next`），替代目前「节点 + LLC 两级距离矩阵」的表述，帮作者与 Tim 收敛。
- kind=testing：若手上有 Hygon 多节点机型，给出开启/关闭该系列的 NUMA 亲和收益对比数据（这是整个系列最缺的证据，见 sched-20260901-004）。

## 参考链接
- lore（Tim Chen 回复）: https://lore.kernel.org/all/da32ba66d95fd88869ba052f97698b9a4d6c3dc6.camel@linux.intel.com/
- lore（Jianyong Wu 回复）: https://lore.kernel.org/all/09261c8222994a41a04ace5f342475df@hygon.cn/

---
id: sched-20260923-006
subject: 'sched/topology: Introduce a NUMA distance matrix with unique distance values'
date: '2026-09-23'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: '<da32ba66d95fd88869ba052f97698b9a4d6c3dc6.camel@linux.intel.com>'
lore_url: 'https://lore.kernel.org/all/da32ba66d95fd88869ba052f97698b9a4d6c3dc6.camel@linux.intel.com/'
authors:
  - 'Jianyong Wu'
maintainers_involved:
  - 'Tim Chen'
current_version: v2
patch_series:
  - version: v2
    msgid: null
    date: '2026-08-27'
    summary: '23 枚 RFC v2，02/23 为两级 NUMA 距离矩阵去重'
    review_outcome: 'Tim Chen 提议 llc_next 数组替代人造 LLC 距离矩阵；作者澄清系统级 LLC 排序目标与节点级去重'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - '去重矩阵 vs llc_next 的路线未收敛'
    - '系列整体缺跨平台收益数据，v3 未发'
  next_action: '作者与 Tim 对齐节点级去重矩阵与节点内 cache 排序的职责边界'
contribution_opportunities:
  - kind: discussion
    description: '对节点级去重矩阵与 llc_next 给出折中判断（如两层并用）'
  - kind: testing
    description: '给出 Hygon 多节点机型上的 NUMA 亲和收益对比数据'
generated_at: '2026-09-24T09:00:00'
source_email_count: 2
related_articles:
  - sched-20260901-004
tags:
  - topology
  - numa_balancing
  - load_balance
---