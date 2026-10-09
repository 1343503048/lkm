# sched_ext: Keep proxy donors with slice left on the local DSQ

> **subject**：`sched_ext: Keep proxy donors with slice left on the local DSQ`
> 本文为增量更新，完整脉络见下。

## TL;DR

- sched-20261002-008：Andrea Righi（NVIDIA，sched_ext 维护者）发往 `sched_ext/for-7.4` 的单补丁修复——commit ee172227d0dc 让 `put_prev_task_scx()` 把保留的 proxy donor 以 `SCX_ENQ_BLOCKED` 交还 `ops.enqueue()`，但三类 put 只是 proxy 记账，BPF 被迫反复做无意义 dispatch；补丁改为有 slice 剩余的 donor 放本地 DSQ 头部，并用新 `SCX_RQ_PROXY_PICK_PENDING` rq 标志区分「记账性 put」与「真实 IMMED 抢占」。
- sched-20261003-001：Tejun Heo 提出根本性质疑——IMMED 对 blocked donor 不该起作用（donor 正被 proxy execution 服务中）；若成立，有 slice 的 donor 无论 IMMED 与否都留本地 DSQ，`SCX_RQ_PROXY_PICK_PENDING` 整个不需要。Andrea 认同并当天发 v2 全部采纳：删 PICK_PENDING、IMMED 全面豁免、blocked-donor 回退折进普通 enqueue 路径。
- sched-20261007-005（今天）：**Tejun 收回自己 10-03 的方向**（"Sorry, I steered this the wrong way"）——对 donor **全面**豁免 IMMED 等于覆盖调度器对该任务的明确意图：被更高调度类抢占的 IMMED donor 会一直坐在本 CPU 的 local DSQ 等 CPU 转回来，而 IMMED 本应把它交还 BPF 立即重新放置。正确条件是「只在其马上要被 pick 时保持本地」——即 `proxy_resched_idle()` 的记账性 put，**也就是 v1 的 PICK_PENDING 语义**，要求回到那个方案（deferred 扫描无需 blocked 豁免、wakeup 重查也可删）。Andrea 回复提出实现：重新引入 `SCX_RQ_PROXY_PICK_PENDING` + 新增 `SCX_RQ_PROXY_BLOCKING` 两个 rq 标志，全部逻辑留在 `ext.c`、不动 `sched/core.c`，并反问方案是否成立。

## 背景与问题

（承接 sched-20261002-008 → sched-20261003-001）proxy execution 下 blocked 在 mutex 上的任务可作为 donor 留在 runqueue；ee172227d0dc 后 `put_prev_task_scx()` 把保留 donor 交还 BPF 造成无意义 dispatch 往返。v1 用「本地 DSQ 头部 + PICK_PENDING 区分记账性 put」解决；v2 按 Tejun 意见改为「IMMED 对 blocked donor 全面豁免」。今天的转折点：v2 的全面豁免**伤到了未被阻塞语义覆盖的另一半**——IMMED 标志本身表达了调度器的放置意图（任务未被服务时应立即回到 BPF），donor 被更高类抢占时这一意图仍应成立；只有「马上要被 pick」的记账性 put 才是纯 proxy 内部事务。问题的本质是把两类 put（记账 vs 真实抢占）重新切开。

## 技术方案

（承接 v1/v2 框架）Tejun 今天定下的目标条件与 Andrea 的实现回应：

1. **回到 PICK_PENDING 语义（Tejun）**：IMMED donor 只在「马上要被 pick」时保持本地——即 `proxy_resched_idle()` 的记账性 put；真实抢占则像任何 IMMED 任务一样交还 BPF 经 `ops.enqueue()` 重新放置。v1 的 `proxy_put` + `PICK_PENDING` 正是这个，要求回退。
2. **连锁简化（Tejun）**：deferred 扫描不再需要 blocked 豁免——记账性 put 之后 donor 在队列头部、rq 正走向 idle，现有 `first && rq_is_open()` 测试自然保留它；`wakeup_preempt_scx()` 的重查也不需要（donor 不会被留在「未阻塞 IMMED 任务不能待」的地方）。
3. **注释请求（Tejun）**：现有一处代码读起来像「flag 保留」，实际原因是 `scx_caps_for_enq()` 把 IMMED 映射到 `SCX_CAP_ENQ_IMMED`、只持 base cap 的子调度器也能把 donor 留本地——要求加注释。
4. **ENQ_LAST 上不再排除 donor（Tejun）**：v2 给 `ENQ_LAST` 条件加的 `!p->is_blocked` 要删——无 ENQ_LAST 的调度器对 donor 本来就不触发（`dispatch_one()` 经 KEEP_LAST 保它并续 slice）；有 ENQ_LAST 的调度器需要这个信号（CPU 带   着队列任务进 idle，BPF 要安排后续事件），donor 与其它 last 任务一样需要。
5. **Andrea 的两标志实现**：重新引入 `SCX_RQ_PROXY_PICK_PENDING`（区分 `proxy_resched_idle()` 临时 put 与 IMMED donor 真实抢占）+ 新增 `SCX_RQ_PROXY_BLOCKING`（在 `sched_proxy_block_task()` 调用前后设置：`proxy_reset_donor()` 触发 `put_prev_task_scx()` 时该标志让 sched_ext 不重排 donor，`block_task()` 随后立刻 dequeue）——两个标志定义在 `sched.h`、逻辑全在 `ext.c`，不动 `sched/core.c`；同时消除暂态 enqueue/dequeue 对与无 ENQ_LAST 调度器上的假 WARN。
6. **遗留难点（Tejun 提出思路）**：`sched_proxy_block_task()` 里 `proxy_reset_donor()` 以 owner 执行上下文为 @next put 仍在队列的 donor——fair owner + 清零 slice 会走 LAST 分支、对无 ENQ_LAST 调度器合法触发 WARN。思路：先 `dequeue_block_task()` 再 reset 再 `__block_task()`，put 看到未排队任务，顺带消掉 `ops.enqueue()/ops.dequeue()` 对。

## 版本演进与当前进展

- v1（10-02）：本地 DSQ 头部 + PICK_PENDING（sched-20261002-008）。
- v2（10-03）：按 Tejun 意见删 PICK_PENDING、IMMED 全面豁免（sched-20261003-001）。
- 10-07：Tejun 承认 v2 方向被自己带偏，要求回到 v1 的 PICK_PENDING 语义（细化版）；Andrea 当日回应全部认可并提出双 rq 标志实现，**v3 待发**。
- 未进任何分支；`Fixes: ee172227d0dc`、base 为 `sched_ext/for-7.4`。

## Maintainer 意见与讨论焦点

- **Tejun Heo**（sched_ext 首席维护者）：主动纠错（"Sorry, I steered this the wrong way"）。核心论点：IMMED 是调度器对该任务的明确意图，全面豁免等于内核替 BPF 调度器做主；只应豁免「马上要被 pick」的记账性 put。附带三个具体要求：删 blocked 豁免与 wakeup 重查、补 caps 映射注释、ENQ_LAST 不排除 donor。
- **Andrea Righi**（作者，NVIDIA）：逐条 ack，并把 Tejun 对 `sched_proxy_block_task()` WARN 的顾虑转化为 `SCX_RQ_PROXY_BLOCKING` 标志方案——关键卖点是**不改 `sched/core.c`**（proxy 的 sched/core 侧刚经历多轮稳定性修复，避免再碰）。
- 分歧已收敛为「两个 rq 标志够不够」的实现问题；无方向性争议。

## 合入评估

*likelihood=medium*（从 high 回调）。方向经维护者两轮修正后重新收敛，但 v2→v3 是一次方案回摆，需要 Andrea 再发一版、Tejun 再 review 一轮才能落；且「逻辑全留 ext.c」的自我约束增加了实现约束。*blocking_issues*：v3 未发、`SCX_RQ_PROXY_BLOCKING` 方案尚无 Tejun 确认。*next_action*：Andrea 发 v3（双标志版），Tejun 确认后进 `sched_ext/for-7.4`。

## 效果评估

无新 benchmark。定性收益沿链继承：消除记账性 put 的 BFP dispatch 往返（v1 数据：dispatch 次数下降）；v3 预期额外恢复 IMMED donor 被抢占时的正确重放置路径。`sched_proxy_block_task()` 的假 WARN 消除是正确性收益。

## 我可以参与的点

- `review`：v3 的天然复核点是 `SCX_RQ_PROXY_BLOCKING` 的设置窗口——它必须在「`proxy_reset_donor()` 可能被调用的所有路径」上包裹住（handover、migration、deactivate），漏一条就是又一个偶发 WARN；这正好接上 Tejun 在 `sched_proxy_block_task()` 上提出的疑虑。
- `testing`：构造「IMMED donor 被更高调度类抢占」场景（如 RT 任务唤醒），对比 v2（donor 困在本地 DSQ）与 v3（交还 BPF 重放置）的 proxy 解析时延。
- 回合视角：OLK-6.6 无 proxy execution 集成，不适用。

## 参考链接

- Tejun 的纠错 review: https://lore.kernel.org/all/09a36d7e76652beedcfb891b587a9c82@kernel.org/
- Andrea 的双标志方案: https://lore.kernel.org/all/asXxp0WabkwdB5aw@gpd4/
- v2 补丁: https://lore.kernel.org/all/20261002221559.3090900-1-arighi@nvidia.com/
- 相关文章：[[sched-20261002-008]]（v1）、[[sched-20261003-001]]（v2）

---
id: sched-20261007-005
date: '2026-10-07'
subject: 'sched_ext: Keep proxy donors with slice left on the local DSQ'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20261002221559.3090900-1-arighi@nvidia.com>'
lore_url: 'https://lore.kernel.org/all/20261002221559.3090900-1-arighi@nvidia.com/'
authors:
  - 'Andrea Righi'
maintainers_involved:
  - 'Tejun Heo'
current_version: v2
patch_series:
  - version: v1
    msgid: '<20261001191216.2391359-1-arighi@nvidia.com>'
    date: '2026-10-02'
    summary: '有 slice 的 donor 放本地 DSQ 头部 + PICK_PENDING 区分记账性 put'
    review_outcome: 'Tejun 提出 IMMED 全面豁免，催生 v2'
  - version: v2
    msgid: '<20261002221559.3090900-1-arighi@nvidia.com>'
    date: '2026-10-02'
    summary: '删 PICK_PENDING；IMMED 全面豁免；折进普通 enqueue 路径'
    review_outcome: '10-07 Tejun 收回方向：全面豁免覆盖调度器意图，要求回到 PICK_PENDING 语义'
upstream_commit: null
fixes_commit: 'ee172227d0dc'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'v3 未发；双 rq 标志方案待 Tejun 确认'
  next_action: 'Andrea 发 v3（PICK_PENDING + PROXY_BLOCKING 双标志版）'
generated_at: '2026-10-08T01:00:00'
contribution_opportunities:
  - kind: review
    detail: '复核 PROXY_BLOCKING 标志是否覆盖 proxy_reset_donor 的全部调用路径'
  - kind: testing
    detail: 'IMMED donor 被更高类抢占场景对比 v2/v3 的重放置时延'
source_email_count: 2
related_articles:
  - sched-20261002-008
  - sched-20261003-001
tags:
  - sched_ext
  - proxy_execution
---
