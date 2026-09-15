# sched/core: Introduce chain-wakeup to activate blocked donors

## TL;DR
本文为增量更新（系列全貌见 related_articles：K Prateek Nayak 的 16 补丁 RFC PoC）。09-15 John Stultz（proxy-exec 共同作者之一）回复 patch 14/16：在跑该系列时命中大量 lockdep 警告——`proxy_activate_blocked_task()` 带着 rq 锁被 pin 住就调用。这正是他自己 patch 里把 `activate_blocked_waiters()` 放到 rq_lock 之外的原因；建议把 `rf` 作为参数传入、用 `rq_unlock(rq, rf)` 后再调，之后 `rq_lock(rq, rf)`，并称这样能解决。合入判断 unknown（仍是 RFC/PoC）。

## 背景与问题
承 sched-20260831-002：proxy-exec 里 sleeping owner 与 blocked donor 的竞态——owner 睡着时 proxy chain 挂在 owner 上、owner 唤醒时做 chain activation，而 blocked donor 可能被并发唤醒事件提前叫醒，激活路径需额外持 `p->blocked_lock` 才不漏 donor。patch 14/16「Introduce chain-wakeup to activate blocked donors」正是这段激活路径的一部分。John Stultz 实测后发现该实现持 rq 锁调用 `proxy_activate_blocked_task()`，触及 lockdep 约束。

## 技术方案
无新代码。John Stultz 给出具体修法建议：给 `proxy_activate_blocked_task()` 传 `rf`（rq_flags）参数，在其内部 `rq_unlock(rq, rf)` 后再做激活、之后 `rq_lock(rq, rf)` 恢复——即把激活调用移出 rq 锁临界区，与其自己补丁里 `activate_blocked_waiters()` 的处理一致。

## 版本演进与当前进展
本日为 patch 14/16 的评审反馈，无新版本。系列仍是 RFC/PoC，无人 Ack/NAK。

## Maintainer 意见与讨论焦点
- **John Stultz (Google)**：确认 patch 14/16 存在 rq 锁 pin 下的 lockdep 告警，并给出 drop/unlock 再 lock 的具体修法；表态这是他自己实现里同样问题的解法、对其有效。
- 未决点：作者 Prateek 尚未回应该修法；锁释放-重取窗口内的并发正确性需作者确认。

## 合入评估
likelihood=unknown。RFC/PoC 阶段，patch 14/16 还有 lockdep 告警待修，方向尚未收敛。blocking_issues：rq 锁 pin 下的 lockdep 告警需按 Stultz 建议改 unlock/relock；锁窗口内的并发语义待作者论证。next_action：作者按 Stultz 建议改 `proxy_activate_blocked_task()` 的锁处理并回应并发正确性。

## 效果评估
无性能数据。John Stultz 报告的是一致性/lockdep 层面问题（"hitting a lot of lockdep warnings"），属正确性缺陷，非性能回退。

## 我可以参与的点
- kind=review：审查 Stultz 建议的 unlock(→调激活→)lock 窗口内，blocked donor 与 owner 状态是否可能被并发事件改变导致漏激活。
- kind=testing：在 proxy-exec 内核上复现该 lockdep 告警并验证 unlock/relock 修法是否消除告警且不引入新竞态。

## 参考链接
- John Stultz 回帖：https://lore.kernel.org/all/CANDhNCreubmsXsbYb6745xvfYK+p-ocxJmUyt2-KTrJOqdtTnw@mail.gmail.com/
- 系列 cover（16 补丁）：https://lore.kernel.org/all/20260826062901.2137-1-kprateek.nayak@amd.com/

---
id: sched-20260915-011
date: '2026-09-15'
subject: 'sched/core: Introduce chain-wakeup to activate blocked donors'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: '<20260826062901.2137-1-kprateek.nayak@amd.com>'
lore_url: 'https://lore.kernel.org/all/CANDhNCreubmsXsbYb6745xvfYK+p-ocxJmUyt2-KTrJOqdtTnw@mail.gmail.com/'
authors:
  - 'K Prateek Nayak'
maintainers_involved:
  - 'John Stultz'
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - 'rq 锁 pin 下的 lockdep 告警需按 Stultz 建议改 unlock/relock'
    - '锁窗口内的并发语义待作者论证'
  next_action: '作者修改 proxy_activate_blocked_task() 的锁处理并回应并发正确性'
contribution_opportunities:
  - kind: review
    description: '审查 unlock→激活→lock 窗口内 donor/owner 状态是否可能被并发改变导致漏激活'
  - kind: testing
    description: '复现 lockdep 告警并验证 unlock/relock 修法是否消除告警且不引入新竞态'
generated_at: '2026-09-16T01:05:00'
source_email_count: 1
related_articles:
  - 'sched-20260831-002'
tags:
  - proxy_execution
---