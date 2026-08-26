# sched_ext: Allow ops.cgroup_set_weight/idle() to be sleepable

## TL;DR

Tao Cui 提议将 `ops.cgroup_set_weight()` 和 `ops.cgroup_set_idle()` 加入 sched_ext 的 sleepable 回调白名单，使 BPF 调度器可以在这些回调中执行可睡眠操作（如动态分配 DSQ）。Andrea Righi 认可方向但指出需先解决并发竞态（已发出独立的 serialize patch），建议在此修复之上再合入本 patch。

## 背景与问题

sched_ext 的 `bpf_scx_check_member()` 拒绝在未在白名单中的 ops 回调上运行 sleepable BPF 程序。当前 `cgroup_set_bandwidth()` 已在白名单中，但 `cgroup_set_weight()` 和 `cgroup_set_idle()` 不在。

实际影响：如果 BPF 调度器为每个 cgroup 维护独立的 idle DSQ，必须在 `ops.cgroup_init()` 中预创建所有 DSQ（即使 cgroup 永远不会设为 idle）。以 2000 个 cgroup 的 VM 为例，需预创建 2000+ 个 DSQ。允许 sleepable 后可延迟到首次 `cpu.idle=1` 写入时才创建。

## 技术方案

- 将 `cgroup_set_weight()` 和 `cgroup_set_idle()` 加入 `bpf_scx_check_member()` 的 sleepable 白名单
- 添加兼容性标记（BTF 可检测），镜像 `scx_compat_marker_cgroup_set_bandwidth_may_sleep()`
- 文档化这两个回调可能阻塞

## 版本演进与当前进展

v1。Andrea Righi review 后认可方向，但指出 Sashiko bot 报告的并发竞态需要先修复（Andrea 已发出独立的 serialize patch）。Andrea 还建议将 commit message 中的描述改为以 DSQ 而非 allocation 为中心。

## Maintainer 意见与讨论焦点

- **Andrea Righi**：认可方向，但要求先合入 serialize cgroup knob updates 修复竞态，再在此基础上合入本 patch。还建议 rewrap 过长的行，并用 DSQ 术语重写 commit message
- **Tao Cui** 回应：同意先等 serialize patch 合入

## 合入评估

- **likelihood: medium** — 方向认可，但依赖 serialize patch 先合入
- **blocking_issues**: 需要先合入 "sched_ext: Serialize cgroup knob updates"（Andrea 已发出）
- **next_action**: 等待 serialize patch 合入后，Tao 按 Andrea 建议修改 commit message 并发出 v2

## 效果评估

作者给出定性分析：2000 cgroup VM 中，从预创建 2000+ DSQ 减少到按需创建 4 个（仅实际标记 idle 的 cgroup）。无具体 benchmark 数字。

## 我可以参与的点

- 当前阶段需等待 serialize patch 合入，暂无直接参与空间
- 后续可在有大规模 cgroup 的环境测试 lazy DSQ 创建的性能收益

## 参考链接

- lore thread: https://lore.kernel.org/r/20260825023549.27826-1-cui.tao@linux.dev
- tip-bot commit: 未获取到

---
id: sched-20260825-004
date: 2026-08-25
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260825023549.27826-1-cui.tao@linux.dev>"
lore_url: "https://lore.kernel.org/r/20260825023549.27826-1-cui.tao@linux.dev"
authors: [Tao Cui]
maintainers_involved: [Andrea Righi]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260825023549.27826-1-cui.tao@linux.dev>"
    date: 2026-08-25
    summary: "将 cgroup_set_weight/idle 加入 sleepable 白名单，允许 BPF 调度器在回调中分配资源"
    review_outcome: "Andrea 认可方向，要求先合入 serialize 修复，并建议修改 commit message"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["需要先合入 Serialize cgroup knob updates 修复竞态"]
  next_action: "等待 serialize patch 合入，Tao 按 Andrea 建议修改 commit message 后发 v2"
contribution_opportunities: []
generated_at: "2026-08-27T10:00:00"
source_email_count: 3
related_articles: [sched-20260825-003]
tags: [sched_ext, cgroup]
---
