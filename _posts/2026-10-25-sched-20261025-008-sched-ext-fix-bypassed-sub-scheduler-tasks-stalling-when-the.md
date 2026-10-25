---
id: sched-20261025-008
date: 2026-10-25
subject: 'sched_ext: Fix bypassed sub-scheduler tasks stalling when the host lacks
  caps'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261023175608.4120910-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20261023175608.4120910-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
- Andrea Righi
current_version: v3
patch_series:
- version: v1
  msgid: <20261022213836.2259069-1-tj@kernel.org>
  date: 2026-10-22
  summary: 14 patches：SCX_CAP_BASE 定为 bypass 唯一 cap，rescue 修复 + cap 感知 bypass 负载均衡
  review_outcome: sashiko 提出 keep 测试/注释/refusal 清单需修
- version: v2
  msgid: <20261023052452.2889061-1-tj@kernel.org>
  date: 2026-10-23
  summary: 15 patches：新增 expire prev slice、补 keep-last 注释、订正 refusal 原因
  review_outcome: 回应 sashiko 意见
- version: v3
  msgid: <20261023175608.4120910-1-tj@kernel.org>
  date: 2026-10-24
  summary: 17 patches + 18/17~20/17：bypass 先于 reenqueue 计数、rescue served time 从 charged
    runtime 计、失 BASE 时接纳迁移任务
  review_outcome: Andrea 对 17/17、19/17 各提一处非阻断设计疑问
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 未见对全系列逐 patch 的外部 review
  next_action: Tejun 回应 Andrea 的 head 保留与 watchdog_timeout 疑问后定稿
contribution_opportunities:
- kind: review
  description: 对 head 保留/普通平衡与 watchdog_timeout recheck 给出分析或补丁
- kind: testing
  description: 多层子调度器 + 快速 cap 撤销负载上回归 stall 路径与 watchdog 语义
generated_at: '2026-10-26T09:00:00'
source_email_count: 2
related_articles:
- sched-20261024-002
- sched-20261023-008
tags:
- sched_ext
title: 'sched_ext: Fix bypassed sub-scheduler tasks stalling when the host lacks caps'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/23/sched-20261023-008-sched-ext-fix-bypassed-sub-scheduler-tasks-stalling-when-the.html">sched-20261023-008</a>（v2）：Tejun Heo 发往 sched_ext/for-7.4 的 bypass stall 修复系列（15 patches）：bypassing 子调度器任务走 host 的 per-cpu bypass DSQ，而某 CPU 的 dispatch 只在 host 持有 `SCX_CAP_BASE` 时下钻，此前 bypass 放置与 bypass 负载均衡忽略这点，任务被排到「host 无 BASE」的 CPU 上卡死或循环。 修复把 `SCX_CAP_BASE` 定为唯一 cap、让 rescue 与 bypass 负载均衡 cap 感知。
- <a class="article-ref" href="/lkm/2026/10/24/sched-20261024-002-sched-ext-fix-bypassed-sub-scheduler-tasks-stalling-when-the.html">sched-20261024-002</a>（v3）：扩到 17 patches + 3 个跟进补丁（18/17、19/17、20/17），全部 `Reported-by: Sashiko`；修正 host 失 BASE 时 migration-disabled 任务放置、rescue served time 从 charged runtime 计等。
- <a class="article-ref" href="/lkm/2026/10/25/sched-20261025-008-sched-ext-fix-bypassed-sub-scheduler-tasks-stalling-when-the.html">sched-20261025-008</a>（今天）：Andrea Righi 上线 review，对 17/17 与 19/17 各提一处设计疑问（非阻断）：失 BASE 时是否该保留旧 head/普通负载均衡；watchdog 计时压 sch 后是否要 recheck `watchdog_timeout`。

## 背景与问题
（承接 v3）bypassing 调度器的任务走 host per-cpu bypass DSQ，但 CPU dispatch 只在 host 持 `SCX_CAP_BASE` 时下钻，任务可能被排到「host 无 BASE」的 CPU 原地卡住。v3 后今日新增 review 焦点：一个被 proxy 迁移的 blocked donor 会被远端 CPU 拒绝，若 host 仍持 BASE 时是否应保留旧 head 或走普通负载均衡，否则反复平衡 pass 可能一直把它推回队尾。

## 技术方案
（承接 v3）17 patches + 18/17~20/17 三个跟进（修 NONE rescuee UAF、stall watchdog 误责 bypassing owner、lone IMMED 等待）。今日无代码变更，为 design review 意见。

## 版本演进与当前进展
*current_version: v3*（`<20261023175608.4120910-1-tj@kernel.org>`）。当日收到 Andrea Righi 对 17/17（`<at4kd-78BbpBX-_4@gpd4>`）、19/17（`<at4l0yXTk7T_ouk0@gpd4>`）的回帖。

## Maintainer 意见与讨论焦点
Andrea Righi：
- 17/17（`sched_ext: Fix queued bypassed tasks stalling when the host loses SCX_CAP_BASE`）：非阻断，但质疑——donor 仍持 BASE 时是否该保留旧 head 或走普通负载均衡？一个被 proxy 迁移的 blocked donor 被远端 CPU 拒绝，反复平衡 pass 可能持续把它推回同一 DSQ 尾部。
- 19/17（`sched_ext: Fix the stall watchdog blaming a bypassing owner for a stuck task`）：改 sch 后是否该 recheck `watchdog_timeout`？stall 测试用的是 task owner 的 timeout，bypass 子任务若 timeout 很短，可能让 host 在 host 自身 timeout 到期前就被 eject。

## 合入评估
*likelihood=high*。Andrea 意见均为「Not a blocker」级的设计疑问，方向性无反对；系列的实质性 blocker 仍是「未见第二 reviewer 的全程确认」。*blocking_issues*：当日仍未见到对全系列逐 patch 的外部 review。*next_action*：Tejun 回应 Andrea 关于 head 保留与 watchdog_timeout 的两处疑问后定稿。

## 效果评估
无量化性能数据；仍是功能级验证（模型检查 + 多层压力测试）消除 stall。

## 我可以参与的点
- *kind: review*：对 Andrea 提出的「失 BASE 时保留旧 head / 普通平衡」与「watchdog_timeout recheck」给出分析或补丁。
- *kind: testing*：多层子调度器 + 快速 cap 撤销负载上回归两条 stall 路径，并为 watchdog 语义提供复习依据。

## 参考链接
- v3 cover: https://lore.kernel.org/all/20261023175608.4120910-1-tj@kernel.org/
- Andrea 17/17 回帖: https://lore.kernel.org/all/at4kd-78BbpBX-_4@gpd4/
- Andrea 19/17 回帖: https://lore.kernel.org/all/at4l0yXTk7T_ouk0@gpd4/
- 前文: <a class="article-ref" href="/lkm/2026/10/24/sched-20261024-002-sched-ext-fix-bypassed-sub-scheduler-tasks-stalling-when-the.html">sched-20261024-002</a> / <a class="article-ref" href="/lkm/2026/10/23/sched-20261023-008-sched-ext-fix-bypassed-sub-scheduler-tasks-stalling-when-the.html">sched-20261023-008</a>
