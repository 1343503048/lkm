# sched_ext: Avoid unnecessary IMMED reenqueues on idle CPUs

## TL;DR
Andrea Righi 修 sched_ext 的一个效率缺陷：两个 IMMED 任务在空闲 CPU 上被唤醒时，内核会**不必要地把两个都踢回 BPF**，而不是让第一个留在本地 DSQ 待下一次 pick。根因是第二次插入触发的 reenqueue scan 里 `rq_is_open()` 看到 `next_class == ext` 就判定 CPU 不可用，尽管 CPU 仍在 idle。作者一天内从 v1 改到 **v2**：v2 改成「CPU idle 时即便 `next_class` 已被抬到 ext 也报告 rq 开放」，保留本地 DSQ 头、只把 head 之后的 IMMED 任务踢回 BPF。virtme-ng 4-vCPU 复现：10000 对唤醒里 9776 次不必要 head reenqueue，修复后归零。Tejun Heo 首轮 review 要求去掉 v1 的 core-sched cookie 检查（它在 idle core 上不成立）与独立的 skipped-head 记账修复，v2 已照做。

## 背景与问题
当两个 IMMED 任务在空闲 CPU 上被唤醒：第一次 wakeup 把任务插入 local DSQ 并在 CPU 离开 idle 前把 `rq->next_class` 抬到 ext；第二次插入排队一次 reenqueue scan。scan 里 `rq_is_open()` 看到 `next_class == ext` 就报告「CPU 不可用」，尽管 CPU 仍 idle，于是把 head 连同其后的任务一起 reenqueue 回 BPF，丢掉了一个本可被下一次 pick 采用的放置。该缺陷自 `SCX_ENQ_IMMED` 实现起就存在（`Fixes: 98d709cba319`），`Reported-by: Tejun Heo`。

## 技术方案
- **v1**：CPU idle 时保留本地 DSQ head 通过 reenqueue scan，若 core sched 使能则要求 cookie 匹配。
- **Tejun 的修正（吸收进 v2）**：① core-sched cookie 检查要拆出——IMMED 在其它地方也不正确处理 core sched（如 core sched 强制 CPU idle 时没人 reenqueue 其 local DSQ 上的 IMMED 任务），core sched 应单独成 patch；且该检查在 idle core 上根本不对（`sched_cpu_cookie_match()` 拿任务 cookie 比 `rq->core->core_cookie`，core-wide pick 从 max-priority pick 设置它，整核 idle 时为 0，带 cookie 的任务在 idle core 上唤醒反而过不了检查、仍被 reenqueue）。② skipped-head 记账修复也要拆出（是自 IMMED 实现就有的独立 gap，与 `rq_is_open()` 改动无关）。
- **v2（最终）**：在 CPU idle 时报告 rq 开放，即便本地插入已把 `next_class` 抬到 ext；只 +8 行，保留 DSQ head、head 之后的 IMMED 任务仍回 BPF。

## 版本演进与当前进展
*current_version: v2*（2026-10-29，`<20261029073508.3901589-1-arighi@nvidia.com>`）。

- **v1**（`<20261028165258.3723153-1-arighi@nvidia.com>`，2026-10-28）：保留 head + core-sched cookie 检查 + 独立 skipped-head 修复。
- **v2**（今日）：按 Tejun 意见去掉 cookie 检查与 skipped-head 修复，改为「idle 即报 rq 开放」。目标分支 `sched_ext/for-7.4-fixes`。

## Maintainer 意见与讨论焦点
- **Tejun Heo（sched_ext 维护者）**：明确「core-sched cookie 检查别放本 patch」——core sched 的 IMMED 处理不完整，需独立 patch；并详细说明 cookie 检查在 idle core 上失效的原因（core_cookie 为 0）；同时要求拆掉 skipped-head 记账修复。v2 全部照做。
- 未解决焦点：core sched 下 IMMED 的完整处理被明确留待独立 patch，本 fix 只覆盖非 core-sched 场景；skipped-head 记账 gap 亦被留待独立 patch。

## 合入评估
*likelihood=high*。目标是 `sched_ext/for-7.4-fixes` 修复分支，Tejun 亲自报障并 review、方向明确，v2 已收敛到最小改动（+8 行）且满足其拆解要求。*blocking_issues*：暂无实质阻塞，等 Tejun 对 v2 的最终 Ack 后即可进 for-7.4-fixes。*next_action*：Tejun 确认 v2 后合入 for-7.4-fixes。

## 效果评估
作者给出两套复现的量化：① virtme-ng 4-vCPU，两个 futex waiter 钉在 CPU0、从 CPU2 一起唤醒，BPF 调度器用 `SCX_ENQ_IMMED` 插入 local DSQ，10000 对唤醒里内核 instrumentation 计数 **9776 次不必要 head reenqueue**（CPU idle 且 next_class==ext），修复后该计数为 0（head 之后的 IMMED 任务仍回 BPF）；② core sched 复现（1ms 内核 mutex 持有 + weighted-vruntime BPF 调度器 + SCX_OPS_ENQ_BLOCKED/ALWAYS_ENQ_IMMED），2000 次/例里 waiter 收到 154（同 CPU owner）/187（跨 CPU owner）次 IMMED reenqueue，v1 修复后归零。注意第二套 core-sched 数字对应 v1 的 cookie 检查，v2 已移除该检查（core-sched 场景留给独立 patch），故 v2 的收益集中在第一套非 core-sched 场景。

## 我可以参与的点
- **testing**：在启用 core sched 的 sched_ext BPF 调度器上验证 v2 行为，确认「IMMED + core sched」在无独立 patch 前是否还有可感知的异常，为 Tejun 提到的独立 core-sched patch 收集数据。
- **review**：核对 v2 的 `rq_is_open()` 改动是否影响其它依赖 `next_class` 判断的路径（如别的 reenqueue/scan 分支）。

## 参考链接
- lore thread（v1）: https://lore.kernel.org/all/20261028165258.3723153-1-arighi@nvidia.com/
- v2: https://lore.kernel.org/all/20261029073508.3901589-1-arighi@nvidia.com/
- Tejun Heo 的 review: https://lore.kernel.org/all/019648c2b11a3aa6a9b14723df813d65@kernel.org/

---
id: sched-20261029-012
date: 2026-10-29
subject: "sched_ext: Avoid unnecessary IMMED reenqueues on idle CPUs"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261028165258.3723153-1-arighi@nvidia.com>"
lore_url: "https://lore.kernel.org/all/20261028165258.3723153-1-arighi@nvidia.com/"
authors: [Andrea Righi]
maintainers_involved: [Tejun Heo]
current_version: v2
patch_series:
  - version: v1
    msgid: "<20261028165258.3723153-1-arighi@nvidia.com>"
    date: 2026-10-28
    summary: "保留 local DSQ head + core-sched cookie 检查 + 独立 skipped-head 记账修复"
    review_outcome: "Tejun 要求去掉 cookie 检查与 skipped-head 修复，并指出 cookie 检查在 idle core 上失效"
  - version: v2
    msgid: "<20261029073508.3901589-1-arighi@nvidia.com>"
    date: 2026-10-29
    summary: "CPU idle 即报 rq 开放，保留 DSQ head；去掉 cookie 检查与 skipped-head 修复（+8 行）"
    review_outcome: "等待 Tejun 对 v2 的最终 Ack"
upstream_commit: null
fixes_commit: "98d709cba319"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "Tejun 确认 v2 后合入 sched_ext/for-7.4-fixes"
contribution_opportunities:
  - kind: testing
    description: "在启用 core sched 的 BPF 调度器上验证 v2 行为，为独立 core-sched patch 收集数据"
  - kind: review
    description: "核对 rq_is_open() 改动是否影响其它依赖 next_class 判断的路径"
generated_at: "2026-10-30T09:30:00"
source_email_count: 3
related_articles: []
tags: [sched_ext]
---