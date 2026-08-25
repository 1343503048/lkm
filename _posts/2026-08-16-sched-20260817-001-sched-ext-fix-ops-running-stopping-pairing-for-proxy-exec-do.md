---
subject: 'sched_ext: Fix ops.running/stopping() pairing for proxy-exec donors'
id: sched-20260817-001
date: 2026-08-16
subsystem: sched
type: feature
status: under_review
severity: high
thread_root_msgid: <uid-42300@qq-imap>
lore_url: https://lore.kernel.org/all/20260817013458.xxxxxxx-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Tejun Heo
- Peter Zijlstra
- John Stultz
- K Prateek Nayak
current_version: v12
patch_series:
- version: v12
  msgid: <uid-42300@qq-imap>
  date: 2026-08-17
  summary: 17 patch 系列：让 proxy execution 与 sched_ext 共存，通过 SCX_OPS_ENQ_BLOCKED 逐调度器能力把
    blocked donor 交给 BPF 调度器。
  review_outcome: Tejun 已对多个子 patch（08/17/12/14 等）给出详细 review（命名/注释/IRQ 锁/条件化简等），尚未给整体
    ack；仍在迭代。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Tejun 要求澄清 SCX_TASK_ENQ_WAKEUP 的用途、部分注释重写、irq 锁语义；系列体量巨大（2024 行）需多轮打磨
  next_action: 等待 Andrea 回应 Tejun 的 review 点并出 v13；核心 sched/core 部分可能先拆分合入。
contribution_opportunities:
- kind: testing
  description: 在开启 CONFIG_SCHED_PROXY_EXEC + CONFIG_SCHED_CLASS_EXT 的内核上跑 enq_blocked
    selftest 与 scx_qmap -X，验证跨 CPU proxy 行为。
- kind: review
  description: 可评审 reject DSQ 远程迁移 race 处理与 SCX_TASK_ENQ_WAKEUP 的语义，提出更简洁方案。
generated_at: '2026-08-18T00:10:00'
source_email_count: 18
related_articles: []
tags:
- proxy_execution
- sched_ext
- sched/core
title: 'sched_ext: Add selftest for blocked donor admission'
layout: article
---

## TL;DR
Andrea Righi 的 v12（17 patch，2024 行）让 **proxy execution 与 sched_ext 共存**——此前二者在构建期互斥（`CONFIG_SCHED_PROXY_EXEC` 与 `CONFIG_SCHED_CLASS_EXT` 不能同时开）。通过新增 per-scheduler 能力 `SCX_OPS_ENQ_BLOCKED`，BPF 调度器可控制是否把 mutex-blocked donor 保持为 runnable 并经 `ops.enqueue()` 带 `SCX_ENQ_BLOCKED` 接收，从而精确控制 donor 的接纳与排序。含 scx_qmap `-X` 选项与 enq_blocked kselftest（实测 proxy 开启后 same-cpu 等待时间降 ~20%、cross-cpu 降 ~13%）。仍在 Tejun 详细 review 中。

## 背景与问题
Proxy execution 让等待者（donor）把调度上下文"捐献"给 mutex owner，使 owner 在 donor 仍 runnable 的情况下运行。当前 proxy-exec 与 sched_ext 构建期互斥。原因是 sched_ext 通过自有接口驱动 dispatch，proxy 切换可能运行一个 BPF 从未经其 DSQ 路径 dispatch 的任务，导致 `kfunc`/helper 看到的 current 与 BPF 侧"以为在跑"的任务不一致；DSQ/vtime/"谁在跑"记账会与核心实际执行脱节。对发行版"一个内核、运行时选特性"是障碍。

## 技术方案
- 把 proxy-exec 作为 sched_ext 的**可选 per-scheduler 能力**：BPF 设 `SCX_OPS_ENQ_BLOCKED` 即可让 blocked donor 保持 runnable，并经 `ops.enqueue()` 带 `SCX_ENQ_BLOCKED` 接收；核心据此沿 mutex-owner 链迁移 donor 调度上下文到 owner 的 rq 执行。未设该 flag 时 mutex waiter 正常阻塞、不参与 proxy。
- donor→owner 切换对调度器视为"函数调用"：donor 仍是 BPF 选中的调度上下文（消耗其 slice/运行时间），owner 仅为内部执行上下文。`rq->donor` 记账调度上下文，`rq->curr` 记录执行上下文。`scx_bpf_task_running()`/`scx_bpf_cpu_curr()`/`scx_bpf_cid_curr()` 仍报告 donor。
- `ops.running()`/`ops.stopping()` 仅在 proxy 解析成功后对 donor 开启会话，新增 `SCX_TASK_RUN_TRACKED` 跟踪（patch 09）。
- NOHZ CFS 带宽检查改跟 `rq->donor` 而非 `rq->curr`，用排队 FAIR 任务数决定 tick 能否停（patch 03）。
- 调度权变更（root/sub-scheduler、进/出 EXT）一律从干净状态开始：先完全 deactivate retained donor，再让新调度器下次阻塞时自定接纳策略（保守规则，RT/DL PI 跨兼容转换留作未来）。
- 远程 DSQ 转移在锁住源 rq 后重查 proxy 敏感状态；与 proxy 竞态的任务停在源 rq 的 reject DSQ，proxy 落定后归还 BPF 调度器（patch 11/12）。
- scx_qmap 加 `-X` 启用 blocked donor 排队（激进策略便于观察）；新增 enq_blocked kselftest（含可加载内核模块制造优先级反转，测 same/cross-CPU 拓扑）。
- diffstat：`kernel/sched/*` + `tools/sched_ext/*` + `tools/testing/selftests/sched_ext/enq_blocked.*`，27 文件 +2024/-215。

## 版本演进与当前进展
- 当前 v12（base: sched_ext/for-7.3），相对 v11：保留 re-enqueue 原因、立即处理迁移禁用后被拒的任务、用 donor 上下文做保护 slice/救援抢占/切片存取的接纳、刷新 NOHZ tick 依赖、把 `SCX_TASK_ENQ_WAKEUP` 移到 bit 16 等。
- 该系列已迭代到 v12（从 v1 于 2026-05 起），历经 Peter/Tejun/John Stultz/sashiko 等多轮反馈，逐步把核心 sched/core 改动与 sched_ext 改动拆分，便于分别合入。
- 当日（08-17）Tejun 对 patch 08/09/11/12/14 等发详细 review（见下）。

## Maintainer 意见与讨论焦点
Tejun Heo 当日多条 review（patch 14/12/11/08/09）：
- 质疑 `SCX_TASK_ENQ_WAKEUP` 是"绕弯检测 owner→donor 情形"，建议直接用 wake_flag 传入而非新增标志位。
- 要求重写若干注释（如 `TASK_ENQ_WAKEUP` 用途、`callback rq` 的措辞）。
- 指出 `sched_non_preferred...` 之外的 proxy 场景需更精确的条件说明（同 CPU donor 运行 owner 时是否也想阻止 scx 迁移）。
- 建议把 `unlikely(PF_EXITING)` 的测试顺序调整、IRQ 锁语义需确认。
- 整体尚未给 ack，但方向认可（proxy-exec 与 sched_ext 兼容是既定目标，patch 拆分利于逐步落地）。

## 合入评估
合入可能性**中等偏上**（方向已被 maintainer 接受，但 2024 行的大系列需多轮打磨，且核心 sched/core 部分可能先于 sched_ext 部分拆分合入）。阻塞点：Tejun 的命名/注释/IRQ 锁 review 需逐条回应；reject DSQ 竞态逻辑需进一步论证。

## 效果评估
enq_blocked selftest（16 contenders，owner nice +19 / donor -20）：
- same-cpu：proxy 开启后 mutex_wait 263.597ms → 209.808ms（**-20.41%**），hold -4.48%。
- cross-cpu：hold 246.794 → 215.486ms（-12.69%），wait 247.298 → 215.498ms（-12.86%）。
明确量化了优先级反转等待时间的下降，数据扎实。

## 我可以参与的点
- 测试：开启两 CONFIG 后跑 enq_blocked + scx_qmap -X 验证跨 CPU proxy。
- 评审：reject DSQ 远程迁移 race 处理与 `SCX_TASK_ENQ_WAKEUP` 语义简化。

## 参考链接
- lore v12 thread: https://lore.kernel.org/all/20260817013458.xxxxxxx-arighi@nvidia.com/
- git tree: git://git.kernel.org/pub/scm/linux/kernel/git/arighi/linux.git scx-proxy-exec
- tip-bot commit: 未获取到
- stable backport: 未获取到
