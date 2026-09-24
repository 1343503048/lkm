---
id: sched-20260917-013
date: '2026-09-17'
subject: 'sched/numa: stop VMA scan filters from gating promotion'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260911001826.2109390-1-gourry@gourry.net>
lore_url: https://lore.kernel.org/all/20260911001826.2109390-1-gourry@gourry.net/
authors:
- Gregory Price
maintainers_involved:
- Andrew Morton
- David Hildenbrand
current_version: v2
patch_series:
- version: v2
  msgid: <20260911001826.2109390-1-gourry@gourry.net>
  date: '2026-09-11'
  summary: 停止让 VMA 扫描过滤器阻碍 NUMA 提升；本日澄清影响面与 Fixes/stable 正当性
  review_outcome: akpm 追问标签正当性，David Hildenbrand 接手 MM 侧审查
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Fixes/stable 标签正当性待澄清
  - 缺 sched/fair.c 侧评审
  next_action: 作者澄清基线行为，等待 MM 与 sched 两侧评审
contribution_opportunities:
- kind: review
  description: 从 sched/fair.c 侧审查 VMA 扫描过滤器对提升路径的影响
- kind: discussion
  description: 评估 Fixes 指向与 cc:stable 的合理性
generated_at: '2026-09-18T09:00:00'
source_email_count: 3
related_articles:
- sched-20260911-008
tags:
- numa_balancing
title: 'sched/numa: stop VMA scan filters from gating promotion'
layout: article
---

## TL;DR
增量更新：Gregory Price 的 NUMA "停止让 VMA 扫描过滤器阻碍提升"系列（v2）引发维护者关注——Andrew Morton 追问"为什么 cc:stable 和 Fixes:"，Gregory 解释 NUMA balancing 自 2022/2023 起就被功能性打破、只因另一个 shmem bug 掩盖了症状；David Hildenbrand 将负责审查 MM 侧，并请人审查 sched/fair.c 侧。合入仍缺 sched 维护者评审。

## 背景与问题
背景见 <a class="article-ref" href="/lkm/2026/09/11/sched-20260911-008-sched-numa-stop-vma-scan-filters-from-gating-promotion.html">sched-20260911-008</a>：VMA 扫描过滤器会阻碍 NUMA 提升，导致 NUMA balancing 失效。本日增量是关于影响面与 Fixes/stable 标签的正当性讨论。

## 技术方案
无方案变化。焦点转为对该系列"严重性"的澄清。

## 版本演进与当前进展
- v2（09-11，`<20260911001826.2109390-1-gourry@gourry.net>`）：当前版本。
- 09-17：Andrew Morton、David Hildenbrand 回帖表态，Gregory Price 进一步说明影响面。

## Maintainer 意见与讨论焦点
- **Andrew Morton**：认为"这看起来非常严重？"，质疑为何 cc:stable 和 Fixes:，并问在肇事 commit 之前是否真的以这些速度运行。
- **Gregory Price（作者）**：解释该改动在功能上把 NUMA balancing 破坏到对常见用例完全失效；之所以没早发现，是因为另一个 bug（hannes 的 shmem 修复，`20260629163337`）使部分数据库负载 70–90% 内存不适配 tiering、掩盖了症状；shmem 修复合入后，饥饿与过滤问题随带宽数字反常而暴露。结论：numa balancing 从 2022/2023 起就坏了，此后所有测试都基于不完整 VMA 覆盖的坏数据。
- **David Hildenbrand**：将审查该系列的 MM（内存管理）侧；自谦对 sched/fair.c 侧不熟，希望有人审查调度侧。
- 分歧点：无技术对立，但缺 sched/fair.c 侧的专家审查。

## 合入评估
*likelihood=medium*。影响面被确认为长期性功能失效，维护者已重视；但 Andrew Morton 对 Fixes/stable 标签的疑问尚未闭环，且 sched/fair.c 侧无人审查。*blocking_issues*：Fixes/stable 标签的正当性待澄清；缺 sched/fair.c 侧评审。*next_action*：作者澄清修复引入前的基线行为，并等待 MM + sched 两侧评审。

## 效果评估
无新增性能数据；作者以"功能长期失效"定性，未附新的 benchmark。

## 我可以参与的点
- kind=review：从 sched/fair.c 侧审查 VMA 扫描过滤器如何阻碍提升迁移，回应 David Hildenbrand 的求助。
- kind=discussion：评估 Fixes: 指向的肇事 commit 与 cc:stable 的合理性（Andrew Morton 正有此问）。

## 参考链接
- lore（v2 cover）: https://lore.kernel.org/all/20260911001826.2109390-1-gourry@gourry.net/
- shmem 掩盖 bug: https://lore.kernel.org/all/20260629163337.1264881-1-hannes@cmpxchg.org/
