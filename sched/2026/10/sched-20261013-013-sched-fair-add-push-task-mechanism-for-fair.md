# sched/fair: Add push task mechanism for fair

> **subject**：sched/fair: Add push task mechanism for fair

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261009-004 / 20261010-001：Vincent Guittot 的 18 补丁 v2「Improving latency of short slice tasks」系列引入 fair push 任务机制（把排不上本 CPU 或不该在本 CPU 的任务推到更合适 CPU），短 slice 任务是第一个使用者，cache-aware 调度是后续扩展方向。
- sched-20261012-014：Shrikanth Hegde 对 07/18 提 review；Vincent 澄清「目标是 wakeup 与 push 事件共用同一 select 函数」，并强调 `fair_check_pushable_task` 与 `select_task_rq_fair` 的职责应分离。
- sched-20261013-013（今天）：Chen Yu 确认理解并准备按此调整——`fair_check_pushable_task()` 的检查应保持轻量（它不持 pi_lock、应 best-effort），由 `select_task_rq_fair()` 负责决定迁到哪个 CPU。

## 背景与问题
（承接 20261010-001 / 20261012-014）短 slice 任务在 EEVDF 下仍有时延来源，CFS 也缺类似 RT 的 push 机制；系列引入默认关闭、由使用者触发的 `sched_push_task` 静态分支。设计要点是 `fair_check_pushable_task()`（是否进入深入决策）与 `select_task_rq_fair()`（选目标 CPU）两段职责要分离。

## 技术方案
（承接 20261012-014）今日 Chen Yu 同意了 Vincent 的职责分离意见：`fair_check_pushable_task()` 因不持 `pi_lock`、只能做轻量/尽力而为的判断，真正「迁到哪个 CPU」的决策交给 `select_task_rq_fair()`。Chen Yu 表示「OK, let me adjust the code」，即后续会将 pushable 检查瘦身为轻量判断、把选核下沉到 `select_task_rq_fair()`。

## 版本演进与当前进展
仍为 v2（18 补丁系列），无新版本；今日是 07/18 补丁的 review 收尾——Chen Yu 认领调整，v3 组件在望。

## Maintainer 意见与讨论焦点
- **Vincent Guittot**（维护者/作者）：坚持 `fair_check_pushable_task` 与 `select_task_rq_fair` 职责分离；push 机制为通用件（put_prev + tick 两处 push），短 slice 任务不启用 tick-push。
- **Chen Yu**（cache-aware 方向使用者）：接受意见，将瘦身 pushable 检查、让选核落到 select_task_rq_fair。
- **Shrikanth Hegde**（前日）：对 07/18 提多处 review（static key、context_unsafe_alias、migration-disabled、失败路径）。
- 焦点已收敛到「pushable 检查职责边界」，无 NAK。

## 合入评估
*likelihood=medium*。系列 v3 在望、review 意见已被认领，但主线 18 补丁整体仍处 v2 修订。*blocking_issues*：v3 未发出。*next_action*：Chen Yu/Vincent 落地 v3（pushable 检查瘦身），继续整体系列 review。

## 效果评估
暂无新增数据；本轮为代码结构微调，无 benchmark。

## 我可以参与的点
- review：跟进 v3 中 `fair_check_pushable_task` 的瘦身是否守住「不持 pi_lock 的 best-effort」边界、以及 cache-aware 使用者（Chen Yu 方向）的接法。
- discussion：讨论 cache-aware 作为 push 使用者的迁移路径（wakeup vs push）是否如 Chen Yu 所述存在 task bouncing。

## 参考链接
- 系列 cover lore：https://lore.kernel.org/all/20261002154415.2270586-1-vincent.guittot@linaro.org/
- 07/18 补丁 lore：https://lore.kernel.org/all/20261002154415.2270586-8-vincent.guittot@linaro.org/

---
id: sched-20261013-013
subject: 'sched/fair: Add push task mechanism for fair'
date: 2026-10-13
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20261002154415.2270586-1-vincent.guittot@linaro.org>'
lore_url: 'https://lore.kernel.org/all/20261002154415.2270586-8-vincent.guittot@linaro.org/'
authors:
  - 'Vincent Guittot'
maintainers_involved:
  - 'Vincent Guittot'
current_version: v2
patch_series:
  - version: v2
    msgid: '<20261002154415.2270586-8-vincent.guittot@linaro.org>'
    date: 2026-10-02
    summary: '07/18 引入 fair push 任务机制'
    review_outcome: 'Shrikanth/Chen Yu 参与 review，Chen Yu 认领将 pushable 检查瘦身'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'v3 未发出'
  next_action: 'Chen Yu/Vincent 落地 v3（pushable 检查瘦身），继续系列 review'
contribution_opportunities:
  - kind: review
    description: '跟进 v3 中 pushable 检查 best-effort 边界与 cache-aware 接法'
  - kind: discussion
    description: '讨论 cache-aware 走 wakeup vs push 的 task bouncing 问题'
generated_at: '2026-10-14T01:00:00+08:00'
source_email_count: 1
related_articles:
  - sched-20261010-001
  - sched-20261012-014
tags: [cfs, load_balance]
---