---
id: sched-20260918-012
date: '2026-09-18'
subject: 'sched_ext: Add lazy preemption support'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260917070751.3617935-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260917070751.3617935-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Tejun Heo
current_version: v6
patch_series:
- version: v6
  msgid: <20260917070751.3617935-1-arighi@nvidia.com>
  date: '2026-09-17'
  summary: 惰性抢占核心支持 + selftests（含 nohz_full）
  review_outcome: Tejun 完整 review；作者全盘接受、将出 v7；Tao Cui Tested-by
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - v7 未发出（落实命名/枚举/测试整改）
  next_action: 作者发 v7 落实 Tejun 全部意见
contribution_opportunities:
- kind: review
  description: 审查 v7 selftests 对静态内核路径的 skip 逻辑
- kind: testing
  description: 在真实多核/NUMA 平台验证长尾延迟与切换率影响
generated_at: '2026-09-19T09:00:00'
source_email_count: 6
related_articles:
- sched-20260917-010
- sched-20260916-007
tags:
- sched_ext
- preempt
title: 'sched_ext: Add lazy preemption support'
layout: article
---

## TL;DR
增量更新：Andrea Righi 的 sched_ext 惰性抢占系列（2 补丁：核心支持 + selftests）本日获 Tejun Heo 完整 review——"整体不错"，提出可折叠进 `for_each_cpu_or()`、改名为 `scx_bpf_task_set_lazy_resched()`/`SCX_OPS_LAZY_RESCHED`、补 bit 枚举等若干点，selftests 亦有详细整改项；作者已全盘接受并表示将出新版。Tao Cui 补上 Tested-by 与实测（惰性抢占在常见场景无唤醒延迟回退、上下文切换率大幅下降）。

## 背景与问题
背景见 sched-20260917-010：sched_ext 需要"惰性抢占"（lazy preemption）能力——让 BPF 调度器把抢占推迟到时间片耗尽等惰性点，避免频繁上下文切换。本系列为 v6。

## 技术方案
- 1/2：新增惰性抢占支持，通过 `SCX_OPS_LAZY_SLICE_EXPIRY` 等 flag + 惰性 resched 标记实现；Tejun 建议改用 `scx_bpf_task_set_lazy_resched()` 命名、把 lazy-only 目标的 `cpus_to_kick_if_idle` 折叠进 `for_each_cpu_or()` 循环。
- 2/2：selftests 覆盖惰性/立即抢占两种模式（含 nohz_full）。

## 版本演进与当前进展
- v6（09-17，`<20260917070751.3617935-1-arighi@nvidia.com>`）：当前版本；本日 Tejun 完整 review，作者接受全部意见、将出 v7。

## Maintainer 意见与讨论焦点
- **Tejun Heo**：1/2 "looks good overall"，具体意见——lazy-only 目标可否折叠进 `for_each_cpu_or()`（避免 idle loop 二次加锁）；命名改成 `scx_bpf_task_set_lazy_resched()` + `SCX_OPS_LAZY_RESCHED`；加 bit 枚举校验；`scx_error()` 的 early return 是否需移出 IDLE 分支；空行/版本注释细节。2/2（selftests）——BPF/用户态共享枚举建议抽到公共头；`CONFIG_` 宏未用；`spawn_gated_worker()` 与 nohz_tick.c 重复；静态内核（PREEMPT_LAZY 默认、无 PREEMPT_DYNAMIC）下测试会"假通过"应跳过；victim 无限时间片 + SIGKILL 前 slice 耗尽会卡死 watchdog；`uei.kind` 未检查导致 abort 误报为无进展；tick 依赖未恢复也通过的测试漏洞。
- **Tao Cui**：v6 在 4-CPU KVM + scx_simple 探针下实测，惰性/立即抢占与 CFS 持平（无唤醒延迟回退）；`SCX_OPS_LAZY_SLICE_EXPIRY` 把 6 个 busy hog 的上下文切换率从 ~1000/s（CFS）降到 ~215/s；Tested-by。
- **Andrea Righi（作者）**：全部接受，将出 v7（含改名 SCX_OPS_LAZY_RESCHED）。
- 无分歧；属"按 review 修订"的正常收敛。

## 合入评估
likelihood=high。方向获维护者认可（"looks good overall"），作者已承诺修订所有意见；有独立 Tested-by 与量化数据。blocking_issues：v7 未发出（落实 Tejun 的命名/枚举/测试整改项）。next_action：作者发 v7 落实 Tejun 全部意见，预期即可合入。

## 效果评估
Tao Cui 实测（v6，4-CPU KVM，scx_simple + SCX_OPS_LAZY_SLICE_EXPIRY，2000 次迭代）：1ms 周期 timer 任务唤醒延迟 avg/p50/p99 在惰性(59/59/64 us)与立即(59/58/64)抢占下均与 CFS(60/59/66)持平，无常见场景回退；上下文切换率从 ~1000/s 降至 ~215/s。

## 我可以参与的点
- kind=review：审查 v7 的 selftests 对静态内核（无 PREEMPT_DYNAMIC、arm64/riscv 等）路径的 skip 逻辑是否严谨。
- kind=testing：在真实多 NUMA/多核平台上验证惰性抢占对长尾延迟与上下文切换率的实际影响。

## 参考链接
- lore（v6 cover）: https://lore.kernel.org/all/20260917070751.3617935-1-arighi@nvidia.com/
