---
id: sched-20261020-012
date: 2026-10-20
subject: '[GIT PULL] sched_ext: Changes for v7.4'
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: <d66695d960cabf99877acde0c533c03e@kernel.org>
lore_url: https://lore.kernel.org/all/d66695d960cabf99877acde0c533c03e@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
current_version: null
patch_series: []
upstream_commit: 1f5dde349ac2fca1f119ae8de3f0d2f1c2a8d338
fixes_commit: null
merged_branch: sched_ext-for-7.4
merge_assessment:
  likelihood: high
  blocking_issues:
  - 当日缓存未见 Linus 合并确认回帖
  - 需在 sched/core 之后合入
  next_action: 等待 Linus 在 sched/core 之后收取本 pull
contribution_opportunities:
- kind: testing
  description: 在 v7.4 窗口 -rc 阶段回归 sched_ext + proxy execution / lazy preemption /
    sub-scheduler 场景
generated_at: '2026-10-21T01:30:00'
source_email_count: 1
related_articles: []
tags:
- sched_ext
- proxy_execution
title: '[GIT PULL] sched_ext: Changes for v7.4'
layout: article
---

## TL;DR

Tejun Heo 向 Linus 发 sched_ext 树的 v7.4 合入窗口 pull request（tag `sched_ext-for-7.4`，截至 `1f5dde349ac2`）。本次依赖 `sched/core`（携带 proxy execution 的 sched_ext hooks），需在其之后合入。亮点：proxy execution 可与 sched_ext 同时启用、lazy preemption、sub-scheduler 的 ecaps/CPU 委托可见性改进、新 kfuncs；另有 5 个在 v7.3 发布前数日进入 for-7.3-fixes 却错过发布窗口的修复随本次合入（其中 3 个标记 stable）。当日缓存未见 Linus 合并确认回帖。

## 背景与问题

v7.4 合入窗口开启，Tejun 汇总 sched-ext 树（`git://git.kernel.org/pub/scm/linux/kernel/git/tj/sched_ext.git`，tag `sched_ext-for-7.4`）提请 Linus 收取。sched_ext 是独立子系统树，此 pull 依赖 `sched/core` 携带的 proxy execution hooks，应在其之后合入。for-7.3-fixes 在本周期内六次合入 for-7.4，用于承接 CID cluster 工作所依赖的改动并解决与 proxy execution 开发的冲突。

## 技术方案

pull 范围（截至 `1f5dde349ac2fca1f119ae8de3f0d2f1c2a8d338`），主要变化：

- **5 个迟到的 for-7.3-fixes 修复**：在 v7.3 发布前数日进入 for-7.3-fixes 却错过发布窗口，随本 pull 合入，其中 3 个标记 stable——pick 重试期间残留的 balance callback、CPU 下线时的 use-after-free、可能卡住任务的 bypass bug。
- **proxy execution 兼容**：sched_ext 现可与 proxy execution 同时启用；BPF 调度器可选择接收「捐赠调度上下文给锁持有者的 mutex 阻塞任务」并自行放置。
- **lazy preemption**：BPF 调度器可像 fair 类一样延迟抢占/kick，把切换推迟到下次返回用户态或 tick。
- **sub-scheduler 增强**：父调度器现在能获知每个委托 CPU 上运行哪个 child、cap 变更何时生效；detaching child 在父调度器恢复 CPU 前先失去 caps。
- **新 kfuncs**：从 dispatch queue 迭代中重入队单任务、上报 cgroup 的 CPU 数、CID 的 NUMA 节点；CID 拓扑新增 cluster 维度。

## 版本演进与当前进展

*current_version: null*。pull request 当日发出（`<d66695d960cabf99877acde0c533c03e@kernel.org>`）。缓存内未见 Linus/pr-tracker-bot 合并确认回帖。

## Maintainer 意见与讨论焦点

Tejun Heo（sched_ext 维护者）作为发起人；Linus 侧无回帖（缓存内未见）。无争议。

## 合入评估

*likelihood=high*。例行 v7.4 窗口 pull，依赖的 `sched/core` proxy execution hooks 已就绪（需先合入）；内容均为此前各自 review 通过、进 for-next/for-7.4-fixes 的改动。*blocking_issues*：当日缓存未见 Linus 合并确认；需在 sched/core 之后合入。*next_action*：等待 Linus 在 sched/core 之后收取本 pull。

## 效果评估

无量化数据，属合并动作。各条改动的性能/正确性效果见其各自补丁系列的历史文章（proxy execution、lazy preemption、sub-scheduler ecaps 等，本日 006/007/008 即为其中几条的合入进展）。

## 我可以参与的点

- `testing`：本 pull 汇入后，在 v7.4 窗口 -rc 阶段集中回归 sched_ext + proxy execution 组合、lazy preemption、sub-scheduler 场景，为真实回归窗口提供信号。

## 参考链接

- GIT PULL：https://lore.kernel.org/all/d66695d960cabf99877acde0c533c03e@kernel.org/
