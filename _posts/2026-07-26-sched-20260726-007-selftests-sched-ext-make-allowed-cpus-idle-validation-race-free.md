---
id: sched-20260726-007
date: 2026-07-26
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <uid-744@qq-imap>
lore_url: unknown
authors:
- Andrea Righi
- Kuba Piecuch
maintainers_involved:
- Andrea Righi
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <uid-734@qq-imap>
  date: 2026-07-22
  summary: 前置补丁（Kuba Piecuch）：WAKE_SYNC 情况下选中 waker CPU 时显式把其标记为 busy，修复 allowed_cpus
    selftest 偶发 'CPU 0 should be marked as busy' 失败。
  review_outcome: Andrea Righi 认可修复，同时指出该 selftest 本身存在竞态、应重做验证逻辑。
- version: v1
  msgid: <uid-744@qq-imap>
  date: 2026-07-26
  summary: 跟进补丁（Andrea Righi）：改写 allowed_cpus selftest 使 idle 校验无竞态——只校验本地 CPU 稳定不变式（ops.select_cpu
    中运行非 idle 上下文的本地 CPU 不得被标记 idle），并新增 bootstrap 阶段在每个在线 CPU 上跑任务以刷新初始 idle mask。
  review_outcome: 作为对前置补丁讨论的落实，刚发出。
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.2-fixes（目标分支）
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 Tejun 将 waker-busy 修复与 selftest 重做一并 pick 到 sched_ext/for-7.2-fixes
contribution_opportunities:
- kind: testing
  description: 在多核/开启 SCX 的机器上反复运行 allowed_cpus selftest（尤其刚 enable SCX 后），验证竞态误报是否消除
- kind: review
  description: review 新的 bootstrap 刷新逻辑与本地 idle 不变式校验，确认不会引入新的 flaky 点
generated_at: '2026-07-27T01:10:00'
source_email_count: 2
related_articles: []
tags:
- sched_ext
- idle
- affinity
title: 'selftests/sched_ext: Make allowed_cpus idle validation race-free'
layout: article
---

## TL;DR
一组针对 sched_ext idle 跟踪与 selftest 竞态的修复：Kuba Piecuch 先修复 WAKE_SYNC 下 waker CPU 未被标记 busy 导致的 `allowed_cpus` selftest 偶发失败；Andrea Righi 跟进重写 selftest 的 idle 校验为无竞态版本。目标分支 `sched_ext/for-7.2-fixes`，合入可能性较高。

## 背景与问题
SCX 内建的 idle CPU 跟踪并不完美，可能与 CPU 实际 idle 状态失步——尤其刚 enable SCX 时 `scx_idle_enable()` 会把所有在线 CPU 标记为 idle。在 `SCX_WAKE_SYNC` 情况下，`scx_select_cpu_dfl()` 若选中的正是 waker CPU，会跳过将其标记为 busy；若该 waker CPU 之前被标为 idle，则选核后（甚至切到 wakee 后）它仍显示 idle，导致 `allowed_cpus` selftest 报 `CPU 0 should be marked as busy` 而偶发失败。进一步地，selftest 原本校验"远程选中的 CPU 选后仍不在 idle mask"——但 idle-to-idle 的 re-pick 可能在 BPF 程序校验前又把该 CPU 标回 idle，这个检查本身就是竞态的。

## 技术方案
前置补丁（Kuba）：在 WAKE_SYNC 命中 waker CPU 分支里显式调用 `scx_idle_test_and_clear_cpu(cpu)` 再 goto out_unlock，确保选中的 waker CPU 被清出 idle mask。跟进补丁（Andrea）：改写 selftest 校验策略——放弃对远程选中 CPU 的 idle 状态做校验（本质竞态），改为校验本地稳定不变式：在 `ops.select_cpu()` 里若 `scx_bpf_cpu_curr()` 报告本地 CPU 正跑非 idle 上下文，则它绝不能出现在 idle mask（本地 CPU 在回调执行期间不会走 pick_task_idle，故 race-free）；同时校验选中 CPU 同时满足 allowed 域与任务 affinity；并新增 bootstrap：通过 `sched_setaffinity` 逐个把任务绑到每个在线 CPU 跑一遍，配合 `ops.running()` 刷新初始 idle mask，保证严格校验前 idle 状态已正确初始化。

## 版本演进与当前进展
前置补丁 7/22 发出，Andrea 7/26 回复认可并指出 selftest 竞态；同日 Andrea 发出 selftest 重做补丁。两者构成一组修复，当前处于 review/待 pick 阶段。

## Maintainer 意见与讨论焦点
Andrea Righi 明确认可 Kuba 的 waker-busy 修复，并主动提出 selftest 本身"不可避免地 racy、会误报"，进而给出重做方案（校验稳定不变式而非瞬态、加 bootstrap）。讨论焦点是如何让 selftest 只验证稳定属性、消除 false positive。未见反对意见，属建设性推进。

## 合入评估
合入可能性较高。目标为 `sched_ext/for-7.2-fixes` 修复分支，两个补丁都是明确的 flaky/竞态修复，由 SCX 活跃维护者主导，等待 Tejun 一并 pick 即可，无明显阻塞。

## 效果评估
前置补丁作者说明"应用后测试失败不再复现，但仍存在极少数如 pick_task_idle() 在选中与校验之间把 CPU 标回 idle 的竞态"，属作者基于实测的判断（明确指出仍有残余竞态）。Andrea 的重做正是为消除这些残余竞态，把校验从瞬态改为稳定不变式。无量化性能数据，效果体现为 selftest 稳定性提升。

## 我可以参与的点
- 在多核/开启 SCX 的机器上反复运行 allowed_cpus selftest（尤其刚 enable SCX 后），验证竞态误报是否消除并回帖
- review 新的 bootstrap 刷新逻辑与本地 idle 不变式校验，确认不引入新的 flaky 点

## 参考链接
- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到（目标 sched_ext/for-7.2-fixes）
