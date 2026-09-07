# sched: Add task enqueue/dequeue trace points

## TL;DR

Gabriele Monaco（Red Hat）8/31 发出 20 补丁 RFC，第 1 篇在通用入队/出队路径 `enqueue_task()`/`dequeue_task()`/`__block_task()` 上加一对新 tracepoint `sched_enqueue`/`sched_dequeue`，并 `EXPORT_TRACEPOINT_SYMBOL_GPL` 导出。补丁带 `Suggested-by: Peter Zijlstra` 且已有 `Reviewed-by: K Prateek Nayak`——即方向是维护者要的、首篇已过一轮 review。当日仅 01/20 进入缓存，整个系列要解决的目标问题不可见，这一点必须说清。

## 背景与问题

现有 sched tracepoint 覆盖的是事件语义（`sched_wakeup`、`sched_switch`、`sched_migrate_*` 等），**没有一对通用的"任务被放进/拿出某个 rq"的观察点**。想在调度类无关的层面观察 runqueue 的实际增删（含 `__block_task()` 这类不走 `dequeue_task()` 的路径），只能靠 kprobe 或改代码。本补丁把这个观察点做成正式 tracepoint，并按维护者建议放进通用 `enqueue_task()`/`dequeue_task()` 层。

需要如实标注：本日邮件缓存里只有 `01/20`，cover letter（`<20260831090524.106845-1-gmonaco@redhat.com>`，仅出现在 References 中）与其余 19 篇都没有取到，因此**该系列最终要用这对 tracepoint 做什么（bpf iter、selftest、还是某种统计）无法从当日数据判断**。

## 技术方案

在 `include/trace/events/sched.h` 用 `DECLARE_TRACE` 直接声明（不带 `TP_fast_assign`/print fmt 的完整 tracepoint 定义），原型是 `(struct task_struct *tsk, int cpu)`：

```
+DECLARE_TRACE(sched_enqueue,
+       TP_PROTO(struct task_struct *tsk, int cpu),
+       TP_ARGS(tsk, cpu));
+
+DECLARE_TRACE(sched_dequeue,
+       TP_PROTO(struct task_struct *tsk, int cpu),
+       TP_ARGS(tsk, cpu));
```

关键设计取舍有三点：

1. **过滤语义**：`enqueue_task()` 里只在 `!(flags & ENQUEUE_DELAYED)` 时打点，`dequeue_task()` 里只在 `!(flags & DEQUEUE_SLEEP)` 时打点——即只记录"真正的激活/撤出 rq"，不记录延迟入队与因睡眠而 dequeue 的情况；`dequeue_task()` 为此先把 `p->sched_class->dequeue_task()` 的返回值存进 `ret` 再打点。
2. **补上不走 `dequeue_task()` 的路径**：`__block_task()`（`kernel/sched/sched.h`）开头也打一次 `trace_sched_dequeue_tp()`，避免 blocked 任务的撤出被漏掉。
3. **导出给模块/BPF**：`EXPORT_TRACEPOINT_SYMBOL_GPL(sched_enqueue_tp)`/`..._dequeue_tp)`，说明预期消费方在内核树外（模块或 BPF 程序），而不是只给 ftrace 用。
4. **开销控制**：两处都先判 `trace_*_enabled()` 再调用，未启用时成本是一次 static key 检查。

## 版本演进与当前进展

- 8/31 17:05 发出 RFC v1（20 补丁），`01/20` 为 `<20260831090524.106845-2-gmonaco@redhat.com>`。
- `01/20` 已带 `Reviewed-by: K Prateek Nayak (AMD)`；`Suggested-by: Peter Zijlstra` 表明这对 tracepoint 来自此前讨论中维护者的建议。
- 当日无新回帖（其余 19 篇补丁与 cover 未进入缓存）。

## Maintainer 意见与讨论焦点

当日线程内没有新意见。已有的信号都写在 trailer 上：Peter Zijlstra 是**建议者**（方向由他提出），K Prateek Nayak 已对首篇给 `Reviewed-by`。潜在争议（从补丁本身可读出的、社区通常会问的）：`DECLARE_TRACE` 形式不带格式化字段，事件里只有 `task_struct *` 与 cpu，是否够用；在 `dequeue_task()` 里为了打点而改写返回值为 `ret` 是否值得；以及把 `__block_task()` 也计入 dequeue 是否与 `DEQUEUE_SLEEP` 过滤的语义自洽（`__block_task()` 正是任务主动阻塞的路径）。这些当日无人提出。

## 合入评估

**possible**。首篇本身很干净、有建议者与维护树 reviewer，作为独立可合入的观测点补齐被接受的可能性不低；但它是 20 补丁 RFC 的第 1 篇，实际推进通常取决于整个系列的用途能否说服人，而当日看不到系列目标。`next_action`：需要 cover/后续补丁的动机说明，以及 sched 维护者对 tracepoint 命名与语义（是否应带 flags/task state、是否应覆盖 `__block_task()`）的表态。

## 效果评估

暂无效果数据。邮件里没有 trace 开销对比、也没有启用/未启用下的性能数字。

## 我可以参与的点

- **明确语义边界**：`DEQUEUE_SLEEP` 被排除、而 `__block_task()` 被计入，这两条组合起来"dequeue"到底表示什么，是可以直接提问或给出建议的地方；如果目标用途需要区分阻塞与迁移，现在提出来成本最低。
- **提出缺字段**：`DECLARE_TRACE` 只带 `tsk` 与 `cpu`，若做 rq 层面的统计分析会需要 `flags`、`sched_class`、`p->on_rq` 状态等；这些是可以在 RFC 阶段直接要求补的。
- **自用观测收益**：如果本地在排查入队/出队相关的负载均衡或 cgroup throttling 问题，可以把这 1 个补丁摘出来试跑并反馈开销与可用性——这类"第一个用户反馈"在 RFC 阶段通常很缺。

## 参考链接

- lore thread（01/20）: https://lore.kernel.org/all/20260831090524.106845-2-gmonaco@redhat.com/
- 系列 cover（References 中出现，正文未取到）: https://lore.kernel.org/all/20260831090524.106845-1-gmonaco@redhat.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260831-010
date: '2026-08-31'
subject: "sched: Add task enqueue/dequeue trace points"
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: "<20260831090524.106845-1-gmonaco@redhat.com>"
lore_url: "https://lore.kernel.org/all/20260831090524.106845-2-gmonaco@redhat.com/"
authors: [Gabriele Monaco, Nam Cao]
maintainers_involved: [Peter Zijlstra, K Prateek Nayak]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260831090524.106845-2-gmonaco@redhat.com>"
    date: 2026-08-31
    summary: "20 补丁 RFC 的第 1 篇：在 enqueue_task()/dequeue_task()/__block_task() 加 sched_enqueue/sched_dequeue tracepoint 并 GPL 导出，排除 ENQUEUE_DELAYED 与 DEQUEUE_SLEEP"
    review_outcome: "01/20 已带 Reviewed-by: K Prateek Nayak 与 Suggested-by: Peter Zijlstra；当日无新意见"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "整个 20 补丁系列的动机（cover 与其余补丁）当日未取到，无法判断终态用途"
    - "tracepoint 携带字段过少（仅 tsk 与 cpu），语义边界（DEQUEUE_SLEEP 排除 vs __block_task 计入）未与维护者确认"
  next_action: "作者需在 RFC 阶段说清系列目标，并确认事件字段与阻塞路径计数语义"
contribution_opportunities:
  - kind: discussion
    description: "就 sched_dequeue 是否应包含 __block_task()、是否需要携带 flags/调度类字段给意见"
  - kind: testing
    description: "把该 tracepoint 摘到自己的分支上跑一轮负载均衡/带宽限流排查，反馈开销与可用性"
generated_at: "2026-09-07T21:16:22"
source_email_count: 1
related_articles: []
tags: [sched_debug]
---
