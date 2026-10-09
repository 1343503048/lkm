# sched/eevdf: Add min slice check when selecting CPU

> **subject**：`sched/eevdf: Add min slice check when selecting CPU`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260929-018：Vincent Guittot 8 补丁系列「Improving latency of short slice tasks」的 patch 8/8——`select_task_rq_fair()` 找不到空闲 CPU 时新增 `select_slice_cpu()` 比较候选 CPU 的 slice，避免短 slice 任务被放到已运行同长或更短 slice 任务的 CPU 上；Peter 建议复用初次扫描、Kayra 质疑 `nr_idle_scan` 语义，Vincent 确认注释需更新并宣布与 idle CPU 搜索合并。
- sched-20261001-010（今天）：Christian Loehle 加入讨论，建议在 8/8 之上**再叠加一个选 CPU 维度**——找 `current->vprot - current->vruntime` 最小的 rq（即保护剩余量最小的 CPU），并点出该方案的代价（会再次抑制长 slice 任务）、希望看到真实负载下不同 slice 长度的表现。合并后的 v2 版本尚未发出。

## 背景与问题

（承接 sched-20260929-018）EEVDF 下短 slice 任务在 `select_task_rq_fair()` 找不到空闲 CPU 时，可能被放到已运行同长或更短 slice 任务的 CPU 上导致显著等待；patch 8/8 在选 CPU 最后阶段加入 min slice 检查（`select_slice_cpu()`）。今天的增量是选型维度的讨论：候选 CPU 上 current 任务的「保护剩余量」（`vprot - vruntime`）与 slice 长度是两个相关但不同的信号——保护剩余量小意味着该 CPU 上的 current 很快会让出。

## 技术方案

（承接）8/8 的 `select_slice_cpu()` 比较候选 CPU 的 slice。Christian 今天的建议：在现有逻辑之上「additionally look for the rq with smallest current->vprot - current->vruntime」——用保护剩余量作为额外（或替代）的选 CPU 依据。他同时指出代价：「it disincentivizes longer slice tasks again」（会再次不鼓励长 slice 任务，因为它们保护剩余量天然更大），因此希望在完整负载（不同 slice 长度混合）上看数据再定。

## 版本演进与当前进展

- v1（09-21，patch 8/8 `<20260921152238.3804392-9-vincent.guittot@linaro.org>`）。
- 09-22 Peter 建议复用初次扫描；09-27 Kayra 质疑 `nr_idle_scan` 语义；09-29 Vincent 确认注释需更新并宣布与 idle CPU 搜索合并。
- 10-01：Christian 建议 vprot-vruntime 维度（`<b37e8f1c-0cc7-4ca1-9e40-620d908464bf@arm.com>`）。合并落地的新版本尚未发出。

## Maintainer 意见与讨论焦点

- **Christian Loehle**（评审者）：「Maybe even additionally look for the rq with smallest current->vprot - current->vruntime? It's an interesting approach, OTOH of course it disincentivizes longer slice tasks again. I'd be interested what this looks like on a full workload with different slice lengths.」——建设性建议 + 明确的保留意见。
- **Vincent Guittot**（作者/维护者）：今日未回帖；其 09-29 的「与 idle CPU 搜索合并」方向未变。
- Peter/Kayra 此前意见均已获作者回应。
- 焦点：合并版 `select_slice_cpu()` 是否吸收 vprot-vruntime 维度；若吸收，如何避免对长 slice 任务的系统性惩罚。

## 合入评估

*likelihood=medium*。方向与系列一脉相承、既有意见均已回应；但「与 idle CPU 搜索合并」的落地版本未出，今天又新增一个待评估的设计维度（vprot-vruntime），收敛步骤增加。*blocking_issues*：`select_slice_cpu()` 与 idle CPU 搜索的合并尚未落地；vprot-vruntime 维度未评估。*next_action*：Vincent 发合并版（含注释更新）时可选择性地带上 vprot-vruntime 实验数据回应 Christian。

## 效果评估

本 patch 无单独效果数据；系列整体 benchmark 见 sched-20260921-001（09-21 当日文章，未在本次增量窗口）。Christian 要求的「full workload with different slice lengths」数据尚无人提供。

## 我可以参与的点

- `testing`：构造「短/中/长 slice 混合 + 无空闲 CPU」的负载，分别测 slice-only 与 vprot-vruntime 两种选 CPU 维度下各 slice 档位的延迟分布，直接回应 Christian 的数据请求——这是当前讨论最缺的一块。

## 参考链接

- Christian 的建议: https://lore.kernel.org/all/b37e8f1c-0cc7-4ca1-9e40-620d908464bf@arm.com/
- patch 8/8: https://lore.kernel.org/all/20260921152238.3804392-9-vincent.guittot@linaro.org/
- Vincent 09-29 回复: https://lore.kernel.org/all/CAKfTPtCyZRjjDWQxoHjG-SdJueTXBCZ4HesjPT0sPikb_dQtEw@mail.gmail.com/

---
id: sched-20261001-010
date: '2026-10-01'
subject: 'sched/eevdf: Add min slice check when selecting CPU'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20260921152238.3804392-9-vincent.guittot@linaro.org>'
lore_url: 'https://lore.kernel.org/all/b37e8f1c-0cc7-4ca1-9e40-620d908464bf@arm.com/'
authors:
  - 'Vincent Guittot'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260921152238.3804392-9-vincent.guittot@linaro.org>'
    date: '2026-09-21'
    summary: 'select_task_rq_fair 找不到空闲 CPU 时新增 select_slice_cpu() 比较 slice 选 CPU'
    review_outcome: 'Peter 建议复用初次扫描；Kayra 质疑 nr_idle_scan 语义；Vincent 宣布与 idle CPU 搜索合并；10-01 Christian 建议 vprot-vruntime 维度'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'select_slice_cpu 与 idle CPU 搜索的合并尚未落地'
    - 'Christian 建议的 vprot-vruntime 维度未评估'
  next_action: 'Vincent 发合并版并可选带上 vprot-vruntime 实验数据'
contribution_opportunities:
  - kind: testing
    description: '混合 slice 负载下对比 slice-only 与 vprot-vruntime 两种选 CPU 维度的延迟分布'
generated_at: '2026-10-09T01:00:00'
source_email_count: 1
related_articles:
  - sched-20260929-018
tags:
  - eevdf
  - load_balance
---
