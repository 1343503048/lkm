# sched: Add task enqueue/dequeue trace points

> **subject**：`sched: Add task enqueue/dequeue trace points`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260831-010：Gabriele Monaco（Red Hat）在 20 补丁 RFC 中首发该 tracepoint 补丁——在通用 `enqueue_task()`/`dequeue_task()`/`__block_task()` 路径加一对 `sched_enqueue`/`sched_dequeue` tracepoint 并 GPL 导出，方向由 Peter Zijlstra 建议、K Prateek Nayak 已 `Reviewed-by`。
- sched-20260929-013：该补丁作为 RV「remaining deadline monitors」10 补丁系列的 05/10 重发。
- sched-20261001-011：Gabriele 把它作为新 15 补丁系列的 01/15 再发 v2；Peter 回帖「不记得来龙去脉、你忘了把其余补丁发给我、changelog 无动机说明——As is I'm clueless as to why we want this」。
- sched-20261002-004（今天）：动机之争开始收敛。Gabriele 回复解释了用途——tracepoint 用于 RV deadline monitor 建模「dl_server 从 idle 变 ready」事件与「任务在调度类 runqueue 间移动」，并为未 CC Peter 致歉；Peter 二轮回复亮出工作原则「partial series 直接进 'later' pile」，并追问 RV 模型的 .c 与 .dot 文件不一致问题、要求把文档折进 .dot 而非单设 .rst（「insert rant on what a piece of shit rst is here」）；Gabriele 承认无 1-1 映射的复用是有意为之（简化模型），并接受把描述折入 .dot 的方向。

## 背景与问题

（承接 sched-20260929-013）现有 sched tracepoint 覆盖事件语义（`sched_wakeup`/`sched_switch`/`sched_migrate_*`），缺一对「任务被放进/拿出 runqueue」的通用观察点；RV 的 deadline monitor 需要它来观测两类事件：dl_server 从 idle 到 ready（有新 fair 任务可用）、任务被移进/移出另一个 scheduler runqueue。补丁已辗转三个宿主系列（20 补丁 RFC → RV 10 补丁 → 15 补丁 v2），Peter 10-01 的「clueless」反应正是系列辗转导致上下文丢失的后果。今天的问题焦点转为 RV 模型自身的工件一致性：Peter 发现 monitor 的 .c 文件里有 enqueue tracepoint attach，.dot 状态图里却没有对应节点——按「.c 是 .dot 的产物」的理解，两者应一致。

## 技术方案

（承接）tracepoint 补丁本体：`include/trace/events/sched.h` 用 `DECLARE_TRACE` 声明 `sched_enqueue`/`sched_dequeue`（原型 `(struct task_struct *tsk, int cpu)`），`EXPORT_TRACEPOINT_SYMBOL_GPL` 导出；`enqueue_task()` 仅 `!(flags & ENQUEUE_DELAYED)` 时打点、`dequeue_task()` 仅 `!(flags & DEQUEUE_SLEEP)` 时打点、`__block_task()` 开头补 `trace_sched_dequeue_tp()`；`trace_*_enabled()` 静态键控制开销。

今天讨论的 RV 模型层面：
- **事件复用是有意的**：throttle 场景用 `handle_sched_enqueue()` 表示 dl_defer_arm 的一个 case（fair 任务未 boost 运行、经另一 scheduler 入队）；boost 场景对称地用 `handle_sched_dequeue()`。Gabriele：「There isn't always a 1-1 mapping with model events and tracepoints... I'm reusing an event that can be triggered from other tracepoints too, ideally to keep the model simpler」——同一 handler 也可由其它 tracepoint 触发。dl_server_resume[_throttled] 本质是 plain enqueue，考虑改名以显名化。
- **文档归属**：Peter 要求 .rst 不存在、graph-easy 与描述作为注释放进 .dot 单文件；Gabriele 接受（「I may look into ways to get both birds with a stone」——既保留 html docs 又满足单文件审查）。

## 版本演进与当前进展

- v1（08-31）：20 补丁 RFC 01/20（sched-20260831-010）。
- 09-29：RV 10 补丁系列 05/10（sched-20260929-013）。
- 10-01：15 补丁系列 v2 01/15（`<20261001152042.124445-2-gmonaco@redhat.com>`）；Peter「clueless」回复（sched-20261001-011）。
- 10-02（今天）：
  - bpf-ci bot 对 v2 01/15 跑过一轮（`<bc804b8da940cc0dab648ec1bec497c3e1097999c1a7a2cea204896c3cd7fd3d@mail.kernel.org>`）。
  - Gabriele（15:09，`<d75888885e2c94c1bc717faa864f609c43db874f.camel@redhat.com>`）解释动机：borrowed from RV 系列 [2]，RV monitor 用这对 tracepoint 建模 dl_server idle→ready 与跨 runqueue 移动；为没把 RV 系列 [3][4] CC 给 Peter 致歉。
  - Peter（18:29，`<20261002102939.GB2823843@noisy.programming.kicks-ass.net>`）：partial series 进 later pile；.c/.dot 不一致「So what gives?」；要求文档折进 .dot、删 .rst。
  - Gabriele（19:55，`<56972260b9221128d7aaf5bb60f90611ec9d7235.camel@redhat.com>`）：承认 to_cmd 脚本要修；解释复用非 1-1 是有意；接受 .dot 单文件方向。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**（sched 维护者）：亮出评审门槛——「So mostly I flat out ignore partial series. It means I have to go dig around to figure out the whole picture, and anything that requires extra effort goes on the 'later' pile」；技术质疑集中在 RV 模型工件不一致（.c 有 attach、.dot 无对应）与文档形式（.rst 应并入 .dot）。语气仍是对宿主系列的审查，不是对 tracepoint 本体的反对（其 `Suggested-by` 仍在 trailer 上）。
- **Gabriele Monaco**（作者）：补齐了动机叙事（RV monitor 的两类事件需求），接受文档折叠方向；暴露的流程问题是「系列辗转三次+抄送遗漏」导致维护者上下文丢失。
- 待决：.dot/.c 一致的解释（Peter 的「So what gives?」尚未被直接回答——Gabriele解释了 handler 复用，但 .dot 图里是否需要补节点仍开放）。

## 合入评估

*likelihood=medium*。动机叙事今天补上了（Peter 索要的东西到位一半），tracepoint 本体干净且有 R-b；但 Peter 的「partial series 进 later pile」原则意味着 15 补丁系列必须完整送达且 RV 模型工件自洽才进入正式评审。*blocking_issues*：15 补丁系列完整性（当日缓存仍只见 01/15）；RV 模型 .dot/.c 不一致的解释未完成；.rst→.dot 文档折叠待落实。*next_action*：Gabriele 修 to_cmd 脚本保证全系列送达、回答 .dot 缺节点问题、把描述折进 .dot 后发 v3。

## 效果评估

无效果数据（trace 开销对比、启用/未启用性能数字均无）。bpf-ci bot 对 v2 01/15 的测试未见失败报告。

## 我可以参与的点

- `review`：帮 Gabriele 回答 Peter 的「.dot 里为什么没有 enqueue 对应节点」——对照 RV monitor 的 .c attach 与 .dot 状态图，给出「补节点 vs 在 .dot 注释里说明复用」的方案。
- `review`：检查 15 补丁系列的完整性（cover 与其余 14 篇的送达情况），确认 Peter 是否能拿到全量——这正是当前最大卡点。

## 参考链接

- Gabriele 的动机解释: https://lore.kernel.org/all/d75888885e2c94c1bc717faa864f609c43db874f.camel@redhat.com/
- Peter 的二轮回复: https://lore.kernel.org/all/20261002102939.GB2823843@noisy.programming.kicks-ass.net/
- Gabriele 的解释+接受方向: https://lore.kernel.org/all/56972260b9221128d7aaf5bb60f90611ec9d7235.camel@redhat.com/
- v2 01/15: https://lore.kernel.org/all/20261001152042.124445-2-gmonaco@redhat.com/

---
id: sched-20261002-004
date: '2026-10-02'
subject: 'sched: Add task enqueue/dequeue trace points'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20261001152042.124445-1-gmonaco@redhat.com>'
lore_url: 'https://lore.kernel.org/all/20261002102939.GB2823843@noisy.programming.kicks-ass.net/'
authors:
  - 'Gabriele Monaco'
maintainers_involved:
  - 'Peter Zijlstra'
current_version: v2
patch_series:
  - version: v2
    msgid: '<20261001152042.124445-2-gmonaco@redhat.com>'
    date: '2026-10-01'
    summary: '15 补丁系列 01/15 重发 sched_enqueue/sched_dequeue tracepoint'
    review_outcome: '10-02 动机解释到位一半；Peter 给出 partial-series 门槛与 .dot/.rst 文档要求'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - '15 补丁系列未完整送达（当日缓存仅见 01/15）'
    - 'RV 模型 .dot/.c 不一致的解释未完成'
    - '.rst→.dot 文档折叠待落实'
  next_action: '作者修 to_cmd 保证全系列送达、回答 .dot 缺节点问题后发 v3'
contribution_opportunities:
  - kind: review
    description: '对照 .c attach 与 .dot 状态图给出复用说明方案'
  - kind: review
    description: '检查 15 补丁系列完整性，确认维护者能拿到全量'
generated_at: '2026-10-03T01:00:00'
source_email_count: 4
related_articles:
  - sched-20260831-010
  - sched-20260929-013
  - sched-20261001-011
tags:
  - sched_debug
  - rv
---
