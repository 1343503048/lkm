# tools/sched_ext: Increment nr_queued when a task is queued to user space

## TL;DR
Wanwu Li（麒麟）的 `scx_userland` 示例调度器修复（1/3）：`enqueue_task_in_user_space()` 从未递增 `nr_queued`，导致 `userland_update_idle()` 里「`if (nr_queued || nr_scheduled)`」的 idle 唤醒判定永远退化为只看 `nr_scheduled`——坐在 enqueued map 里、尚未被用户态调度器 drain 的任务对即将 idle 的 CPU 不可见。补丁在 push 成功时递增 `nr_queued`（用户态侧已按文档在 drain 后清零）。带 `Fixes:`。

## 背景与问题
`tools/sched_ext/scx_userland` 里 `userland_update_idle()` 决定「CPU 要 idle 时是否唤醒用户态调度器」，条件是 `if (nr_queued || nr_scheduled)`。文档（变量声明与 `userland_update_idle()` 的 NOTE）都写着 `nr_queued` 应由 BPF 组件在任务入队到用户空间时递增，但 `enqueue_task_in_user_space()` 从未这样做——成功的 push 只递增了统计计数器 `nr_user_enqueues`，于是 `nr_queued` 恒为 0，条件静默退化为只看 `nr_scheduled`。后果：停留在 enqueued map、尚未被用户态调度器 drain 的任务，对即将 idle 的 CPU 不可见，可能错过该唤醒用户态调度器去处理它们的时机。

## 技术方案
在 `enqueue_task_in_user_space()` 的 push 成功分支（非 `SCX_DSQ_GLOBAL` 直插分支）里，除了 `__sync_fetch_and_add(&nr_user_enqueues, 1)` 之外，新增 `__sync_fetch_and_add(&nr_queued, 1)`。用户态侧已按文档在 map 被 drain 后清零 `nr_queued`，因此无需在用户态侧再改。1 行改动（tools/sched_ext/scx_userland.bpf.c）。

## 版本演进与当前进展
v1 本日发出（系列 1/3，thread root `<20260924143659.268595-1-liwanwu@kylinos.cn>`），本日未见 review 回复。

## Maintainer 意见与讨论焦点
本日无维护者/资深成员回复。属示例调度器 `scx_userland` 的工具侧缺陷修复，作者自证了 `nr_queued` 恒 0 的退化路径。

## 合入评估
*likelihood=medium*。问题清晰、修复 1 行且与文档语义一致；但属 tools/sched_ext 示例调度器的正确性修复，尚未见 Tejun Heo 等 sched_ext 维护者表态。*blocking_issues*：无明确反对，待维护者 review。*next_action*：Tejun/Andrea 等 sched_ext 维护者审阅后收取。

## 效果评估
无量化数据；正确性修复——恢复 `nr_queued` 的记账，让 idle 判定按文档设计工作，避免「已入队待 drain 的任务对 idle CPU 不可见」的漏判。

## 我可以参与的点
- kind=review：核对 `nr_queued` 递增点是否覆盖所有入队到用户空间的路径（尤其 `SCX_DSQ_GLOBAL` 直插分支是否需要同样处理），以及用户态清零时机与递增是否配对。
- kind=testing：跑 `scx_userland` 示例调度器，验证 CPU idle 时的唤醒行为在修复前后一致且无漏唤醒。

## 参考链接
- lore thread (patch 1/3): https://lore.kernel.org/all/20260924143659.268595-2-liwanwu@kylinos.cn/

---
id: sched-20260924-006
date: '2026-09-24'
subject: 'tools/sched_ext: Increment nr_queued when a task is queued to user space'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20260924143659.268595-1-liwanwu@kylinos.cn>'
lore_url: 'https://lore.kernel.org/all/20260924143659.268595-2-liwanwu@kylinos.cn/'
authors:
  - 'Wanwu Li'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260924143659.268595-1-liwanwu@kylinos.cn>'
    date: '2026-09-24'
    summary: 'push 成功时递增 nr_queued，恢复 idle 判定'
    review_outcome: '暂无 review 回复'
upstream_commit: null
fixes_commit: 'cc4448d0856d'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: 'sched_ext 维护者审阅后收取'
contribution_opportunities:
  - kind: review
    description: '核对 nr_queued 递增点覆盖与用户态清零配对'
  - kind: testing
    description: '跑 scx_userland 验证 idle 唤醒行为无漏唤醒'
generated_at: '2026-09-25T09:00:00'
source_email_count: 1
related_articles: []
tags:
  - sched_ext
---