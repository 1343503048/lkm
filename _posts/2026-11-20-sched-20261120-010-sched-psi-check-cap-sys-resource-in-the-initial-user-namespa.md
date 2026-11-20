---
id: sched-20261120-010
date: '2026-11-20'
subject: 'sched/psi: Check CAP_SYS_RESOURCE in the initial user namespace'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261120085135.40368-1-dennylin0707@gmail.com>
lore_url: https://lore.kernel.org/all/20261120085135.40368-1-dennylin0707@gmail.com/
authors:
- Hungyu Lin
maintainers_involved:
- Mickaël Salaün
current_version: v2
patch_series:
- version: v1
  msgid: <20261106120004.90041-1-dennylin0707@gmail.com>
  date: '2026-11-06'
  summary: cap_raised 改 file_ns_capable，找回 userns 检查与 LSM mediation
  review_outcome: Mickaël/Sieun 给 Reviewed-by/Tested-by
- version: v2
  msgid: <20261120085135.40368-1-dennylin0707@gmail.com>
  date: '2026-11-20'
  summary: 无代码改动，仅收集 Reported-by/Tested-by/Reviewed-by tag
  review_outcome: 待维护者收取
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 维护者收取并进入 stable 回退
contribution_opportunities: []
generated_at: '2026-11-21T09:00:00+08:00'
source_email_count: 216
related_articles:
- sched-20261106-013
- sched-20261110-013
tags:
- psi
title: 'sched/psi: Check CAP_SYS_RESOURCE in the initial user namespace'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-013-sched-psi-check-cap-sys-resource-in-the-initial-user-namespa.html">sched-20261106-013</a>：Hungyu Lin 修复 PSI trigger 权限检查回归（`cap_raised()` 替换 `capable()` 丢失 userns 检查与 LSM hook）。
- <a class="article-ref" href="/lkm/2026/11/10/sched-20261110-013-sched-psi-check-cap-sys-resource-in-the-initial-user-namespa.html">sched-20261110-013</a>：获 LSM 维护者 Mickaël Salaün 与报告者 Sieun Yang 的 Reviewed-by/Tested-by。
- <a class="article-ref" href="/lkm/2026/11/20/sched-20261120-010-sched-psi-check-cap-sys-resource-in-the-initial-user-namespa.html">sched-20261120-010</a>（今天）：**v2 发出**——无代码改动，仅收集 Reported-by/Tested-by/Reviewed-by tag；`Fixes` + `Cc: stable` 齐全。

## 背景与问题

（承接）commit `d82caa273565` 把 `/proc/pressure/*` 的 CAP_SYS_RESOURCE 检查从 open() 挪到 `psi_trigger_create()` 时，用 `cap_raised(file->f_cred->cap_effective, ...)` 替换 `capable()`：既不做 initial user namespace 检查、也不走 LSM capable hook，导致「建了 user namespace 的非特权用户」拿到特权 trigger（非 2s 整数倍窗口、由 SCHED_FIFO psimon kthread 服务），LSM 的 CAP_SYS_RESOURCE 拒绝策略也被绕过。v7.4-rc1 + Landlock ABI 12 下可复现。

## 技术方案

判定从 `cap_raised(file->f_cred->cap_effective, CAP_SYS_RESOURCE)` 改为 `file_ns_capable(file, &init_user_ns, CAP_SYS_RESOURCE)`——通过 `security_capable()` 找回 initial user namespace 检查与 LSM mediation。1 行改动。v2 无代码变化，仅拼接 tag。

## 版本演进与当前进展

*current_version: v2（2026-11-20，`<20261120085135.40368-1-dennylin0707@gmail.com>`，单补丁）*。v1（2026-11-06）→ v2（仅收集 tag）。

## Maintainer 意见与讨论焦点

- **Mickaël Salaün（LSM/Landlock maintainer）**：Reviewed-by + Tested-by。
- **Sieun Yang（报告者）**：Reported-by + Tested-by。
- 无 NAK；回归修复、`Fixes: d82caa273565` + `Cc: stable` 齐全，等待 PSI/sched 维护者（Johannes/Peter）收取。

## 合入评估

*likelihood=high*。安全回归修复、1 行改动、LSM 维护者与报告者双 Tested-by，`Fixes`/`Cc: stable` 齐全。*blocking_issues*：无实质阻塞，仅待维护者收取并标 stable。*next_action*：维护者收取，进入 stable 回退。

## 效果评估

无性能数据；价值在权限正确性——修复后无真实 CAP_SYS_RESOURCE 的用户无法创建特权 trigger、LSM 拒绝策略重新生效（Mickaël 与 Sieun 均实测确认）。

## 我可以参与的点

- 当前阶段补丁已获双 Tested-by 且 tag 齐全，暂无明显参与空间，可持续观察维护者收取与 stable 回退。

## 参考链接

- lore thread（v2）: https://lore.kernel.org/all/20261120085135.40368-1-dennylin0707@gmail.com/
