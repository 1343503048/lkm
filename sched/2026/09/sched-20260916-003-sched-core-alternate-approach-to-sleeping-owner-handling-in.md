# sched/core: Alternate approach to sleeping-owner handling in PROXY_EXEC

## TL;DR
K Prateek Nayak（AMD）在 08-26 发出的 RFC/PoC（16 枚），提出与 John Stultz 正在推进的「sleeping-owner enqueuing」不同的另一条路线：用一组新的 per-task 状态（`blocked_cpu`、`is_linked` 等）把整条 blocked 等待链绑定到单一 CPU 上统一唤醒。本日 John Stultz 给出详细评审，作者本人坦承「更多东西需要打磨」，且两人正在就「谁的路线上游先行」做取舍。属开放讨论，合入可能性未知。

## 背景与问题
proxy execution 下，当锁 owner 睡眠时，直接或间接等待该锁的任务链会被 enqueue 到睡眠 owner 上。John Stultz 的方案（`activate_blocked_waiters()` + 多任务列表，即他本人称之为「一大块 patch」的 sleeping-owner enqueuing）与 Prateek 的这套 RFC 是解决同一问题的两种设计。Prateek 的动机是提供一种「更深度融入调度器逻辑」的替代方案，并附带 lock-nesting 优化。

## 技术方案
Prateek 的方案核心：当任务 blocked 且 queued 到睡眠 owner 上时（`p->is_linked = 1`），整条链绑定到单一 CPU（`p->blocked_cpu`），后续 Patch 13 以 `(SLEEP | MIGRATING)` 阻塞并在 `p->on_rq` 转 0 前 `__set_task_cpu()` 到 `owner->blocked_cpu`。需要第二个变量 `blocked_cpu` 是因为 `p->wake_cpu` 可能变化，而整条链需要一个统一的唤醒 CPU。相比 John 的方案，其 locking 更简单，但引入了 `blocked_cpu`、`is_linked/needs_rq_sync`、`sched_migrated_on_blocking`、`lock_nesting` 等多组新状态，并依赖 `ENQUEUE/DEQUEUE_MIGRATING` 标志的微妙语义。

## 版本演进与当前进展
- **RFC v1（PoC）**（2026-08-26，`<20260826062901.2137-1-kprateek.nayak@amd.com>`）：16 枚补丁。本日（09-16）John Stultz 首次系统性评审，作者逐点回应。作者计划在 proxy futex 代码前后重新 rebase 后发下一版。

## Maintainer 意见与讨论焦点
- **John Stultz**：认可方向——「definitely interesting，看起来更深度融入调度器逻辑，应该能带来比我的方案更好的结果」。但列出代价：新增大量 per-task 状态、状态间依赖（`sched_migrated_on_blocking` 绑定 `is_linked`）、依赖 `ENQUEUE/DEQUEUE_MIGRATING` 显得微妙（他自己也常搞错这些 flag）。优点：locking 更简单。担心 `proxy_activate_blocked_task()` 的 rq_lock 持锁时长。并直接问「你摸清 Peter 的态度了吗」。
- **K Prateek Nayak（作者）**：承认 rq_lock 只在 slow path 且仅几次 on_rq/list 操作；推测 Peter 可能更偏好 John 的方案（因为 John 的还处理 delayed tasks、不加东西进 `ttwu_runnable()`、也没有「疯狂的 (DEQUEUE_SLEEP | DEQUEUE_MIGRATING)」行为及其对 PELT/SCHED_DEADLINE 的更大影响）；坦言这套 RFC 更多是为了引发讨论，若走这条路还有不少要打磨。
- **具体 patch 争议**：04/16（no owner 时激活 blocked donor）作者承认一个 bug——没走 `proxy_resched_idle()` 时 idle task 不会置 `NEED_RESCHED`，CPU 可能带着 runnable 任务空转，需要修；09/16 双方就 `blocked_cpu` 与 `wake_cpu` 的区别达成共识（整条链需要统一唤醒 CPU）。
- 两人正在做的关键取舍：John 想尽快推进自己那套 sleeping-owner enqueuing 上游，纠结是继续自己的大 patch 还是转向 Prateek 的系列。

## 合入评估
likelihood=unknown。作者明确表示这是 PoC/讨论性质，尚需大量打磨；Peter Zijlstra 尚未表态（作者计划在 LPC 上找 Peter 交流）；且与 John Stultz 的上游路线存在取舍关系，方向本身未定。blocking_issues：与 John 方案的上游取舍未决、04/16 的 idle 空转 bug、PELT/SCHED_DEADLINE 语义风险、Peter 尚未评审。next_action：等 John/Peter 定方向；作者 rebase 后发 v2。

## 效果评估
作者称在 John 的堆栈中间测试过、未到 futex 位就「脑袋打转」，无公开基准数据。John 称「在测试中表现还行」。均属主观观察，未见量化数据。

## 我可以参与的点
- kind=review：评估该方案对 PELT 与 SCHED_DEADLINE 记账的影响（作者自己也点名这是风险点），对照 John 的方案给出对比。
- kind=testing：在 proxy futex 相关 workload 下对比两套 sleeping-owner 方案的行为（尤其 blocked 任务唤醒顺序与锁握手延迟）。

## 参考链接
- RFC cover：https://lore.kernel.org/all/20260826062901.2137-1-kprateek.nayak@amd.com/
- John Stultz 评审：https://lore.kernel.org/all/CANDhNCpEYgckCPYhjL8oQGYv9r8joP_1tBps4bGQFD3vWDCetA@mail.gmail.com/

---
id: sched-20260916-003
date: '2026-09-16'
subject: 'sched/core: Alternate approach to sleeping-owner handling in PROXY_EXEC'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: '<20260826062901.2137-1-kprateek.nayak@amd.com>'
lore_url: 'https://lore.kernel.org/all/20260826062901.2137-1-kprateek.nayak@amd.com/'
authors:
  - 'K Prateek Nayak'
maintainers_involved:
  - 'John Stultz'
current_version: null
patch_series:
  - version: v1
    msgid: '<20260826062901.2137-1-kprateek.nayak@amd.com>'
    date: '2026-08-26'
    summary: '16 枚 PoC，sleeping-owner 处理的替代方案（blocked_cpu / is_linked 链绑定）'
    review_outcome: 'John Stultz 认可方向但列出一组状态复杂度代价，作者拟 rebase 后发 v2'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - '与 John Stultz 方案的上游取舍未决'
    - '04/16 未置 NEED_RESCHED 导致 idle 空转的 bug'
    - 'PELT / SCHED_DEADLINE 记账语义风险'
    - 'Peter Zijlstra 尚未评审'
  next_action: '等 Peter/John 定方向，作者 rebase 后发 v2'
contribution_opportunities:
  - kind: review
    description: '评估对 PELT 与 SCHED_DEADLINE 记账的影响，与 John 方案对比'
  - kind: testing
    description: '在 proxy futex workload 下对比两套 sleeping-owner 方案行为'
generated_at: '2026-09-17T09:00:00'
source_email_count: 9
related_articles:
  - sched-20260831-002
tags:
  - proxy_execution
---
