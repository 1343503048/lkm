# sched_ext: Add scx_tickbug, a scheduler that holds a task on an idle CPU

## TL;DR

Radu Toader 为 sched_ext 新增一个**测试用**调度器 `scx_tickbug`（tools/sched_ext，为此系列 1/2）：它唯一的目的就是让一个任务在「runqueue 非空、但 CPU 处在 idle loop」的状态上保持可控时长。这个状态就是 `tick_irq_exit()` 里一个 gate 所测量/依赖的状态——已有示例调度器能到达但**保持不住**（如 `scx_central` 只持几十微秒），而本调度器被踢除 kick，让窗口宽到 `-H` 指定的时长，从而可测量 idle-time 记账在中断落入该状态时被跳过所造成的影响（如 sched_clock 失同步、下一次 tick 把整段 idle 时长记到任务头上）。纯工具、非策略。

## 背景与问题

`enqueue_task_scx()` 会先抬高 `rq->nr_running` 再调 `ops.enqueue()`，所以一个「把任务 stash 到自己 map、不给 CPU 任何可 pick 的东西」的调度器会让任务保持 runnable 且计在该 CPU 上——CPU 于是进 idle loop 又不空。这个状态下 `idle_cpu()` 为 false（`idle_rq()` 看 `rq->nr_running`）而 `is_idle_task(current)` 为 true。`tick_irq_exit()` 过去用 `idle_cpu()` 判断，于是该 idle loop 里每个中断都跳过 `tick_nohz_irq_exit()`，`TS_FLAG_IDLE_ACTIVE` 保持清位、之后的 idle 退出又跳过 `sched_clock_idle_wakeup_event()`——在 sched_clock 不稳定时，CPU 时钟永不重同步、下一个被 pick 的任务带着陈旧的 `exec_start` 起步、下一次 tick 把整段 idle 时长算到它头上。作者想测量这个 gate 的行为，但没有现成工具能「长时间持有」该状态。

## 技术方案

`scx_tickbug` 的关键：`is_tagged()`（comm 精确等于 "spin" 的任务）被推进 `hold_q` BPF 队列并**故意不 kick CPU**，于是任务留在 `target_cpu` 的 `rq->nr_running` 里、CPU 停在 idle loop；唯一的释放来源是固定在另一颗 CPU 上的周期定时器，窗口宽到 `hold_ns` 可扫。为了机器可继续用：per-CPU kthread 走本地 DSQ 且带抢占（保证 ksoftirqd 不被饿死、定时器 softirq 能跑），非 tagged 任务走共享 DSQ。两个实测才发现的坑：释放定时器只能在实际持有时才 kick（否则会抢占刚释放的任务、损失一半 CPU 使用），以及「已在运行」的 tagged 任务重回本地 DSQ 而非被持（`nr_requeue` 计数之，保证 hold 只延迟启动、不打断运行）。BPF 侧统计 `nr_held`/`held_at`/`total_held_ns`/`max_held_ns`，向用户态报告实际达到的平均与最坏 hold 时长（这是实验的自变量，否则用户态不可观测）。

## 版本演进与当前进展

*current_version: v1（2026-11-06 发出，patch 1/2）*。本缓存仅含 1/2；当日无评审。作者注明整个补丁是 Claude Code 工具生成。

## Maintainer 意见与讨论焦点

当日无维护者回复。作为测试工具（非内核核心代码、仅 `tools/sched_ext/`），风险面小；但「LLM 全量生成」可能招致对代码质量的更仔细审阅。

## 合入评估

*likelihood=unknown*。工具性补丁、无行为影响于内核本体，但需 Tejun Heo 对 scx 示例调度器目录的取舍。*blocking_issues*：① 无评审；② 需确认这类「测量专用」调度器是否愿意纳入 tools/sched_ext 长期维护。*next_action*：等 Tejun Heo 评审。

## 效果评估

作者剧情说明（未见量化表格）：初版定时器无条件 kick 导致任务损失约一半 CPU 使用，修正后缓解。工具本身即为测量装置，其「效果」是让 `tick_irq_exit()` idle gate 的影响首次可被 sweep 测量。

## 我可以参与的点

- **testing**：用 `scx_tickbug` 实测 `tick_irq_exit()` idle gate 在不稳定 sched_clock 系统上对 exec_start 陈旧/整段 idle 记账的影响，产出数据回帖——这正是该工具想推动的测量。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261105200205.1178097-2-radu.m.toader@gmail.com/

---
id: sched-20261106-016
date: 2026-11-06
subject: "sched_ext: Add scx_tickbug, a scheduler that holds a task on an idle CPU"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261105200205.1178097-2-radu.m.toader@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261105200205.1178097-2-radu.m.toader@gmail.com/"
authors: [Radu Toader]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261105200205.1178097-2-radu.m.toader@gmail.com>"
    date: 2026-11-06
    summary: "新增 scx_tickbug 测试调度器，可控时长持有 idle-loop-带任务状态。"
    review_outcome: "暂无评审；作者注 LLM 全量生成。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - "无评审"
    - "需确认测量专用调度器是否纳入 tools/sched_ext 长期维护"
  next_action: "等 Tejun Heo 评审"
contribution_opportunities:
  - kind: testing
    description: "用 scx_tickbug 实测 tick_irq_exit idle gate 对 sched_clock 失同步的影响"
generated_at: "2026-11-07T09:00:00+08:00"
source_email_count: 2
related_articles: []
tags: [sched_ext, idle]
---