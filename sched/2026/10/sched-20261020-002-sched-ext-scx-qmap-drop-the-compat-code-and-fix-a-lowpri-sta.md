# sched_ext: scx_qmap: Drop the compat code and fix a lowpri starvation

## TL;DR

Tejun Heo 发往 `sched_ext/for-7.5` 的两补丁系列：scx_qmap 参考调度器删除只为兼容旧内核而保留的 `__COMPAT_*` 回退代码（1/2），并修复 lowpri 任务的饥饿 bug（2/2）——nice 19 任务被 `lowpri_timerfn()` 每 10ms 重入队到 SHARED_DSQ，而 `qmap_dispatch()` 先消费 SHARED_DSQ、再弹 FIFO，导致足够多的 nice 19 CPU hog 饿死其它任务、直至 watchdog 将调度器弹出。修复后 lowpri 任务改回自己的 FIFO。Andrea Righi 已给整系列 `Reviewed-by`，另指出还残留一处 `__COMPAT_ENUM_OR_ZERO` 可一并清理。

## 背景与问题

scx_qmap 常被用来演练随其随发内核一起落地的 sched_ext 特性，其实已「耦合于所随发内核」（实现了 `ops.sub_cid_sched_updated()` 与 `ops.sub_child_ecaps_updated()`），因此那些 `__COMPAT_*` 兼容判断只剩下一堆未经测试的 fallback，应当删除（1/2，无功能变化）。

2/2 修的是一个真实饥饿 bug：scx_qmap 把 nice 19 任务放在 LOWPRI_DSQ，`lowpri_timerfn()` 每 10ms 重入队它们；重入队任务走 `qmap_enqueue()` 的 `SCX_ENQ_REENQ` 路径进入 SHARED_DSQ，而 `qmap_dispatch()` 在弹 FIFO 之前先消费 SHARED_DSQ。于是：① nice 19 任务的 slice 到期 → 进 LOWPRI_DSQ；② 10ms 内 `lowpri_timerfn()` 把它重入队到 SHARED_DSQ；③ `qmap_dispatch()` 发现 SHARED_DSQ 非空、不再弹任何 FIFO。作者实测：十几个 nice 19 CPU hog 就能让 FIFO 超过 5 秒不被弹出，root 调度器因等在 FIFO 上的 watchdog kworker 无法签到而被弹出。`Fixes: 84b1a0ea0b7c ("sched_ext: Implement scx_bpf_dsq_reenq() for user DSQs")`。

## 技术方案

两补丁（`tools/sched_ext/scx_qmap.bpf.c` + `scx_qmap.c`，+28/-26）：

- **1/2 Drop the compat code**：删除 `__COMPAT_has_generic_reenq()`、`__COMPAT_is_enq_cpu_selected()`、`__COMPAT_scx_bpf_events()` 等回退，直接调用内核接口（`SCX_ENQ_CPU_SELECTED`、`scx_bpf_events()` 等），并在文件头部注释里注明「scx_qmap 耦合于所随发内核、不在其他内核上加载」。无功能变化。
- **2/2 Queue re-enqueued lowpri tasks on their FIFO**：给 `qmap_enqueue()` 引入 `lowpri` 布尔（`p->scx.weight < 2 && !(p->flags & PF_KTHREAD)`），`SCX_ENQ_REENQ && lowpri` 的任务不再插 SHARED_DSQ，而是排入它自己的 FIFO，等 LOWPRI_DSQ 等待结束后按其 FIFO 的轮次被派发。注释同步说明 SHARED_DSQ 的消费优先级问题。

验证：在 nice 0 与 nice 19 CPU hog 下，root 与 sub-scheduler 实例均测试——不加修复时 root 数秒内被 watchdog 弹出；加上修复后运行完成、FIFO 持续被派发。基于 `sched_ext/for-7.4-fixes`（ff343a94e44d）。

## 版本演进与当前进展

*current_version: v1*。当日首版发出（封面 `<20261019213221.2919481-1-tj@kernel.org>`，含 2 补丁），Andrea Righi 已 review。

## Maintainer 意见与讨论焦点

Andrea Righi（sched_ext 维护者之一）：「Both look good to me. Reviewed-by: Andrea Righi」；随后补一条 nit——scx_qmap.c 里还残留一处 `ppt = __COMPAT_ENUM_OR_ZERO("scx_consts", "SCX_RESCUE_DISABLE");`，建议一并丢弃。无分歧。

## 合入评估

*likelihood=high*。作者即 sched_ext 维护者、目标 `sched_ext/for-7.5`，修复带真实 `Fixes:` 与复现数据，且已获 Andrea `Reviewed-by`。*blocking_issues*：Andrea 指出的残留 `__COMPAT_ENUM_OR_ZERO` nit 待折入。*next_action*：Tejun 清理剩余 compat 后应用到 `sched_ext/for-7.5`。

## 效果评估

作者给出功能验证：不加 2/2 时，十几个 nice 19 CPU hog 使 FIFO 超过 5 秒不被弹出、root 被 watchdog 弹出；加上后运行正常完成、FIFO 持续派发。无量化延迟数字，属正确性/饥饿修复。

## 我可以参与的点

- `testing`：用 scx_qmap 复现 nice 19 饥饿场景（十几个 nice 19 CPU hog + watchdog），验证修复后 root/sub-scheduler 不再被弹出、FIFO 公平派发。
- `review`：核对「重入队 lowpri 任务改回 FIFO」是否覆盖 `lowpri_timerfn()` 之外所有 `SCX_ENQ_REENQ` 到达路径，避免其它路径仍把它送进 SHARED_DSQ。

## 参考链接

- 封面信：https://lore.kernel.org/all/20261019213221.2919481-1-tj@kernel.org/
- 1/2 Drop the compat code：https://lore.kernel.org/all/20261019213221.2919481-2-tj@kernel.org/
- 2/2 Queue re-enqueued lowpri tasks on their FIFO：https://lore.kernel.org/all/20261019213221.2919481-3-tj@kernel.org/

---
id: sched-20261020-002
date: 2026-10-20
subject: "sched_ext: scx_qmap: Drop the compat code and fix a lowpri starvation"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261019213221.2919481-1-tj@kernel.org>"
lore_url: "https://lore.kernel.org/all/20261019213221.2919481-1-tj@kernel.org/"
authors: ["Tejun Heo"]
maintainers_involved: ["Andrea Righi"]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261019213221.2919481-1-tj@kernel.org>"
    date: 2026-10-20
    summary: "两补丁：1/2 删除 scx_qmap 的 __COMPAT_* 兼容回退；2/2 修复 lowpri 任务重入队到 SHARED_DSQ 导致的饥饿（改回 FIFO）"
    review_outcome: "Andrea Righi 整系列 Reviewed-by，并指出残留 __COMPAT_ENUM_OR_ZERO 可一并清理"
upstream_commit: null
fixes_commit: "84b1a0ea0b7c"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["Andrea 指出 scx_qmap.c 仍残留 __COMPAT_ENUM_OR_ZERO nit 待折入"]
  next_action: "Tejun 清理剩余 compat 后应用到 sched_ext/for-7.5"
contribution_opportunities:
  - kind: testing
    description: "复现 nice 19 饥饿场景并验证修复后 root/sub-scheduler 不再被 watchdog 弹出"
  - kind: review
    description: "核对 SCX_ENQ_REENQ 全部路径下 lowpri 任务是否都改回 FIFO"
generated_at: "2026-10-21T01:30:00"
source_email_count: 5
related_articles: []
tags: [sched_ext]
---