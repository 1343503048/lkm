---
id: sched-20261022-008
date: 2026-10-22
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
  summary: SMT Buddy Assist：SMT sibling push + burst 阈值 + newidle 限制 LLC
  review_outcome: Peter 否定方向、指路 cache-aware；作者将加接口后续版本回应
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - 需证明 SMT push 相对 cache-aware 的增量价值
  next_action: 作者加用户接口并用数据回应方向质疑
contribution_opportunities:
- kind: review
  description: 评估 SMT push 与 cache-aware 在突发/跨 LLC 场景的优劣
- kind: discussion
  description: 就 burst 阈值与 LLC 限制设计是否合理参与讨论
generated_at: '2026-10-23T01:20:00'
source_email_count: 2
related_articles:
- sched-20261021-003
tags:
- cfs
- load_balance
- hyperthreading
title: 'sched/fair: Introduce the SMT_BUDDY_ASSIST feature'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-003-sched-fair-introduce-the-smt-buddy-assist-feature.html">sched-20261021-003</a>：Li kunyu 发往 sched 的 RFC 六补丁系列「SMT Buddy Assist」：利用 SMT 兄弟核互相 assist，在周期性负载均衡里向 SMT sibling push、push 成功后排除该 sibling、newidle 均衡限制到 LLC 域，并加 burst 阈值，目标是降低突发唤醒下的任务分布不均。当日 Peter Zijlstra 给出严厉 review（代码缩进「horrific」、误以为 SMT mask 只有 2 CPU、静态阈值「horrible」，并给出跟踪平均 rq-depth + `cpumask_any_distribute()` 轮转的替代方向）；Kayra Cizmeci 也质疑 cover 里 benchmark 的「acceptable」表述。
- <a class="article-ref" href="/lkm/2026/10/22/sched-20261022-008-sched-fair-introduce-the-smt-buddy-assist-feature.html">sched-20261022-008</a>（今天）：Peter 进一步否定「用 SMT push 硬扛跨 LLC 迁移」的方向——「这是 cache-aware scheduling 该解决的问题」，并指路 Tim Chen 的 cache-aware 系列与 Vincent 的相关补丁。作者 Li kunyu 回帖感谢，表示将在后续版本加入用户接口（`always|advise|never`），并说明其后续思路：检查 `cfs.h_nr_runnable`、不再关注睡眠任务。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-003-sched-fair-introduce-the-smt-buddy-assist-feature.html">sched-20261021-003</a>）系列要解决「突发唤醒导致任务分布不均」：一批任务同时被唤醒（burst）时，周期性负载均衡没能及时摊开，导致个别 CPU 过载而 SMT 兄弟空闲。今日 Peter 把问题定性为「跨 LLC 的过度迁移」，认为应诉诸 cache-aware scheduling 而非 SMT push 这种「蛮力」手段，并承认 cache-aware 对 OpenMP（单进程）与 MPI（大量单线程）两类 stream 负载暂无效。

## 技术方案
（承接 003）RFC 六补丁（`kernel/sched/fair.c` + docs）：周期性负载均衡里新增 SMT sibling push、`is_smt_buddy_run()` 跳过 SMT 域、push 成功后排除 sibling、newidle 均衡限制到 LLC 域、大规模 burst 阈值、文档。今日无新补丁；作者口头承诺后续版本将：加入用户接口（`always|advise|never`）、改为检查 `cfs.h_nr_runnable` 计数、不再聚焦睡眠任务。Peter 建议的替代方向是 Tim Chen 的 cache-aware scheduling（`cover.1787955777...tim.c.chen`）与 Vincent Guittot 的某个 push 相关补丁（`20261002154415.2270586-8-vincent.guittot`）。

## 版本演进与当前进展
*current_version: v1*（`<20261020083746.37068-1-likunyu@open-hieco.net>`）。当日无新版本，为方向性讨论。

## Maintainer 意见与讨论焦点
Peter Zijlstra 明确不认可当前方向：跨 LLC 迁移问题应交给 cache-aware scheduling，「SMT push 这步我不太明白你为什么做」，并给了两个可参考的既有补丁链接。作者未正面反驳，选择吸收接口建议并在后续版本继续 SMT push 路线（认为「与 cache-aware 那套并不实质冲突」）。

## 合入评估
*likelihood=low*。RFC 尚处早期，主维护者 Peter 对技术路线持保留态度、指向了不同解法；*blocking_issues*：需证明 SMT push 相对 cache-aware 的增量价值，或吸收 cache-aware 思路重设计；*next_action*：作者在后续版本加入用户接口并用数据回应 Peter 的方向性质疑。

## 效果评估
无新量化数据；此前 cover 中的 benchmark 已被 Kayra 质疑「acceptable」表述不够严谨。

## 我可以参与的点
- *kind: review*：评估「SMT push」与「cache-aware scheduling」在突发/跨 LLC 场景的优劣，给出对比数据或观点。
- *kind: discussion*：就 SMT 兄弟 assist 的 burst 阈值与 LLC 限制设计是否合理参与讨论。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261020083746.37068-1-likunyu@open-hieco.net/
- Peter 今日回帖：https://lore.kernel.org/all/20261022074044.GA4120091@noisy.programming.kicks-ass.net/
