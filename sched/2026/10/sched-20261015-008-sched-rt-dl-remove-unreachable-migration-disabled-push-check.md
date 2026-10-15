# sched/rt,dl: Remove unreachable migration-disabled push checks

## TL;DR
Shubhang Kaushik（Ampere）清理 `push_rt_task()`/`push_dl_task()` 里不可达的 migration-disabled 分支：候选任务由 `pick_next_pushable_task()`/`pick_next_pushable_dl_task()` 选出，两者本身就跳过 migration-disabled 任务；`find_lock_lowest_rq()` 等中途掉锁后也会重新检查并拒绝状态变化的任务。故 push 侧的 migration-disabled fallback 永远走不到，v2 把 RT 与 DL 两处的死代码一并删除，并顺带移除只服务该分支的 `@pull` 参数。无行为变化，v2 刚发、暂无 review。

## 背景与问题
`push_rt_task()` 用 `pick_next_pushable_task()` 选 `next_task`，该 helper 不返回 migration-disabled 任务。选完后源 rq 锁仍被持有，被选中的 queued 任务不可能在持锁期间运行并改变 migration-disabled 状态。`find_lock_lowest_rq()` 会临时掉源 rq 锁，但重取锁后重新检查 `is_migration_disabled()` 并拒绝状态变化的任务，随后调用方要么退出、要么用同一 helper 重选——同样排除 migration-disabled 任务。因此 `push_rt_task()`（以及对称的 `push_dl_task()`）里针对 migration-disabled 的 fallback 分支不可达。

## 技术方案
v2（kernel/sched/rt.c 等）：
- 删除 `push_rt_task()` 的 migration-disabled fallback 与 `push_dl_task()` 的对应检查。
- 删除只服务该分支的 `@pull` 参数。
- 明确不改 `pull_rt_task()`/`pull_dl_task()` 的 migration-disabled 处理（它们用不同的候选选择器，并保留既有的 donor-push recovery）。

v1 只删了 RT 侧，v2 扩展到 DL 侧。

## 版本演进与当前进展
- v1（`sched/rt: Remove unreachable migration-disabled push path`，<20261014-sched-rt-dead-md-push-v1-1-5f9757be3c80@gentwo.org>）：只删 RT 侧。
- v2（`sched/rt,dl: Remove unreachable migration-disabled push checks`，<20261014-sched-rt-dead-md-push-v2-1-9f57f1a530dc@gentwo.org>）：扩展 DL 侧并澄清两处 push 都排除 migration-disabled 任务。
- 作者自测（80 核 SMP 非 SMT Ampere Altra）：开启/关闭 RT_PUSH_IPI 反复改 SCHED_FIFO affinity，均完成且清理 worker；RT_PUSH_IPI 开启时 function tracing 确认 `rto_push_irq_work_func()` 经 irq_work 反复执行。

## Maintainer 意见与讨论焦点
暂无维护者或 reviewer 表态。死代码论证依赖「持锁期间任务不改变 migration-disabled 状态」这一不变量，需 RT/DL 维护者（Steven Rostedt、Juri Lelli）确认。

## 合入评估
*likelihood=unknown*。论证严谨但 v2 刚发、无人 review。*blocking_issues*：无 review。*next_action*：等 RT/DL 维护者确认死代码判断与不变量。

## 效果评估
无性能/行为差异（死代码清理）。作者给出构建/运行测试通过，未见量化数据。

## 我可以参与的点
- *review*：独立验证「push 侧 migration-disabled fallback 不可达」的论证是否成立，特别是 `find_lock_lowest_rq()` 掉锁重取后的重检查是否覆盖全部路径。

## 参考链接
- v2 patch：https://lore.kernel.org/all/20261014-sched-rt-dead-md-push-v2-1-9f57f1a530dc@gentwo.org/
- v1 patch：https://lore.kernel.org/all/20261014-sched-rt-dead-md-push-v1-1-5f9757be3c80@gentwo.org/

---
id: sched-20261015-008
date: 2026-10-15
subject: "sched/rt,dl: Remove unreachable migration-disabled push checks"
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: "<20261014-sched-rt-dead-md-push-v2-1-9f57f1a530dc@gentwo.org>"
lore_url: "https://lore.kernel.org/all/20261014-sched-rt-dead-md-push-v2-1-9f57f1a530dc@gentwo.org/"
authors: ["Shubhang Kaushik"]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v1
    msgid: "<20261014-sched-rt-dead-md-push-v1-1-5f9757be3c80@gentwo.org>"
    date: 2026-10-15
    summary: "删除 push_rt_task() 不可达的 migration-disabled fallback 与 @pull 参数"
    review_outcome: "暂无 review"
  - version: v2
    msgid: "<20261014-sched-rt-dead-md-push-v2-1-9f57f1a530dc@gentwo.org>"
    date: 2026-10-15
    summary: "扩展删除 push_dl_task() 的对应检查"
    review_outcome: "暂无 review"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["暂无 review"]
  next_action: "等 RT/DL 维护者确认死代码判断与不变量"
contribution_opportunities:
  - kind: review
    description: "独立验证 push 侧 migration-disabled fallback 不可达的论证是否完整"
generated_at: "2026-10-16T01:05:00"
source_email_count: 2
related_articles: []
tags: [rt, deadline]
---