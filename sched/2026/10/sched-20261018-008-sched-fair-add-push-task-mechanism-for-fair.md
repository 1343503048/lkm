# sched/fair: Add push task mechanism for fair

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261009-004 / 20261010-001：Vincent Guittot 的 18 补丁 v2「Improving latency of short slice tasks」系列引入 fair push 任务机制（把排不上本 CPU 或不该在本 CPU 的任务推到更合适 CPU），短 slice 任务是首个使用者，cache-aware 调度是后续扩展方向。
- sched-20261012-014：Shrikanth Hegde 对 07/18 提 review；Vincent 澄清「wakeup 与 push 共用同一 select 函数」，强调 `fair_check_pushable_task` 与 `select_task_rq_fair` 职责分离。
- sched-20261012-015：Kayra 质疑 10/18 tick-push 路径看似「有意不生效」；Vincent 澄清 push 是通用件（put_prev + tick 两处），短 slice 任务不用 tick-push，tick-push 留给 misfit/EAS/cache-aware。
- sched-20261013-013：Chen Yu 确认理解并准备把 pushable 检查瘦身、选核下沉到 `select_task_rq_fair()`。
- sched-20261014-011：Vincent 逐条回答 Shrikanth（IBM）对 07/18 的细节疑问（调用频率、static key、skip current、变量命名）。
- sched-20261015-016：Shrikanth 用 clang-23 线程安全分析报告 07/18 的锁注解问题；Vincent 回应补 `__releases`/`__acquires` 注解。
- sched-20261018-008（今天）：Kayra Cizmeci 对整个系列再 review，针对 07/18 提一个 proxy exec 交互的问题——curr（持 mutex 的 fair 任务）可能被加进 pushable 列表而它仍是 current，质疑「curr 是否不该被 push」。

## 背景与问题

（承接 20261009-004 → 20261015-016）短 slice 任务在 EEVDF 下仍有时延来源，CFS 缺类似 RT 的 push 机制；系列引入默认关闭、由使用者触发的 `sched_push_task` 静态分支，设计要点是 `fair_check_pushable_task()`（轻量是否深入）与 `select_task_rq_fair()`（选目标 CPU）两段职责分离。今天 Kayra 对 07/18 与 proxy execution 备选的交互提出质疑。

## 技术方案

（承接）今日无新代码，是 Kayra 对整个系列（含 proxy exec 相关补丁）的再 review，指出现象：

在 rq 上有 fair 任务 TA 持有 mutex M、RT 任务 TB 阻塞在 M 上。进入 `__schedule()` → `pick_next_task()` 选出 TB 为 next，但把 TA 加进 pushable 任务列表；随后进入 proxy exec 路径，donor 设为 TB，但进 `find_proxy_task()` 时 next 被改成 TA。于是 TA 仍在 push 列表上，尽管它仍是 curr。Kayra 问「Am I missing something? Should curr not be pushed?」——即 pushable 列表里是否不应包含当前正在运行的 curr（会与自己迁移冲突）。此为对 07/18 的质疑，尚待 Vincent 回应。

## 版本演进与当前进展

*current_version: v2*（系列仍为 18 补丁 v2，见 related 010-001）。今日为 review 问答的延续，无新版本发出。

## Maintainer 意见与讨论焦点

Kayra Cizmeci（资深 reviewer，此前对 10/18 tick-push 提过质疑）今天把矛头转向 07/18 与 proxy exec 的交互：pushable 任务列表的成员判定在 proxy 场景下是否会把 curr 本身（TA）错误纳入，从而与「curr 不该被 push」的既有语义冲突。该问题与系列配套的 proxy exec 改动的 `find_proxy_task()` 流程耦合，属尚未解决的分歧，等待 Vincent 澄清。

## 合入评估

*likelihood=medium*。系列已迭代多版、多位 reviewer（Shrikanth/Chen Yu/Kayra）持续密集 review，方向获认可但尚未收敛：今天 Kayra 又抛出 proxy exec 下 curr 进入 push 列表的语义问题，说明 07/18 与 proxy 路径的边界仍需澄清。*blocking_issues*：curr 是否应进 pushable 列表（proxy exec 场景）、既有锁注解与检查瘦身未完全收尾。*next_action*：Vincent 回应 Kayra 的 proxy exec 疑问并视需要改版。

## 效果评估

本系列目标是短 slice 任务时延优化（效果数据见 20261009-004 的原始 benchmark）；今日无新 benchmark，纯 review 问答。

## 我可以参与的点

- `review`：proxy exec 下 pushable 列表成员判定（curr 不应被 push）是今天的开放问题，可帮忙分析 07/18 的 `fair_check_pushable_task()`/`find_proxy_task()` 交互并提供反例或确认。
- `discussion`：对「push vs wakeup 迁移」的任务 bouncing（见 20261010-001）迟迟未闭环，可用最新内核复查 bouncing 是否仍存在。

## 参考链接

- 系列封面信：https://lore.kernel.org/all/20261002154415.2270586-1-vincent.guittot@linaro.org/
- Kayra Cizmeci 今日再 review（07/18）：https://lore.kernel.org/all/atRseHwvpRJGtjIy@scheduler.schedules/

---
id: sched-20261018-008
date: 2026-10-18
subject: "sched/fair: Add push task mechanism for fair"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261002154415.2270586-1-vincent.guittot@linaro.org>"
lore_url: "https://lore.kernel.org/all/20261002154415.2270586-1-vincent.guittot@linaro.org/"
authors: ["Vincent Guittot"]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v2
    msgid: "<20261002154415.2270586-1-vincent.guittot@linaro.org>"
    date: 2026-10-09
    summary: "18 补丁：EEVDF 改进 + fair push 机制 + EAS slice 整合，短 slice 任务为首个使用者"
    review_outcome: "Shrikanth/Chen Yu/Kayra 多轮 review，职责分离与锁注解逐步收敛"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["proxy exec 下 curr 进入 pushable 列表的语义待澄清", "检查瘦身与锁注解未完全收尾"]
  next_action: "Vincent 回应 Kayra 的 proxy exec 疑问并视需要改版"
contribution_opportunities:
  - kind: review
    description: "分析 07/18 的 fair_check_pushable_task() 与 find_proxy_task() 交互，确认 curr 不应被 push"
  - kind: discussion
    description: "用最新内核复查 push vs wakeup 迁移的 task bouncing 是否仍存在"
generated_at: "2026-10-19T09:00:00"
source_email_count: 1
related_articles: ["sched-20261010-001", "sched-20261012-014", "sched-20261012-015", "sched-20261013-013", "sched-20261014-011", "sched-20261015-016"]
tags: [cfs, eevdf, load_balance]
---