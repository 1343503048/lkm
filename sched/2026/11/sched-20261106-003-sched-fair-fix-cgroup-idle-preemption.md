# sched/fair: Fix cgroup::idle preemption

## TL;DR

Peter Zijlstra 发出 3 补丁系列修复 cgroup SCHED_IDLE 任务组的抢占问题：patch 1 用 guard 清理 `sched_group_set_idle()`、patch 2 把 `cfs_rq::idle` 改为「祖先 tg::idle 之和」、patch 3（RFC）携带 Vincent Guittot 的 `sched/eevdf: Fix sched idle task group preemption` 修复并改造为用新的 idle 状态做优化。Kayra Cizmeci 当日密集 revqa：指出 patch 2 存在任务组创建竞态（Peter 确认需 rq->lock 并给了修正版本）、并追问 `se_is_idle()` 对任务路径的处理；Peter 补上「任务策略为空闲 或 所在 cfs_rq 空闲」的判定。方向被认可，但 patch 2 需出 v2、patch 3 的 `find_matching_se()` 仍被 Peter 本人质疑。

## 背景与问题

cgroup 里标为 `idle`（`SCHED_IDLE`）的任务组应当「不抢占、也不抢占别的任务」——但 EEVDF「扁平化后并入单一 runqueue」之后（commit `85570f10a4c6` "sched/eevdf: Move to a single runqueue"），抢占路径解析层级的方式变了，导致 idle 任务组的抢占语义出错：Jakub Okoński 报告了具体失败。Vincent Guittot 此前已发过单独修复（十月迭代多轮），Peter 今天重拾该问题，用一个 LLM 生成的测试用例验证后认为「现在真的能用了」，遂把 Vincent 的补丁放在系列最后、改造为用新的 idle 状态做优化。

## 技术方案

- **Patch 1**（`Use guard in sched_group_set_idle()`）：用 scope-guard 清理锁处理，纯重构，无行为变化，Kayra 直接给 Reviewed-by。
- **Patch 2**（`Make cfs_rq::idle the sum of ancestor tg::idle`）：让 `cfs_rq->idle` 累积整棵子树的 idle 状态，使 `cfs_rq_is_idle()`（`idle > 0`）在「任一祖先 idle」时都成立——这样 task_group 的 idle 属性沿层级向下传播。
- **Patch 3**（RFC，`sched/eevdf: Fix sched idle task group preemption`，From: Vincent）：新增 `find_matching_se()` 把 `se`/`pse` 沿层级上溯到同一父节点下的兄弟实体，再比较二者 idle 状态决定抢占；`wakeup_preempt_sched_idle()` 返回 `PREEMPT_WAKEUP_RESCHED/NONE/PICK` 三种动作。

讨论集中在两处：① Kayra 指出 patch 2 有竞态——新组 GB 在 `sched_create_group()` 与落入父组之间，父组 GA 的 idle 若先置 1 再置 0，会得到「GB idle=-1 而 GA idle=0」的失真状态，`h_nr_idle` 开始腐坏；Peter 确认「你说得对，需要 rq->lock」，并给出把 `cfs_rq->idle` 赋值挪到 `online_fair_sched_group()`（持 rq lock）里的修正 diff。② `se_is_idle()` 目前对任务只看 policy，不看其所在 cgroup 的 idle——Peter 建议改成 `task_has_idle_policy(task_of(se)) || cfs_rq_is_idle(cfs_rq_of(se))`；Kayra 认可「应该能行」，并顺带指出这期间还修掉了 `set_next_buddy()` 的一个相关问题。

## 版本演进与当前进展

*current_version: v1（2026-11-06 发出）*。当日即有一轮密集往返：patch 1 已获 Reviewed-by；patch 2 需按竞态讨论出 v2；patch 3 保持 RFC（Peter 本人「仍在 `find_matching_se()` 上没被说服」，且 Kayra 对 idle 组内非 idle 策略任务的行为有疑问）。

## Maintainer 意见与讨论焦点

Peter Zijlstra（作者兼 sched 维护者）在 cover 里直言：「我还是不认同整个 `find_matching_se()` 的思路——我们把子树标成 idle，本质上是说『别管它』，那再去关心它在某个层级上到底怎么被抢占就很怪」。这是他自己的保留点。Kayra Cizmeci 的意见是建设性的补漏洞（竞态 + 任务路径），并最终认可修正方向。没有出现 NAK。

## 合入评估

*likelihood=medium*。方向正确且是维护者亲自主导、patch 1 已过审、patch 2 竞态有明确修正方向，但 patch 3 的 `find_matching_se()` 未被作者本人完全认可、patch 2 尚需 v2。*blocking_issues*：① patch 2 的任务组创建竞态需随修正出 v2；② patch 3 的 `find_matching_se()` 语义待作者自己敲定。*next_action*：作者出 patch 2/3 的修订版（并入 rq->lock 修正与 `se_is_idle()` 的任务路径处理）。

## 效果评估

作者用 LLM 生成的测试用例验证「现在真的能用了」（cover 原文「It appears to actually work now」），但未附具体数字。patch 3 的 Fixes 指向 `85570f10a4c6` 的回归，Reported-by Jakub Okoński。暂无量化性能数据。

## 我可以参与的点

- **review**：跟进 patch 3 的 `find_matching_se()` 语义——这是 Peter 自己存疑、尚未被他人深挖的点；也可帮忙验证竞态修正后 patch 2 在各 cgroup 层级/热插拔场景下 `h_nr_idle` 的一致性。
- **testing**：用 cgroup 嵌套 + SCHED_IDLE 任务组的场景做压力测试，确认「idle 不抢占、也不被 idle 抢占」的语义在扁平化 runqueue 下成立。

## 参考链接

- lore thread（cover）: https://lore.kernel.org/all/20261105165525.011876858@infradead.org/
- patch 3 所引 Vincent 原修复 lore: https://patch.msgid.link/20261019182622.1584454-1-vincent.guittot@linaro.org（来自补丁正文）

---
id: sched-20261106-003
date: 2026-11-06
subject: "sched/fair: Fix cgroup::idle preemption"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261105165525.011876858@infradead.org>"
lore_url: "https://lore.kernel.org/all/20261105165525.011876858@infradead.org/"
authors: [Peter Zijlstra, Vincent Guittot]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261105165525.011876858@infradead.org>"
    date: 2026-11-06
    summary: "3 补丁：guard 清理 + cfs_rq::idle 祖先求和 + RFC 携带 Vincent 的 idle 组抢占修复。"
    review_outcome: "patch 1 Reviewed-by；patch 2 有竞态需 v2；patch 3 find_matching_se 被作者质疑。"
upstream_commit: null
fixes_commit: "85570f10a4c6"
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "patch 2 的任务组创建竞态需随修正出 v2"
    - "patch 3 的 find_matching_se 语义待作者自己敲定"
  next_action: "作者出 patch 2/3 修订版（并入 rq->lock 与 se_is_idle 任务路径处理）"
contribution_opportunities:
  - kind: review
    description: "深挖 patch 3 find_matching_se 语义，或验证竞态修正后 patch 2 的 h_nr_idle 一致性"
  - kind: testing
    description: "cgroup 嵌套 + SCHED_IDLE 任务组场景压测抢占语义"
generated_at: "2026-11-07T09:00:00+08:00"
source_email_count: 11
related_articles: []
tags: [cfs, eevdf, cgroup]
---