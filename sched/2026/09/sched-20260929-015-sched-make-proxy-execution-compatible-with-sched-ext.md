# sched: Make proxy execution compatible with sched_ext

> **subject**：`sched: Make proxy execution compatible with sched_ext`

## TL;DR

本文为增量更新，完整脉络见 related_articles。本系列的目标是让 proxy execution 与 sched_ext 可扩展调度类兼容——proxy execution 把阻塞在互斥量上的任务（donor）的调度上下文借给锁持有者运行，sched_ext 需要一组 hook 才能在这一机制下正确记账。

- sched-20260927-004：Tejun 回复「I can pull from sched/core and then apply sched_ext parts on top」，分区敲定——Peter 收 core 侧、Tejun 收 sched_ext 侧。
- sched-20260928-002：Peter 把本系列 5 枚 core/hook 预备补丁全部应用到 tip/sched/core；core 侧与 hook 骨架已落地，sched_ext 功能实现待 Tejun 侧跟进。
- sched-20260929-015（今天）：Tejun 把 6-16 应用到 sched_ext/for-7.4（在 tip/sched/core `be100c77178e` 之上，附多段冲突解决说明），并请作者验证；Andrea 重跑全部 proxy-exec 测试，冲突解决无问题、仅见无关的 virtio console 警告。

## 背景与问题

（承接 sched-20260928-002）proxy execution 让阻塞任务把执行上下文「借」给锁持有者运行，sched_ext 的 donor 记账、tick 归属、限流语义都与 core 调度路径强耦合，需要一组 sched_ext 侧 hook 才能在 proxy execution 下正确工作。核心张力：Peter 不喜欢 sched_ext 专属 hook，但也不喜欢把 sched_ext 逻辑塞进 core。今天背景无新增，进展是 sched_ext 功能侧实际落地。

## 技术方案

（承接）本系列在 `__schedule()` 三个点位暴露 sched_ext 观察点：`scx_allow_proxy_exec()`、`scx_proxy_donor_start()`、`scx_proxy_reenqueue_retry()`。今天无新代码，进展是 Tejun 应用 6-16 到 sched_ext/for-7.4 时列出的一系列冲突解决（针对 `c72945693b90` 改 `set_next_task_scx()` 签名、`7a919c7f86de` 拆分 `scx_reenq_reject()`、`7de9a6fb44ea` 保留 `scx_reenq_wait_dispatching()`、`be100c77178e` 已含修复后的 `scx_proxy_reenqueue_retry()` 签名、`cb86607ada73` 的上下文变化等），均已在应用时处理。

## 版本演进与当前进展

*current_version: v14*。9/29 进展：Tejun Heo 把本系列 6-16 应用到 `sched_ext/for-7.4`（基于 tip/sched/core `be100c77178e`），并请 Andrea 验证冲突解决；Andrea Righi 回复「reran all my proxy-exec tests on sched_ext/for-7.4. The conflict resolutions look good. The only issues I saw were unrelated virtio console warnings... fixed by b144dc5a2414. Otherwise, everything works great!」。core 侧（5 枚预备补丁）此前已进 tip/sched/core，现在 sched_ext 功能实现也进入 for-7.4。

## Maintainer 意见与讨论焦点

- **Tejun Heo**（sched_ext 维护者）：应用 6-16 到 for-7.4，附详细冲突解决清单，请作者验证。
- **Andrea Righi**（作者/维护者）：验证通过，冲突解决无问题，仅发现无关的 virtio console 警告（已由 `b144dc5a2414` 修复）。
- 无 NAK。无遗留分歧——此前「hook 职责耦合」的代码组织讨论不构成障碍。

## 合入评估

*likelihood=merged*。core 侧 5 枚补丁已进 tip/sched/core，sched_ext 功能实现（6-16）已进 sched_ext/for-7.4，作者验证通过。*blocking_issues*：无实质项（等待 sched_ext/for-7.4 随 7.4 合并窗口进 mainline）。*next_action*：跟踪 sched_ext/for-7.4 随 7.4 合并窗口的 PR。

## 效果评估

作者自述「reran all my proxy-exec tests... everything works great」，未附 benchmark 数字；正确性由自测背书，暂无量化性能数据。

## 我可以参与的点

- `testing`：在 sched_ext + proxy execution 组合下跑互斥锁竞争压力测试，补充 donor 记账/tick 路径的实测覆盖。
- `review`：评估已落地的 sched_ext hook 实现中 `SNT_CONFIRM` 等 hook 的职责耦合（此前作者自评「looks a bit confusing」）。

## 参考链接

- lore（v14 cover）: https://lore.kernel.org/all/20260922165445.943315-1-arighi@nvidia.com/
- Tejun 应用 6-16: https://lore.kernel.org/all/72d8d44fee50dc88f500bdb808eb21f6@kernel.org/
- Andrea 验证: https://lore.kernel.org/all/arrSdAzAUpkjbFng@gpd4/

---
id: sched-20260929-015
date: '2026-09-29'
subject: 'sched: Make proxy execution compatible with sched_ext'
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: '<20260922165445.943315-1-arighi@nvidia.com>'
lore_url: 'https://lore.kernel.org/all/20260922165445.943315-1-arighi@nvidia.com/'
authors:
  - 'Andrea Righi'
maintainers_involved:
  - 'Tejun Heo'
  - 'Peter Zijlstra'
current_version: v14
patch_series:
  - version: v14
    msgid: '<20260922165445.943315-1-arighi@nvidia.com>'
    date: '2026-09-22'
    summary: '重做 donor 确认机制、删 scx_proxy_donor_start()，hrtick v4 前置'
    review_outcome: '09-28 Peter 收 5 枚 core/hook 预备补丁进 tip/sched/core；09-29 Tejun 应用 6-16 进 sched_ext/for-7.4，Andrea 验证通过'
upstream_commit: null
fixes_commit: null
merged_branch: 'tip/sched/core'
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: '跟踪 sched_ext/for-7.4 随 7.4 合并窗口的 PR'
contribution_opportunities:
  - kind: testing
    description: '在 sched_ext + proxy execution 组合下跑互斥锁竞争压力测试补实测覆盖'
  - kind: review
    description: '评估已落地的 sched_ext hook 实现中 SNT_CONFIRM 等 hook 的职责耦合'
generated_at: '2026-09-30T01:15:00'
source_email_count: 2
related_articles:
  - sched-20260928-002
  - sched-20260927-004
tags:
  - sched_ext
  - proxy_execution
---