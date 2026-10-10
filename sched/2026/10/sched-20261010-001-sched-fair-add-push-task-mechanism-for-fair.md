# sched/fair: Add push task mechanism for fair

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261009-004：Vincent Guittot 的 18 补丁 v2「Improving latency of short slice tasks」系列，通过 EEVDF lag/slice 改进 + 新引入的 fair push 任务机制（把排不上本 CPU 或不该在本 CPU 的任务推到更合适的 CPU）+ EAS slice 整合来降低短 slice 任务时延；当日 Tim Chen/Kayra/Chen Yu 密集 review，抓出 force-push 早退、static key 泄漏、slice 判断顺序等问题，作者确认修，v3 在望。
- sched-20261010-001（今天）：讨论转向 push 机制的「cache-aware 调度」潜在使用者——Vincent 问「为何不在 wakeup 路径也迁移任务」，Chen Yu 回应：wakeup 路径聚合太快、多 CPU 无同步地往同一 LLC 迁任务，曾在启用 cache-aware wakeup 迁移时观察到 task bouncing；建议到最新内核复查是否仍如此、能否缓解。

## 背景与问题
（承接 sched-20261009-004）短 slice 任务在 EEVDF 下仍有两类时延来源：EEVDF lag/slice 记账让唤醒后未必能在最快 CPU 上跑；CFS 也没有类似 RT 的 push 机制。push 机制被设计成「默认不启用、被使用者触发才开」（`sched_push_task` static branch），短 slice 任务是第一个使用者，作者明确 cache-aware 调度是后续扩展方向（Vincent 10-09：「the cache-aware scheduler is one that could also take advantage」）。

今天的具体问题是 cache-aware 作为 push 使用者的**迁移路径选择**：Chen Yu 先前提出让 cache-aware 敏感任务走 push 路径被推到 preferred LLC；Vincent 追问为何不在 wakeup 路径直接迁移。Chen Yu 今天回应——wakeup 路径聚合任务太快、多 CPU 会无同步地把任务迁到同一 LLC，启用 cache-aware wakeup 迁移时观察到 task bouncing。

## 技术方案
（承接系列方案）push 机制默认关闭、由使用者触发；对 cache-aware 敏感任务，可用 push 路径推到 preferred LLC。今天不涉及代码改动，是一轮迁移路径的设计讨论：

- Vincent 的问题（10-09）：「Is there any reason that you don't want to migrate the task at wakeup too?」——push 与 wakeup 两处选核本应一致，质疑为何不把 cache-aware 迁移也放进 wakeup 路径。
- Chen Yu 的回应（今天）：wakeup 路径对任务的聚合发生得太快，多个 CPU 会在没有同步的情况下竞相把任务迁到同一 LLC，导致 task bouncing（任务在 LLC 间来回弹跳）。他倾向 push（触发门槛更高、频次更低，能降低与 cache-aware 负载均衡器的竞争），但未否定 wakeup 迁移，建议「We can double-check in the latest kernel to see if that is still the case, and to see if we can mitigate that」——即先复查最新内核里该 bouncing 是否仍存在、能否缓解。

## 版本演进与当前进展
*current_version: v2*（系列整体 18 枚，`<20261002154415.2270586-1-vincent.guittot@linaro.org>`）。今天无新版发出：

- Chen Yu 回帖（`<aspc8doovTKdBqPC@chenyu-dev>`）：回应 Vincent「为何不在 wakeup 迁移」的提问，给出 task bouncing 观察，并提议到最新内核复查、看能否缓解。
- 该枚 patch（07/18 push mechanism）本身无版本变化；系列 v2 的 bug 修正（static key 泄漏等）仍待作者落地后发 v3。

## Maintainer 意见与讨论焦点
- **Vincent Guittot**（作者 / sched 维护者）：10-09 追问为何不在 wakeup 路径迁移（push 与 wakeup 选核应一致）；同时确认 cache-aware 是 push 的潜在使用者。
- **Chen Yu**（Intel）：今天解释 wakeup 路径的 task bouncing 现象，倾向 push 是 cache-aware 的合适载体。
- 分歧点：cache-aware 敏感任务的「迁移时机」——wakeup 内联迁移 vs push 机制。属设计讨论、尚无定论，无 NAK。

## 合入评估
*likelihood=medium*（系列整体）。push 机制是系列核心之一、方向无争议；但 cache-aware 使用者的迁移路径（wakeup vs push）刚展开讨论，需 Chen Yu 复查最新内核的 bouncing、Vincent 据此决定是补 wakeup 迁移还是继续 push-only。*blocking_issues*：cache-aware 迁移路径尚无结论；系列 v2 修 bug 后尚未发 v3。*next_action*：Chen Yu 复查最新内核 wakeup 迁移 bouncing；Vincent 发系列 v3。

## 效果评估
本枚 patch 独立的 cache-aware 效果数据暂无。此前的 hackbench 实测（Chen Yu 10-07，Xeon 192 核）为 push 系列整体：8 组 hackbench 模式中 3 改进 / 5 退化（最大退化 threads 8×20 为 -7.42%），作者当时判断「没有明显差异」。今天关于 task bouncing 的讨论为定性描述，未见量化数据。

## 我可以参与的点
- 在最新内核上复测「cache-aware 迁移在 wakeup 路径的 task bouncing」并回帖数据（这正是 Chen Yu 提议的 double-check）；
- 若有大小核 / EAS 平台，可验证 push 机制对短 slice 任务时延的影响。

## 参考链接
- 系列 cover: https://lore.kernel.org/all/20261002154415.2270586-1-vincent.guittot@linaro.org/
- patch 07/18: https://lore.kernel.org/all/20261002154415.2270586-8-vincent.guittot@linaro.org/
- Chen Yu 今日回帖: https://lore.kernel.org/all/aspc8doovTKdBqPC@chenyu-dev/

---
id: sched-20261010-001
date: '2026-10-10'
subject: 'sched/fair: Add push task mechanism for fair'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20261002154415.2270586-1-vincent.guittot@linaro.org>'
lore_url: 'https://lore.kernel.org/all/20261002154415.2270586-1-vincent.guittot@linaro.org/'
authors:
  - 'Vincent Guittot'
maintainers_involved:
  - 'Vincent Guittot'
  - 'Chen Yu'
current_version: v2
patch_series:
  - version: v2
    msgid: '<20261002154415.2270586-1-vincent.guittot@linaro.org>'
    date: '2026-10-02'
    summary: '18 枚系列中的 07/18：为 CFS 引入类似 RT push 的公平任务 push 机制'
    review_outcome: 'cache-aware 作为 push 使用者的迁移路径（wakeup vs push）今日展开讨论'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'cache-aware 迁移路径（wakeup vs push）尚无结论'
    - '系列 v2 修 bug 后尚未发 v3'
  next_action: 'Chen Yu 复查最新内核 wakeup 迁移 bouncing；Vincent 发系列 v3'
contribution_opportunities:
  - kind: testing
    description: '在最新内核复测 cache-aware wakeup 迁移的 task bouncing 并回帖数据'
  - kind: review
    description: '在大小核/EAS 平台评估 push 机制对短 slice 时延的收益'
generated_at: '2026-10-11T09:00:00'
source_email_count: 1
related_articles:
  - sched-20261009-004
tags:
  - cfs
  - load_balance
---