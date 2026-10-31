---
id: sched-20261031-011
date: 2026-10-31
subject: 'sched/deadline: total_bw leak when a task leaves SCHED_DEADLINE while not
  queued'
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: <2b5fb3f22bca6aa383be8f4781923392@kernel.org>
lore_url: https://lore.kernel.org/all/2b5fb3f22bca6aa383be8f4781923392@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Juri Lelli
- Tejun Heo
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Juri 的修复在 KEEP_PARAMS 场景重复归还、total_bw 转负
  - CPU offline 后切换路径 dl_bw_cpus()=0 除零 Oops，需加防护
  - 修复仍为 inline 提议，未成正式 patch、无 Tested-by
  next_action: Juri 吸收两点反馈后出正式补丁并复测三条路径
contribution_opportunities:
- kind: testing
  description: 复跑 KEEP_PARAMS 与 CPU-offline 切换序列，验证下一版补丁后负数 total_bw 与除零 Oops 消失
- kind: review
  description: 核对 KEEP_PARAMS 语义（保持 DEADLINE 是否本就不应释放带宽）与 dl_bw_cpus() 为 0 的防护位置
generated_at: '2026-11-01T09:00:00'
source_email_count: 1
related_articles:
- sched-20261030-001
tags:
- deadline
title: 'sched/deadline: total_bw leak when a task leaves SCHED_DEADLINE while not
  queued'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/30/sched-20261030-001-sched-deadline-total-bw-leak-when-a-task-leaves-sched-deadli.html">sched-20261030-001</a>：Tejun Heo 报告 SCHED_DEADLINE 带宽泄漏（未入队任务切策略不归还 `total_bw`），Juri Lelli 当日给出 inline 修复（`switched_from_dl()` 无 pending timer 分支直接 `__dl_sub()`）。
- <a class="article-ref" href="/lkm/2026/10/31/sched-20261031-011-sched-deadline-total-bw-leak-when-a-task-leaves-sched-deadli.html">sched-20261031-011</a>（今天）：Tejun 实测 Juri 的补丁——基本泄漏确实修好（三种 case 泄漏归 0、60s 随机策略抖动后 `total_bw` 回到初值），但暴露两个新问题：`SCHED_FLAG_KEEP_PARAMS` 反复切换会把 `total_bw` 扣成负数，且「CPU 下线后再把睡眠 DEADLINE 任务切 SCHED_OTHER」会在 `__dl_sub()` 里除以 `dl_bw_cpus()=0` 直接 Oops。

## 背景与问题
（承接）DEADLINE 任务在未入队状态切走时不归还 `total_bw` 的泄漏。今日在验证 Juri 修复时进一步发现补丁语义的两个边界缺陷，均属于「归还带宽」路径的过度扣减或异常除数。

## 技术方案
（承接 Juri 的 inline 修复方向）今日无新补丁，为实测反馈。Tejun 的数据把问题定位到两处：

- `sched_setattr(SCHED_OTHER)` + `SCHED_FLAG_KEEP_PARAMS` 对睡眠 DEADLINE 任务：任务**仍是 DEADLINE**，但每次调用都释放带宽、退出再释放一次，导致重复归还（0.2 CPU 任务 209715：DEADLINE set 后 +209715 → 第 1 次 KEEP_PARAMS 归 0 → 第 2 次 -209715 → 第 3 次 -419430 → 退出 -629145）。之后新 2ms/10ms 任务 `-EBUSY`（3ms/10ms 却可准入）、CPU offline 也 `-EBUSY`。
- 任务 CPU offline 后把睡眠 DEADLINE 任务切 SCHED_OTHER：补丁新增的 `__dl_sub()` 里 `dl_bw_cpus(task_cpu(p))` 对该 root domain 为 0 → 除零 `Oops: divide error`。

未打补丁的 mainline 在这些 case 下「只泄漏、不崩溃」。

## 版本演进与当前进展
*current_version: null*（修复仍为 inline 提议，未成正式 patch）。进展：从「修主泄漏」进入「修补丁的回归」阶段——Juri 的补丁需要补上 KEEP_PARAMS 重复归还与 CPU offline 除零两处守卫。

## Maintainer 意见与讨论焦点
- **Tejun Heo（实测反馈）**：确认主泄漏修复有效（归 0），并给出一手回归数据（负数 `total_bw` 与除零 Oops 的精确序列）。
- **Juri Lelli（DEADLINE maintainer，前一日）**：提出的 inline 修复方向仍成立，但尚未回应今日两点反馈。
- 未解决：KEEP_PARAMS 场景如何避免重复归还、`dl_bw_cpus()` 除零如何保护，待 Juri 回应。

## 合入评估
*likelihood=medium*。主修复方向已验证有效，但今日两点回归使补丁不能直接转正，需再迭代。*blocking_issues*：KEEP_PARAMS 重复归还；CPU offline 后切换的除零保护；仍无正式 patch/Tested-by。*next_action*：Juri 吸收两点反馈后出正式补丁并复测三条路径。

## 效果评估
今日有精确数字（Tejun 实测）：主泄漏三种 case 均归 0、60s 随机策略抖动后 `total_bw` 回到初值；KEEP_PARAMS 三次调用后 `total_bw` 到 -419430、退出后 -629145；除零 Oops 为 `switched_from_dl+0x13a/0x3e0` 的 `divide error`。

## 我可以参与的点
- **testing**：复跑 Tejun 的 KEEP_PARAMS 与 CPU-offline 切换序列，验证下一版补丁后负数 `total_bw` 与除零 Oops 均消失。
- **review**：核对 KEEP_PARAMS 语义（保持 DEADLINE 是否本就应不释放带宽）与 `dl_bw_cpus()` 为 0 的防护位置。

## 参考链接
- Tejun 今日实测回帖: https://lore.kernel.org/all/1a24bcdde0bb6e4a8c839351002e841d@kernel.org/
- 系列起点（Tejun 报告）: https://lore.kernel.org/all/2b5fb3f22bca6aa383be8f4781923392@kernel.org/
