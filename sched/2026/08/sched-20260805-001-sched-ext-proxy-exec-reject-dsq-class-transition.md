# sched_ext: Block proxy donors across scheduler transitions

# sched_ext: proxy execution 系列的两个 review 收尾（reject DSQ 泛化 + 跨类切换的代理 donor 阻断）

## 摘要

Andrea Righi 的 sched_ext proxy execution 大系列（目标 7.3）在 08-05 收到 Tejun 的两处 review 反馈，均针对 15 个 patch 中的第 9/7 号，属于「代码拆分 + 语义澄清」层面的收尾，不影响整体方向。

- **PATCH 09/15 — 泛化 reject DSQ 的 re-enqueue 路径**：Tejun 要求把「代码移动（code movement）」和「实际改动」拆成独立 patch，并建议把拒绝原因直接从拒绝点存进 `p->scx.flags`，而不是先写到 `p->scx.reject_reason` 再搬运。Andrea 已 ack，会拆分 patch 并直接把 reason 写入 `p->scx.flags`。
- **PATCH 07/15 — 跨调度类切换时阻断 proxy donor**：Tejun 提了一个边界问题——是否存在「代理执行实例需要跨调度类切换存活」的使用场景。Andrea 指出 RT/DL 的 PI（priority inheritance）正是这种场景：当 D（FAIR）因普通 mutex 被提升到 RT 时，若每次类切换都调用 `sched_proxy_block_task()` 把 D 移出运行队列，PI 提升就会在普通 mutex 边界中断，O 只能以自己的调度上下文运行，丢失了对 chain 的代理。因此**不能无条件在全局类切换时阻断**，而应作为「逐类是否支持保留 proxy donor」的能力来泛化。

## 技术细节

### reject DSQ re-enqueue 泛化（09/15）

当前实现 `scx_reenq_reject()` 从 `rq->scx.reject_dsq.list` 取出任务，先 `scx_dispatch_dequeue()` 出队，再清 `reject_reason`、把 reason 或进 `p->scx.flags` 的低位。

Tejun 的两点：
1. move + change 混在一个 patch 里增加 review 摩擦，应分离。
2. 是否可以把 reason 在「拒绝发生的点」就直接写进 `p->scx.flags`（用 `SCX_TASK_REENQ_REASON_MASK` 那段位域），省掉 `reject_reason` 这个中间变量。

Andrea 同意两者都可行。

### 跨类切换的 proxy donor 阻断（07/15）

Tejun 在 `prepare_switch_scx()` 里加了 `sched_proxy_block_task(rq, p)`，并问「是否所有类切换都该无条件阻断 proxy donor」。

Andrea 的反例（RT/DL PI 跨越普通 mutex）：
```
H (RT) 等待 rtmutex R，R 被 D 持有
D (FAIR) 等待普通 mutex M，M 被 O 持有
rt_mutex_setprio(D, H) 把 D 从 FAIR 提升为 RT
```
若 FAIR→RT 切换调用 `sched_proxy_block_task()`，D 会被移出运行队列，PI boost 停在普通 mutex 边界，O 不再被代理执行。RT/DL 的 deboost 过渡也有同样问题。

结论：应当把「是否支持保留 proxy donor」做成 per-class 能力位，不能全局无条件阻断，否则会丢掉有用的 PI 行为。

## 影响与风险

- 影响面：仅 sched_ext 的 proxy execution 内部路径，不触达非 SCX 任务。
- 风险：低。两处都是实现细节/语义澄清，没有引入新的行为回退。
- 待办：Andrea 需要 re-spin 第 9/7 号 patch（拆分 + 直接写 flags），以及把 proxy donor 保留能力抽象成 per-class 标志。

## 评价

属于大型 feature 进入 maintainer 精修阶段的正常 review 往返。方向明确、reviewer 反馈具体且可操作，合入 7.3 的概率高。

---
subject: "sched_ext: Block proxy donors across scheduler transitions"
id: sched-20260805-001
date: "2026-08-05"
title: "sched_ext: proxy execution 系列的两个 review 收尾（reject DSQ 泛化 + 跨类切换的代理 donor 阻断）"
series: "sched_ext proxy execution（7.3）"
type: feature
status: under_review
severity: none
merge_likelihood: high
tags: [sched_ext, proxy_execution, core_sched]
authors: ["Andrea Righi <arighi@nvidia.com>", "Tejun Heo <tj@kernel.org>"]
reviewers: ["Tejun Heo <tj@kernel.org>"]
related_articles: ["sched-20260804-001"]
emails: ["uid-21918@qq-imap", "uid-21667@qq-imap"]
---
