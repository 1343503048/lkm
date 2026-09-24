# cgroup/cpuset: Defer sched domain rebuild to common unlock path

## TL;DR
Guopeng Zhang 提交清理：`update_prstate()` 末尾的 `rebuild_sched_domains_locked()` 检查是冗余的——其两个调用者随后都会走 `cpuset_update_sd_hk_unlock()`（在释放 cpuset 锁前统一重建 sched domain）。维护者 Ridong Chen 认可删冗余代码，但指出标题里 "defer" 用词误导（实际只是删冗余代码，并非异步化）。

## 背景与问题
`update_prstate()` 的两个调用者 `cpuset_partition_write()` 与 `cpuset_css_killed()` 在其后都紧跟着调用 `cpuset_update_sd_hk_unlock()`，后者在释放 cpuset 锁前、`force_sd_rebuild` 置位时重建 sched domain。因此 `update_prstate()` 内的检查纯属冗余。commit 3bfe47967191 已从 `cpuset_write_resmask()` 移除了同样的检查，本补丁把 `update_prstate()` 里剩余的一份也删掉。

## 技术方案
删除 `kernel/cgroup/cpuset.c` 中 `update_prstate()` 末尾两行：

```c
if (force_sd_rebuild)
    rebuild_sched_domains_locked();
```

sched domain 重建统一收敛到公共解锁路径 `cpuset_update_sd_hk_unlock()`。

## 版本演进与当前进展
- v1（09-18，`<20260918102730.72263-1-guopeng.zhang@linux.dev>`）：首版，本日 Ridong Chen 回复标题用词问题。

## Maintainer 意见与讨论焦点
- **Ridong Chen**：认可删冗余代码，但认为标题 "Defer sched domain rebuild" 误导——"defer" 让人以为是异步工作，实际只是移除一段冗余代码。
- 分歧点：补丁标题措辞（作者需澄清或改标题）。

## 合入评估
*likelihood=medium*。纯冗余删除、语义等价、风险极低；标题措辞需澄清后即可合入。*blocking_issues*：标题 "defer" 用词待澄清/修正。*next_action*：作者回应 Ridong 意见，说明并非异步化、仅删冗余，或修改标题后重发。

## 效果评估
无性能数据；纯代码清理（删 2 行），无行为变化。

## 我可以参与的点
- kind=review：确认 `update_prstate()` 两个调用者在所有路径上都必然随后触发 `cpuset_update_sd_hk_unlock()`（无遗漏分支），佐证删除是安全的。

## 参考链接
- lore（patch）: https://lore.kernel.org/all/20260918102730.72263-1-guopeng.zhang@linux.dev/

---
id: sched-20260918-019
date: '2026-09-18'
subject: 'cgroup/cpuset: Defer sched domain rebuild to common unlock path'
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: '<20260918102730.72263-1-guopeng.zhang@linux.dev>'
lore_url: 'https://lore.kernel.org/all/20260918102730.72263-1-guopeng.zhang@linux.dev/'
authors:
  - 'Guopeng Zhang'
maintainers_involved:
  - 'Ridong Chen'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260918102730.72263-1-guopeng.zhang@linux.dev>'
    date: '2026-09-18'
    summary: '删除 update_prstate() 冗余的 rebuild_sched_domains_locked()'
    review_outcome: 'Ridong 认可删冗余，但指出标题 defer 用词误导'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - '标题 defer 用词待澄清/修正'
  next_action: '作者回应 Ridong 意见或改标题后重发'
contribution_opportunities:
  - kind: review
    description: '确认两个调用者路径都必然触发公共解锁重建，佐证安全'
generated_at: '2026-09-19T09:00:00'
source_email_count: 2
related_articles: []
tags:
  - cgroup
  - topology
---