---
id: sched-20260923-002
subject: 'sched: Make proxy execution compatible with sched_ext'
date: '2026-09-23'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260922165445.943315-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260922165445.943315-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Peter Zijlstra
- Tejun Heo
current_version: v14
patch_series:
- version: v13
  msgid: <20260831134338.1531664-1-arighi@nvidia.com>
  date: '2026-08-31'
  summary: 18 枚，sched_ext 与 proxy execution 兼容
  review_outcome: Peter 逐 patch 评审，Andrea 准备 v14
- version: v14
  msgid: <20260922165445.943315-1-arighi@nvidia.com>
  date: '2026-09-22'
  summary: 16 枚，落实 Peter/Tejun v13 意见（WF_TTUW_RQ 拆分、static key 门控、ownership-transition
    清理、NOHZ tick 跟踪）
  review_outcome: 首日，待复审
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - v14 待 Peter/Tejun 复审
  - WF_TTUW_RQ 方案 vs Peter 原 is_blocked 重构思路的最终取舍未定
  next_action: 等 Peter/Tejun 复审 v14
contribution_opportunities:
- kind: review
  description: 复核 WF_TTUW_RQ 拆分与 NOHZ_FULL 保守 tick 策略对 PELT/psi 记账的副作用
- kind: testing
  description: 在真实 sched_ext 调度器锁密集负载上验证 blocked-donor admission 收益与稳定性
generated_at: '2026-09-24T09:00:00'
source_email_count: 17
related_articles:
- sched-20260916-002
- sched-20260910-002
tags:
- proxy_execution
- sched_ext
- nohz
title: 'sched: Make proxy execution compatible with sched_ext'
layout: article
---

## TL;DR
本文为增量更新，完整背景见 sched-20260916-002（v13，18 枚）及更早文章。Andrea Righi 发出 v14（16 枚）：基本落实了 Peter Zijlstra 在 v13 评审中的全部意见——`WF_ON_RQ` 更名 `WF_TTUW_RQ` 并拆为预备 patch、blocked-donor admission 用 `scx_enabled()` static key 门控、retained-donor 清理移到 sched_ext ownership-transition 路径、NOHZ_FULL 下保守重开 tick。新 kselftest `enq_blocked` 给出实测：启用 blocked-donor admission 后 mutex wait 延迟在 same-CPU 拓扑降 20.41%、cross-CPU 降 12.86%。系列方向获认可、无 NAK，进入 v14 复审等待期。

## 背景与问题
背景见 sched-20260916-002：让 proxy execution（拆分调度上下文 rq->donor 与执行上下文 rq->curr）与 sched_ext 兼容，解除 `CONFIG_SCHED_PROXY_EXEC` 与 `CONFIG_SCHED_CLASS_EXT` 的编译期互斥，使发行版能构建单内核、运行时按需选择特性。互斥根源是 sched_ext 调度器通过 DSQ 与 BPF 自主驱动 dispatch，而 proxy handoff 会运行一个 BPF 从未 dispatch 过的任务，导致 kfunc/helper 观测到的「当前任务」与 BPF 侧账本不一致。

## 技术方案
系列核心机制不变（donor 保留为调度上下文、mutex owner 仅作执行上下文；`SCX_OPS_ENQ_BLOCKED` 能力让 BPF 经 `ops.enqueue()` 接收 mutex-blocked donor，`SCX_ENQ_BLOCKED` 标记区分 blocked-donor admission 与普通 wakeup）。v14 关键设计收敛：

- 调度面向的 current-task kfunc（`scx_bpf_task_running()`/`scx_bpf_cpu_curr()`/`scx_bpf_cid_curr()`）统一报告 BPF 选中的 donor，而非恰好代为执行的 mutex owner。
- blocked donor 仅在 proxy resolution 成功后进入 `ops.running()`/`ops.stopping()` 会话，`ops.stopping()` 只对进入过会话的任务调用，与物理 rq->curr 无关。
- 任何调度类/BPF 调度器所有权切换都从干净任务状态开始：先完全 deactivate retained donor，再让新调度器按自己的 admission 策略接管。
- `scx_qmap` 加 `-X` 选项启用 mutex-blocked 任务入队；新 kselftest `enq_blocked`（含内核模块 mutex）构造 nice -20 donor / nice +19 owner / nice 0 竞争者的优先级反转场景，覆盖 same-CPU 与 cross-CPU 拓扑。

## 版本演进与当前进展
- **v14**（2026-09-22 23:51 UTC 发出，`<20260922165445.943315-1-arighi@nvidia.com>`，16 枚）：本日进入缓存。相对 v13（18 枚）的主要变化：

  - `WF_ON_RQ` → `WF_TTUW_RQ`，精确标识「跳过 activation 与 enqueue」的那条 wakeup 路径，并把 core marker 拆为独立预备 patch（Peter Zijlstra）。
  - 去掉 next-class `sched_change_begin()` 参数，retained-donor 清理移到 sched_ext ownership-transition（Peter Zijlstra）。
  - blocked-donor admission 钩子用 `scx_enabled()` static key 门控，并清理 root-scheduler activation 路径（Peter Zijlstra）。
  - 移除「不可能出现的 lower-priority donor」情形说明（Peter Zijlstra）。
  - NOHZ_FULL 上显式跟踪已 resolve 的 proxy 会话，proxy 执行期间保守重开周期 tick；`scx_proxy_reenqueue_retry()` 扩展 NOHZ 状态跟踪（Peter Zijlstra）。
  - reject-DSQ enqueue 结果统一走一个清理点（Tejun Heo）。
  - `scx_qmap` 的 cid 自掩码竞争后校验并回退 rescue placement（Richard Cheng）。
  - 澄清为何 waking EXT donor 必须在 rq->donor 复位前 dequeue、删除多余的 cached donor-state 变量（K Prateek Nayak）。
  - 删除「sched/core: Avoid false migration warning for proxy donors」——已上游合入为 `fe3c73d7bc76`。

## Maintainer 意见与讨论焦点
本日为 v14 首日，尚无对 v14 的复审；但 v14 是对 v13 评审意见的逐条落实。v13 阶段（见 sched-20260916-002）的核心分歧——`WF_ON_RQ` 语义 vs Peter 提出的 `is_blocked`+`{EN,DE}QUEUE_BLOCKED` 大重构——在 v14 以「`WF_TTUW_RQ` 精确定义 + 拆预备 patch」的方式落地，未采纳 Peter 标注「未测试」的 `is_blocked` 全量重构路线，这一路线取舍仍需 Peter 复审确认。无 NAK。

## 合入评估
likelihood=medium。方向获认可、无 NAK，v13 的维护者意见几乎全部落实、且带 kselftest 实测数据；但系列规模大（16 枚、改动 ~2051 行、触及 core.c 与 ext 核心路径），v14 本身尚未被复审，`WF_TTUW_RQ` 与 NOHZ tick 保守策略需 Peter 最终认可。blocking_issues：v14 待复审；`WF_ON_RQ` 改名方案 vs Peter 原 `is_blocked` 重构思路的最终取舍未定。next_action：等 Peter/Tejun 对 v14 复审；若 `WF_TTUW_RQ` 被接受则可推进合入。

## 效果评估
cover 中 kselftest `enq_blocked` 给出实测（10 trials，16 contenders，nice -20 donor / +19 owner）：

- same-CPU：mutex_hold -4.48%，**mutex_wait -20.41%**
- cross-CPU：mutex_hold -12.69%，**mutex_wait -12.86%**

即启用 blocked-donor admission 后，锁等待时间显著下降，为 proxy-exec + sched_ext 组合的正确性/收益提供了可复现数据。

## 我可以参与的点
- kind=review：从 PELT/psi 记账角度复核 `WF_TTUW_RQ` 拆分后、以及 NOHZ_FULL 保守重开 tick 的副作用（承 v13 阶段 Prateek 提出的 `psi_enqueue()` 双记账隐患）。
- kind=testing：在真实 sched_ext 调度器（如 scx_lavd）上验证 blocked-donor admission 对锁密集负载的收益与稳定性，补 kselftest 之外的真实工作负载数据。

## 参考链接
- lore（v14 cover）: https://lore.kernel.org/all/20260922165445.943315-1-arighi@nvidia.com/
- v13 cover: https://lore.kernel.org/all/20260831134338.1531664-1-arighi@nvidia.com/
- John Stultz 早期工作引用 [1]: https://lore.kernel.org/all/20251206001451.1418225-1-jstultz@google.com
