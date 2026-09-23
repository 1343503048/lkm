# futex: Make FUTEX_*_PING use Proxy Execution.

## TL;DR
本文为增量更新，完整背景见 sched-20260918-011（该系列 cover 标题为「FUTEX_PING: A stealable futex using Proxy Execution.」）。Jihan LIN 对 07/12 补丁给出设计意见：该方案可复用 owner walk 以避免争用路径上的额外链式遍历，但认为「sleep 前做死锁检测」与 PI futex 更一致，且最后一次锁尝试若能直接向用户态返回 `-EDEADLK` 则额外的遍历物有所值——这与 Peter Zijlstra 先前「死锁检测应在 block 时做、返回 -EDEADLK」的立场呼应。

## 背景与问题
背景见 sched-20260918-011 与 sched-20260917-012：Google/Android 场景下 FUTEX_PI 强制严格 PI/FIFO 语义导致 SCHED_OTHER 性能崩溃，需要「RT 保持 PI、SCHED_OTHER 可被偷取」的新 futex，借助 Proxy Execution 由锁 owner 代为执行被阻塞的 waiter。

## 技术方案
系列方案不变（见 sched-20260918-011）。本日讨论落在 07/12 的具体实现取舍上：

- **Jihan LIN**：肯定该方案「可复用 owner walk」，能避免争用 futex 路径上的额外链式遍历；但同时提出——sleep 前做死锁检测会更贴近 PI futex 的行为，且如果最后一次锁尝试能直接向用户态返回 `-EDEADLK`，那额外的一次遍历就值得付出。

## 版本演进与当前进展
- v1（09-17，RFC 00/12）：见 sched-20260917-012。本日无新版，为 07/12 的持续评审。

## Maintainer 意见与讨论焦点
本日为 Jihan LIN 的单条评审意见，无维护者新表态。其「sleep 前死锁检测 + 返回 -EDEADLK」的观点与 Peter Zijlstra 此前明确提出的「死锁检测应在 block 时做、那是返回 -EDEADLK 的理想上下文」方向一致，是对该设计点的社区侧呼应。分歧仍为 Peter 此前列出的路线问题（新 futex op vs 复用 mutex、严格性归属、死锁检测实现位置），未见收敛。

## 合入评估
likelihood=low。仍处早期 RFC，Peter 明确「不急着合」并要求死锁检测器与路线论证；本日新增意见强化了「block 时死锁检测 + -EDEADLK」这一设计点，但作者尚未回应。blocking_issues：缺用户态死锁检测器；「新 futex vs mutex-based」路线未定；PI 严格性语义自洽问题。next_action：作者回应死锁检测设计与路线质疑后才有推进空间。

## 效果评估
无本日新增 benchmark（Rostedt 的历史性能论据见 sched-20260918-011）。

## 我可以参与的点
- kind=discussion：就「死锁检测应在 block 时（sleep 前）做并返回 -EDEADLK」给出具体实现可行性论证（Peter 与 Jihan 观点一致，但尚无落地设计）。
- kind=review：评估 07/12 复用 owner walk 的方案在争用路径上的正确性与复杂度，帮助作者回应 Jihan 的取舍。

## 参考链接
- lore（Jihan LIN 回复）: https://lore.kernel.org/all/d60be130-23eb-4e11-9bb0-1df0ec6ad42e@gmail.com/
- lore（RFC cover，见前作）: https://lore.kernel.org/all/20260917043339.2093426-1-suleiman@google.com/

---
id: sched-20260923-012
subject: 'futex: Make FUTEX_*_PING use Proxy Execution.'
date: '2026-09-23'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: '<20260917043339.2093426-1-suleiman@google.com>'
lore_url: 'https://lore.kernel.org/all/20260917043339.2093426-1-suleiman@google.com/'
authors:
  - 'Suleiman Souhlal'
  - 'John Stultz'
maintainers_involved:
  - 'Peter Zijlstra'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260917043339.2093426-1-suleiman@google.com>'
    date: '2026-09-17'
    summary: 'RFC 00/12：可偷取 futex + Proxy Execution'
    review_outcome: 'Peter 质疑 PI 严格性、要求死锁检测器；Jihan LIN 本日呼应 block 时死锁检测 + -EDEADLK'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - '缺用户态死锁检测器'
    - '新 futex vs mutex 路线未定'
    - 'PI 严格性语义自洽问题'
  next_action: '作者回应死锁检测设计与路线质疑'
contribution_opportunities:
  - kind: discussion
    description: '论证 block 时（sleep 前）死锁检测并返回 -EDEADLK 的实现可行性'
  - kind: review
    description: '评估 07/12 复用 owner walk 在争用路径的正确性与复杂度'
generated_at: '2026-09-24T09:00:00'
source_email_count: 1
related_articles:
  - sched-20260918-011
  - sched-20260917-012
tags:
  - proxy_execution
---