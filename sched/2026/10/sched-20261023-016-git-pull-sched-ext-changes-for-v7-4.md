# [GIT PULL] sched_ext: Changes for v7.4

## TL;DR
本文为增量更新，完整脉络见下。

- sched-20261020-012：Tejun Heo 向 Linus 发 sched_ext 树的 v7.4 合入窗口 pull request（tag `sched_ext-for-7.4`，截至 `1f5dde349ac2`）。亮点：proxy execution 与 sched_ext 可同时启用、lazy preemption、sub-scheduler 的 ecaps/CPU 委托可见性改进、新 kfuncs；另有 5 个错过 v7.3 发布窗口的 for-7.3-fixes 修复（其中 3 个标记 stable）随本 pull 合入。当日缓存未见 Linus 合并确认回帖。
- sched-20261023-016（今天）：**pr-tracker-bot 确认已合并进 torvalds/linux.git**，合并提交 `98aec86f8c6bf2e1091fefb99eaba8b910e8eef1`。sched_ext v7.4 窗口内容正式进入主线。

## 背景与问题
（承接 sched-20261020-012）v7.4 合入窗口，Tejun 汇总 sched-ext 树提请 Linus 收取。此 pull 依赖 `sched/core` 携带的 proxy execution hooks、需在其之后合入。今日进展即该依赖已满足、Linus 已收取。

## 技术方案
（承接 20261020-012）pull 范围截至 `1f5dde349ac2fca1f119ae8de3f0d2f1c2a8d338`：5 个迟到的 for-7.3-fixes 修复（3 个 stable）、proxy execution 兼容、lazy preemption、sub-scheduler 增强、新 kfuncs。今日无内容变化，仅为合并动作确认。

## 版本演进与当前进展
pull request 已于 10-19 发出（`<d66695d960cabf99877acde0c533c03e@kernel.org>`）；今日 pr-tracker-bot 回帖确认 merged，合并提交 `98aec86f8c6bf2e1091fefb99eaba8b910e8eef1`。

## Maintainer 意见与讨论焦点
无争议。pr-tracker-bot 为自动合并确认，代表 Linus 已收取。sched_ext 的 v7.4 窗口内容（含 3 个 stable 标记修复）进入主线，后续将随 v7.4 -rc 阶段接受回归验证。

## 合入评估
*likelihood=merged*。已合并进 torvalds/linux.git（合并提交 `98aec86f8c6bf2e1091fefb99eaba8b910e8eef1`），无剩余卡点。

## 效果评估
无量化数据，属合并动作。各条改动的性能/正确性效果见其各自补丁系列的历史文章。

## 我可以参与的点
- *kind: testing*：在 v7.4 -rc 阶段集中回归 sched_ext + proxy execution 组合、lazy preemption、sub-scheduler 场景，为回归窗口提供信号。

## 参考链接
- pr-tracker-bot 合并确认: https://lore.kernel.org/all/179270222039.170280.6235702575882879557.pr-tracker-bot@kernel.org/
- 合并提交: https://git.kernel.org/torvalds/c/98aec86f8c6bf2e1091fefb99eaba8b910e8eef1
- 前文: sched-20261020-012

---
id: sched-20261023-016
date: 2026-10-23
subject: "[GIT PULL] sched_ext: Changes for v7.4"
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: "<d66695d960cabf99877acde0c533c03e@kernel.org>"
lore_url: "https://lore.kernel.org/all/d66695d960cabf99877acde0c533c03e@kernel.org/"
authors: ["Tejun Heo"]
maintainers_involved: ["Tejun Heo"]
current_version: null
patch_series: []
upstream_commit: "98aec86f8c6bf2e1091fefb99eaba8b910e8eef1"
fixes_commit: null
merged_branch: "torvalds/linux.git (sched_ext-for-7.4)"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "随 v7.4 -rc 阶段回归验证"
contribution_opportunities:
  - kind: testing
    description: "v7.4 -rc 阶段回归 sched_ext + proxy execution / lazy preemption / sub-scheduler 场景"
generated_at: "2026-10-24T09:15:00"
source_email_count: 1
related_articles: ["sched-20261020-012"]
tags: [sched_ext, proxy_execution]
---