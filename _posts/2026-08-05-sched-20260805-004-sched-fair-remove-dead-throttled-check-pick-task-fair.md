---
subject: sched fair remove dead throttled check pick task fair
id: sched-20260805-004
date: '2026-08-05'
title: sched fair remove dead throttled check pick task fair
series: Remove dead throttled check in pick_task_fair()
type: cleanup
status: superseded
severity: low
merge_likelihood: medium
tags:
- cfs
- cgroup
authors:
- Peter Zijlstra <peterz@infradead.org>
reviewers: []
related_articles: []
emails:
- uid-21962@qq-imap
- uid-21301@qq-imap
layout: article
---

# sched/fair: 删除 pick_task_fair() 中失效的 throttled 检查

## 摘要

本系列针对 `pick_task_fair()` 里一段「任务所在 cfs_rq 已被 throttle 时跳过」的检查，结论是**这段代码是死代码，应当删除**。在 08-05 的讨论里 Peter Zijlstra 直接给出了合入版 commit（`85570f10a4c6`），说明该检查在 CFS 带宽控制重构后已不可能命中。

要点：
- **Peter 的原始 patch（21301）**：在 `pick_task_fair()` 里移除对 `throttled_hierarchy()` 的判断。理由：自 CFS 带宽（throttle）逻辑改为基于 `tg->cfs_rq` 的 per-entity 之后，`pick_task_fair` 永远不会被传入一个处于 throttle 状态的 cfs_rq——上游的 `put_prev_task` / `set_next_task` 路径已经保证不会选中 throttled 的实体。
- **后续引用（21962）**：某处代码（疑似另一系列）引用了这段逻辑，Peter 在回复里提示「这段已经没了，见 `85570f10a4c6`」，表明该清理已经落地主线。

## 技术细节

`pick_task_fair()` 旧逻辑（示意）：
```
for_each_sched_entity(se) {
    cfs_rq = cfs_rq_of(se);
    if (throttled_hierarchy(cfs_rq))   // 死代码
        return NULL;
    ...
}
```

删除依据：CFS 带宽控制现在在 `dequeue_task_fair` / `throttle_cfs_rq` 时就从可运行实体集合里摘除被 throttle 的 se，因此 `pick_task_fair` 遍历到的 se 必然都未 throttle，该分支恒为 false。

## 影响与风险

- 影响面：仅 `pick_task_fair()` 的控制流，删掉一个永不命中的分支，理论上有极微小的指令缓存获益。
- 风险：低。已被 maintainer 合入（`85570f10a4c6`），属于确认安全的清理。
- 注意：任何仍依赖该检查的下游 patch 需要 rebase 到删除后的版本。

## 评价

典型的 maintainer 级清理，已合入。无后续动作，仅作为「本日引用该 commit 的上下文」记录。
