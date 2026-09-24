# sched_ext: Don't run ops.dequeue() with a DSQ lock held

## TL;DR
增量更新：Qiurong Fang 的 sched_ext 修复系列（v4，2-patch：确保 `ops.dequeue()` 不在持有 DSQ 锁时运行）本日被 Tejun Heo 合入 `sched_ext/for-7.3-fixes`，将随 7.3-rc 周期进入主线。

## 背景与问题
背景见 sched-20260917-009：sched_ext 在下内核路径中可能带着 DSQ 锁调用 BPF `ops.dequeue()`，被调度的 BPF 回调里再触发需持锁的操作会导致自死锁/重入问题，需要把 dequeue 回调移到解锁之后。

## 技术方案
调整 sched_ext 的锁定顺序，确保运行 `ops.dequeue()` 前已释放 DSQ 锁，覆盖交互路径与本地路径。

## 版本演进与当前进展
- v4（09-17，`<20260917075242.2813147-1-fangqiurong@kylinos.cn>`）：本日 Tejun 合入 1-2 到 `sched_ext/for-7.3-fixes`。

## Maintainer 意见与讨论焦点
- **Tejun Heo**："Applied 1-2 to sched_ext/for-7.3-fixes. Thanks."，无分歧。

## 合入评估
*likelihood=merged*。已合入 sched_ext/for-7.3-fixes 分支。*blocking_issues*：无。*next_action*：跟踪该 Fixes 分支是否被 Linus 收纳。

## 效果评估
邮件未附性能数据；属锁顺序/正确性修复，无直接性能影响。

## 我可以参与的点
当前阶段暂无明显参与空间，可持续观察该修复是否随 7.3 合并窗进入主线。

## 参考链接
- lore（v4）: https://lore.kernel.org/all/20260917075242.2813147-1-fangqiurong@kylinos.cn/

---
id: sched-20260918-007
date: '2026-09-18'
subject: 'sched_ext: Don''t run ops.dequeue() with a DSQ lock held'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: '<20260917075242.2813147-1-fangqiurong@kylinos.cn>'
lore_url: 'https://lore.kernel.org/all/20260917075242.2813147-1-fangqiurong@kylinos.cn/'
authors:
  - 'Qiurong Fang'
maintainers_involved:
  - 'Tejun Heo'
current_version: v4
patch_series:
  - version: v4
    msgid: '<20260917075242.2813147-1-fangqiurong@kylinos.cn>'
    date: '2026-09-17'
    summary: '确保 ops.dequeue() 不在持有 DSQ 锁时运行'
    review_outcome: 'Tejun 本日合入 sched_ext/for-7.3-fixes'
upstream_commit: null
fixes_commit: null
merged_branch: 'sched_ext/for-7.3-fixes'
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: '等待 for-7.3-fixes 分支被 Linus 收纳'
contribution_opportunities: []
generated_at: '2026-09-19T09:00:00'
source_email_count: 1
related_articles:
  - sched-20260917-009
  - sched-20260916-006
tags:
  - sched_ext
---