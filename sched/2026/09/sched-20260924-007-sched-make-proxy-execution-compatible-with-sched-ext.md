# sched: Make proxy execution compatible with sched_ext

## TL;DR
- sched-20260910-002：Peter Zijlstra 对 Andrea Righi 的 proxy-execution 兼容 sched_ext 系列（v13，18 枚）的正式评审——在 03/04/05/07/08/09/14/15 共 8 个补丁上留下 10 条意见，08/18（WF_ON_RQ）与 09/18（跨调度类转换阻塞 donor）的设计被直接质疑，03/18、14/18 的前提被指「不可能发生」，15/18 给了明确可接受的改法。
- sched-20260916-002：Peter 继续逐 patch 评审 v13，焦点在 08/18 的 `WF_ON_RQ` 语义与 07/18 的 reject-DSQ 重试点设计；暂无 NAK，但 08/18 方向仍有开放讨论。合入可能性中等。
- sched-20260923-002：Andrea Righi 发出 v14（16 枚），基本落实 Peter 在 v13 评审中的全部意见，附 kselftest `enq_blocked`（blocked-donor admission 使 mutex wait 延迟 same-CPU 降 20.41%、cross-CPU 降 12.86%），进入 v14 复审等待期。
- sched-20260924-007（今天，增量更新）：Peter Zijlstra 在 v14 基础上提出一个新方向的收口构想——把 `sched_class->switching_to` 从 `void` 改为返回 `bool`，让 sched_ext 的 `switching_to_scx()` 在 `!scx_allow_proxy_exec(p)` 时返回 true 以直接 `block_task()`（取代原 `sched_proxy_block_task()` 提前回调），并顺手把 `uclamp_enabled` 字段改成 `flags` 位图（`SC_UCLAMP`）加 `SC_CONFIRM`（`SNT_CONFIRM`）确认 set_next_task。Peter 本人也备注「不确定 SC_CONFIRM 是否真更好」。K Prateek Nayak 追问是否还需检查 `ctx->queued`，避免 block 掉一个本已下 rq 的任务。方向仍在收敛中，未 NAK。

## 背景与问题
- sched-20260910-002：代理执行把调度上下文（`rq->donor`）与执行上下文（`rq->curr`）拆开以缓解优先级反转；本系列（sched_ext/for-7.4）目标是解除 `CONFIG_SCHED_PROXY_EXEC` 对 `!SCHED_CLASS_EXT` 的依赖，让 BPF 调度器全面接管 donor/curr 拆分后的策略与记账。
- sched-20260916-002：系列目标进一步明确为——让 sched_ext 感知 proxy 带来的 donor/curr 分离、blocked donor 的 runqueue 驻留、以及任务在 EXT 调度类与其它类之间切换时的清理时机。
- sched-20260923-002：背景延续：互斥根源是 sched_ext 通过 DSQ 与 BPF 自主驱动 dispatch，而 proxy handoff 会运行一个 BPF 从未 dispatch 过的任务，导致 kfunc/helper 观测到的「当前任务」与 BPF 侧账本不一致。
- sched-20260924-007（今天）：无新背景，属 v14 落地后对「blocked-donor 处理」实现形态的进一步重构讨论。

## 技术方案
- sched-20260910-002：全部是 Peter 对既有 v13 补丁的设计反馈（03/18 NOHZ CFS bandwidth、04/18 假迁移告警、08/18 WF_ON_RQ、09/18 跨类转换阻塞、15/18 委派 donor admission 等）。
- sched-20260916-002：落在 07/18（`scx_proxy_reenqueue_retry`）、08/18（`WF_ON_RQ`）、09/18（`sched_proxy_block_task()` 清理迁移到 sched_ext ownership-transition）三处。
- sched-20260923-002：v14 关键收敛——current-task kfunc 统一报告 BPF 选中的 donor；blocked donor 仅在 proxy resolution 成功后进入 `ops.running()/stopping()` 会话；`WF_ON_RQ`→`WF_TTUW_RQ`；`scx_qmap` 加 `-X`、新 kselftest `enq_blocked`。
- sched-20260924-007（今天）：Peter 提出（附完整 diff）：
  - 把 `struct sched_class` 的 `switching_to` 由 `void` 改为 `bool (*switching_to)(...)`，`sched_change_end()` 里 `if (block && p->is_blocked) { block_task(rq, p, ...); ctx->queued = false; }`——即把「blocked donor 阻塞」收敛进 `switching_to` 返回值，取代原先「提前在 `sched_change_begin()` 前跑 `sched_proxy_block_task()`」的设计。
  - `switching_to_scx()` 返回 `!scx_allow_proxy_exec(p)`；`switching_to_idle/stop` 保持 `BUG()` 返回 false。
  - 用 `sched_class->flags`（`SC_UCLAMP = 1<<0`，`SC_CONFIRM = 1<<1`）替代 `uclamp_enabled` 字段；`__schedule()` 中 `set_next_task(rq, donor, SNT_PICK)` + `if (flags & SC_CONFIRM) set_next_task(..., SNT_CONFIRM)`，并给 `enum snt_e` 增 `SNT_CONFIRM`。Peter 自己备注「although I'm not convinced SC_CONFIRM is actually making it better」。
  - 引用了另一条 pending 系列 `hrtick-restart-v4`（`20260917-sched-fair-hrtick-restart-v4-1-...@gentwo.org`），表示「would something like the below on top of both this work?」。
- K Prateek Nayak 追问：`switching_to` 返回 block 的分支「Shouldn't this also check for `ctx->queued`? Otherwise we may block an already off rq task.」。
- 05/16（sched_ext hooks）上 Peter 另指出一处「与原型不符、且 `next == rq->idle` 情况下 next 参数用法存疑——像是把参数当 `proxy = next != rq->donor` 用，但那是关于 tick 而非把 current 放回 dsq」。

## 版本演进与当前进展
- v13（18 枚，sched-20260910-002 起）→ **v14（16 枚，09-22，`<20260922165445.943315-1-arighi@nvidia.com>`）**：落实 v13 评审意见（WF_TTUW_RQ、static-key 门控、NOHZ_FULL 保守重开 tick 等），本日（09-24）进入 Peter 的新一轮重构构想期，尚未出 v15。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**（本日）：提出 `switching_to` 返回 bool + `flags` 位图的收口重构，且对 `SC_CONFIRM` 是否更优持保留（「not convinced」）；05/16 上指出原型不符与 next 参数语义存疑。
- **K Prateek Nayak（AMD）**：追问 block 分支是否缺 `ctx->queued` 检查，避免 block 已下 rq 的任务。
- 无 NAK；讨论聚焦「blocked donor 的实现形态」仍在收敛。

## 合入评估
*likelihood=medium*。方向获认可、v14 已实质落地，但 Peter 又提出 `switching_to` 返回 bool + flags 的进一步重构，加上 K Prateek 的 `ctx->queued` 追问与 05/16 的 next 参数存疑，说明 v14 尚需一到两轮改版。*blocking_issues*：blocked-donor 实现形态（返回 bool vs 提前回调）未定；05/16 next 参数语义待澄清。*next_action*：作者按 Peter 的返回 bool 构想出新版并回应 K Prateek 的 `ctx->queued` 问题。

## 效果评估
- 沿用 v14 的 kselftest `enq_blocked` 数据（sched-20260923-002）：blocked-donor admission 使 mutex wait 延迟 same-CPU 降 20.41%、cross-CPU 降 12.86%。本日无新增 benchmark。

## 我可以参与的点
- kind=review：评估 Peter 的 `switching_to` 返回 bool 方案里 `block_task()` + `ctx->queued = false` 的时序，以及 K Prateek 提出的 `ctx->queued` 检查是否必要。
- kind=discussion：`SC_CONFIRM`（`SNT_CONFIRM`）是否真能替代 `scx_proxy_donor_start()` 并改善语义，给出取舍判断。

## 参考链接
- lore (v14 cover): https://lore.kernel.org/all/20260922165445.943315-1-arighi@nvidia.com/
- Peter 返回 bool 构想: https://lore.kernel.org/all/20260924075925.GE4121620@noisy.programming.kicks-ass.net/
- Peter flags/SC_CONFIRM diff: https://lore.kernel.org/all/20260924075237.GH2009045@noisy.programming.kicks-ass.net/
- K Prateek ctx->queued 追问: https://lore.kernel.org/all/05319013-86e6-4a80-bb8f-385657cee410@amd.com/
- Peter 05/16 意见: https://lore.kernel.org/all/20260924075107.GC4121339@noisy.programming.kicks-ass.net/

---
id: sched-20260924-007
date: '2026-09-24'
subject: 'sched: Make proxy execution compatible with sched_ext'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20260922165445.943315-1-arighi@nvidia.com>'
lore_url: 'https://lore.kernel.org/all/20260922165445.943315-1-arighi@nvidia.com/'
authors:
  - 'Andrea Righi'
maintainers_involved:
  - 'Peter Zijlstra'
  - 'Tejun Heo'
current_version: v14
patch_series:
  - version: v14
    msgid: '<20260922165445.943315-1-arighi@nvidia.com>'
    date: '2026-09-22'
    summary: '16 枚：落实 v13 评审意见，WF_TTUW_RQ + blocked-donor admission 等'
    review_outcome: 'Peter 提出 switching_to 返回 bool + flags 重构，K Prateek 追问 ctx->queued'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'blocked-donor 实现形态（switching_to 返回 bool vs 提前回调）未定'
    - '05/16 next 参数语义与原型不符待澄清'
  next_action: '作者按返回 bool 构想出新版并回应 ctx->queued 问题'
contribution_opportunities:
  - kind: review
    description: '评估 switching_to 返回 bool 方案的时序与 ctx->queued 检查必要性'
  - kind: discussion
    description: '判断 SC_CONFIRM/SNT_CONFIRM 能否替代 scx_proxy_donor_start'
generated_at: '2026-09-25T09:00:00'
source_email_count: 5
related_articles:
  - sched-20260923-002
tags:
  - sched_ext
  - proxy_execution
---