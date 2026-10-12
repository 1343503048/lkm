# sched_ext: Honor SCX_PICK_IDLE_CORE in CPU selection shortcuts

## TL;DR

Hui Su 修 sched_ext 在 SMT 系统上一个 strict-core 选择被绕过的 bug：`SCX_PICK_IDLE_CORE`（要求选核的 SMT 兄弟都 idle）在 restricted `select_cpu` kfunc 路径和两条 `WAKE_SYNC` 捷径上都没被校验，会把任务摆到只有单线程 idle 的核上；补丁跳过这些捷径并在 restricted 路径校验 idle SMT mask，配套自测覆盖三处。当日新发、基于作者自己已获 Andrea R-b 的 respect-affinity v3 之上。

## 背景与问题

`SCX_PICK_IDLE_CORE` 要求选出的 CPU 的 SMT 兄弟全部 idle（strict-core）。但 restricted `select_cpu` kfunc 路径现在从任务状态推导候选 CPU 后，未检查该条件就 `scx_idle_test_and_clear_cpu()` 抢占 idle 位；`scx_select_cpu_dfl()` 里的两条 `WAKE_SYNC` 捷径在 SMT 系统上也会绕过 strict-core。这使 BPF 调度器显式要求 strict-core 时仍被摆到「半个核被占用」的核上。

## 技术方案

两个小改动（`kernel/sched/ext/idle.c` +5/-1）：

- `scx_select_cpu_dfl()` 的 WAKE_SYNC 捷径加条件 `!(sched_smt_active() && (flags & SCX_PICK_IDLE_CORE))`，要求 strict-core 时跳过把 wakee 迁到 waker CPU 的捷径。
- `select_cpu_restricted()` 在清 idle 位前加校验：`(flags & SCX_PICK_IDLE_CORE) && sched_smt_active() && !cpumask_test_cpu(cpu, ...smt)` 则返回 `-EBUSY`。

未设 flag 或非 SMT 系统保持「individual-idle」原行为。自测（0/2 的 patch 2）扩展 `allowed_cpus` 用例覆盖 restricted 路径 + 两条 WAKE_SYNC 捷径，无 SMT 对时保留通用 smoke test。

## 版本演进与当前进展

v1 当日新发（0/2 系列，含 cover + 修复 + selftest），基于 `[PATCH v3] sched_ext: idle: Respect task affinity...`（同作者）之上。作者自述 x86_64 KVM/QEMU 下三处用例修复前复现 strict-core 违规、修复后返回 -EBUSY；strict-core 用例连续 50 次通过。暂无回帖。

## Maintainer 意见与讨论焦点

当日暂无 review。`Fixes: 683d2d0faba1` 且 `Cc: stable@vger.kernel.org`，属于 sched_ext idle 选择路径的正确性修复。

## 合入评估

*likelihood=medium*。修复方向清晰、有自测，但依赖前置 respect-affinity v3 先合入，且 strict-core 校验逻辑尚需 Andrea Righi 等确认。*blocking_issues*：前置补丁依赖、暂无 review。*next_action*：等 review，前置补丁落地后随即可取。

## 效果评估

作者自测数据：三处 differential 用例修复前复现 strict-core 违规、修复后 -EBUSY；strict-core 用例 50 连跑通过；非 SMT 覆盖保留 smoke test。无性能数字（属正确性修复）。

## 我可以参与的点

- `testing`：在真实 SMT 机器上跑 `allowed_cpus` selftest 的 strict-core/WAKE_SYNC 用例并回帖结果。
- `review`：核对 restricted 路径与两条 WAKE_SYNC 捷径对 `sched_smt_active()` 门槛判断是否覆盖完整（如 NUMA 同节点 + core 的组合）。

## 参考链接

- lore（cover 0/2）: https://lore.kernel.org/all/20261012065114.3516902-1-sh_def@163.com/
- lore（修复 1/2）: https://lore.kernel.org/all/20261012065114.3516902-2-sh_def@163.com/
- lore（selftest 2/2）: https://lore.kernel.org/all/20261012065114.3516902-3-sh_def@163.com/

---
id: sched-20261012-002
date: '2026-10-12'
subject: 'sched_ext: Honor SCX_PICK_IDLE_CORE in CPU selection shortcuts'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261012065114.3516902-1-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20261012065114.3516902-1-sh_def@163.com/
authors:
- Hui Su
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261012065114.3516902-2-sh_def@163.com>
  date: '2026-10-12'
  summary: restricted select_cpu 路径与 WAKE_SYNC 捷径在 SMT 系统上绕过 SCX_PICK_IDLE_CORE
  review_outcome: 当日新发，暂无 review
fixes_commit: 683d2d0faba1
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 基于同作者的 respect-affinity v3 之上，需先收那枚前置修复
  - 尚无 review
  next_action: 等 Andrea Righi 等对 strict-core 校验逻辑的 review
contribution_opportunities:
- kind: testing
  description: 在真实 SMT 机器上跑 allowed_cpus selftest 的 strict-core 用例，回帖结果
- kind: review
  description: 核对 WAKE_SYNC 两条捷径 + restricted 路径三处对 sched_smt_active() 的判断是否完整
generated_at: '2026-10-13T01:40:00'
source_email_count: 3
related_articles: []
tags:
- sched_ext
- hyperthreading
---
