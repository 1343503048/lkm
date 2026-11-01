# sched/deadline: Fix stale rq->dl_server after a server pick returns RETRY_TASK

## TL;DR

Tejun Heo 的 sched/urgent 补丁修复了 `__pick_next_task()` 中 server pick 返回 RETRY_TASK 重启后 `rq->dl_server` 残留的问题。本窗口内作者又补充报告了 core scheduling 的 `pick_next_task()` 中还有三处会留下 stale `rq->dl_server`，原补丁范围需要扩展。

## 背景与问题

原补丁（`[PATCH sched/urgent] sched/deadline: Fix stale rq->dl_server after a server pick returns RETRY_TASK`）覆盖了 non-core 路径 `__pick_next_task()`：dl server pick 返回 RETRY_TASK 并 restart 时，`rq->dl_server` 可能残留。本次窗口内 Tejun 追加报告：core scheduling 的 `pick_next_task()` 还有三种方式会留下错误的 `rq->dl_server`，在 mainline `d89e1d186ec9` 的 SMT VM + fair server 下均能复现。

## 技术方案

三处 core-sched 场景：1) core 全局选择中，cookie pass 通过 `sched_core_find()` 或 forced idle 替换本 CPU 首轮 pick 时，未清除 server pick 设置的 `rq->dl_server`，`put_prev_set_next_task()` 会把 server 交给替换任务（源自 `bd9bbc96e835` "sched: Rework dl_server"，稳定复现）；2) cookie pass 清除每个 sibling 的 `rq_i->core_dl_server`，导致首轮 server pick 幸存的 sibling 从 fast path 无 server 运行（同源，稳定复现）；3) 某个 non-core `__pick_next_task()` 在 `sched_balance_newidle()` 里 drop rq lock 时启用了 core scheduling，`core_pick_in_flight` 只统计 core-path pick，`__sched_core_flip()` 不会等它，sibling 的 core 选择于是对本 rq 跑 `pick_task()` 并设置 `rq->dl_server`，再由 non-core pick 交给 fair class 选中的任务（仅偶发复现，需要 patch 的 2ms 延迟加宽 newidle 窗口 + 循环切换 cookie，即便修复 RETRY_TASK restart 仍会发生）。作者给出三套带 debug 计数器的内核补丁与 stress-ng/coresched 复现脚本（case 1/2/3）。

## 版本演进与当前进展

v1（原补丁，本次窗口外，`<20261030221842.4071610-1-tj@kernel.org>`）覆盖 non-core 路径。本窗口内作者追加三处 core-sched 场景报告，并说明修复应扩展范围。

## Maintainer 意见与讨论焦点

本窗口内未获取到独立 reviewer/maintainer 回帖（作者自述 + 复现脚本）。讨论焦点是 core scheduling + proxy execution 下 `rq->dl_server` 生命周期管理的完整性。

## 合入评估

可能性中等（medium）。原补丁标 sched/urgent，但作者又发现三处 core-sched 残留，范围需扩展后才能完整修复；需等待维护者（Ingo/Peter/Juri 等）对扩展后的方案表态。阻塞项：core-sched `pick_next_task()` 的三处 stale dl_server 尚未纳入修复。

## 效果评估

作者提供三套 debug 计数器与复现脚本，均能稳定（case 1/2）或偶发（case 3）复现 stale `rq->dl_server` 交接；无性能数据（正确性修复）。

## 我可以参与的点

- testing：按作者提供的脚本（SMT 拓扑 + stress-ng + coresched + chrt）在本地复现三处 stale dl_server，验证修复。
- review：评估把 core-sched 路径纳入 `rq->dl_server` 生命周期管理的整体方案。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261030221842.4071610-1-tj@kernel.org/
- Tejun 追加报告: https://lore.kernel.org/all/0de31a5e777c6cafce329dd9571b0049@kernel.org/

---
id: sched-20261101-004
subject: "sched/deadline: Fix stale rq->dl_server after a server pick returns RETRY_TASK"
date: 2026-11-01
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261030221842.4071610-1-tj@kernel.org>"
lore_url: "https://lore.kernel.org/all/20261030221842.4071610-1-tj@kernel.org/"
authors: [Tejun Heo]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261030221842.4071610-1-tj@kernel.org>"
    date: 2026-10-30
    summary: "修复 __pick_next_task() 中 server pick 返回 RETRY_TASK 后的 stale rq->dl_server（non-core 路径）"
    review_outcome: "本窗口内作者追加 core-sched 三处 stale dl_server 场景，范围待扩展"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "core-sched pick_next_task() 还有三处会留下 stale rq->dl_server，原补丁仅覆盖 non-core 路径"
  next_action: "作者需把 core-sched 路径的三处 stale dl_server 纳入修复后重新提交"
contribution_opportunities:
  - kind: testing
    description: "用作者提供的 SMT+stress-ng+coresched 脚本复现三处 stale dl_server"
  - kind: review
    description: "评估把 core-sched 路径纳入 rq->dl_server 生命周期管理的整体方案"
generated_at: "2026-11-02T09:00:00"
source_email_count: 1
related_articles: []
tags: [deadline, dl_server, core_sched, proxy_execution]
---