---
id: sched-20260912-012
subject: 'sched/fair: Only apply cpufreq pressure where frequency is invariant'
date: '2026-09-12'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260821073927.455475-1-wujianyong@hygon.cn>
lore_url: https://lore.kernel.org/all/SI2PR04MB4931A8BA0EF213B0238BD9E4E3BD2@SI2PR04MB4931.apcprd04.prod.outlook.com/
authors:
- Jianyong Wu
maintainers_involved:
- Vincent Guittot
- K Prateek Nayak
current_version: v3
patch_series:
- version: v3
  msgid: null
  date: null
  summary: 承 sched-20260910-009 的覆盖时点（当日缓存未收到 v3 正文）。
  review_outcome: 09-09 Prateek 提问；09-12 作者认领并宣布按 Vincent 意见换方向：boost 状态切换间保持参考频率固定。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 重写版本（预期 v4）未发出，新方案无设计细节
  next_action: 等作者新版本（设计说明+数据）；关注参考频率固定方案的实现路径
contribution_opportunities:
- kind: review
  description: 新版发出后审参考频率取值点与 boost 抖动稳定性
generated_at: '2026-09-14T12:40:00'
source_email_count: 1
related_articles:
- sched-20260910-009
- sched-20260908-008
tags:
- cfs
- cpufreq
title: 'sched/fair: Only apply cpufreq pressure where frequency is invariant'
layout: article
---

## TL;DR
Jianyong Wu 当日回应 K Prateek Nayak 09-09 的提问，认领后续工作：愿意按 Vincent 的跟进意见重构方案——在 boost 状态切换之间保持参考频率（reference frequency）固定。系列仍处于「作者重写中、等待新版本」状态。本文为增量更新，此前多轮覆盖见 <a class="article-ref" href="/lkm/2026/09/10/sched-20260910-009-sched-fair-only-apply-cpufreq-pressure-where-frequency-is-in.html">sched-20260910-009</a> 及其相关文章。

## 背景与问题
（承 <a class="article-ref" href="/lkm/2026/09/10/sched-20260910-009-sched-fair-only-apply-cpufreq-pressure-where-frequency-is-in.html">sched-20260910-009</a>）cpufreq pressure（IO/CPU 压力信号对频率的影响）只在频率不变（frequency invariant）平台上生效的系列；讨论聚焦 boost 状态切换时参考频率漂移导致的压力计算失真，Vincent 与 Prateek 先后给出方向性意见。

## 技术方案
当日无新代码。Jianyong 的回应要点：「Thanks for asking, I would happy to take a stab at this. Based on Vincent's follow-up, I think we may need a different approach to keep the reference frequency fixed across boost state changes.」——即接受 Vincent 的跟进意见，放弃在现有实现上打补丁，转向「boost 切换间固定参考频率」的新方案。具体设计未在缓存中给出。

## 版本演进与当前进展
*current_version: v3（承 <a class="article-ref" href="/lkm/2026/09/10/sched-20260910-009-sched-fair-only-apply-cpufreq-pressure-where-frequency-is-in.html">sched-20260910-009</a> 的覆盖时点；当日缓存仅作者回应一封，无新版本）*。

- 系列已多轮覆盖（09-02-008/09-03-010/09-07-006/09-08-008/09-09-012/09-10-009）；
- 09-09 Prateek 提问 → 09-12 作者认领并宣布换方向。重写版本（预期 v4）未发出。

## Maintainer 意见与讨论焦点
- **Vincent Guittot**（承前）：follow-up 意见成为作者新方案的依据；
- **K Prateek Nayak**（09-09）：提出的问题促成本次认领；
- 分歧未闭合处：「boost 状态间固定参考频率」的新方案尚无设计细节，是否引入新的 per-policy 状态/接口未知。

## 合入评估
*likelihood=medium*：作者与两位评审的沟通顺畅、方向明确（重构而非修补）；但新方案未成形。*blocking_issues*：重写版本未发出；「固定参考频率」的实现路径与开销未披露。*next_action*：等作者的新版本（预期含设计说明与数据）；关注方案是否仍限定在 frequency-invariant 平台。

## 效果评估
无新效果数据（承前：系列的核心收益数据在早期版本，v3 之后以设计讨论为主）。

## 我可以参与的点
- kind=review：新版本发出后，重点审「boost 切换间固定参考频率」的实现——参考频率的取值点（policy 级还是 CPU 级）与 boost on/off 抖动场景下的稳定性，这是 Vincent/Prateek 意见的技术核心。

## 参考链接
- Jianyong Wu 的认领回帖：https://lore.kernel.org/all/SI2PR04MB4931A8BA0EF213B0238BD9E4E3BD2@SI2PR04MB4931.apcprd04.prod.outlook.com/
- 系列线程根（v1，08-21，msgid 取自当日回帖 References）：https://lore.kernel.org/all/20260821073927.455475-1-wujianyong@hygon.cn/
