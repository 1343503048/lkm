---
id: sched-20260827-004
date: '2026-08-27'
subject: 'sched/proxy: Defer donor commit until after proxy resolution'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260827-sched-proxy-v3-1-1af63ac5ae56@zohomail.com>
lore_url: https://lore.kernel.org/all/20260827-sched-proxy-v3-1-1af63ac5ae56@zohomail.com/
authors:
- Xukai Wang
maintainers_involved: []
current_version: v3
patch_series:
- version: v1
  msgid: null
  date: 2026-07-07
  summary: 首次提出推迟 donor 提交；讨论中给出重试频率测量
  review_outcome: 见 sched-20260810-007
- version: v2
  msgid: <20260713-sched-proxy-v2-0-729170082633@zohomail.com>
  date: 2026-07-13
  summary: put_prev_set_next_task()/rq_set_donor() 移到 proxy 分支之后；zap_balance_callbacks()
    移入 proxy_resched_idle()
  review_outcome: 未获取到
- version: v3
  msgid: <20260827-sched-proxy-v3-1-1af63ac5ae56@zohomail.com>
  date: 2026-08-27
  summary: 数据进 changelog；保存/恢复 rq->dl_server；donor 与执行任务显式区分；修 W=1 警告
  review_outcome: 当日暂无 review 意见
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 依附的 CONFIG_SCHED_PROXY_EXEC 本体仍在 RFC 阶段
  - 只测了频率未测开销，收益论证不完整
  next_action: 等维护者表态或补端到端开销数据
contribution_opportunities:
- kind: testing
  description: 量化被放弃的 put_prev/set_next 回调的周期开销并回帖
- kind: discussion
  description: 结合 04/16 sleeping-owner 讨论线给出 donor 生命周期的一致性分析
generated_at: '2026-09-07T22:05:00'
source_email_count: 1
related_articles:
- sched-20260810-007
tags:
- preempt
- deadline
title: 'sched/proxy: Defer donor commit until after proxy resolution'
layout: article
---

## TL;DR
本文为增量更新（完整背景见 related_articles）。Xukai Wang 发出 v3：把 `pick_next_task()` 的"选择"与"提交"（`put_prev_set_next_task()`）解耦，推迟到 proxy 解析成功之后。v3 的最大变化是把 v1 讨论里的量化数据正式写进 commit message——60 秒压测中被放弃的 blocked donor 提交有 3224 次，且重试**从不**选中同一个 donor，把问题从"看着冗余"升级为"有数据支撑的浪费"。当日无人回复。

## 背景与问题
proxy execution 下 `pick_next_task()` 可能选中一个 blocked donor，它还要过 `find_proxy_task()`；若解析返回 NULL，`__schedule()` 走 pick_again 重选，但上一轮已经为被放弃的候选做过 `put_prev_task()`/`set_next_task()`，紧接着又为新候选再做一遍。作者在无该补丁的内核里加临时计数器实测（60 秒 proxy-mutex 压测）：`spec_commit_blocked` 5407 次，其中解析失败重试 3224 次、解析直接落到 idle 1660 次、成功 523 次；3224 次失败重试里 0 次选回同一 donor，2258 次选了别的 donor，966 次落到 idle——即已提交的工作几乎全部作废。作者同时声明：这些计数器只度量发生频率，回调的周期开销与端到端影响未测。

## 技术方案
`pick_next_task()` 只返回候选；提交移到 `__schedule()` 中 proxy 解析之后：

```
donor = pick_next_task(rq, &rf);
next = donor;
...
next = find_proxy_task(rq, donor, &rf);
...
put_prev_set_next_task(rq, rq->donor, donor);
rq_set_donor(rq, donor);
```

候选被放弃时直接丢弃，不做 sched-class 的 put_prev/set_next。连带两个语义修正：(1) 推迟提交改变了 `find_proxy_task()` 看到的 `rq->dl_server` 状态（原来 `put_prev_set_next_task()` 已消费并清空它），v3 在解析期间保存/清空并在成功时才恢复；(2) proxy 候选不再必然是已提交的 `rq->donor`，`proxy_deactivate()` 只在候选仍是已提交 donor 时才先切 idle，`zap_balance_callbacks()` 移入 `proxy_resched_idle()` 并用 `CONFIG_SCHED_PROXY_EXEC` 保护。

## 版本演进与当前进展
- v1：2026-07-07 发出（07 月的讨论里首次给出重试频率数据，见 sched-20260810-007）。
- v2：2026-07-13：把最终的 `put_prev_set_next_task()`/`rq_set_donor()` 移到 proxy/非 proxy 分支之后；`zap_balance_callbacks()` 从 NULL/idle 路径移入 `proxy_resched_idle()`。
- v3（本日）：补 motivation 与实测数据；处理 `rq->dl_server` 语义；donor/执行任务在 `__schedule()` 中显式区分；保住常见路径"先提交再刷新同 donor 的 sched-class 回调"的既有顺序；修 kernel test robot 报的 W=1 !CONFIG_SCHED_PROXY_EXEC unused-function 警告。
- 当日无 review 回复。

## Maintainer 意见与讨论焦点
v3 当天无人表态。历史上该思路属于 Peter Zijlstra/社区对 proxy-exec "donor 与运行任务要区分"的讨论线；v3 的 changelog 显示它在回应的两类问题：DL server 状态在解析窗口的可见性、以及 W=1 编译警告。未解决点：作者自己承认只量化了频率、没量化开销——维护者完全可能以"那到底浪费了多少周期"要求补数据。

## 合入评估
**unclear**。补丁本身质量在改善（数据进 changelog、语义边界处理细致），但它依附的 `CONFIG_SCHED_PROXY_EXEC` 整体仍在多轮 RFC 阶段（本日 Prateek 的 PoC 也在同一主题下讨论），单木难成林；此类重构通常要随 proxy-exec 主系列一起收。`blocking_issues`：proxy-exec 本体未定稿；缺端到端开销数据。`next_action`：等 maintainer 对数据与 dl_server 处理方式的表态，或补周期开销测量。

## 效果评估
仅有频率数据（5407/3224/1660/523，重试 0 次同 donor），作者明确标注"cycle cost 与端到端影响未测"——不能据此声称性能收益，属主观预期。

## 我可以参与的点
- 补作者没做的测量：在 proxy-exec 实验树上量化被放弃的 put_prev/set_next 的周期开销（perf tracepoint 即可），回帖就是该系列缺的那块证据。
- 与 0831 的 Andrea/Prateek 讨论线（donor-owner 关系）有交叉，做过 proxy mutex 压测的机型数据都有价值。

## 参考链接
- v3 本封: https://lore.kernel.org/all/20260827-sched-proxy-v3-1-1af63ac5ae56@zohomail.com/
- v2（作者 changelog 内给出的 patch.msgid.link 链接）: msg `20260713-sched-proxy-v2-0-729170082633@zohomail.com`
- tip-bot commit: 未获取到
- stable backport: 未获取到
