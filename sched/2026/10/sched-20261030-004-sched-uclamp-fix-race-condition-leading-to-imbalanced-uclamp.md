# sched/uclamp: Fix race condition leading to imbalanced uclamp_rq

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261025-001：Qais Yousef 发单补丁修 uclamp 的 static key 非原子翻转导致的 runqueue 计数失衡竞态，方案「视为既成事实 + idle 入口纠错」；lkp 当日报 `init_uclamp_rq` 链接错误。
- sched-20261026-002（v2）：修掉链接错误，idle 检测改 `WARN_ON(uclamp_is_imbalanced(rq))`；Peter 建议把 `uclamp_flags` 折进 hole、用 `UCLAMP_FLAG_IDLE` 判断是否需扫 bucket。
- sched-20261029-001（v4）：拆 2 补丁（1/2 修竞态 + 2/2 用 wrapper 换 open-coding 的 `UCLAMP_FLAG_IDLE`）；Christian 指出 CFS 带宽节流经 `dequeue_task_fair()` 递减 `nr_running` 却不调 `uclamp_rq_dec()`。
- sched-20261030-004（今天）：讨论从「idle-entry 纠错是否充分」升级为「CFS/RT 带宽节流的 partial-dequeue 不经过 core {en,de}queue、造成一个同时既 enqueued 又 dequeued 的“薛定谔任务”」。Peter 提议让 `throttle_cfs_rq_work()`/`tg_unthrottle_up()` 自己补 `uclamp_rq_{dec,inc}()`；Qais 认可并将此修复合入本栈；Christian 复现 RT 路径同样触发；Peter 要求审计**所有** `uclamp_enabled` 类，包括 sched_ext。Kayra 给 2/2 的 wrapper 改动 Reviewed-by。

## 背景与问题
（承接 20261025-001 → 20261029-001）原有主线是 static key 跨 CPU 非原子使能造成的 `uclamp_rq` 增而无减竞态。今日新暴露的更深一层：core 会为启用了 uclamp 的调度类维护 uclamp 计数，但**带宽节流却绕过 core 的 enqueue/dequeue** 直接操作任务，造成「任务既在队（throttle 前）又被部分 dequeue、而 uclamp 计数不动」的中间态——Christian 用 Sashiko 的原报与自己的复现证实这会真正触发 `uclamp_rq_dec_id()` 的 `WARN_ON_ONCE(!bucket->tasks)`（`active=1 && bucket->tasks=0`）。

## 技术方案
（承接 v4，今日为方向讨论）Peter 提出的替代/补充方案：与其继续纠结 idle-entry 纠错，不如让节流路径自己补 uclamp 记账——在 `throttle_cfs_rq_work()`（dequeue 侧）与 `tg_unthrottle_up()`（enqueue 侧）里，与它们已有的 `{de,en}queue_task_fair()` 配套地调用 `uclamp_rq_{dec,inc}()`。Qais 认同「bug 在节流路径而非当前补丁集方向」，并打算：
- 翻出此前「去掉 `uclamp_enabled` 位、改由 `enqueue/dequeue_task_$class` 统一处理」的旧补丁，评估是否复活；
- 把「节流路径补 uclamp 记账」作为独立修复并入本栈；
- 尚不确定是否给该独立修复打 `Fixes` 标签供 LTS 收取（qais 谨慎）。

Christian 补充：RT group throttling（`sched_rt_rq_dequeue()`）同样可以在不经 `uclamp_rq_dec` 的情况下复现 idle 路径问题，也需要一并修。Peter 收尾：所有 `uclamp_enabled` 的类都要审计，包含 sched_ext。

## 版本演进与当前进展
*current_version: v4*（2026-10-29 发出；今日无新版本，为深度 review 与范围扩展）。今日 Kayra 对 2/2（wrapper 化）给 Reviewed-by；1/2 的范围正在从「idle-entry 纠错」扩展为「节流路径正确 uclamp 记账」的更大修复集。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra（maintainer）**：主动给出「节流路径自己补 uclamp_rq_{dec,inc}」的具体方向，并强调要审计所有 uclamp_enabled 类（含 sched_ext）。态度正面、方向明确。
- **Qais Yousef（作者）**：认同 bug 在节流路径，愿意把该修复并入本栈；对是否打 Fixes/LTS 持谨慎。
- **Christian Loehle / Kayra Cizmeci**：Christian 复现并扩展范围到 RT；Kayra 给 2/2 Reviewed-by。
- **未解决**：修复的落点（是在 throttle 函数内补记账，还是去掉 `uclamp_enabled` 位统一走 class enqueue/dequeue）尚无定论；RT group throttling 与 sched_ext 的 audit 尚未展开。

## 合入评估
*likelihood=medium*。维护者已认可问题真实性并给出方向，2/2 已获 Reviewed-by；但 1/2 的核心方案演化为一个更大的节流-uclamp 记账修复集，涉及 RT 与 sched_ext 审计，范围扩大后短期内难以落地。*blocking_issues*：确定修复落点（throttle 内补记账 vs 去 `uclamp_enabled` 位）、RT/sched_ext 审计、是否 Fixes/LTS。*next_action*：作者发下一版，把节流路径的 uclamp 记账修复并入并补 RT 路径。

## 效果评估
Christian 在 PREEMPT_RT 的 Radxa Orion O6（arm64）上复现了 `WARN_ON_ONCE`（`kernel/sched/core.c:1845 uclamp_rq_dec_id`，`active=1 && bucket->tasks=0`），确认「确实 force idle + 计数失衡」为真。其余为逻辑推演，无性能数据。

## 我可以参与的点
- **review**：审计 RT group throttling（`sched_rt_rq_dequeue()`）与 sched_ext 的 uclamp_enabled 路径，确认哪些类存在同源「节流绕开 uclamp 记账」问题。
- **testing**：在 CFS/RT 带宽节流场景（cgroup cpu.max + RT runtime）复跑，验证修好后 `WARN_ON_ONCE(!bucket->tasks)` 不再触发。

## 参考链接
- lore thread（v4）: https://lore.kernel.org/all/20261029131354.11030-1-qyousef@layalina.io/

---
id: sched-20261030-004
date: 2026-10-30
subject: "sched/uclamp: Fix race condition leading to imbalanced uclamp_rq"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261029131354.11030-1-qyousef@layalina.io>"
lore_url: "https://lore.kernel.org/all/20261029131354.11030-1-qyousef@layalina.io/"
authors: [Qais Yousef]
maintainers_involved: [Peter Zijlstra]
current_version: v4
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "修复落点待定：throttle 函数内补 uclamp 记账 vs 去掉 uclamp_enabled 位走 class enqueue/dequeue"
    - "RT group throttling 与 sched_ext 的 uclamp_enabled 路径审计未完成"
  next_action: "作者发下一版，把节流路径 uclamp 记账修复并入并补 RT 路径"
contribution_opportunities:
  - kind: review
    description: "审计 sched_rt_rq_dequeue() 与 sched_ext 的 uclamp_enabled 节流路径"
  - kind: testing
    description: "在 CFS/RT 带宽节流场景复跑，验证 WARN_ON_ONCE(!bucket->tasks) 不再触发"
generated_at: "2026-10-31T09:00:00"
source_email_count: 8
related_articles: [sched-20261025-001, sched-20261026-002, sched-20261029-001]
tags: [uclamp, cfs]
---