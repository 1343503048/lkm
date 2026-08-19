# sched/deadline: Skip bandwidth accounting with SCHED_FLAG_KEEP_PARAMS

## TL;DR

Andrea Righi 修复了 `SCHED_FLAG_KEEP_PARAMS` 标志的两个副作用：即使设置了该标志，`__sched_setscheduler()` 仍会错误地触发 class 切换回调和 deadline 带宽记账。v1 刚发出，PeterZ 已 review，合入可能性高。

## 背景与问题

`SCHED_FLAG_KEEP_PARAMS` 允许 `sched_setattr()` 更新通用任务属性，同时保留任务现有的调度参数和 class。但 `__sched_setscheduler()` 中有两条路径在 guarded parameter update 之前仍然对请求的 policy 执行了操作：

1. **Class 回调路径**：当从请求 policy 计算出的 class 与任务当前 class 不同时，会标记为 class change 并调用 `switching_from()`/`switched_from()`/`switching_to()`/`switched_to()` 回调，即使 `p->sched_class` 实际未变
2. **Deadline 带宽路径**：执行 deadline admission control，可能对从未进入 deadline class 的任务进行带宽记账

## 技术方案

**Patch 1/2** - `sched: Skip class callbacks with SCHED_FLAG_KEEP_PARAMS`：
- 仅在 sched class 实际允许改变时才设置 `DEQUEUE_CLASS`
- 添加 `Fixes:` 标签指向 `637b0682821b ("sched: Fold sched_class::switch{ing,ed}_{to,from}() into the change pattern")`

**Patch 2/2** - `sched/deadline: Skip bandwidth accounting with SCHED_FLAG_KEEP_PARAMS`：
- 当 `SCHED_FLAG_KEEP_PARAMS` 设置且 policy 未变时，显式拒绝 policy 变更请求（返回 `-EINVAL`）
- 防止对非 deadline 任务进行带宽记账

代码改动很小：`kernel/sched/syscalls.c` 1 file changed, 4 insertions(+), 2 deletions(-)

## 版本演进与当前进展

v1 刚发出，包含两个 patch。PeterZ 已在 0/2、1/2、2/2 上回复 review。

## Maintainer 意见与讨论焦点

PeterZ 对两个 patch 都给出了反馈。从讨论看，方向被认可，但有一些细节需要调整。没有明确的 NAK。

## 合入评估

- **likelihood**: high
- 修复逻辑清晰，代码改动最小化
- 有明确的 `Fixes:` 标签
- PeterZ 已参与 review，无阻塞性问题

## 效果评估

暂无性能数据。这是正确性修复，解决的是错误触发回调和带宽记账问题。

## 我可以参与的点

当前阶段暂无明显参与空间。系列已成熟，等待合入。

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260730055011.2267333-1-arighi@nvidia.com
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
subject: "sched/deadline: Skip bandwidth accounting with SCHED_FLAG_KEEP_PARAMS"
id: sched-20260730-001
date: 2026-07-30
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20260730055011.2267333-1-arighi@nvidia.com>"
lore_url: "https://lore.kernel.org/lkml/20260730055011.2267333-1-arighi@nvidia.com"
authors: [Andrea Righi]
maintainers_involved: [Peter Zijlstra, Andrea Righi]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260730055011.2267333-1-arighi@nvidia.com>"
    date: 2026-07-30
    summary: "2-patch series fixing two side effects in __sched_setscheduler() when SCHED_FLAG_KEEP_PARAMS is set"
    review_outcome: "PeterZ reviewed and provided feedback on both patches"
upstream_commit: null
fixes_commit: "637b0682821b"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "Address PeterZ feedback, likely ready for tip"
contribution_opportunities: []
generated_at: "2026-07-31T00:10:00"
source_email_count: 11
related_articles: []
tags: [core_sched, cgroup]
---
