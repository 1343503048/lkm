# sched/psi: Check CAP_SYS_RESOURCE in the initial user namespace

## TL;DR

Hungyu Lin 修复 PSI trigger 的权限检查回归：commit `d82caa273565` 把 CAP_SYS_RESOURCE 检查从 `/proc/pressure/*` 的 open() 挪到 `psi_trigger_create()`，却用 `cap_raised()` 直接测 opener 的 effective 位，替换掉了原来的 `capable()`——而 `cap_raised()` 既不做 initial user namespace 检查、也不走 LSM 的 capable hook。结果是：创建了 user namespace 的非特权用户（在其命名空间内拥有完整 effective 位）就能拿到特权 trigger（非 2s 整数倍窗口、由 SCHED_FIFO psimon kthread 服务），LSM 拒绝 CAP_SYS_RESOURCE 的策略也被绕过。修复改用 `file_ns_capable()`，把 user namespace 与 LSM 检查找回来。1 行改动，`Cc: stable`。

## 背景与问题

`d82caa273565`（"sched/psi: Allow unprivileged polling of N*2s period"）的本意是让非特权用户能轮询 N*2s 周期的 PSI 平均值，同时把特权窗口（非 2s 倍数、SCHED_FIFO kthread 服务）留给有 CAP_SYS_RESOURCE 的人。但实现把 `capable(CAP_SYS_RESOURCE)` 换成了 `cap_raised(file->f_cred->cap_effective, CAP_SYS_RESOURCE)`：后者不检查 initial user namespace、也不经 `security_capable()` LSM 钩子。用户新建 user namespace 后在其中拥有完整 effective 位，于是无需真实 root 就能创建特权 trigger。

## 技术方案

把判定从 `cap_raised(file->f_cred->cap_effective, CAP_SYS_RESOURCE)` 改为 `file_ns_capable(file, &init_user_ns, CAP_SYS_RESOURCE)`——`file_ns_capable()` 会经 `security_capable()` 对照 given user namespace 检查 opener 的凭证，从而恢复 `capable()` 原有的 user namespace 与 LSM 语义。改动 `kernel/sched/psi.c` 仅 1 行。

## 版本演进与当前进展

*current_version: v1（2026-11-06 发出）*。当日无评审。

## Maintainer 意见与讨论焦点

当日无维护者回复。补丁是权限检查的回归修复，`Fixes`/`Cc: stable` 齐全，无 NAK。

## 合入评估

*likelihood=high*。1 行、语义明确（恢复被误删的检查）、`Fixes`/`Cc: stable` 齐全，属低争议安全修复。*blocking_issues*：无显著阻塞（仅待审阅收取）。*next_action*：等待 PSI 维护者（Suren Baghdasaryan 等）审阅并合入。

## 效果评估

无运行时性能数据。效果为安全语义恢复：非特权用户在其 user namespace 内不再能创建特权 trigger，LSM 对 CAP_SYS_RESOURCE 的拒绝重新生效。

## 我可以参与的点

当前阶段暂无明显参与空间：1 行安全修复、待收取，可持续观察是否补上回归测试（例如在 userns 内尝试创建非 2s 窗口 trigger 应失败）。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261106120004.90041-1-dennylin0707@gmail.com/

---
id: sched-20261106-013
date: 2026-11-06
subject: "sched/psi: Check CAP_SYS_RESOURCE in the initial user namespace"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261106120004.90041-1-dennylin0707@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261106120004.90041-1-dennylin0707@gmail.com/"
authors: [Hungyu Lin]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261106120004.90041-1-dennylin0707@gmail.com>"
    date: 2026-11-06
    summary: "cap_raised 改 file_ns_capable 恢复 PSI trigger 的 userns/LSM 检查。"
    review_outcome: "暂无评审。"
upstream_commit: null
fixes_commit: "d82caa273565"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待 PSI 维护者审阅并合入"
contribution_opportunities: []
generated_at: "2026-11-07T09:00:00+08:00"
source_email_count: 1
related_articles: []
tags: [psi]
---