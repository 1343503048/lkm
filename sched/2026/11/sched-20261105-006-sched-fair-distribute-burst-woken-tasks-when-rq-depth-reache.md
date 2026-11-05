# sched/fair: Distribute burst-woken tasks when rq depth reaches 3x average

## TL;DR

李坤宇（Li kunyu）的补丁试图在 wakeup 路径上、当目标 runqueue 深度达到平均 nr_running 的 3 倍时，改用「分布」策略把突发唤醒的任务导流到其它 CPU，避免任务在保证有 idle CPU 可用的情况下仍堆叠到同一 CPU。两位资深 reviewer（Kayra Cizmeci、K Prateek Nayak）给出密集意见（补丁甚至不适用于 mainline），作者正在逐条消化与修订，尚未定型。

## 背景与问题

任务在 burst 唤醒场景下容易集中落在同一 runqueue，即使系统里有 idle CPU。作者目标是在 `select_task_rq_fair()` 的唤醒路径里用「runqueue 深度（nr_running）达到平均深度的 3 倍」作为过载信号，把唤醒任务分散，降低等待延迟。

## 技术方案

补丁在 `select_task_rq_fair()` 里新增 `target_rq = want_affine ? this_rq() : cpu_rq(prev_cpu)` 起手，配合 `rq_burst_overloaded()` 判定（把 `nr_running` 与 `avg_nr_running * 3` 比较），命中时走「分布」分支；作者在修订版里进一步按 `env->cpus` 数量优化统计、并在 `out_balanced` 路径调整 `next_balance` 的赋值（`time_after(next_balance, now)` 时提前 `next_balance = now`）。

Reviewer 的主要技术质疑：

- **Kayra**：补丁对 mainline 不适用（`kernel/sched/fair.c:9972` patch failed）；为何对 `new_cpu` 也做该判定；`span_weight` 是域内全部 CPU 而 `sum_nr_running` 只按 `env->cpus` 统计，口径不一致可能导致误判；`balance_interval` 只在 `LBF_ALL_PINNED` 时被拉长等。
- **Prateek**：建议把 `(avg * 3) >> SCHED_CAPACITY_SHIFT` 预存到 rd 省去每次运算；质疑为何在「没用到 select_idle_sibling 数据时还调用它」；在顶层域上 `avg_nr_running` 长时间不变显得可疑；是否在开码实现 `update_avg()`；建议仅在 `old_avg != new_avg` 时选择性更新，并与 `READ_ONCE(rq->nr_running) << SCHED_CAPACITY_SHIFT` 的比较结果缓存起来。

## 版本演进与当前进展

*current_version: v1（作者已在私仓迭代但未正式发 v2）*。今日进展：作者回复 Kayra 表示已把仓库更新到最新并修复识别到的问题、重做了测试，对 `new_cpu` 复用现有逻辑的取舍尚在权衡；回复 Prateek 表示部分建议已纳入新代码，对 `balance_interval` 的移除与 `next_balance` 调整说明「测试结果相当不错」，并称下一轮测试会继续跟进其余建议。

## Maintainer 意见与讨论焦点

无调度维护者直接表态，但两位活跃的调度 reviewer 给出了非常具体的技术分歧：补丁当前不适用于 mainline（基础错误）；统计口径（`span_weight` vs `env->cpus`、`sum_nr_running`）自洽性问题；`balance_interval`/`next_balance` 改动是否引入副作用；以及重复计算 `avg*3` 的工程化问题。总体方向（用 nr_running 深度分布突发唤醒）未被子否定，但实现距离可评审还有明显差距。

## 合入评估

*likelihood=low*。补丁尚不能 apply 到 mainline，设计细节存在多处口径不一致待作者澄清，且只有一版初稿。*blocking_issues*：① 无法 apply 到 mainline；② span_weight/env->cpus 统计口径不一致；③ balance_interval 改动的必要性未论证。*next_action*：作者发布能 clean apply 的 v2，逐一回应 Kayra/Prateek 的方法论质疑并附 benchmark 数据。

## 效果评估

作者自述「测试结果相当不错」但未给出具体数字，属主观判断，未见测试数据。当前阶段缺乏可量化的延迟/吞吐改进证明。

## 我可以参与的点

- testing：在 burst 唤醒场景（如多生产者唤醒 worker 池）复测该分布策略，提供延迟/吞吐数字（与当前「堆叠到同 CPU」基线对比）。
- review：帮作者厘清 `span_weight`（域全 CPU）与 `env->cpus`（负载均衡候选）的统计口径差异，这直接关系到过载判定是否会误判。

## 参考链接

- lore thread（补丁）: https://lore.kernel.org/all/20261104091842.266273-1-likunyu@open-hieco.net/

---
id: sched-20261105-006
date: 2026-11-05
subject: "sched/fair: Distribute burst-woken tasks when rq depth reaches 3x average"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261104091842.266273-1-likunyu@open-hieco.net>"
lore_url: "https://lore.kernel.org/all/20261104091842.266273-1-likunyu@open-hieco.net/"
authors: [Li kunyu]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261104091842.266273-1-likunyu@open-hieco.net>"
    date: 2026-11-04
    summary: "wakeup 路径按 rq 深度（3x 平均 nr_running）分布突发唤醒任务。"
    review_outcome: "Kayra/Prateek 密集质疑：不能 apply、统计口径不一致、balance_interval 改动未论证。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - "补丁无法 apply 到 mainline"
    - "span_weight 与 env->cpus 统计口径不一致"
    - "balance_interval 改动的必要性未论证"
  next_action: "发布能 clean apply 的 v2 并附 benchmark 数据"
contribution_opportunities:
  - kind: testing
    description: "在 burst 唤醒场景提供延迟/吞吐对比数据"
  - kind: review
    description: "厘清 span_weight 与 env->cpus 统计口径对过载判定正确性的影响"
generated_at: "2026-11-06T09:00:00+08:00"
source_email_count: 4
related_articles: []
tags: [cfs, load_balance]
---