# sched: call into io_uring when a PF_IO_HANDOFF task blocks

## TL;DR
Jens Axboe 15 补丁系列中的第 2 个当日入缓存：新增 PF_IO_HANDOFF 任务标志（io_uring 在 inline 提交可能阻塞期间设置），sched_submit_work() 在该类任务阻塞时调用 io_uring_task_sleeping()——目前是占位空函数，为后续「任务阻塞时移交 io_uring 身份/状态」的机制预留调度器钩子。仅此一封入缓存，封面与其余补丁未获取到。

## 背景与问题
io_uring 任务在内核态 inline 提交请求时可能阻塞；目前 sched_submit_work() 对 PF_WQ_WORKER/PF_IO_WORKER 两类任务有睡眠前回调，io_uring 本身没有对应钩子。系列（含 include/linux/thread_handoff.h，从 core.c 新增 include 可见）在推进「thread handoff」方向：任务因 io_uring 阻塞时把身份/状态移交出去，本补丁是调度器侧的接入点。

## 技术方案
- include/linux/sched.h：把 PF__HOLE__00800000 保留位启用为 PF_IO_HANDOFF（"io_uring: hand identity off if the task blocks"）；
- kernel/sched/core.c：sched_submit_work() 增加 `else if (task_flags & PF_IO_HANDOFF) io_uring_task_sleeping(tsk);`，与 wq_worker_sleeping()/io_wq_worker_sleeping() 并列；并 include <linux/io_uring.h>；
- include/linux/io_uring.h：io_uring_task_sleeping() 目前为空内联占位（"Placeholder for now"）；
- kernel/fork.c：copy_process() 清位列表加入 PF_IO_HANDOFF，防止标志跨 fork 泄漏。

## 版本演进与当前进展
current_version: v1（本补丁 msgid `<20260911154148.644489-3-axboe@kernel.dk>`，[PATCH 02/15]，09-11 23:40 入缓存）。系列其余 14 个补丁与 cover letter 未入当日缓存，系列整体动机、目标树与评审状态未获取到。

## Maintainer 意见与讨论焦点
当日缓存内无任何回帖；io_uring 侧与 sched 侧维护者的表态均未获取到。占位函数意味着设计（移交什么、如何唤醒）尚未展开，讨论焦点尚待后续补丁出现。

## 合入评估
likelihood=unknown：系列只露出 1/15 个补丁，无法评估整体；调度器侧改动本身极小（3 行 + 一个标志位）。blocking_issues：封面与设计补丁未获取到；PF 标志位占用（原 hole 0x00800000）与 sched_submit_work() 回调链的扩展是否被 sched 侧接受未知。next_action：跟踪系列的完整投递（lore 上应有 00/15 cover），重点看 io_uring_task_sleeping() 从占位变为实作后的阻塞路径设计。

## 效果评估
暂无效果数据：占位补丁，无 benchmark 或行为差异说明。

## 我可以参与的点
- kind=discussion：系列完整发出后，评估 PF_IO_HANDOFF 在 sched_submit_work() 的回调时机（iowait 计账、blk 蕴含 flush 之前的相对顺序）是否合理——这是调度器侧唯一的接入点，值得在设计定型前反馈。

## 参考链接
- 本补丁（02/15）：https://lore.kernel.org/all/20260911154148.644489-3-axboe@kernel.dk/
- 系列 cover letter：未获取到（未入当日缓存）

---
id: sched-20260911-019
subject: 'sched: call into io_uring when a PF_IO_HANDOFF task blocks'
date: '2026-09-11'
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: '<20260911154148.644489-3-axboe@kernel.dk>'
lore_url: 'https://lore.kernel.org/all/20260911154148.644489-3-axboe@kernel.dk/'
authors:
  - 'Jens Axboe'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1 (02/15)
    msgid: '<20260911154148.644489-3-axboe@kernel.dk>'
    date: 2026-09-11
    summary: '新增 PF_IO_HANDOFF 标志与 sched_submit_work() 回调点（io_uring_task_sleeping() 暂为占位）；仅此一封入缓存。'
    review_outcome: '当日无回帖；系列其余补丁未获取到。'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - '系列 15 补丁仅露出 1 封，整体设计与目标树未获取到'
  next_action: '跟踪系列完整投递与 io_uring_task_sleeping() 的实作'
contribution_opportunities:
  - kind: discussion
    description: '系列完整发出后评估 sched_submit_work() 回调时机与顺序的合理性'
generated_at: '2026-09-14T11:35:00'
source_email_count: 1
related_articles: []
tags: []
---
