---
subject: 'sched_ext: Bandwidth-limited rescue execution for stranded tasks'
id: sched-20260803-001
date: 2026-08-03
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260801085150.2697653-1-tj@kernel.org>
lore_url: https://lore.kernel.org/lkml/20260801085150.2697653-1-tj@kernel.org
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
current_version: v2
patch_series:
- version: v1
  msgid: <20260801085150.2697653-1-tj@kernel.org>
  date: 2026-08-01
  summary: 首次提出内核侧 rescue 执行机制：scheduler 用 SCX_ENQ_RESCUE 标记可能被 cap 拒绝的入队，内核以小带宽运行该任务，超时未服务则升级为
    protected 执行；过载时 eject 消耗最高的子调度器。
  review_outcome: 由 sashiko AI 做了一轮 review，指出若干实现问题。
- version: v2
  msgid: <20260803055435.2697653-1-tj@kernel.org>
  date: 2026-08-03
  summary: 按 AI review 修正：scx_sched_all 移出 CONFIG_EXT_SUB_SCHED 块（无条件定义）；overload
    grace 与 usage-decay 时间戳改用 jiffies_64 防 32 位回绕；删除未读的 always_enq_immed rodata 镜像。共
    12 个 patch。
  review_outcome: v2 刚发出，暂无明显 NAK，AI review 已消化。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待社区（尤其 SCX 子调度器方向的 reviewer）对 overload ejection 与 protected 升级语义的反馈；按惯例
    Tejun 自行维护 for-next，合入阻力小。
contribution_opportunities:
- kind: testing
  description: 在子调度器持有 caps 且任务亲和不在授予 cid 上的场景下压测，验证 rescue 升级为 protected 后是否真能避免
    watchdog stall，并回帖数据。
- kind: review
  description: overload ejection 选择『最近 rescue 消耗最高』的子调度器这一启发式是否最优，可提出更公平的驱逐策略（如按 cpu
    维度加权）。
generated_at: '2026-08-04T00:20:00'
source_email_count: 3
related_articles: []
tags:
- sched_ext
- affinity
title: 'sched_ext: Bandwidth-limited rescue execution for stranded tasks'
layout: article
---

# sched_ext: 为 stranded 任务引入带宽受限的 rescue 执行


## TL;DR
sched_ext 引入了内核侧的「rescue 执行」机制，解决子调度器持有的 CPU 授权（caps）不覆盖其任务亲和、导致任务被 cap 反复拒绝/饿死直至 watchdog 触发的问题。v2 已按 AI review 修正，合入阻力小，值得 SCX 开发者跟进。

## 背景与问题
子调度器（sub-scheduler）只持有父调度器授予的 cids，但这些 cids 不一定覆盖其任务的 CPU 亲和。一个无法在任一授权 cpu 上运行的任务没有好的归宿：入队被 cap 拒绝后反复重入队，直到重复上限把调度器 eject，或者直接饿死触发 watchdog。这是 SCX 子调度器落地时的真实可用性短板。

## 技术方案
- scheduler 用 `SCX_ENQ_RESCUE` 标记「可能被 cap 拒绝」的入队，内核不再弹回，而是在目标 cpu 上以小配置带宽直接运行该任务（rescue）。
- rescue 初始是非破坏性的：持有 caps 的调度器大体仍掌控 cpu（如 preemption cap 仍允许持有者抢占 rescuee）。
- 若 rescue 长时间未得到服务，升级为 protected 执行（新增 `SCX_TASK_PROTECTED`，配合 0006 在入队提交时同步 slice/dsq_vtime 写入，使内核授予的 slice 能扛住调度器自身的写入）。
- 当某 cpu 的 rescue 队列持续超过过载阈值，内核 eject 该 cpu 上「最近 rescue 消耗最高」的子调度器，而不是错怪等待者所属的调度器。
- 0001-0005 为准备（重命名、helper 可见性、dsq-move flag 校验、`SCX_ENQ_IGNORE_CAPS` 豁免抢占上限）；0011-0012 修正 scx_qmap 的 pinned-task 直接派发并加 rescue 作为示范消费者。

## 版本演进与当前进展
当前 v2（2026-08-03）。v1 于 08-01 发出，经 sashiko AI review 后 v2 做了三处修正：`scx_sched_all` 改为无条件定义；overload/decay 时间戳用 `jiffies_64` 防 32 位回绕；删除未读的 `always_enq_immed` 镜像。12 个 patch 结构清晰，v2 暂无负面 review。

## Maintainer 意见与讨论焦点
主要维护者 Tejun Heo 自己提出并消化了 AI review，邮件中未出现其他 reviewer 的 NAK 或方向性质疑。潜在讨论点在于 overload ejection 的启发式选择（最高 rescue 消耗者）是否公平，目前无人提出反对。

## 合入评估
合入可能性高。Tejun 维护 `sched_ext/for-7.3` 分支，该系列本就标 `sched_ext/for-7.3`，无明显阻塞。后续只需社区对 ejection/protected 语义的确认。

## 效果评估
邮件未给出具体 benchmark 数字，仅描述行为语义改善（避免 stall / watchdog）。属于「作者主观判断，未见数据」的可用性修复，但问题本身的触发路径（cap 拒绝 → watchdog）描述明确。

## 我可以参与的点
- 在子调度器持有 caps 且任务亲和与授予 cid 不重叠的场景下压测，验证 rescue → protected 升级能真正避免 watchdog stall，回帖复现/验证数据。
- 对 overload ejection 启发式（驱逐最高 rescue 消耗者）提出更公平方案并参与讨论。

## 参考链接
- lore thread (v2): https://lore.kernel.org/lkml/20260803055435.2697653-1-tj@kernel.org
- lore thread (v1): https://lore.kernel.org/lkml/20260801085150.2697653-1-tj@kernel.org
