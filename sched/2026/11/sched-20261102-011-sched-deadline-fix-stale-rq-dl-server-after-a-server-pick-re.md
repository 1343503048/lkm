# sched/deadline: Fix stale rq->dl_server after a server pick returns RETRY_TASK

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261101-004：Tejun Heo 的 sched/urgent 补丁修 `__pick_next_task()` 中 server pick 返回 RETRY_TASK 重启后 `rq->dl_server` 残留；随后作者追加 core scheduling 的 `pick_next_task()` 还有三处会留下 stale `rq->dl_server`，原补丁范围待扩展。
- sched-20261102（今天）：SCHED_DEADLINE 维护者 Juri Lelli 回帖澄清——他近期分享的 total_bw 修复系列**不涉及**这个 stale `rq->dl_server` case，等于确认该缺陷的修复仍未有人接手。

## 背景与问题

（承接）原补丁覆盖 non-core 路径 `__pick_next_task()`；作者追加报告 core-sched 的 `pick_next_task()` 三处场景会残留 stale `rq->dl_server`（cookie pass 替换、core_dl_server 清除、non-core pick 启用 core sched 的偶发路径）。今天 Juri 的回复排除了「已由现有 DL 补丁覆盖」的可能，意味着三处 core-sched stale 仍需专门修复。

## 技术方案

（承接）无新代码；原补丁方向（restart 时清 dl_server）不变，core-sched 三处需纳入 `rq->dl_server` 生命周期管理。

## 版本演进与当前进展

v1 未更新；今日为维护者范围澄清。

## Maintainer 意见与讨论焦点

Juri Lelli（SCHED_DEADLINE 维护者）确认自己的 total_bw 系列与该 stale dl_server case 无关，隐含「此事需另作处理」。无 NAK。

## 合入评估

likelihood=medium。修复仍需扩展 core-sched 三处，且尚无最终补丁覆盖；作者（Tejun）需动手或等待。

## 效果评估

（承接）作者在 mainline `d89e1d186ec9` SMT VM + fair server 下复现三处，其中两处稳定、一处偶发。

## 我可以参与的点

- new_patch：把 core-sched 路径的 `rq->dl_server` 清除/恢复补全，形成覆盖三处的完整修复。
- testing：用作者提供的 SMT+stress-ng+coresched 脚本三套复现验证。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261030221842.4071610-1-tj@kernel.org/

---
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261030221842.4071610-1-tj@kernel.org>
authors:
- Tejun Heo
maintainers_involved:
- Juri Lelli
current_version: v1
patch_series: []
merge_assessment:
  likelihood: medium
  blocking_issues:
  - core-sched pick_next_task() 三处 stale rq->dl_server 尚无覆盖补丁
  next_action: 扩展修复覆盖 core-sched 三处后重发
contribution_opportunities:
- kind: new_patch
  description: 补全 core-sched 路径 rq->dl_server 清除/恢复
- kind: testing
  description: 用作者 SMT+stress-ng+coresched 脚本复现三处
upstream_commit: null
fixes_commit: null
merged_branch: null
source_email_count: 1
related_articles:
- sched-20261101-004
tags:
- deadline
- dl_server
- core_sched
id: sched-20261102-011
subject: 'sched/deadline: Fix stale rq->dl_server after a server pick returns RETRY_TASK'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
---
