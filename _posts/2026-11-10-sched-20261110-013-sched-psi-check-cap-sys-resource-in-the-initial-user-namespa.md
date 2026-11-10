---
id: sched-20261110-013
date: '2026-11-10'
subject: 'sched/psi: Check CAP_SYS_RESOURCE in the initial user namespace'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20261109.iej8biD4ohph@digikod.net>
lore_url: https://lore.kernel.org/all/20261109.iej8biD4ohph@digikod.net/
authors:
- Hungyu Lin
maintainers_involved:
- Mickaël Salaün
current_version: v1
patch_series:
- version: v1
  msgid: <20261106120004.90041-1-dennylin0707@gmail.com>
  date: '2026-11-06'
  summary: cap_raised 改 file_ns_capable，恢复 userns 检查与 LSM mediation
  review_outcome: Mickaël Salaün Reviewed-by + Tested-by；Sieun Yang Reported-by +
    Tested-by
upstream_commit: null
fixes_commit: d82caa273565
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: PSI/sched 维护者收取并标记 stable 回退
contribution_opportunities: []
generated_at: '2026-11-11T09:00:00+08:00'
source_email_count: 2
related_articles:
- sched-20261106-013
tags:
- psi
- cgroup
title: 'sched/psi: Check CAP_SYS_RESOURCE in the initial user namespace'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-013-sched-psi-check-cap-sys-resource-in-the-initial-user-namespa.html">sched-20261106-013</a>：Hungyu Lin 修复 PSI trigger 权限检查回归：commit `d82caa273565` 把 CAP_SYS_RESOURCE 检查从 `/proc/pressure/*` open() 挪到 `psi_trigger_create()`，却用 `cap_raised()` 直接测 opener 的 effective 位替换掉原来的 `capable()`——既不做 initial user namespace 检查、也不走 LSM capable hook，导致「建了 user namespace 的非特权用户」能拿到特权 trigger（非 2s 整数倍窗口、SCHED_FIFO kthread 服务），LSM 的 CAP_SYS_RESOURCE 拒绝策略也被绕过。修复改用 `file_ns_capable()`，1 行改动，`Cc: stable`。
- <a class="article-ref" href="/lkm/2026/11/10/sched-20261110-013-sched-psi-check-cap-sys-resource-in-the-initial-user-namespa.html">sched-20261110-013</a>（今天）：**获得 LSM 维护者与报告者背书**——Mickaël Salaün（Landlock/LSM）给 Reviewed-by + Tested-by，确认 `file_ns_capable()` 同时恢复 initial user namespace 检查与 LSM mediation；Sieun Yang（此前私下向维护者报告的 Landlock 用例）给 Reported-by + Tested-by，在 v7.4-rc1 + Landlock ABI 12 上实测确认修复后 Landlock 限制 CAP_SYS_RESOURCE 时特权 trigger 创建被正确拒绝。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-013-sched-psi-check-cap-sys-resource-in-the-initial-user-namespa.html">sched-20261106-013</a>）`d82caa273565` 的本意是让非特权用户能轮询 N*2s 周期 PSI 平均值，把特权窗口留给有 CAP_SYS_RESOURCE 的人，但实现用 `cap_raised()` 替换 `capable()` 后，initial user namespace 检查与 LSM 钩子双双丢失。Sieun Yang 曾于 2026-11-04 私下向维护者报告了 PSI/Landlock 的 CAP_SYS_RESOURCE 失配问题并附复现，今日在公开线程确认补丁修复了它。

## 技术方案

（承接）判定从 `cap_raised(file->f_cred->cap_effective, CAP_SYS_RESOURCE)` 改为 `file_ns_capable(file, &init_user_ns, CAP_SYS_RESOURCE)`。今日 Mickaël Salaün 确认该改法「用 `file_ns_capable()` + `&init_user_ns` 同时找回 initial user namespace 检查与 LSM mediation」，并明确与 Landlock 的 capabilities 控制直接可见。

## 版本演进与当前进展

*current_version: v1（2026-11-06 发出）*。今日无新版本：补丁获得 LSM 维护者 Reviewed-by + Tested-by 与报告者 Tested-by，进入可收取状态。

## Maintainer 意见与讨论焦点

- **Mickaël Salaün（LSM/Landlock maintainer）**：Reviewed-by + Tested-by，明确「`file_ns_capable()` + `&init_user_ns` 找回 userns 检查与 LSM mediation」。
- **Sieun Yang（报告者）**：Reported-by + Tested-by，v7.4-rc1 + Landlock ABI 12 实测确认修复。
- 无 NAK、无分歧。`Fixes`/`Cc: stable` 齐全，属明确回归修复，等待 PSI/sched 维护者收取。

## 合入评估

*likelihood=high*。回归修复、1 行改动、LSM 维护者与报告者双 Tested-by，`Fixes` 与 `Cc: stable` 齐全。*blocking_issues*：无实质阻塞，仅待 PSI/sched 维护者（Johannes/Peter）收取并标记 stable。*next_action*：维护者收取，并进入 stable 回退。

## 效果评估

无性能数据。价值在权限正确性：修复后可确认「无真实 CAP_SYS_RESOURCE 的用户无法创建特权 trigger、LSM 拒绝策略重新生效」（Mickaël 与 Sieun 均实测确认）。

## 我可以参与的点

- 当前阶段已近收取，暂无明显参与空间，可持续观察是否进入 stable 回退。

## 参考链接

- Mickaël Salaün 的 Reviewed-by: https://lore.kernel.org/all/20261109.iej8biD4ohph@digikod.net/
- Sieun Yang 的 Tested-by: https://lore.kernel.org/all/e360517ba7fa8262912a5c01b224ad9@cweb016.nm/
