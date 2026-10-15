# sched: Account I/O waits independently of delayed dequeue

## TL;DR
Christian Loehle（Arm）修 blkio delay / iowait 记账与 EEVDF delayed dequeue 的耦合问题：`__block_task()` 里才启动 blkio 记账，导致「delay dequeue 期间就醒来」的任务漏记整段或首段 I/O 睡眠，且最终 dequeue 可能在别的任务上下文里给错任务打时间戳。v2 把两类记账（`delayacct_blkio_*` 与 `rq->nr_iowait`）都挪到 `try_to_block_task()`（任务决定阻塞时）启动、`unblock_task()` 清除，并用 `iowait_cpu` 保存计费 CPU 以应对延迟期间迁移。Kayra Cizmeci 与 Zhan Xusheng（报告者）双 `Reviewed-by`。带 `Fixes: 152e11f6df29 ("sched/fair: Implement delayed dequeue")`，合入可能性高。

## 背景与问题
Zhan Xusheng 报告（<20261014081731.1068794-1-zhanxusheng@xiaomi.com>）：blkio delay 记账在 `__block_task()` 里才 `delayacct_blkio_start()`，把记账区间绑在「从 runqueue 移除」这个时间点上。EEVDF delayed dequeue 下，任务在真正被 dequeue 前若被唤醒，就漏掉 I/O 睡眠的起始段——极端情况整段睡眠都被漏掉；而且最终 dequeue 可能发生在另一个任务的上下文（proxy execution / delayed dequeue），`delayacct_blkio_start()` 会给错任务打时间戳。v1 只改了 blkio delay，v2 进一步把 `rq->nr_iowait` 也纳入同样的处理（否则 delayed 任务在 `procs_blocked` 里也缺失）。

## 技术方案
v2（include/linux/sched.h + kernel/sched/core.c + kernel/sched/sched.h，+22/−18）：
- 新增 `unblock_task()`：若 `p->is_blocked && p->in_iowait` 先 `delayacct_blkio_end(p)`，再清 `is_blocked`；`ttwu_do_wakeup()` 改调它。
- 记账起点挪到 `try_to_block_task()`（当前任务确定阻塞时），早于 delayed dequeue 或 proxy execution 可能把任务继续留在 runqueue 的时刻；终点统一在清除 `is_blocked` 时（含 queued wakeup 与 proxy execution 继续执行的路径）。用 `is_blocked` 判定排除了「blocking 之前」的 wakeup。
- 在 `task_struct` 新增 `iowait_cpu`：等待开始时保存计费 CPU。延迟任务可能在仍 queued 时迁移，proxy execution 也可能移动 blocked 任务；unblock 时递减「保存的 CPU」的计数（与任务当前位置无关），并移除旧的基于 dequeue 的记账。
- CPU iowait 仍用「计费 CPU 上的计数」对 idle 时间分类，不累计整段 per-task blocked 时长。

## 版本演进与当前进展
- v1（`sched: Account blkio delay independently of delayed dequeue`，<4ce12bff-9532-4b27-98f2-a807bbccfaf7@arm.com>）：只改 blkio delay，未处理 `nr_iowait`。
- v2（`sched: Account I/O waits independently of delayed dequeue`，<fd8578a1-e60b-4993-ab51-2b5d63abcf77@arm.com>）：把 `rq->nr_iowait` 一并纳入，并新增 `iowait_cpu` 计费 CPU 机制，回应「任务延迟期间迁移导致计数落到错误 CPU」的问题。
- 当日 Kayra Cizmeci、Zhan Xusheng 双 `Reviewed-by`。Kayra 另指出 `io_schedule_timeout()` 上方有一段过时注释（声称会碰 `nr_iowait`，实则不会），建议顺手修正或删除。

## Maintainer 意见与讨论焦点
暂无维护者直接表态（Peter Zijlstra 在同日并行的 `nr_iowait_cpu()` / `cputime` 线程中活跃，但未在本线程回复）。Christian 在 v1 讨论中表示「Peter 想采纳哪个都行」，并倾向认为 `/proc/stat` 的观测粒度足够粗，不必强求 blkio delay 与 `nr_iowait` 跟踪完全相同的状态迁移。

## 合入评估
*likelihood=high*。修复动机清晰（报告者 + 作者一致），两位 reviewer 无异议给 `Reviewed-by`，且 v2 已回应迁移计费的边界问题。*blocking_issues*：尚无维护者（Peter）的最终 ACK；Kayra 提到的过时注释需一并处理。*next_action*：作者整理注释后等 Peter 收取；无实质争议。

## 效果评估
暂无量化数据。这是记账正确性修复，作者未给出基准；「漏记」的严重程度取决于 delayed dequeue 时间与 `/proc/stat` 观测粒度（Christian 主观判断影响不大，未见数据）。

## 我可以参与的点
- *review*：核对 `unblock_task()` 在新路径（proxy execution 的 `find_proxy_task()` 递减、`should_block == false` 分支）下的 `nr_iowait` 配对是否正确——Zhan 已确认过一部分。
- *testing*：用 blkio delay 记账观测工具（如 delayacct）验证 delayed dequeue 场景下启动/结束时间戳不再错位。

## 参考链接
- v2 patch：https://lore.kernel.org/all/fd8578a1-e60b-4993-ab51-2b5d63abcf77@arm.com/
- v1 patch：https://lore.kernel.org/all/4ce12bff-9532-4b27-98f2-a807bbccfaf7@arm.com/
- 原始报告：https://lore.kernel.org/all/20261014081731.1068794-1-zhanxusheng@xiaomi.com/

---
id: sched-20261015-004
date: 2026-10-15
subject: "sched: Account I/O waits independently of delayed dequeue"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<fd8578a1-e60b-4993-ab51-2b5d63abcf77@arm.com>"
lore_url: "https://lore.kernel.org/all/fd8578a1-e60b-4993-ab51-2b5d63abcf77@arm.com/"
authors: ["Christian Loehle"]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v1
    msgid: "<4ce12bff-9532-4b27-98f2-a807bbccfaf7@arm.com>"
    date: 2026-10-15
    summary: "仅改 blkio delay 记账：起点从 __block_task() 挪到 try_to_block_task()"
    review_outcome: "讨论是否需跟踪 iowait_cpu 以应对延迟期间迁移"
  - version: v2
    msgid: "<fd8578a1-e60b-4993-ab51-2b5d63abcf77@arm.com>"
    date: 2026-10-15
    summary: "把 rq->nr_iowait 一并纳入，新增 iowait_cpu 保存计费 CPU，移除旧 dequeue 记账"
    review_outcome: "Kayra Cizmeci、Zhan Xusheng 双 Reviewed-by"
upstream_commit: null
fixes_commit: "152e11f6df29"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["尚无维护者最终 ACK；Kayra 提到的过时注释需一并处理"]
  next_action: "整理注释后等 Peter 收取"
contribution_opportunities:
  - kind: review
    description: "核对 proxy execution 路径下 nr_iowait 配对的完整性"
  - kind: testing
    description: "用 delayacct 验证 delayed dequeue 场景下时间戳不再错位"
generated_at: "2026-10-16T01:05:00"
source_email_count: 7
related_articles: []
tags: [eevdf, cfs]
---