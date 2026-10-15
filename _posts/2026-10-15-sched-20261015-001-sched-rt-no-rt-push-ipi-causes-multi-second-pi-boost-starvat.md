---
id: sched-20261015-001
date: 2026-10-15
subject: 'sched/rt: NO_RT_PUSH_IPI causes multi-second PI-boost starvation in pro-audio
  workloads (dd29c017aed6)'
subsystem: sched
type: regression
status: under_review
severity: high
thread_root_msgid: <CAEB5A_91hob8ddOhW=PrO1=O7GrFmSxY3r1-_Ard6x8KHHuJGA@mail.gmail.com>
lore_url: https://lore.kernel.org/all/CAEB5A_91hob8ddOhW=PrO1=O7GrFmSxY3r1-_Ard6x8KHHuJGA@mail.gmail.com/
authors:
- Martin King
maintainers_involved:
- Steven Rostedt
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: dd29c017aed6
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 尚无修复补丁
  next_action: 实现 prio_changed_rt() 感知 rto mask 并在 PI boost 时触发 push 的修复补丁，并在真实 pro-audio
    负载上验证
contribution_opportunities:
- kind: new_patch
  description: 按 Steven 方向实现修复：让 prio_changed_rt() 感知 rto mask 并在 boost 时触发 push
- kind: testing
  description: 在真实 RT/pro-audio 负载上复现并验证，确认三条件是否完整覆盖现场
- kind: discussion
  description: 厘清 NO_RT_PUSH_IPI 关闭 push-IPI 的原始性能考量
generated_at: '2026-10-16T01:05:00'
source_email_count: 2
related_articles:
- sched-20260815-013
- sched-20260903-006
tags:
- rt
- regression
- rt_bandwidth
title: 'sched/rt: NO_RT_PUSH_IPI causes multi-second PI-boost starvation in pro-audio
  workloads (dd29c017aed6)'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/08/15/sched-20260815-013-sched-rt-no-rt-push-ipi-causes-multi-second-pi-boost-starvat.html">sched-20260815-013</a>：Martin King 报告并修复一个 RT 回归——`CONFIG_NO_RT_PUSH_IPI` 下 RT push 失败时 `rt_rq->rto` 计数未扣除，残留计数让后续 PI-boost/迁移误判「有 overload」，导致饥饿与迁移停滞。
- <a class="article-ref" href="/lkm/2026/09/03/sched-20260903-006-regression-sched-rt-no-rt-push-ipi-causes-multi-second-pi-boost.html">sched-20260903-006</a>：Thorsten Leemhuis 催办——该回归已被列入他的 regression 清单，但自 8 月中旬无进展，无修复补丁。
- <a class="article-ref" href="/lkm/2026/10/15/sched-20261015-001-sched-rt-no-rt-push-ipi-causes-multi-second-pi-boost-starvat.html">sched-20261015-001</a>（今天）：Chaosheng Qu 给出窄化合成复现器与数据；Steven Rostedt 读后**立即定位根因并确认是合法 bug**——PI-boost 本应触发一次额外的 RT 迁移分析，但 `prio_changed_rt()` 没做——修法是让 `prio_changed_rt()` 感知 rto mask 并在 boost 时触发 push。修复方向由维护者拍板，尚无补丁。

## 背景与问题
（承接 20260815-013 → 20260903-006）`dd29c017aed6`（"sched/rt: Have RT_PUSH_IPI be default off for non PREEMPT_RT"）使非 PREEMPT_RT 系统在 RT 任务被释放/提升时不再发 RT push IPI；pro-audio（DAW）用户据此报告多秒级 PI-boost 饥饿（Martin King 于 8 月 14 日首次报告）。今天 Steven Rostedt 与 Chaosheng Qu 把机制彻底厘清：PI 继承把低优先级持锁任务 boost 到高优先级、且它因本 CPU 被更高优先级 hog 占住而无法运行时，存在一个「死亡窗口」——本 CPU 不能跑它，pull 侧够不到它，push 侧 IPI 又因 NO_RT_PUSH_IPI 从未排队，任务卡到 hog 主动 schedule out。

## 技术方案
（承接 20260815-013/20260903-006）8 月的补丁方向是「push 失败分支扣除 `rto` 计数」，但该回归至今仍开放，说明另有根因。今天 Steven 给出更本质的修法：

> We need to make the prio_changed_rt() aware of the rto mask and trigger a push if needed.

即 PI-boost 时应触发一次额外的 RT 迁移分析（当前代码缺这一步）。Chaosheng Qu 的合成复现器（QEMU/KVM 4 vCPU，v7.3-rc7，经 `/sys/kernel/debug/sched/features` 切换）验证了 push 侧从不排队这一机制：cpu1 上 FIFO 10 的持锁者 L 被 FIFO 90 的 waiter W boost 到 90，但被同 CPU 的 FIFO 99 hog X 占住；cpu3 的 spare R 只有 FIFO 60，boost 前 `find_lock_lowest_rq()` 不把 cpu3 当合法目标——迁移机会恰恰由 boost 创造，却被错失。

## 版本演进与当前进展
- 2026-08-14：Martin King 报告 + 早期修复尝试（rto 计数）。
- 2026-09-03：Thorsten 催办，无新补丁。
- 今天：Chaosheng 合成复现器 + Steven 定位根因、明确修法；尚无实现补丁。

## Maintainer 意见与讨论焦点
Steven Rostedt（RT 调度维护者）明确：「I think this is a legitimate bug and should be fix. We need to make the prio_changed_rt() aware of the rto mask and trigger a push if needed.」即方向已定。遗留点：尚无实现补丁；Martin 原始负载是否完整命中 Chaosheng 归纳的三条件（PI boost + owner CPU overload + affinity 排除刚 idle CPU）仍未完全确认。

## 合入评估
*likelihood=high*。回归获维护者确认属实、修法明确。*blocking_issues*：尚无修复补丁。*next_action*：实现 `prio_changed_rt()` 感知 rto mask 并触发 push 的 patch，并在真实 pro-audio / Martin 的 livefx 负载上验证。

## 效果评估
Chaosheng Qu 的合成数据（dwell 1500ms，100ms「及时迁移」阈值）：RT_PUSH_IPI off（默认）8 次 0/8 及时恢复、owner resume median 1499.6ms；on 6/6 及时恢复、median 0.8ms；无 boost 对照 0/2（1499.2ms）。dwell 拉到 4000ms 时 waiter 阻塞 2.26s 才恢复。8 次 off 中 7 次从未迁移。affinity 反例（含刚 idle CPU）下两路径 0.5–6.2ms 都能救出。

## 我可以参与的点
- *new_patch*：按 Steven 方向实现修复——让 `prio_changed_rt()` 感知 rto mask 并在 PI boost 时触发 push。
- *testing*：在真实 RT/pro-audio（或 Martin 的 livefx）负载上复现并验证；确认三条件是否完整覆盖现场。
- *discussion*：厘清 NO_RT_PUSH_IPI 关闭 push-IPI 的原始性能考量，判断修复应否默认恢复该行为或加条件触发。

## 参考链接
- Steven Rostedt 的确认与修法：https://lore.kernel.org/all/20261015084615.05957ae3@gandalf.local.home/
- Chaosheng Qu 的合成复现器：https://lore.kernel.org/all/20261015061915.126442-1-chaosheng.qu.linux@gmail.com/
- 原始报告线程根：https://lore.kernel.org/all/CAEB5A_91hob8ddOhW=PrO1=O7GrFmSxY3r1-_Ard6x8KHHuJGA@mail.gmail.com/
