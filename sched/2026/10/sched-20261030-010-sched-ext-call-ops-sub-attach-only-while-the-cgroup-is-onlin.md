# sched_ext: Call ops.sub_attach() only while the cgroup is online

## TL;DR
Tejun Heo 修 sched_ext cgroup sub-scheduler 的一个竞态：`ops.sub_attach()` 在 enable work 检查 cgroup 是否仍 online **之前**执行，父调度器可能为一个「rmdir 已经返回」的 cgroup 收到 attach 回调，让父侧的 cgroup 清理与 sub-scheduler attach 产生竞争。修法：在 `scx_sub_enable_workfn()` 里 `cgroup_lock()` 下检查 `CSS_ONLINE`，仅对 online 的 cgroup 调 `ops.sub_attach()`，否则 `-ENODEV` 报错退出（`+17/-0`）。`Fixes: ebeca1f930ea`。Andrea Righi 已给 **Reviewed-by**。

## 背景与问题
sched_ext 的 cgroup sub-scheduler 机制允许父调度器在子 cgroup 上挂接 sub-scheduler。`scx_sub_enable_workfn()` 里，原实现直接对 cgroup 调 `ops.sub_attach()`，而「cgroup 是否仍 online」的检查（enable work 本身的校验）在此之前并未生效——于是当 cgroup 正在被 rmdir 删除时，父调度器可能为一个已不在线的 cgroup 收到 attach，与父侧「按 cgroup 清理」逻辑发生竞态，使父调度器难以正确处理 attach/cleanup 的生命周期。

## 技术方案
在 `kernel/sched/ext/sub.c` 的 `scx_sub_enable_workfn()` 中，把 `ops.sub_attach()` 的调用包进 `cgroup_lock()`：

```c
cgroup_lock();
if (!(cgrp->self.flags & CSS_ONLINE)) {
    cgroup_unlock();
    scx_error(sch, "cgroup is not online");
    ret = -ENODEV;
    goto err_disable;
}
ret = SCX_CALL_OP_RET(parent, sub_attach, NULL, &sub_attach_args);
cgroup_unlock();
```

并在 `internal.h` 的 `sub_attach` kerneldoc 里注明「sub-scheduler 的 cgroup 在整个调用期间保持 online；若之后离线，`ops.sub_detach()` 会跟进」。这样父调度器只会在 cgroup 在线时收到 attach，语义与 cleanup 路径一致。

## 版本演进与当前进展
*current_version: v1*（2026-10-29 发出）。当日获 Andrea Righi **Reviewed-by**（"Reviewed-by: Andrea Righi <arighi@nvidia.com>"）。

## Maintainer 意见与讨论焦点
- **Andrea Righi（sched_ext co-maintainer）**：给出 Reviewed-by，无异议。
- 无遗留分歧。

## 合入评估
*likelihood=high*。co-maintainer 已 Reviewed-by、`Fixes:` 明确、改动小且语义清晰，属 `for-7.4-fixes` 修复窗口的常规收取。*blocking_issues*：暂无。*next_action*：合入 `sched_ext/for-7.4-fixes`。

## 效果评估
无性能数据；修复为 cgroup sub-scheduler 生命周期的正确性问题（消除 rmdir 竞态），未提供复现。

## 我可以参与的点
- **review**：核对 `cgroup_lock()` 与 `SCX_CALL_OP_RET` 之间是否可能与父调度器回调产生锁序问题。
- **testing**：在启用 cgroup sub-scheduler 的 scx 父调度器上做 cgroup 频繁 rmdir 压力测试，确认无 attach-for-dead-cgroup。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261029222859.3099324-1-tj@kernel.org/

---
id: sched-20261030-010
date: 2026-10-30
subject: "sched_ext: Call ops.sub_attach() only while the cgroup is online"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261029222859.3099324-1-tj@kernel.org>"
lore_url: "https://lore.kernel.org/all/20261029222859.3099324-1-tj@kernel.org/"
authors: [Tejun Heo]
maintainers_involved: [Andrea Righi]
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "合入 sched_ext/for-7.4-fixes"
contribution_opportunities:
  - kind: review
    description: "核对 cgroup_lock() 与父调度器回调之间的锁序"
  - kind: testing
    description: "cgroup 频繁 rmdir 压力测试，确认无 attach-for-dead-cgroup"
generated_at: "2026-10-31T09:00:00"
source_email_count: 2
related_articles: []
tags: [sched_ext, cgroup]
---