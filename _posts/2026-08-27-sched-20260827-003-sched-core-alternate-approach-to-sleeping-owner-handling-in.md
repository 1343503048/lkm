---
id: sched-20260827-003
date: '2026-08-27'
subject: 'sched/core: Alternate approach to sleeping-owner handling in PROXY_EXEC'
subsystem: sched
type: discussion
status: rfc
severity: none
thread_root_msgid: <20260826062901.2137-1-kprateek.nayak@amd.com>
lore_url: https://lore.kernel.org/all/ao8SOkBYH1uLh6Sa@gpd4/
authors:
- Andrea Righi
- K Prateek Nayak
maintainers_involved:
- Andrea Righi
current_version: v1
patch_series:
- version: v1
  msgid: <20260826062901.2137-1-kprateek.nayak@amd.com>
  date: 2026-08-26
  summary: 16 补丁 PoC：sleeping owner 挂 blocked donor 做 chain-wakeup，NULL owner 时按新路径激活
    donor
  review_outcome: 08-27 Andrea 给出 typo/字段名意见并提议对 MUTEX_FLAG_WAITERS 强制 handoff；作者全部
    ack，性能问题待 benchmark
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - PoC 性质、不可 bisect，NULL-owner 语义下 proxy chain 可行性未定
  - 强制 handoff 备选的性能代价待数据（08-31 数据已否定）
  next_action: 收敛 04/16 的 NULL-owner 激活方案；Patch 1-4 拆分独立先行
contribution_opportunities:
- kind: testing
  description: 在自家树验证可独立的 Patch 1-4 并回帖 Tested-by
- kind: review
  description: 审阅 wait_lock 下 waiter 不消失论证与 proxy 状态的交互
generated_at: '2026-09-07T22:05:00'
source_email_count: 3
related_articles:
- sched-20260826-001
- sched-20260831-002
tags:
- preempt
title: 'sched/core: Alternate approach to sleeping-owner handling in PROXY_EXEC'
layout: article
---

## TL;DR
本文为增量更新（完整背景见 related_articles）。K Prateek Nayak 的 16 补丁 proxy-exec sleeping-owner RFC PoC 在 08-27 收到 Andrea Righi 的首轮实质 review：06/16 上是 typo/字段名级别的修正且作者全部 ack；04/16 上 Andrea 提出"owner 为 NULL 时从 `mutex_unlock_slowpath()` 强制 handoff"的备选，Prateek 认可细节推理但担心牺牲 optimistic spinning 收益，答应去跑 benchmark。后续结论（强制 handoff 不可行）见 sched-20260831-002。

## 背景与问题
该 RFC PoC 处理 proxy execution 中 sleeping owner 与 blocked donor 的竞态：owner 睡着时 blocked donor 挂在 owner 上做 chain-wakeup，以及找不到 owner 时如何激活 donor。08-27 的讨论集中在 Patch 04/16（`sched/core: Activate blocked donor when no owner is found`）与 06/16（`sched/core: Queue blocked donor onto sleeping owner for chain-wakeup`）两处。

## 技术方案
04/16 的争点：mutex owner 可以长期为 NULL（直到被唤醒的 waiter 真正拿到锁），Andrea 建议在 proxy execution 开启且 mutex 带 `MUTEX_FLAG_WAITERS` 时直接从 `mutex_unlock_slowpath()` 强制一次 handoff，使 owner 始终可识别。Prateek 回复确认该做法"negates some of the benefits of optimistic spinning + mutex_try_lock()"，表示会实测"对 `MUTEX_FLAG_WAITERS` 总是强制 handoff"对 benchmark 的影响。他还论证了一个正确性子问题：`wait_lock` 下 waiter 至少会试一次 `mutex_trylock()` 才去查 pending signal，所以 `MUTEX_FLAG_PICKUP` 置起后 waiter 不会凭空消失，handoff 不会丢唤醒。

## 版本演进与当前进展
- 08-26：Prateek 发出 RFC v1（16 补丁，cover `<20260826062901.2137-1-kprateek.nayak@amd.com>`，见 sched-20260826-001）。
- 08-27：Andrea 对 06/16 提出 3 处拼写错误与一处字段名错误（应为 `owner->blocked_head` 而非 `owner->blocked_list`）；Prateek 全部 ack，并确认 06/16 注释里的 slow-path 函数名应改为 Patch 14 引入的 `proxy_activate_blocked_task()`。04/16 的强制 handoff 讨论当日以"作者去跑数据"收尾。系列未出新版本。

## Maintainer 意见与讨论焦点
- Andrea Righi（NVIDIA，proxy-exec/sched_ext 侧活跃 reviewer）：review 认真但全部是小问题 + 一个方向性备选方案；无 NAK、无 Ack。
- 未解决问题：强制 handoff 的性能代价（Prateek 承诺 benchmark）；06/16 的 `blocked_head` 改名需要在下一版落实。
- Peter Zijlstra / 核心调度维护者当日未介入。

## 合入评估
**unlikely**（就当前形态）。系列自述 PoC、不可 bisect，属方向探索；08-27 的讨论也仍以注释/命名级别为主。卡点仍是整个 PoC 的根本问题——NULL-owner 语义下 proxy chain 的可实现性（08-31 的数据表明 Andrea 的 handoff 备选不可行，问题回到方案本身，见 sched-20260831-002）。`next_action`：等 Andrea 的 `find_proxy_task()` 相关问题被回答、Patch 1–4 独立先行。

## 效果评估
当日无数据。Prateek 仅承诺"看强制 handoff 是否改变 benchmark 结果"；该实验数据在 08-31 线程中给出（-11%~-122% 回退，见 sched-20260831-002）。

## 我可以参与的点
- 该系列与 sched_ext proxy-exec 演进强绑定，回合 OLK-6.6 尚早；现阶段可参与的是把 Patch 1–4（可独立成立的 fix）在自家树验证并回帖 Tested-by。
- `wait_lock` 下 waiter 不消失的论证纯靠推理，如熟悉 kernel/locking 可帮忙审阅该路径与 proxy 状态的交互。

## 参考链接
- Andrea 对 06/16 的意见: https://lore.kernel.org/all/ao8SOkBYH1uLh6Sa@gpd4/
- Prateek 对 06/16 的回复: https://lore.kernel.org/all/a534560e-3225-4f6f-9376-dfaaedf33d83@amd.com/
- Prateek 对 04/16 的回复: https://lore.kernel.org/all/74324f25-2e8c-4f90-8f22-c1788615b95e@amd.com/
- Andrea 的 04/16 原始建议: https://lore.kernel.org/all/ao8Mlls40IG9Vp6g@gpd4/
- tip-bot commit: 未获取到
- stable backport: 未获取到
