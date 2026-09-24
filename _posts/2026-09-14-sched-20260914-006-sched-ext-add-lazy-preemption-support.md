---
id: sched-20260914-006
date: '2026-09-14'
subject: 'sched_ext: Add lazy preemption support'
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: <20260914144620.2032614-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260914144620.2032614-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Tejun Heo
current_version: v3
patch_series:
- version: v1
  msgid: <20260911195800.974364-1-arighi@nvidia.com>
  date: 2026-09-12
  summary: SCX_ENQ_PREEMPT_LAZY/SCX_KICK_PREEMPT_LAZY/SCX_OPS_LAZY_SLICE_EXPIRY；拒绝立即+lazy
    与 lazy+KICK_WAIT；未知 kick flag 拒绝化；623 行 kick selftest
  review_outcome: Tejun 五条意见（per-task expiry、NO_HZ_FULL 角例、清掩码合并、kick_one_cpu 收敛优先级）
- version: v2
  msgid: <20260914084955.1798562-1-arighi@nvidia.com>
  date: 2026-09-14
  summary: lazy slice expiry 变 per-task 属性；新增 scx_bpf_task_set_slice_expiry()；NO_HZ_FULL
    恢复 tick；kick 优先级收敛进 kick_one_cpu()；扩展 selftest
  review_outcome: Cheng-Yang Chou 指出 selftest 在 PREEMPT_DYNAMIC=n 下需兼容分支
- version: v3
  msgid: <20260914144620.2032614-1-arighi@nvidia.com>
  date: 2026-09-14
  summary: 按 Sashiko 意见收尾：冗余 rq clock 更新、pin 锁、PR_SET_PDEATHSIG、nohz_tick 超时、nr_lazy_victim_running
    delta
  review_outcome: 尚未有维护者复核
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - Tejun 尚未对 v2/v3 复核
  - Cheng-Yang 的 PREEMPT_DYNAMIC=n selftest 兼容修复需落地
  next_action: 等 Tejun 对 v3 复核；落地 selftest 兼容修复后可望进入 for-7.4
contribution_opportunities:
- kind: review
  description: 核对 PREEMPT_DYNAMIC=n 分支与 lazy slice expiry 默认化对存量 SCX 调度器的影响
- kind: testing
  description: 启用 SCX_OPS_LAZY_SLICE_EXPIRY 实测 lazy 抢占对延迟/吞吐的量化影响
generated_at: '2026-09-15T09:30:00'
source_email_count: 9
related_articles:
- sched-20260912-005
tags:
- sched_ext
- preempt
title: 'sched_ext: Add lazy preemption support'
layout: article
---

## TL;DR
增量更新，v1 全貌见 sched-20260912-005。09-14 当日 Andrea Righi 连续发出 v2 与 v3：v2 按 Tejun Heo 对 v1 的五条意见重构（lazy slice expiry 变为 per-task 属性、新增 `scx_bpf_task_set_slice_expiry()`、NO_HZ_FULL 下 infinite-slice 任务恢复 tick、kick 优先级收敛进 kick_one_cpu()、清掩码合并）；v3 按 Sashiko 的收尾意见微调（冗余 rq clock 更新、pin 锁、PR_SET_PDEATHSIG、nohz_tick 超时、delta 计数）。selftest 全绿（kick 6/0/0、nohz_tick 1/0/0），Tejun 方向认可但尚未对 v2/v3 复核；Cheng-Yang Chou 发现 selftest 在 PREEMPT_DYNAMIC=n 下的兼容问题并给修复建议。

## 背景与问题
fair 调度类支持 lazy rescheduling：lazy 请求不立即抢占，推迟到返回用户态或被下个 tick 升级，避免不必要内核态抢占。sched_ext 此前只向 BPF 调度器暴露立即抢占，无法做同样取舍（承 sched-20260912-005）。

## 技术方案
v2/v3 最终方案（v3 cover 描述）：

- 新增 lazy 版 enqueue 与 kick 抢占 flag：过期当前 SCX 任务 slice，调度边界推迟到返回用户态或下个 tick；
- `SCX_OPS_LAZY_SLICE_EXPIRY` 选默认 lazy slice 过期；调度器可对单任务用 `scx_bpf_task_set_slice_expiry()` 双向覆盖默认（保留 sub-scheduler 任务归属边界）；bypass 仍强制立即重调度；
- NO_HZ_FULL 角例：lazy enqueue/kick 针对 infinite-slice 任务恢复 tick（清 SCX_RQ_CAN_STOP_TICK + 更新 TICK_DEP_BIT_SCHED 依赖），保证 tick 已停止的目标仍有前进；
- selftest 覆盖立即/lazy、kick 模式合并与优先级、enqueue 抢占、per-task slice-expiry 覆盖、非法 flag、NO_HZ_FULL infinite-slice lazy 抢占。

测试（v3 cover，virtme-ng）：

```
$ vng -a "preempt=lazy" -- tools/testing/selftests/sched_ext/runner -t kick
  kick: PASSED 6, SKIPPED 0, FAILED 0
$ vng -a "preempt=lazy nohz_full=8-15" -- .../runner -t nohz_tick
  nohz_tick: CPU 8 received 7 finite-slice ticks; PASSED 1, SKIPPED 0, FAILED 0
```

## 版本演进与当前进展
- v1（09-11/09-12，sched-20260912-005）：双补丁首发，当日零回帖。
- Tejun 09-14 评审 v1（五条）：(1) kick 路径可简化；(2) lazy slice expiry 做成 per-task flag、ops flag 只做默认值；(3) NO_HZ_FULL 角例——远程 infinite-slice + tick 停止时 resched_curr_lazy() 不发 IPI、清 slice 也不重启 tick，kick/enqueue 都要给 tick-stopped 目标安排前进；(4) 为何不在原清 cpus_to_preempt 处同时清两个掩码（含 skipped-kick 路径）；(5) 是否真要拒绝全部组合——PREEMPT 应赢过 PREEMPT_LAZY、WAIT 可强制立即、plain kick + lazy 仍清 slice 并立即重调度，建议在 kick_one_cpu() 收敛优先级。
- Andrea 09-14 逐条回应：同意 per-task slice-expiry（p->scx.slice_expires_lazy，enable() 前从 SCX_OPS_LAZY_SLICE_EXPIRY 初始化、任意回调可覆盖）；同意加公共 helper（清 SCX_RQ_CAN_STOP_TICK + 更新 tick 依赖 + resched_curr_lazy）；同意清掩码合并；同意优先级 PREEMPT|WAIT > plain kick > PREEMPT_LAZY，lazy+immediate 组合仍清 slice、enqueue 与 kick 接口一致。
- v2（09-14）：按上述五条落地，并扩展 selftest（组合/有序 kick、per-task 覆盖、NO_HZ_FULL）。
- v3（09-14，当日第二版）：按 Sashiko 意见——避免恢复 tick 依赖时的冗余 rq clock 更新、lazy kick 投递用 pinned rq 锁 helper、无限自旋测试 worker 设 PR_SET_PDEATHSIG、用 nr_lazy_victim_running 的 delta 而非绝对值、增大 nohz_tick watchdog 与 phase 超时。
- Cheng-Yang Chou 09-14（review v2 selftest）：在 for-next + PREEMPT_LAZY=y + PREEMPT_DYNAMIC=n 构建，kick 测试 PASSED 6；指出 sched_init_debug() 只在 CONFIG_PREEMPT_DYNAMIC 下建 debugfs 文件，而 PREEMPT_LAZY 可脱离 PREEMPT_DYNAMIC 构建（select PREEMPT_BUILD if !PREEMPT_DYNAMIC），两个测试在不比较 TIF 时已通过，建议加 `#if defined(CONFIG_PREEMPT_LAZY) && !defined(CONFIG_PREEMPT_DYNAMIC)` 分支 return 1。

## Maintainer 意见与讨论焦点
- **Tejun Heo（sched_ext 维护者）**：对 v1 "This mostly looks fine to me"，但要求 kick 路径简化、per-task slice-expiry、NO_HZ_FULL 角例必须处理——v2/v3 已逐条落地，尚未对 v2/v3 复核。
- **Cheng-Yang Chou（社区 reviewer）**：selftest 的 PREEMPT_DYNAMIC=n 兼容修复建议。
- **Sashiko**：v2→v3 的收尾意见（rq clock、pin 锁、测试进程回收、超时、delta 计数）。
- 分歧/未闭合处：Tejun 对 v2/v3 未表态；`SCX_OPS_LAZY_SLICE_EXPIRY` 默认 lazy 的行为对存量 BPF 调度器（scx_simple 等）的兼容性未见讨论。

## 合入评估
*likelihood=high*：维护者方向认可、意见被逐条落实、selftest 齐备且全绿。*blocking_issues*：Tejun 尚未对 v2/v3 复核；Cheng-Yang 的 PREEMPT_DYNAMIC=n selftest 兼容修复需落地。*next_action*：等 Tejun 对 v3 复核；落地 Cheng-Yang 的 selftest 修复后可望进入 for-7.4。

## 效果评估
无性能数字——系列是能力对齐（与 fair 同等 lazy 选择权）而非性能优化。正确性由 selftest 覆盖：kick 6/0/0、nohz_tick 1/0/0（CPU 8 收到 7 个 finite-slice ticks，间接验证 NO_HZ_FULL forward-progress）。系列仍缺 lazy 抢占对调度延迟/吞吐的量化对比。

## 我可以参与的点
- kind=review：核对 Cheng-Yang 的 PREEMPT_DYNAMIC=n 分支是否应进入正式补丁，以及 lazy slice expiry 默认化对存量 SCX 调度器的行为影响。
- kind=testing：在自定义 BPF 调度器启用 SCX_OPS_LAZY_SLICE_EXPIRY，实测 lazy 抢占对调度延迟/吞吐的量化影响，补系列缺失的性能数据。

## 参考链接
- v3 cover：https://lore.kernel.org/all/20260914144620.2032614-1-arighi@nvidia.com/
- v2 cover：https://lore.kernel.org/all/20260914084955.1798562-1-arighi@nvidia.com/
- Tejun 评审：https://lore.kernel.org/all/050b21a95813f39e131ff1509ad76120@kernel.org/
- Andrea 回应 Tejun：https://lore.kernel.org/all/aqeOsEWZpsCLqlKT@gpd4/
- Cheng-Yang Chou 评审：https://lore.kernel.org/all/20260914225115.Gb03c@cchengyang.duckdns.org/
