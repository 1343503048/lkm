---
id: sched-20260920-002
date: '2026-09-20'
subject: 'cgroup/cpuset: Remove redundant sched domain rebuild from update_prstate()'
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: <20260920025256.24991-1-guopeng.zhang@linux.dev>
lore_url: https://lore.kernel.org/all/20260920025256.24991-1-guopeng.zhang@linux.dev/
authors:
- Guopeng Zhang
maintainers_involved:
- Ridong Chen
current_version: v2
patch_series:
- version: v1
  msgid: <20260918102730.72263-1-guopeng.zhang@linux.dev>
  date: '2026-09-18'
  summary: 删除 update_prstate() 冗余的 rebuild_sched_domains_locked()
  review_outcome: Ridong 认可删冗余，但指出标题 defer 用词误导
- version: v2
  msgid: <20260920025256.24991-1-guopeng.zhang@linux.dev>
  date: '2026-09-20'
  summary: 重命名标题避免 defer 误导，代码不变
  review_outcome: Ridong Reviewed-by
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 cpuset 维护者收取
contribution_opportunities: []
generated_at: '2026-09-21T09:00:00'
source_email_count: 4
related_articles:
- sched-20260918-019
tags:
- cgroup
- topology
title: 'cgroup/cpuset: Remove redundant sched domain rebuild from update_prstate()'
layout: article
---

## TL;DR
增量更新：Guopeng Zhang 的 cpuset 冗余 sched domain 重建清理发布 v2，按 Ridong Chen 的意见把易误导的 "defer" 标题改为「Remove redundant ...」，代码不变（仍为删除 `update_prstate()` 末尾两行冗余的 `rebuild_sched_domains_locked()`）。Ridong Chen 在 v2 上给出 Reviewed-by。

## 背景与问题
背景见 sched-20260918-019：`update_prstate()` 的两个调用者 `cpuset_partition_write()` 与 `cpuset_css_killed()` 在其后都紧跟着调用 `cpuset_update_sd_hk_unlock()`，后者在释放锁前、`force_sd_rebuild` 置位时重建 sched domain，因此 `update_prstate()` 内的重建检查纯属冗余。commit 3bfe47967191 已从 `cpuset_write_resmask()` 移除同样的检查，本补丁删掉 `update_prstate()` 里剩余的一份。

## 技术方案
删除 `kernel/cgroup/cpuset.c` 中 `update_prstate()` 末尾两行：

```c
-	if (force_sd_rebuild)
-		rebuild_sched_domains_locked();
```

sched domain 重建统一收敛到公共解锁路径 `cpuset_update_sd_hk_unlock()`。v2 与 v1 的 diff 完全一致（1 文件 2 删），仅改标题措辞。

## 版本演进与当前进展
- v1（09-18，标题 "Defer sched domain rebuild to common unlock path"，`<20260918102730.72263-1-guopeng.zhang@linux.dev>`）：见 sched-20260918-019。
- 本日作者回帖（`<f27e12d8-2e34-4c10-9773-d1af5b8538b6@linux.dev>`）回应 Ridong：承认标题 "Defer" 用词不当（实际只是删冗余代码，并非异步化），承诺 v2 修改。
- v2（09-20，`<20260920025256.24991-1-guopeng.zhang@linux.dev>`）：重命名标题为 "Remove redundant ..."，代码不变。
- Ridong Chen（`<a932b397-de99-42ba-91e7-cea923fa6f9f@linux.dev>`）在 v2 上给出 Reviewed-by。

## Maintainer 意见与讨论焦点
- **Ridong Chen**（cpuset 活跃 reviewer）：v1 认可删冗余，但指出标题 "defer" 用词误导；v2 重命名后给出 Reviewed-by，异议已消除。
- 分歧/未决：无，标题歧义已在 v2 解决。

## 合入评估
*likelihood=high*。纯冗余删除、语义等价、风险极低，Ridong Chen 已 Reviewed-by，且沿用了 commit 3bfe47967191 的既有清理模式。*blocking_issues*：无。*next_action*：等待 cpuset 维护者（Waiman Long / Tejun Heo）收取。

## 效果评估
无性能数据；纯代码清理（删 2 行），无行为变化。

## 我可以参与的点
当前阶段暂无明显参与空间（已获 Reviewed-by 的清理性补丁），可持续观察 cpuset sched domain 重建的相关后续整理。

## 参考链接
- lore（v2 patch）: https://lore.kernel.org/all/20260920025256.24991-1-guopeng.zhang@linux.dev/
- lore（Ridong Reviewed-by v2）: https://lore.kernel.org/all/a932b397-de99-42ba-91e7-cea923fa6f9f@linux.dev/
- lore（v1）: https://lore.kernel.org/all/20260918102730.72263-1-guopeng.zhang@linux.dev/
