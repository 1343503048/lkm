---
id: sched-20261027-007
date: 2026-10-27
subject: 'sched/fair: Introduce the SMT_BUDDY_ASSIST feature'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20261020083746.37068-1-likunyu@open-hieco.net>
lore_url: https://lore.kernel.org/all/20261020083746.37068-1-likunyu@open-hieco.net/
authors:
- Li kunyu
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <20261020083746.37068-1-likunyu@open-hieco.net>
  date: 2026-10-20
  summary: RFC 6 patches：SMT sibling push / is_smt_buddy_run / 排除 sibling / newidle
    限 LLC / burst 阈值
  review_outcome: Peter 严厉 review，方向未认可
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 静态 burst 阈值设计受质疑
  - 与 relax_domain_level 功能重叠未获信服
  next_action: 作者发 v2 后等 Peter 复核方向
contribution_opportunities:
- kind: testing
  description: burst 负载上独立复现 patch4 与 relax_domain_level 对照
- kind: review
  description: 评估静态 burst 阈值能否被动态 rq-depth 跟踪替代
generated_at: '2026-10-28T09:00:00'
source_email_count: 5
related_articles:
- sched-20261021-003
- sched-20261022-008
- sched-20261023-014
tags:
- cfs
- load_balance
title: 'sched/fair: Introduce the SMT_BUDDY_ASSIST feature'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-003-sched-fair-introduce-the-smt-buddy-assist-feature.html">sched-20261021-003</a>（RFC v1，6 patches）：Li kunyu 的「SMT Buddy Assist」RFC——利用 SMT 兄弟核互相 assist，在周期性负载均衡里向 SMT sibling push、push 成功后排除该 sibling、newidle 均衡限制到 LLC 域，并加 burst 阈值，目标是降低突发唤醒下的任务分布不均。Peter Zijlstra 当日给出严厉 review（缩进「horrific」、静态阈值「horrible」等）。
- <a class="article-ref" href="/lkm/2026/10/22/sched-20261022-008-sched-fair-introduce-the-smt-buddy-assist-feature.html">sched-20261022-008</a> / <a class="article-ref" href="/lkm/2026/10/23/sched-20261023-014-sched-fair-introduce-the-smt-buddy-assist-feature.html">sched-20261023-014</a>：持续 review，作者吸收意见。
- <a class="article-ref" href="/lkm/2026/10/27/sched-20261027-007-sched-fair-introduce-the-smt-buddy-assist-feature.html">sched-20261027-007</a>（今天）：作者回帖逐点汇报 v2 改动方向（改用 `rq->cfs.h_nr_runnable`、新增 `migrate_smt_task` 迁移类型等），并把 patch4 与 `relax_domain_level=4` 做了对照测试（hackbench -14.94% vs -1.x%）。

## 背景与问题
（承接 20261021-003）要解决「突发唤醒导致任务分布不均」：一批任务同时被唤醒（burst）时周期性负载均衡没能及时摊开，个别 CPU 过载而 SMT 兄弟空闲。作者的「SMT Buddy Assist」让 SMT 兄弟核在 burst 场景互相协助，落到 6 个补丁。

## 技术方案
（承接 RFC v1）6 补丁思路不变：周期性负载均衡新增 SMT sibling push、`is_smt_buddy_run()` 在 buddy 运行跳过 SMT 域、push 成功后排除 sibling、newidle 均衡限制 LLC 域、burst 阈值、文档。今日作者汇报的 v2 演化方向：

- `rq->nr_running` → `rq->cfs.h_nr_runnable`，只统计正在运行或已排队的 CFS 任务。
- 新增条件：当前 CPU 任务数须大于其 SMT sibling，避免迁移过多尚未开始运行的新任务。
- 新增 `migrate_smt_task` 迁移类型，跳过不满足 CPU affinity 的 sibling 从而全面检查所有 sibling。
- patch2 里当 SMT 域跳过场景时调用 `update_group_capacity(sd, cpu)` 更新等效 CPU 容量。

## 版本演进与当前进展
*current_version: v1*（RFC，`<20261020083746.37068-1-likunyu@open-hieco.net>`）。作者尚未发 v2，今日为对 Tim Chen、Kayra 等 review 意见的逐点回应与对照测试。

## Maintainer 意见与讨论焦点
Peter Zijlstra 早期（20261021）已给严厉 review、尚未方向性认可；今日的对照测试（patch4 vs `relax_domain_level=4`）是作者为回应「是否等同已有 relax_domain_level 机制」的自证：两者有效调度层级相同、总平均接近（+3.28%），但 hackbench 上 smt_buddy -14.94% vs relax -1.x%，作者认为 relax 只作参考、不能解决所遇问题。作者还提出「设了 relax_domain_level 则禁用 patch4」的折中。争议未消：静态阈值被 Peter 判「horrible」、方向仍待认可。

## 合入评估
*likelihood=unknown*（RFC 早期，maintainer 尚未表态方向）。*blocking_issues*：静态 burst 阈值设计受质疑、与 relax_domain_level 的功能重叠未让 Peter 信服。*next_action*：作者发 v2（含对照数据与阈值重构）后等 Peter 复核方向。

## 效果评估
作者对照测试：patch4 与 `relax_domain_level=4` 总平均接近（+3.28%）；hackbench 上 smt_buddy -14.94% vs relax -1.x%（作者自测数据，未附完整环境/误差）。

## 我可以参与的点
- *kind: testing*：在 burst 型负载上独立复现 patch4 与 relax_domain_level 的对照，验证 hackbench 结论与稳定性。
- *kind: review*：评估「静态 burst 阈值」是否可被动态 rq-depth 跟踪替代（Peter 曾建议的方向）。

## 参考链接
- 线程: https://lore.kernel.org/all/20261020083746.37068-1-likunyu@open-hieco.net/
