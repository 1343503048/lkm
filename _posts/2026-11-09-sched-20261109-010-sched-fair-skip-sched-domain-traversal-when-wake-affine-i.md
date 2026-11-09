---
id: sched-20261109-010
date: '2026-11-09'
subject: 'sched/fair: Skip sched-domain traversal when wake affine is disabled'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261109120522.1704752-2-srikar@linux.ibm.com>
lore_url: https://lore.kernel.org/all/20261109120522.1704752-2-srikar@linux.ibm.com/
authors:
- Srikar Dronamraju
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261109120522.1704752-2-srikar@linux.ibm.com>
  date: '2026-11-09'
  summary: want_affine == false 时跳过 sched-domain 遍历，直接走 select_idle_sibling 快路径
  review_outcome: Kayra 指出 SD_BALANCE_WAKE 未设置、替代改法会改 behavior
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - SD_BALANCE_WAKE 不存在的前提问题待回应
  next_action: 作者回应 Kayra、澄清行为变化或改版
contribution_opportunities:
- kind: review
  description: 核实 SD_BALANCE_WAKE 是否真的未被设置，判断 WF_FORK 路径语义影响
- kind: testing
  description: 在 wake_wide 高频负载下测补丁的延迟影响
generated_at: '2026-11-10T09:00:00+08:00'
source_email_count: 2
related_articles: []
tags:
- load_balance
- cfs
- topology
title: 'sched/fair: Skip sched-domain traversal when wake affine is disabled'
layout: article
---

## TL;DR

Srikar Dronamraju 发单补丁：`select_task_rq_fair()` 中 when `want_affine == false`（`wake_wide()` 返回 true 或醒来的 CPU 不在任务允许 mask 内）的 TTWU wakeup 本已走快路径，但仍会进入 sched-domain 遍历随即 break——把这类 wakeup 直接跳入既有快路径，省掉无谓的 sd 遍历。Kayra Cizmeci 回帖指出 `SD_BALANCE_WAKE` 实际根本没被设置，并给出一个更直接的替代改法。

## 背景与问题

`select_task_rq_fair()` 里，`wake_wide()` 返回 true、或醒来的 CPU 不在任务 allowed CPU mask 内的 TTWU wakeup，`want_affine` 被置 false；这类 wakeup 不做 wake-affine 放置，现有代码已把它当快路径（在找到 SD_BALANCE_WAKE 域之前就退出 sched-domain 遍历，落回 `select_idle_sibling()`）。但即便如此，`select_task_rq_fair()` 仍会进入 sched-domain 遍历然后几乎立刻 break，属不必要的开销。

## 技术方案

补丁做四点清理：把 `want_affine` 移进使用它的 WF_TTWU 块；`want_affine == false` 时完全跳过 sched-domain 遍历；从 SD_WAKE_AFFINE 检查里删掉冗余的 `want_affine` 判断；删除对应的 `!want_affine` 循环终止逻辑。行为上保持既有放置语义不变。改动 `kernel/sched/fair.c` 9 行（+5/-4）。

Kayra 的评审意见：`SD_BALANCE_WAKE` 在代码里根本没被设置，所以「定位 SD_BALANCE_WAKE 域」的既有注释/逻辑本就不成立；若要做这件事，不如在 WF_TTWU 块里 `if (!want_affine) return select_idle_sibling(p, prev_cpu, new_cpu);`——但这会改变 WF_FORK/WF_TTWU 的行为（旧代码 WF_FORK=1、WF_TTWU=0 时跳过第一个 if 块再在 find domain 后走慢路径；新代码则返回 `select_idle_sibling()`）。

## 版本演进与当前进展

*current_version: v1（2026-11-09，`<20261109120522.1704752-2-srikar@linux.ibm.com>`）*。单补丁 v1，当日获 Kayra 一条评审。

## Maintainer 意见与讨论焦点

- **Kayra Cizmeci**：指出 `SD_BALANCE_WAKE` 未被设置、作者的前提之一不成立；提出替代改法但提醒其会改变 behavior（WF_FORK/WF_TTWU 语义）。属实现层面的再商榷，非反对优化方向。
- 尚无维护者（Peter/Vincent）表态。

## 合入评估

*likelihood=low*。优化方向（省掉无谓 sd 遍历）无异议，但实现细节被指「前提不成立、替代改法有行为变化」，需作者消化并可能改版；当前无人背书。*blocking_issues*：① `SD_BALANCE_WAKE` 不存在的前提问题待作者回应；② 是否值得为微优化改动热路径存疑。*next_action*：作者回应 Kayra、澄清行为变化或改版。

## 效果评估

无 benchmark，属清理性微优化；作者主张「保持放置语义、省掉无谓遍历」，但未给性能数据（作者主观判断，未见测试数据）。

## 我可以参与的点

- **review**：评估 `SD_BALANCE_WAKE` 是否真的任何地方都不设置（Kayra 的主张），并判断「跳过遍历」在 WF_FORK 路径的语义影响。
- **testing**：在 wake_wide 高频的负载（大量短任务 fork/wakeup）下测补丁的线程/延迟影响。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261109120522.1704752-2-srikar@linux.ibm.com/
- Kayra 的评审: https://lore.kernel.org/all/avHZrLRHmIgRu-a7@scheduler.schedules/
