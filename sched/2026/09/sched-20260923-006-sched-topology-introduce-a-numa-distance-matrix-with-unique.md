# sched/topology: Introduce a NUMA distance matrix with unique distance values

## TL;DR
- sched-20260901-004：Jianyong Wu（海光）的 23 补丁 RFC v2（NUMA/LLC 两级亲和性打分负载均衡）进入 Peter Zijlstra 逐片精读。已定型：per-node `numa_counts[]` 记账被要求改成按需累加（作者同意删）、per-sd 数组补 `__counted_by_ptr`；未定：距离矩阵去重算法（贪心边着色只能到 2Δ+1，Peter 希望更紧上界）与 commit message 质量。
- sched-20260923-006（今天）：继续 02/23 距离矩阵去重讨论——Tim Chen 提出用 `llc_next` 数组替代「人造 LLC 距离矩阵」（更省存储、更直白），并质疑去重算法会耗尽可用距离槽；Jianyong 逐条回应，澄清系列目标是系统级 LLC 亲和排序、去重只作用于节点层。分歧未收敛，属设计路线讨论。

## 背景与问题
- sched-20260901-004：上游 cache-aware 负载均衡只在 LLC 粒度决策，跨 NUMA 节点放置交给独立的 NUMA balancing，二者互不知情。该系列给拓扑加一张**去重后的 NUMA 距离矩阵**，让每个节点的距离值互不相同，供 load balance 按「任务数 × 距离差」算 affinity 得分。海光这类非全对称互连平台节点间距离非单值，需要去重矩阵才有区分度。
- sched-20260923-006（今天）：背景无新增。

## 技术方案
- sched-20260901-004：两级矩阵（NUMA 节点距离矩阵 + 节点内 LLC 距离小矩阵）；用贪心边着色去重保证每行无重复（Peter 指出上界应为 Δ/Δ+1、贪心只能到 2Δ+1）；在 rq/sd 上维护 `llc_counts[]`/`numa_counts[]` 供 affinify score 使用；per-sd scratch 数组避免热路径分配。关键取舍是「热路径记账 vs 慢路径按需累加」，Peter 主张后者、作者接受。
- sched-20260923-006（今天）：出现一条替代路线——**Tim Chen** 提议 `llc_next` 数组（如 `[1 0 3 2 5 4 7 6]`）表达「同一 NUMA 节点内 cache 排序」，比人造矩阵更省存储、更直白，且人造矩阵的「距离槽」个数无保证（可能耗尽）。**Jianyong Wu** 澄清：目标是系统级 LLC 亲和排序，需分层（节点级排序 + 节点内 LLC 排序），此 patch 只管节点级；`llc_next` 描述不了「该访问哪个等距节点」，正是去重矩阵要消解的歧义；去重只作用于节点矩阵，且算法预留距离空间，不会耗尽。

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
- kind=testing：若手上有 Hygon 多节点机型，给出开启/关闭该系列的 NUMA 亲和收益对比数据——这是整个系列最缺的证据（23 枚架构性改动至今无跨平台收益背书）。

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