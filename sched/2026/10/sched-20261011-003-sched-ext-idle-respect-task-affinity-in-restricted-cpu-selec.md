# sched_ext: idle: Respect task affinity in restricted CPU selection

## TL;DR

Hui Su 修复 sched_ext restructed `select_cpu` kfunc 路径在单 CPU / migration-disabled 任务上可能返回「不在任务亲和性 (`p->cpus_ptr`) 内」的空闲 CPU 的问题（v1 只校验 caller 提供的 `@allowed` 掩码）。经 Andrea Righi review 后，v2 改为从任务状态推导候选 CPU（单 CPU 任务用 `cpumask_first(p->cpus_ptr)`、migration-disabled 任务用 `task_cpu(p)`），并在 `scx_idle_test_and_clear_cpu()` 之前做亲和性校验。带 `Fixes:` 与 `Cc: stable`。Andrea 在 v2 上又指出该改法会破坏 `SCX_PICK_IDLE_IN_NODE`，建议把校验因式分解为 helper 并补 node 校验——尚需 v3。

## 背景与问题

restricted `select_cpu` kfunc 路径（`select_cpu_from_kfunc()`）处理单 CPU 与 migration-disabled 任务时不走 `scx_select_cpu_dfl()`，而是直接以 `prev_cpu` 为候选。`prev_cpu` 只是提示（hint），亲和性变更后可能已不可用；当 caller 传入 `@allowed` 时，该路径只把 `prev_cpu` 与该掩码比对，因此可能 claim 并返回一个不在 `p->cpus_ptr` 内的空闲 CPU。这属于 sched_ext BPF kfunc 的正确性缺陷，`Fixes: 683d2d0faba1`（"sched_ext: idle: Introduce scx_bpf_select_cpu_and()"）。

## 技术方案

v1：`prev_cpu` 需同时属于 `p->cpus_ptr` 与 caller 掩码才消费其 idle 状态（`+2/−1`）。Andrea 指出 `prev_cpu` 只是 hint，建议直接改从任务状态推导候选。v2 采纳：候选从任务状态推导——单 CPU 任务用 `p->cpus_ptr` 中唯一 CPU，migration-disabled 任务用 `task_cpu(p)`，并在 claim idle 之前对「任务有效亲和性 + caller 掩码」做校验（`+14/−6`）。关键点：校验必须在 `scx_idle_test_and_clear_cpu()` 之前，因为该调用成功后即消费 CPU 的 idle bit，之后的 placement 校验无法撤销这一副作用；单 CPU / migration-disabled 任务跳过 `ops.select_cpu()`，故此路径可从 `ops.enqueue()` 等其它上下文抵达，普通 `ops.select_cpu()` 路径经 `scx_select_cpu_dfl()` 不受影响。

## 版本演进与当前进展

- v1（10-11）：只补 `prev_cpu` 对 `p->cpus_ptr` 的校验（回应 Andrea「prev_cpu 不可信」）。base-commit `7b63ef2d55f2`。
- Andrea v1 review：建议改从任务状态推导候选（`cpumask_first(p->cpus_ptr)` / `task_cpu(p)`），并要求在补丁描述里说明「claim 会消费 idle bit」「per-CPU / migration-disabled 任务跳过 `ops.select_cpu()`、影响 `ops.enqueue()` 上下文」。
- v2（10-11）：按要求改为从任务状态推导候选并前置亲和性校验、补文档说明。
- Andrea v2 review：意识到该改法会破坏 `SCX_PICK_IDLE_IN_NODE`（candidate 需与 `prev_cpu` 同 node），建议把校验因式分解为 `select_cpu_restricted()` helper 并加入 `scx_cpu_node_if_enabled()` 的 node 校验。

## Maintainer 意见与讨论焦点

- **Andrea Righi**（sched_ext 维护者）：「The fix makes sense」整体认可方向；v1 建议从任务状态推导候选；v2 坦言「Sorry, I suggested this, but I just realized that we break SCX_PICK_IDLE_IN_NODE if we do this」，并给出把校验折进 helper 的完整示例（含 `SCX_PICK_IDLE_IN_NODE` 的 node 分支）。未解决点：当前 v2 在 `SCX_PICK_IDLE_IN_NODE` 标志下候选 node 校验缺失。

## 合入评估

*likelihood=medium*。维护者全程积极评审、方向清晰且是明确 bug（带 `Fixes:` + `Cc: stable`）；但 Andrea 刚指出 v2 破坏 `SCX_PICK_IDLE_IN_NODE`，需 v3 做 helper 因式分解并补 node 校验。*blocking_issues*：v3 需将校验折进 `select_cpu_restricted()` helper 并补 `SCX_PICK_IDLE_IN_NODE` 的 node 校验。*next_action*：作者按 Andrea 示例发 v3。

## 效果评估

作者自测：x86_64 KVM/QEMU 私有 BPF 测试 harness——baseline 返回亲和性外的 CPU1、v2 返回 `-EBUSY`；stale `prev_cpu` 场景 baseline 返回 `-EBUSY`、v2 选中任务空闲的 CPU0；caller 掩码排除候选 CPU 时 v2 返回 `-EBUSY`。stock sched_ext `allowed_cpus` selftest 通过；另构建了 `CONFIG_PREEMPT_RCU=y` 的 vmlinux/bzImage 及 `CONFIG_PREEMPT_RCU=n`、`CONFIG_SMP=n` 的 `kernel/sched/build_policy.o`。

## 我可以参与的点

- `review`：核对 Andrea 提议的 helper 因式分解在 `SCX_PICK_IDLE_IN_NODE` 语义下是否与 `scx_select_cpu_dfl()` 的 node 处理一致。
- `testing`：在启用 `SCX_PICK_IDLE_IN_NODE` 的 BPF 调度器上复测单 CPU / migration-disabled 任务的受选 CPU 是否符合亲和性与 node 约束。

## 参考链接

- lore（v2）: https://lore.kernel.org/all/20261011131700.1351541-1-sh_def@163.com/
- lore（v1）: https://lore.kernel.org/all/20261011025256.4180374-1-sh_def@163.com/
- lore（Andrea v2 review）: https://lore.kernel.org/all/asufkdwCQvilJEqr@gpd4/

---
id: sched-20261011-003
date: '2026-10-11'
subject: 'sched_ext: idle: Respect task affinity in restricted CPU selection'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20261011025256.4180374-1-sh_def@163.com>'
lore_url: 'https://lore.kernel.org/all/20261011025256.4180374-1-sh_def@163.com/'
authors:
  - 'Hui Su'
maintainers_involved:
  - 'Andrea Righi'
current_version: v2
patch_series:
  - version: v1
    msgid: '<20261011025256.4180374-1-sh_def@163.com>'
    date: '2026-10-11'
    summary: 'prev_cpu 需同时属于 p->cpus_ptr 与 caller 掩码才消费 idle 状态'
    review_outcome: 'Andrea 建议从任务状态推导候选而非依赖 prev_cpu'
  - version: v2
    msgid: '<20261011131700.1351541-1-sh_def@163.com>'
    date: '2026-10-11'
    summary: '候选从任务状态推导（单 CPU 用 cpus_ptr、migration-disabled 用 task_cpu），claim idle 前做亲和性校验'
    review_outcome: 'Andrea 指出破坏 SCX_PICK_IDLE_IN_NODE，建议折成 helper 并补 node 校验'
upstream_commit: null
fixes_commit: '683d2d0faba1'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'v3 需把校验折进 select_cpu_restricted() helper 并补 SCX_PICK_IDLE_IN_NODE 的 node 校验'
  next_action: '作者按 Andrea 的 helper 示例发 v3'
contribution_opportunities:
  - kind: review
    description: '核对 helper 因式分解在 SCX_PICK_IDLE_IN_NODE 语义下与 scx_select_cpu_dfl() 一致'
  - kind: testing
    description: '在启用 SCX_PICK_IDLE_IN_NODE 的 BPF 调度器上复测单 CPU/migration-disabled 任务'
generated_at: '2026-10-12T01:00:00'
source_email_count: 5
related_articles: []
tags:
  - sched_ext
  - idle
  - affinity
---