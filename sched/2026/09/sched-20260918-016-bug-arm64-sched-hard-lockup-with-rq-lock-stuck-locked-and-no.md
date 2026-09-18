# [BUG] arm64/sched: hard lockup with rq->__lock stuck locked and no apparent owner

## TL;DR
华为鲲鹏（Great Wall RK5260 V5，128 核 arm64）上报告一起 hard lockup：`rq[3].__lock` qspinlock 一直处于 locked 状态、却找不到持有者，124 个 CPU 挂在该锁的 MCS 队列里，CPU3 经 futex_wait → schedule() 阻塞在拿 rq 锁。内核为自研 5.15.131。Will Deacon 回应"得先换更新的内核再谈"，即无法在该旧内核上进一步排查。属孤立的疑难 lockup 报告，暂无修复。

## 背景与问题
- 平台：Huawei/HiSilicon Kunpeng，Great Wall QingTian RK5260 V5，BIOS 华为 6.65（2023-09）。
- 内核：5.15.131-5.xxxx.aarch64（自研，2024-02 构建），128 CPU，512 GB 内存，故障前运行 744 天。
- 症状：`Kernel panic - not syncing: Hard LOCKUP`。受影响锁 `&runqueues[3].__lock`，锁值 `counter=0x00d00101`（locked=1、pending=1、tail=0xd0），即仍有活跃 owner、一个 pending waiter、一个 MCS 队列。
- 异常点：qspinlock 队列内部看似一致，但找不到仍在以 own 身份执行的 CPU。

## 技术方案
无补丁——这是一份带 vmcore 的 bug 报告，请求社区协助分析。关键现场：
- CPU3 SDEI 记录 `pc = queued_spin_lock_slowpath+0x200`，`x3/x19` 指向 rq[3].__lock，`x0` 指向 per-CPU qnode（说明 CPU3 已加入 MCS 队列）；栈为 `queued_spin_lock_slowpath → do_raw_spin_lock → raw_spin_rq_lock_nested → __schedule → schedule → futex_wait_queue_me → futex_wait → do_futex`，任务为 `ovs-monitor (PID 648437)`。
- 124 个 CPU 有活跃 MCS qnode，CPU116 在 pending 路径，CPU29 在队头，CPU51 在队尾（tail 编码 `0xd0 → (0xd0>>2)-1 = 51`）。
- 报告者无法判断是调度器/qspinlock 问题、内存损坏、还是平台/CPU 一致性（coherency）问题。

## 版本演进与当前进展
- 首报（09-18，`<4348f073.6ff0.1a0b389b7c1.Coremail.lw8186@163.com>`）：本日 Will Deacon 回复要求换更新内核复测，无后续。

## Maintainer 意见与讨论焦点
- **Will Deacon**：直言 "you really need to try something more recent if we're going to help you"，—— 5.15.131 过于陈旧，上游无法基于它排查，需要在新内核（或至少更近的 LTS）上复现。

## 合入评估
likelihood=unknown。这是 bug 报告而非补丁，无法谈合入；当前被卡在"需在新内核复现"。blocking_issues：旧内核（5.15.131）无法获得上游支持；vmcore 分析亦无结论。next_action：报告者在更新内核上尝试复现，若能复现则携带 vmcore/复制脚本重新上报。

## 效果评估
无性能数据。严重度为 hard lockup（整机 panic），但触发条件未知（运行 744 天后出现、疑似偶发/平台相关）。

## 我可以参与的点
- kind=review：基于 vmcore 现场（qspinlock 无 owner、124 CPU 等待）分析是否为已知的 qspinlock/内存损坏/平台 coherency 问题——这恰是华为鲲鹏平台，具备本地复现与分析条件。
- kind=discussion：协助判断该类"锁一致但无 owner"现象在 arm64 qspinlock 上是否与内存一致性/看门狗时序有关。

## 参考链接
- lore（报告）: https://lore.kernel.org/all/4348f073.6ff0.1a0b389b7c1.Coremail.lw8186@163.com/

---
id: sched-20260918-016
date: '2026-09-18'
subject: '[BUG] arm64/sched: hard lockup with rq->__lock stuck locked and no apparent owner'
subsystem: sched
type: bug
status: stalled
severity: critical
thread_root_msgid: '<4348f073.6ff0.1a0b389b7c1.Coremail.lw8186@163.com>'
lore_url: 'https://lore.kernel.org/all/4348f073.6ff0.1a0b389b7c1.Coremail.lw8186@163.com/'
authors:
  - '含笑傲月'
maintainers_involved:
  - 'Will Deacon'
current_version: v1
patch_series:
  - version: v1
    msgid: '<4348f073.6ff0.1a0b389b7c1.Coremail.lw8186@163.com>'
    date: '2026-09-18'
    summary: '首报：arm64 rq.__lock 无 owner hard lockup，附 vmcore'
    review_outcome: 'Will Deacon 要求换更新内核复测'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - '旧内核 5.15.131 无法获上游支持'
    - 'vmcore 分析无结论'
  next_action: '报告者在新内核上尝试复现并重新上报'
contribution_opportunities:
  - kind: review
    description: '基于 vmcore 分析 qspinlock 无 owner 现象的根因'
  - kind: discussion
    description: '判断是否与平台 coherency/看门狗时序有关'
generated_at: '2026-09-19T09:00:00'
source_email_count: 2
related_articles: []
tags:
  - arm64
  - hang
  - crash
---