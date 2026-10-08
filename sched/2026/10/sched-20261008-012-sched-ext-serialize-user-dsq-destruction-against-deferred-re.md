# sched_ext: Serialize user DSQ destruction against deferred reenqueues

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260930-002：Hui Su 修 sched_ext deferred reenqueue 的 use-after-free——被 deferral 的用户 DSQ 节点可在 RCU 回调 `exit_dsq()` 到达前就被 detach，deferred 路径其后仍裸用 DSQ 指针、回调可能先释放 DSQ；v1 用「detach 前先取引用」的办法，Andrea Righi 认可 race 但建议避免反复排队 RCU 回调地持引用。
- sched-20261008-012（今天）：按 Tejun 的建议放弃引用计数、保持 deferred reenqueue 热路径不变，改在**罕见的 DSQ 销毁路径**上加同步（扫每 CPU 的 deferred 列表 + 检查游标，若有活跃游标再推迟一轮 RCU 回收），重命名补丁为「Serialize user DSQ destruction against deferred reenqueues」发 v3，KASAN + LOCKDEP 干净。

## 背景与问题

（承接 sched-20260930-002）`scx_bpf_dsq_reenq()`（`84b1a0ea0b7c`）引入的 deferred reenqueue 机制下，被 defer 的用户 DSQ 节点可能在 RCU 回调到达 `exit_dsq()` 之前就被 `process_deferred_reenq_users()` detach 走；一旦 detach，`exit_dsq()` 找不到该节点，而 deferred 路径在放弃 `deferred_reenq_lock` 后仍继续裸用 DSQ 指针（查 ID、调 `reenq_user()`）。首轮 RCU 宽限期只排空「找到 @dsq 的生产者」，覆盖不了「已 detach 并继续用 @dsq 的消费者」。KASAN 报 `slab-use-after-free in run_deferred`。

## 技术方案

（承接 + 今日 v3）放弃 v1 的「detach 前取引用」——不在 deferred reenqueue 热路径加引用计数（遵循 Tejun 的方向），改为同步稀有的销毁路径：

- 首轮宽限期后，逐个 rq 取其 deferred 锁，unlink 尚未 detach 的请求，关闭「detach 到游标」窗口；
- `reenq_user()` 的迭代游标在其最后一次访问前一直留在 `@dsq->list` 上；`destroy_dsq()` 要求 `@dsq->nr == 0`，故 sweep 后列表仍非空即说明存在活跃游标，此时把回收再推迟一轮 RCU 回调，直到游标退出。

作者补充的验证：一个仅测试用的 pre-fix fixture 在 detach 请求后、最终 DSQ 访问前直接调 `free_dsq_rcufn()`，KASAN 报 `run_deferred+0x1312/0x1710` 的 UAF（`swapper/3/0` 读 8 字节，经 `ttwu_do_activate → try_to_wake_up`）；v3 另用 active-cursor 测试验证「游标链着时回收保持延迟、游标移除后再完成」，KASAN 与 PROVE_LOCKING/LOCKDEP 均干净。

## 版本演进与当前进展

- v1（09-30，见 related 文章）：detach 前取引用；Andrea 建议避免反复排队 RCU 回调。
- v3（今日，`<20261008024753.4096008-1-sh_def@163.com>`）：重命名为「Serialize user DSQ destruction against deferred reenqueues」，按 Tejun 建议去掉引用计数、改销毁路径同步；`Fixes: 84b1a0ea0b7c`、`Cc: stable`。

## Maintainer 意见与讨论焦点

- **Tejun Heo**（sched_ext 维护者）：建议不在热路径加引用计数、把同步集中到销毁路径（v3 即此方向的落地）。
- **Andrea Righi**（sched_ext 联合维护者）：v1 时认可 race 属实，但担心「活跃 detach reenqueue 持引用期间反复排队 RCU 回调」；v3 的「sweep + 检查游标、必要时再推迟一轮」正是回应这一顾虑。
- 无 NAK；v1 的引用管理分歧在 v3 已通过改到销毁路径化解。

## 合入评估

*likelihood=medium*。真实的 memory-safety bug（KASAN UAF）、带 `Fixes:`/`Cc: stable`、方向按维护者（Tejun）建议落地且回应了 Andrea 的顾虑；但 v3 尚无显式 R-b/A-b，且作者仍无自然复现器（靠 fixture 强制窗口验证），stable 回退评估仍需权衡。*blocking_issues*：v3 未获显式 R-b/A-b；无可自然复现的测试供 stable 评估。*next_action*：等 Tejun/Andrea 对 v3 的 R-b/A-b，随后合入 for-7.4 并随 stable 回合。

## 效果评估

KASAN/LOCKDEP 回归：pre-fix fixture 稳定报 `slab-use-after-free in run_deferred`；v3 的销毁路径 sweep + 游标检查下 KASAN 与 PROVE_LOCKING 干净。无性能数据（同步只在罕见销毁路径上）。

## 我可以参与的点

- `testing`：尝试构造 deferred reenqueue 的**自然**复现（作者目前只有 fixture），并验证 v3 下不存在 DSQ 提前释放或泄漏。
- `review`：评估「sweep 后列表非空即再推迟一轮 RCU 回调」在存在多个活跃 `reenq_user()` 游标/长迭代时的回收进度与 busy 边界。

## 参考链接

- v3 补丁: https://lore.kernel.org/all/20261008024753.4096008-1-sh_def@163.com/
- v1/related: https://lore.kernel.org/all/20260930101722.2468434-1-sh_def@163.com/

---
id: sched-20261008-012
subject: 'sched_ext: Serialize user DSQ destruction against deferred reenqueues'
date: '2026-10-08'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: '<20261008024753.4096008-1-sh_def@163.com>'
lore_url: 'https://lore.kernel.org/all/20261008024753.4096008-1-sh_def@163.com/'
authors:
  - 'Hui Su'
maintainers_involved:
  - 'Tejun Heo'
  - 'Andrea Righi'
current_version: v3
patch_series:
  - version: v1
    msgid: '<20260930101722.2468434-1-sh_def@163.com>'
    date: '2026-09-30'
    summary: 'Hold DSQ refs：detach 前先取 DSQ 引用，回调与 deferred 路径各自释放'
    review_outcome: 'Andrea 认可 race，但建议避免反复排队 RCU 回调'
  - version: v2
    msgid: null
    date: null
    summary: '空窗期（无日报）内发出，msgid 未获取到'
    review_outcome: null
  - version: v3
    msgid: '<20261008024753.4096008-1-sh_def@163.com>'
    date: '2026-10-08'
    summary: '改销毁路径同步（sweep deferred 列表 + 检查游标，必要时再推迟一轮 RCU）'
    review_outcome: 'KASAN/LOCKDEP 干净，待 Tejun/Andrea R-b/A-b'
upstream_commit: null
fixes_commit: '84b1a0ea0b7c'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'v3 尚无显式 R-b/A-b'
    - '无自然复现测试供 stable 回退评估'
  next_action: '等 Tejun/Andrea 对 v3 的 R-b/A-b 后合入并随 stable 回合'
contribution_opportunities:
  - kind: testing
    description: '构造 deferred reenqueue 的自然复现并验证 v3 无提前释放/泄漏'
  - kind: review
    description: '评估多活跃游标/长迭代下「列表非空即再推迟一轮」的回收进度边界'
generated_at: '2026-10-09T01:00:00'
source_email_count: 3
related_articles:
  - sched-20260930-002
tags:
  - sched_ext
---