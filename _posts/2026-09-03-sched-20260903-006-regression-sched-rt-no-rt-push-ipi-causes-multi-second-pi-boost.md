---
id: sched-20260903-006
date: '2026-09-03'
subject: '[REGRESSION] sched/rt: NO_RT_PUSH_IPI causes multi-second PI-boost starvation
  in pro-audio workloads (dd29c017aed6)'
subsystem: sched
type: bug
status: stalled
severity: high
thread_root_msgid: <CAEB5A_91hob8ddOhW=PrO1=O7GrFmSxY3r1-_Ard6x8KHHuJGA@mail.gmail.com>
lore_url: https://lore.kernel.org/all/6db9c47f-a1f8-49dd-9e80-f9014d75f9e8@leemhuis.info/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: '2026-09-07'
authors:
- Martin King
maintainers_involved:
- Thorsten Leemhuis
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无修复补丁，且 Steven Rostedt 截至 09-03 未回复催办
  - 原始报告的复现与量化数据未保留在邮件缓存中，问题边界不清
  - 已列入 tracked regression，若继续沉默可能升级为对 dd29c017aed6 的回退要求
  next_action: 等 RT 维护者回应是否已解决；社区侧补一份 NO_RT_PUSH_IPI 开/关下的 PI-boost 唤醒延迟对照数据
contribution_opportunities:
- 在非 PREEMPT_RT 下量化 sched_feat(NO_RT_PUSH_IPI) 开/关对 PI-boost 唤醒延迟的影响
- 核对 dd29c017aed6 之后是否已有提交恢复 PI 提升场景的 push，回答回归追踪者的问题
- 把该回归纳入 OLK-6.6 跟进同类默认值变更的风险清单
source_email_count: 1
related_articles: []
tags:
- rt
- regression
title: '[REGRESSION] sched/rt: NO_RT_PUSH_IPI causes multi-second PI-boost starvation
  in pro-audio workloads (dd29c017aed6)'
layout: article
---

## TL;DR

`dd29c017aed6`（"sched/rt: Have RT_PUSH_IPI be default off for non PREEMPT_RT"）使非 PREEMPT_RT 系统在 RT 任务位于其他 CPU 上被释放/提升时不再发 RT push IPI，专业音频（DAW）用户据此报告了多秒级的 PI-boost 饥饿。
本日唯一的动静是回归追踪者 Thorsten Leemhuis 的催办：该问题**已被列入他追踪的 regression 清单**，但从 8 月中旬起再无进展，他直接问 Steven Rostedt 是否因出差漏掉了、或者已经悄悄修好了。截至 09-03 缓存中没有修复补丁，也没有对该回归的技术回复。

## 背景与问题

报告由 Martin King 于 8 月 14 日发出（主题带 `[REGRESSION]`，指向 `dd29c017aed6`），场景是 pro-audio：音频工作站内多线程以 RT 优先级运行并依赖优先级继承（PI）提升，当持锁的低优先级线程被放到别的 CPU 上、而其 PI 提升后的高优先级 waiter 无法通过 push IPI 被及时搬到该 CPU 时，唤醒延迟会退化到秒级并造成掉帧。
注意：本日缓存里只有 Thorsten Leemhuis 的催办信。原始报告的复现步骤、内核版本、量化延迟数据，以及 Steven Rostedt 8 月 14 日的回复正文**均未保留在邮件缓存中**（08-15 目录里的两条记录正文为空、msgid 为占位值），因此上述场景细节仅来自主题行与后续讨论可推出的部分，具体数值未获取到。

## 技术方案

- 本日无补丁、无修复提案，属回归追踪阶段。
- 需要评估的方向（从回归主题可确定）：`NO_RT_PUSH_IPI` 下 RT push 路径失去 IPI 后，PI-boost 后的任务如何被搬回锁持有者所在 CPU——可选方向包括对 PI 提升后的 waiter 恢复 push IPI、把该默认值重新与 `PREEMPT_RT` 解耦、或在 `rt_mutex` 提升路径上补一次显式 push。
- 缓存中未出现任何维护者对上述方向的取舍表态。

## 版本演进与当前进展

- 8 月 14 日：Martin King 发出回归报告（原始正文未保留）。
- 8 月 14/15 日：Steven Rostedt 有回复（正文未保留），随后线程静默约三周。
- 9 月 3 日 19:27：Thorsten Leemhuis 催办，明确 "This made it to my list of tracked regression -- but it looks like there was no progress for a while."，并问 "Steven, did that maybe fall through the cracks due to the travel you mentioned? Or was this resolved meanwhile and I just missed it?"
- 本日内无修复补丁、无 v1、无讨论收敛迹象；线程状态为停滞。

## Maintainer 意见与讨论焦点

- **Thorsten Leemhuis（kernel regressions 追踪者）**：本日唯一发言者。他的两个事实性判断是「已进入 tracked regression 清单」与「已有一段时间没有进展」；他还把停滞归因于 Steven Rostedt 提到过的出差（"fall through the cracks due to the travel you mentioned"），并主动询问是否已经解决而他自己漏看。这是流程压力而非技术意见。
- **Steven Rostedt**：被点名的一方，此前对该 RT push/IPI 代码区域做过改动并参与讨论，但 09-03 未回复，其 8 月回复正文未保留，**具体技术意见未获取到**。
- Peter Zijlstra / Ingo Molnar（RT 调度维护者）：本线程内 09-03 无表态，也未见任何 `Reported-by`/`Fixes` 回应。

## 合入评估

likelihood: **unclear**（无补丁可评估）。
依据与卡点：修复本身没有对象——本日内没有补丁、没有维护者对该回归的技术判断、也没有确认「已修复」的回复。真正的信号是流程性的：进入 Thorsten Leemhuis 的 tracked regression 清单意味着它会在 `Documentation/admin-guide/bug-hunting` 类的追踪列表中被持续点名，若下一周期仍无回应，通常会升级为对 `dd29c017aed6` 的回退要求。
因此下一步取决于 Steven Rostedt 或 RT 维护者是否回帖：要么说明已解决（则本条关闭），要么给出对 `NO_RT_PUSH_IPI` 与 PI-boost 交互的正式立场。

## 效果评估

邮件正文中未提供效果数据。本日唯一的邮件（Thorsten Leemhuis 的催办）不含任何测量结果；原始报告的 DAW 掉帧与多秒级饥饿量化数据未保留在缓存中，因此延迟分布、受影响内核版本区间、可复现性比例均为「未获取到」。主题行本身给出的可确认事实是：量级为 multi-second、现象为 PI-boost 饥饿、场景为 pro-audio、引入提交为 `dd29c017aed6`。

## 我可以参与的点

1. 这是当前最缺人手的一类工作：复现并给出数据。在 `PREEMPT_RT=n` 的配置下开 `CONFIG_RT_MUTEXES` + PI 场景（`pthread_mutex` 优先级继承 + 跨 CPU 的 RT 任务），量化 `rt_mutex_setprio()` 提升后的唤醒延迟直方图，并在 `sched_feat(NO_RT_PUSH_IPI)` 开/关两种取值下对照——这正是原报告里可能缺的证据。
2. 若不便复现，可做的次优贡献是核对该回归的当前状态：确认 `dd29c017aed6` 之后是否有其它提交已经恢复 PI-boost 场景下的 push（回答 Thorsten 的 "was this resolved meanwhile"）。
3. 对 OLK-6.6 的直接价值：6.6 里 RT push 与 `NO_RT_PUSH_IPI` 的行为与该提交前的形态更接近，若华为侧有低延迟音频/电信类负载，这条回归的结论会影响将来是否跟进同类默认值变更，值得纳入回合风险评估。

## 参考链接

- 本日邮件（Thorsten Leemhuis 催办）：https://lore.kernel.org/all/6db9c47f-a1f8-49dd-9e80-f9014d75f9e8@leemhuis.info/
- 线程根（Martin King 的原始报告，正文未保留在缓存中）：https://lore.kernel.org/all/CAEB5A_91hob8ddOhW=PrO1=O7GrFmSxY3r1-_Ard6x8KHHuJGA@mail.gmail.com/
- 相关代码/commit：
  - `dd29c017aed6` "sched/rt: Have RT_PUSH_IPI be default off for non PREEMPT_RT"
  - `kernel/sched/rt.c` RT push / push IPI 与 `pull_rt_task()` 路径；`kernel/locking/rtmutex.c` `rt_mutex_setprio()` 提升后的 push 触发点
