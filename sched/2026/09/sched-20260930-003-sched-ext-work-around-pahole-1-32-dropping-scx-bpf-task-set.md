# sched_ext: Work around pahole 1.32 dropping scx_bpf_task_set_lazy_resched() from BTF

> **subject**：`sched_ext: Work around pahole 1.32 dropping scx_bpf_task_set_lazy_resched() from BTF`

## TL;DR

Tejun Heo 的 sched_ext 修复：clang + pahole 1.32 下 x86-64 vmlinux BTF 缺失 `scx_bpf_task_set_lazy_resched()`，导致 sched_ext 初始化失败（`Failed to register kfunc sets (-22)`）。原因是 clang 只在 prologue 把 `lazy` 参数挪进 callee-saved 寄存器后才描述它，pahole 1.32 因「不是参数寄存器」而拒绝。补丁用 `barrier_data()` 把参数钉在栈上，使位置描述不点名任何寄存器（`OPTIMIZER_HIDE_VAR()` 可修 x86-64 但会弄坏 arm64）。带 `Fixes: f8e5a4e3f3be`；Tejun 已 **Applied to sched_ext/for-7.4**，Andrea Righi 给 `Reviewed-by`（讨论后决定保留 `barrier_data()` 而非改 ABI 类型）。

## 背景与问题

`scx_bpf_task_set_lazy_resched()` 的 `bool lazy` 参数在 clang 下只在 prologue 把值挪进 callee-saved 寄存器之后才被描述，pahole 1.32 因该位置不是参数寄存器而拒绝生成 BTF 条目，导致 x86-64 vmlinux BTF 缺失该 kfunc，sched_ext 初始化报 `sched_ext: Failed to register kfunc sets (-22)`。已发布的 pahole 无论最终怎么修都会受影响，需在内核侧规避。

## 技术方案

用 `barrier_data()` 让参数保持在栈上，使其位置描述不点名任何寄存器，从而通过 pahole 1.32 的 BTF 生成。`OPTIMIZER_HIDE_VAR()` 能修 x86-64 但会破坏 arm64，故弃用。Andrea 分析指出问题由 `bool` 类型触发（`bool movl %esi,%ebp` 被 drop，`u32`/`u64` 同代码但 clang 保留 RSI 入口区间所以 pahole 满意），提议改类型为 `u32` 或用 `u64 flags` 替代 `barrier_data()`；Tejun 认为 `bool` 语义正确、`barrier_data()` 有效，倾向维持现状（除非未来变成带 `u64 flags` 的更宽接口）。

## 版本演进与当前进展

v1 单补丁（`<7c139810be5ffc9764ed4236efc28794@kernel.org>`）。当日 Tejun 已回「Applied to sched_ext/for-7.4」。

## Maintainer 意见与讨论焦点

- **Tejun Heo**（sched_ext 维护者/作者）：自投 `sched_ext/for-7.4` 并应用；在类型讨论中表示 `bool` 语义正确、希望 clang 能被修好、`barrier_data()` workaround 有效，除非有更大理由否则维持现状。
- **Andrea Righi**（sched_ext 维护者）：感谢定位（此前他为此把 pahole 锁在 1.31），确认问题由 `bool` 触发，提出「改 `lazy` 为 `u32`/`u64 flags`」的替代；随后表态「目前没有正当理由改 ABI，代码侧 workaround 优于 ABI workaround，保留 `barrier_data()`」，给 `Reviewed-by`。
- **bpf-ci bot**：自动提示 `Fixes: f8e5a4e3f3be` 是否为本分支历史内可达 commit（属 CI 例行校验，非人工意见）。

## 合入评估

*likelihood=merged*。已由 Tejun 应用到 `sched_ext/for-7.4`。*blocking_issues*：无。*next_action*：随 for-7.4 合入窗口收进主线。

## 效果评估

定性效果：修复 sched_ext 在 clang + pahole 1.32 下的 BTF 缺失与初始化失败（`-22`），无性能数据（属构建/BTF 正确性修复）。

## 我可以参与的点

- `testing`：用 clang + pahole 1.32 构建并加载任意 scx 调度器，确认 kfunc 集注册成功、`scx_bpf_task_set_lazy_resched()` 可被 BPF 调用，回帖验证结果。
- `review`：跟踪 pahole 上游对「callee-saved 寄存器中参数」的 BTF 处理修复进展，评估未来能否移除 `barrier_data()` workaround。

## 参考链接

- lore（补丁）: https://lore.kernel.org/all/7c139810be5ffc9764ed4236efc28794@kernel.org/
- Tejun「Applied」: https://lore.kernel.org/all/c0b95acfee4d3becce0718035c45e4dd@kernel.org/
- Andrea 的类型分析: https://lore.kernel.org/all/arwPVufx2ZUOc_sp@gpd4/

---
id: sched-20260930-003
date: '2026-09-30'
subject: 'sched_ext: Work around pahole 1.32 dropping scx_bpf_task_set_lazy_resched() from BTF'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: '<7c139810be5ffc9764ed4236efc28794@kernel.org>'
lore_url: 'https://lore.kernel.org/all/7c139810be5ffc9764ed4236efc28794@kernel.org/'
authors:
  - 'Tejun Heo'
maintainers_involved:
  - 'Tejun Heo'
  - 'Andrea Righi'
current_version: v1
patch_series:
  - version: v1
    msgid: '<7c139810be5ffc9764ed4236efc28794@kernel.org>'
    date: '2026-09-30'
    summary: '用 barrier_data() 把 lazy 参数钉在栈上，规避 pahole 1.32 丢失 BTF kfunc'
    review_outcome: 'Andrea Reviewed-by；Tejun Applied to sched_ext/for-7.4'
upstream_commit: null
fixes_commit: 'f8e5a4e3f3be'
merged_branch: 'sched_ext/for-7.4'
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: '随 sched_ext/for-7.4 合入窗口收进主线'
contribution_opportunities:
  - kind: testing
    description: '用 clang+pahole 1.32 构建并加载 scx 调度器验证 kfunc 注册成功'
  - kind: review
    description: '跟踪 pahole 上游修复进展，评估未来移除 barrier_data() workaround'
generated_at: '2026-10-01T01:00:00'
source_email_count: 6
related_articles: []
tags:
  - sched_ext
---