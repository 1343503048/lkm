# sched/wait: avoid modifying entry on failed priority registration

## TL;DR

Hui Su 修复 `add_wait_queue_priority_exclusive()` 的一个小正确性问题：该函数在检查是否已存在其他 priority waiter 之前就设置了 `WQ_FLAG_EXCLUSIVE` 与 `WQ_FLAG_PRIORITY`，导致注册因 `-EBUSY` 失败时，entry 未被入队却已被修改了 flags。补丁把 flags 更新移到失败检查之后。刚发出，暂无 review。

## 背景与问题

`add_wait_queue_priority_exclusive()` 在「检查 wait 队列头部是否已存在带 `WQ_FLAG_PRIORITY` 的 waiter」这一失败检查之前，就先对入参 `wq_entry` 设置 `WQ_FLAG_EXCLUSIVE | WQ_FLAG_PRIORITY`。于是当队列里已有 priority waiter、函数返回 `-EBUSY` 时，调用方的 entry 被留下未入队、但其 flags 已被修改——如果调用方后续复用该 entry，可能带着本不该有的 `EXCLUSIVE/PRIORITY` 标志。这是代码质量问题而非崩溃类缺陷，属于失败路径上的副作用。

## 技术方案

把 `wq_entry->flags |= WQ_FLAG_EXCLUSIVE | WQ_FLAG_PRIORITY` 这行从锁外移到「`-EBUSY` 失败检查之后、`list_add()` 之前」，使被拒绝的注册不再无谓地修改 entry。`kernel/sched/wait.c` 1 文件，+1/−2。

## 版本演进与当前进展

v1 刚发出（2026-10-11），暂无 review 意见。

## Maintainer 意见与讨论焦点

无。暂未见表态。

## 合入评估

*likelihood=medium*。改动极小且方向明确（失败路径不产生副作用），但刚发出、无维护者 review。*blocking_issues*：无 review（刚发出）。*next_action*：等 sched 维护者 review 收取。

## 效果评估

无性能数据。作者用私有 x86_64/QEMU differential oracle 验证：旧路径在 `-EBUSY` 时会修改 entry flags，打补丁后 flags 保持不变——仅行为正确性验证，无数字。

## 我可以参与的点

- `review`：核对 `add_wait_queue_priority_exclusive()` 的现有调用方是否有依赖「失败时 flags 已被设置」的行为（从语义看不太可能，但可确认）。
- `testing`：在真实 waitqueue 场景下复测 `-EBUSY` 路径 entry flags 是否保持不变。

## 参考链接

- lore（本补丁）: https://lore.kernel.org/all/20261011015019.4056529-1-sh_def@163.com/

---
id: sched-20261011-002
date: '2026-10-11'
subject: 'sched/wait: avoid modifying entry on failed priority registration'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20261011015019.4056529-1-sh_def@163.com>'
lore_url: 'https://lore.kernel.org/all/20261011015019.4056529-1-sh_def@163.com/'
authors:
  - 'Hui Su'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20261011015019.4056529-1-sh_def@163.com>'
    date: '2026-10-11'
    summary: '把 WQ_FLAG_EXCLUSIVE|WQ_FLAG_PRIORITY 的设置移到 -EBUSY 失败检查之后'
    review_outcome: '暂无 review'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - '无 review（刚发出）'
  next_action: '等 sched 维护者 review 收取'
contribution_opportunities:
  - kind: review
    description: '核对现有调用方是否依赖失败时 flags 已被设置的行为'
  - kind: testing
    description: '在真实 waitqueue 场景复测 -EBUSY 路径 entry flags 保持不变'
generated_at: '2026-10-12T01:00:00'
source_email_count: 1
related_articles: []
tags:
  - wait
---
