---
id: sched-20261009-009
date: '2026-10-09'
subject: 'sched_ext: Report a sub-scheduler''s attach-time ecaps before lifting its
  enable bypass'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261009094356.2852794-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20261009094356.2852794-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20261009094356.2852794-1-tj@kernel.org>
  date: '2026-10-09'
  summary: 拆 sync_pcpu_ecaps；enable 路径 bypass 期间提前上报 attach grant
  review_outcome: 当日无回帖
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 缺第二人独立测试
  next_action: 合入 for-7.4 并吸引使用者复测 attach 路径
contribution_opportunities:
- kind: testing
  description: 复测 attach 时父级已有排队任务的时序
- kind: review
  description: 审 enable 路径每 CPU 上报时 prev stash/restore 的完整性
generated_at: '2026-10-10T01:30:00'
source_email_count: 3
related_articles: []
tags:
- sched_ext
- cgroup
title: 'sched_ext: Report a sub-scheduler''s attach-time ecaps before lifting its
  enable bypass'
layout: article
---

## TL;DR
Tejun Heo 发往 `sched_ext/for-7.4` 的 2 补丁系列，修正 sub-scheduler 的一个归属时序缺口：子调度器通过 `ops.sub_ecaps_updated()` 了解自己持有哪些 cid，但父级在它 attach 时做的 grant 要到其 enable bypass 被解除（任务交接给它）之后才报告——于是子调度器在接到任何 cid 通知前就先收到首批 `ops.enqueue()`，不得不在拿到 grant 前把任务先「囤」在别处。补丁让 enable 路径在子调度器仍被 bypass 时就把 attach 时 grant 报到每个 CPU，使其首个任务到达时已有完整 cid 视角。作者 TLC 模型检验了顺序，当日无回帖。

## 背景与问题
sched_ext 的分层 sub-scheduler 模型里，父调度器通过 grant/revoke 向子调度器委派 capabilities。子调度器靠 `ops.sub_ecaps_updated()` 得知自己持有哪些 cid，但 attach 时父级的 grant 只在 enable bypass 解除（也是任务被交接给它的时刻）后才上报。于是子调度器会先收到 `ops.enqueue()`（任务已到达）却还一个 cid 都没被通知，必须先找个地方暂存任务。

## 技术方案
- patch 1（`sched_ext: Factor out sync_pcpu_ecaps()`）：把 per-CPU 的 ecaps 同步从 dispatch 侧的 drain（`__scx_process_sync_ecaps()`）里拆出为独立函数，使其能在别处运行。纯重构、无功能变化。
- patch 2（`sched_ext: Report ... enable bypass`）：让 enable 路径在子调度器仍 bypassing 时就在每个 CPU 上报 attach 时 grant，使首个任务到达时就具备完整 cid 视图、可立即放置。bypassing 期间不会有其它 op 到达，中间状态安全。

改动全部在 `kernel/sched/ext/sub.c`（+134/-60）。作者用「父级已有排队任务时子调度器 attach、attach 期间 cid revoke/重新 grant、detach 再 re-attach」等场景验证：没有任务在 attach 时被 rescue 或 stall，root 调度器不受影响；enable 路径、per-CPU sync、父级 grant 之间的顺序用 TLC 模型检验过。base 为 `sched_ext/for-7.4`（`3d7c2f550eef`），git 分支 `tj/sched_ext.git sub-attach-ecaps`。

## 版本演进与当前进展
v1 首发（PATCHSET `<20261009094356.2852794-1-tj@kernel.org>`，1/2 + 2/2）。当日无回帖。

## Maintainer 意见与讨论焦点
当日无回帖。作者即 sched_ext 顶层维护者、系列落在自己的 `for-7.4` 分支，属维护者自修设计缺口；通常需 Andrea Righi（联合维护者）或使用者复测背书。

## 合入评估
*likelihood=high*。维护者自修、落在自己的特性分支、有 TLC 模型检验与多 attach 场景验证；缺的是一个独立复测。*blocking_issues*：缺第二人独立测试。*next_action*：合入 `sched_ext/for-7.4`，吸引 sub-scheduler 使用者复测 attach 路径。

## 效果评估
无性能数据（正确性/时序修复）。作者给出的验证涵盖「父级已排队任务时 attach、revoke/重新 grant、detach/re-attach」场景下无任务被 rescue 或 stall，属功能正确性证明。

## 我可以参与的点
- `testing`：用带 sub-scheduler 的 BPF 调度器复测 attach 时「父级已有排队任务」的时序，确认首个 `ops.enqueue()` 前已收到完整 cid 视图。
- `review`：审 patch 2 中 enable 路径每 CPU 上报 attach grant 时对 dispatch 上下文中 prev 的 stash/restore 处理是否完整。

## 参考链接
- 系列 cover: https://lore.kernel.org/all/20261009094356.2852794-1-tj@kernel.org/
