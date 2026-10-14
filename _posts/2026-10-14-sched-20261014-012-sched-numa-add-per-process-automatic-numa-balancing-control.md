---
id: sched-20261014-012
subject: 'sched/numa: Add per-process automatic NUMA balancing control'
date: 2026-10-14
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260908122446.56708-1-lizhe.67@bytedance.com>
lore_url: https://lore.kernel.org/all/20260908122446.56708-1-lizhe.67@bytedance.com/
authors:
- Li Zhe
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260908122446.56708-1-lizhe.67@bytedance.com>
  date: 2026-09-08
  summary: prctl 式逐进程自动 NUMA balancing 控制（0/4），逐进程跟踪模式
  review_outcome: 作者回应方向建议，向 per-cgroup/三元键松动，接口仍未定
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 接口粒度与形态未定，无维护者表态
  next_action: 维护者对接口粒度定调；作者可能转向 review Yafang 的 per-cgroup 系列
contribution_opportunities:
- kind: discussion
  description: 对照 K8s/容器运行时用例评估三条接口路线的迁移成本与继承语义
generated_at: '2026-10-15T01:00:00+08:00'
source_email_count: 2
related_articles:
- sched-20261013-004
tags:
- numa_balancing
title: 'sched/numa: Add per-process automatic NUMA balancing control'
layout: article
---

> **subject**：sched/numa: Add per-process automatic NUMA balancing control

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/13/sched-20261013-004-sched-numa-add-per-process-automatic-numa-balancing-control.html">sched-20261013-004</a>：Li Zhe（字节跳动）9/8 的「per-process 自动 NUMA balancing 控制」系列（0/4，prctl 式逐进程开关）在昨日迎来方向讨论——Chen Yu 建议把全局开关做成三元（类比 THP always/advise/never），Yafang Shao 主张从开始就做成 BPF-cgroup 式可扩展语义；方向（prctl vs cgroup/BPF vs 三元全局键）未收敛。
- <a class="article-ref" href="/lkm/2026/10/14/sched-20261014-012-sched-numa-add-per-process-automatic-numa-balancing-control.html">sched-20261014-012</a>（今天）：作者 Li Zhe 回应——「三元全局键听起来可行」；自身用例（K8s/容器运行时用 prctl 设属性）下 prctl 与 per-cgroup 都能满足，**若维护者倾向 per-cgroup，愿意帮忙 review Yafang 的系列**。作者立场向 per-cgroup 松动，但接口形态仍未定。

## 背景与问题
（承接 20261013-004）全局 `numa_balancing` 开关对每个 workload 一视同仁，无法在进程间差异化控制自动 NUMA balancing。昨日讨论聚焦接口形态：逐进程 prctl 在大规模场景是负担、prctl 未必适配 mTHP 等新内存语义、生产上（LLC-aware 调度）希望按 cgroup 粒度控制。

## 技术方案
（承接 20261013-004）今日为作者对方向建议的表态，无新补丁：作者认可 Chen Yu 的三元全局键「sounds possible」，并明确其生产用例是「K8s 或容器运行时经 prctl 设置 NUMA balancing 属性、子进程继承」；同时表示 per-cgroup（Yafang 路线）同样适用，愿意在维护者偏向 per-cgroup 时帮助 review Yafang 系列。三路线（prctl / 三元全局键 / BPF-cgroup）仍在等维护者定调。

## 版本演进与当前进展
原系列 0/4 为 v1（9/8 发，无版本号）；今日无新版本补丁，为作者对昨日方向讨论的回应。

## Maintainer 意见与讨论焦点
- 无维护者（Peter/Juri/Dietmar 等）表态。
- **Li Zhe**（作者，今日）：对三元全局键「可行」，对 per-cgroup「也可接受」，主动表示可帮 review Yafang 系列——态度开放、未坚持 prctl。
- **Chen Yu / Yafang Shao**（前日）：分别主张三元全局键与 BPF-cgroup。
- 未决：最终接口粒度与形态仍取决于维护者；作者已不再坚持原 prctl 方案。

## 合入评估
*likelihood=unknown*。作者立场松动、愿配合 per-cgroup，但无维护者表态、接口形态（prctl vs 三元键 vs BPF-cgroup）未定，与 Yafang 的并行 RFC 关系仍待理清。*blocking_issues*：方向未定、无 pull 信号。*next_action*：维护者（或资深评审）对接口粒度定调；若走 per-cgroup，作者将转向 review Yafang 系列。

## 效果评估
暂无效果数据；讨论为接口设计，无 benchmark 数字。

## 我可以参与的点
- discussion：接口粒度（per-process prctl vs 三元全局键 vs per-cgroup BPF）是关键分歧，可结合生产场景（K8s/容器运行时如何设置 NUMA balancing 属性）提供输入；作者已明确其 use case 与继承语义，可帮忙对照评估三条路线的迁移成本。

## 参考链接
- 系列 cover lore：https://lore.kernel.org/all/20260908122446.56708-1-lizhe.67@bytedance.com/
- 今日作者回应：https://lore.kernel.org/all/27125190-b343-42c5-889f-c7377084f5d8@bytedance.com/
