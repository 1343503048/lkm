# sched/eevdf: Move to a single runqueue

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20260923-001 / 20261007-009：Aishwarya Rambhadran（ARM）报告 v7.2→v7.3 在 AWS Graviton3 上个别 schbench 线程配置 p99 回退 ~30%，bisect 指向「sched/eevdf: Move to a single runqueue」commit；后续怀疑点收敛到 WA_WEIGHT/task_h_load。
- sched-20261012-022：Mike Galbraith 以 7.2+flat 对照观察到 cgroup vs cgroup 的 CPU 分配抖动被放大，但未给数字。
- sched-20261016-002：Jakub Okoński 给出可复现的量化回归——单运行队列疑似破坏 `cpu.idle` cgroup 的 wakeup preemption 语义，wakelat p99 从 12µs 恶化到 2029µs。
- sched-20261018-009：Mike Galbraith 定位到他观察到的那条抖动与 single-runqueue 无关，而来自延迟实体 requeueing 修正 `333238da9a19`。
- sched-20261020-003（今天）：Vincent Guittot 把 `cpu.idle` 抢占修复以内联补丁发到本线程征求 Jakub/Mike 测试，并随后独立成篇（`sched/eevdf: Fix sched idle task group preemption`，本日 001）；Jakub 确认该修复修好了 cpu.idle 用例，但同 cgroup 的 nice 19 spinner 相对 7.2.9 仍回退、且全部 cgroup_mode 均复现。Vincent 将 nice 19 场景划为另行排查。

## 背景与问题

（承接 20260923-001/20261007-009/20261012-022/20261016-002/20261018-009）单运行队列改动落地 v7.3 后，社区持续追查 schbench/wakelat 的 p99 尾延迟回退。此前已分流为两条线索：一是 Mike Galbraith 定位到与 single-runqueue 无关的 `333238da9a19`（延迟实体 requeueing 前更新时间）；二是 remaining 的「sched_idle 任务组抢占」问题——单运行队列下扁平层级把所有 runnable 任务放进同一 cfs_rq，`wakeup_preempt_fair()` 直接比较 `se_is_idle(se/pse)` 而不再沿 task group 层级确认 sched_idle 组。

今天这条线程聚焦第二条线索：Vincent Guittot 回复 Mike Galbraith 的观察，明确「是的，我们没有考虑任务组是否是 sched_idle」，并贴出 80 行内联补丁请 Jakub、Mike 测试。

## 技术方案

（承接，今日以定位与验证为主，方案已独立成篇为 001 补丁）Vincent 的修复要点：新增 `find_matching_se()` 把两个 sched_entity 对齐到「共同父级的兄弟实体」层级，再以 `se_is_idle()` 判定 idle 属性，据此决定 wakeup 抢占走向（idle 让位非 idle → RESCHED；非 idle 让位 idle → NONE；两侧同类 → 走原 EEVDF 判定）。

Jakub 今日给出的验证结论：该修复修好了其 `cpu.idle` 测试用例，但「在 7.3.0 之上、同 cgroup 放一个 nice 19 spinner」时仍相对 7.2.9 回退——他认为「不完整」。Vincent 回应：此补丁只针对 sched_idle 组场景、nice 19 会另行细看，并反询是否已测过不同 `cgroup_mode` 下的 nice 19。Jakub 补充：nice 19 测试在 up/smp/concur/max/tasks 全部模式下结果一致（仍回退）。Vincent 收尾「Okay，多谢测试结果」。

## 版本演进与当前进展

*current_version: null*（系列已合入，本日为回归定位与修复验证，无新补丁版本）。

## Maintainer 意见与讨论焦点

Vincent Guittot（sched 维护者）主导修复：确认「未考虑 sched_idle 任务组」是根因，贴出内联补丁并组织测试。分歧点被明确划出：nice 19 同 cgroup 场景的回退**不属于**本次 sched_idle 修复范围，作者「会另行 closer look」。报告人 Jakub Okoński 认为按 7.2.9 基线看修复「不完整」，并要求返回类型为 `enum preempt_wakeup_action`（已随 v2 修正）。尚无数值化的 nice 19 回退幅度。

## 合入评估

*likelihood=merged*（针对 single-runqueue 系列本身：已合入主线并随 v7.3 出货）。今日进展是它的后续回归处理：sched_idle 组抢占缺口已由 Vincent 的修复补丁（本日 001）解决。*blocking_issues*：nice 19 同 cgroup 回退仍未解决（跨全部 cgroup_mode 复现），待 author 跟进。*next_action*：Vincent 另发补丁排查 nice 19 回退。

## 效果评估

今日为定性验证：Jakub 确认修复使 `cpu.idle` 用例恢复正常；此前其报告（20261016-002）给出 wakelat p99 12µs→2029µs 的量化锚点。nice 19 相对 7.2.9 的回退幅度数字今日未给出（仅「仍回退」）。修复本身无性能数据，属抢占正确性修复。

## 我可以参与的点

- `testing`：复现 nice 19 同 cgroup 回退并给出相对 7.2.9 的量化对比（up/smp/concur/max/tasks 各 cgroup_mode），补上今天缺失的数据。
- `review`：核对 `find_matching_se()` 对多层 task group 层级对齐、以及 `se_is_idle()` 判定在 flat hierarchy 下的正确性。

## 参考链接

- 系列根线程：https://lore.kernel.org/all/20260605105513.354837583@infradead.org/
- Vincent 今日内联修复 + 讨论：https://lore.kernel.org/all/atZM6uF0CqCNh__I@vingu-cube/
- 修复补丁独立成篇：https://lore.kernel.org/all/20261019182622.1584454-1-vincent.guittot@linaro.org/

---
id: sched-20261020-003
date: 2026-10-20
subject: "sched/eevdf: Move to a single runqueue"
subsystem: sched
type: discussion
status: merged_stable
severity: none
thread_root_msgid: "<20260605105513.354837583@infradead.org>"
lore_url: "https://lore.kernel.org/all/20260605105513.354837583@infradead.org/"
authors: ["Peter Zijlstra"]
maintainers_involved: ["Vincent Guittot"]
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: merged
  blocking_issues: ["nice 19 同 cgroup 场景相对 7.2.9 回退仍未解决（跨全部 cgroup_mode 复现）"]
  next_action: "Vincent 另发补丁排查 nice 19 回退；sched_idle 组场景已由本日 001 修复"
contribution_opportunities:
  - kind: testing
    description: "复现 nice 19 同 cgroup 回退并给出相对 7.2.9 的量化对比"
  - kind: review
    description: "核对 find_matching_se() 层级对齐与 se_is_idle() 在 flat hierarchy 下的正确性"
generated_at: "2026-10-21T01:30:00"
source_email_count: 5
related_articles: ["sched-20261007-009", "sched-20261012-022", "sched-20261016-002", "sched-20261018-009"]
tags: [eevdf, regression]
---