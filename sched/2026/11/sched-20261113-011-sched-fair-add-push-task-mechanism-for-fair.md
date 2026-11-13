# sched/fair: Add push task mechanism for fair

## TL;DR
本文为增量更新，完整脉络见下。

- sched-20261106-002：Vincent Guittot 的 v3 大系列（20 补丁）改进短 slice 任务调度延迟；dragonboard rb5 上 4 短任务同时醒来平均延迟约 1051us→61us。
- sched-20261107-004 / 20261112-015：Kayra 评审 02-06 给 Reviewed-by；Peter 提议把 `cfs_tasks` 做成 RB-tree 或 augmented list（按 `{slice, exec_start}` 排序），Vincent 回应可用 RB 树并愿在下一版加 slice 排序；02/20 的 DEQUEUE_CLASS 问题被确认。
- sched-20261113-011（今天）：**Li kunyu 追问 08/20 与 13/20 里的类比较应为 `sched_class_above()` 语义、以及 push 是否应移入 load balance 路径**，Vincent 逐条回应；**kernel test robot（lkp）报 12/20 在 nios2 allnoconfig W=1 构建下出 warning**。

## 背景与问题
（承接 20261106-002 … 20261112-015）短 slice 任务在 EEVDF 下因 slice 短、lag 反复累积排不上队，多任务同时醒来堆叠同一 idle CPU。Vincent 的 v3 用「正 lag 衰减 + 选 CPU 考虑 slice + fair 类 push 回调」解决。今日收口在两个子问题：push 触发点的类判断语义，与 push 决策应放 hot path 还是 load balance。

## 技术方案
- **08/20 `sched/fair: Add push task mechanism for fair`**：Li kunyu 指出 `if (next->sched_class != &fair_sched_class)` 会把「next 不是 fair 类」时把所有 CFS 任务都迁移，语义上应只在 next 类**严格高于** fair 时才成立，建议改 `sched_class_above(next->sched_class, &fair_sched_class)`。Vincent 回应：想找的是「把 prev 放回 runnable 列表时更好的 CPU」；next 是 fair 类则在 `set_next_task_fair()` 里排队回调，next 不是 fair 则立刻排（切换后再执行），并补充「严格更高是多数情况，但存在 sched_ext 的 dl server 抢占 fair 任务的情形」。
- **13/20 `sched/eevdf: Try to push short slice task on a better CPU`**：Li kunyu 质疑在 CFS hot path（`put_prev_task_fair()`/`set_next_task_fair()`）做 push 是否合适、能否移入 load balance 路径。Vincent 明确回应 LB 不合适（LB 周期长于调度约束、EAS 关闭 LB、periodic LB 只看 CPU 不逐任务、push 是按任务即时响应），并补充 Chen Yu 正在用该 push 机制做 cache-aware scheduling。
- **12/20 `sched/fair: Support not wakeup case in select_idle_sibling`**：lkp 报 nios2 allnoconfig W=1 构建 warning（未被合入前需修）。

## 版本演进与当前进展
v3 系列（20261106）→ 今日继续 patch 级评审。无新版本，但 08/20 与 13/20 的类判断语义、push 放置位置进一步明确，12/20 有构建 warning 待修。

## Maintainer 意见与讨论焦点
- **Vincent Guittot（作者）**：正面回应类判断与 LB 放置的疑问，确认「push 按任务、即时响应」是设计意图，不在 LB 做。
- **Li kunyu（外部评审）**：两处追问（`sched_class_above()` 语义、hot path 成本），无 NAK。
- **kernel test robot**：12/20 构建 warning。
- 无 NAK；pending 项为 12/20 的构建 warning 修正与下一版 slice 排序实现。

## 合入评估
系列活跃推进、设计意图逐渐清晰，但仍有构建 warning 与待实现（slice 排序），合入概率中等；lee 到 warning 修复与下一版。

## 效果评估
此前测得 rb5 上 4 短任务同时醒来平均延迟约 1051us→61us（承接 20261106-002）；今日无新 benchmark。

## 我可以参与的点
- **review**：核对 `sched_class_above()` 是否覆盖「sched_ext dl server 抢占 fair」的全部非对称场景。
- **testing**：在其它板卡/架构复现 lkp 的 nios2 构建 warning，或验证 08/20/13/20 push 行为。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261106151947.3991524-1-vincent.guittot@linaro.org/
- lkp 构建 warning（12/20）: https://lore.kernel.org/all/202611131321.iXTrhEmV-lkp@intel.com/

---
id: sched-20261113-011
subject: "sched/fair: Add push task mechanism for fair"
date: 2026-11-13
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261106151947.3991524-1-vincent.guittot@linaro.org>"
lore_url: "https://lore.kernel.org/all/20261106151947.3991524-1-vincent.guittot@linaro.org/"
authors: [Vincent Guittot]
maintainers_involved: [Vincent Guittot, Li kunyu]
current_version: v3
patch_series:
  - version: v3
    msgid: "<20261106151947.3991524-1-vincent.guittot@linaro.org>"
    date: 2026-11-06
    summary: "20 补丁：正 lag 衰减 + slice 选 CPU + fair push 回调"
    review_outcome: "Kayra Reviewed-by 02-06；Peter 提议 cfs_tasks RB-tree；今日明确类判断与 push 放置"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "12/20 存在 nios2 allnoconfig W=1 构建 warning"
    - "下一版需实现 slice 排序"
  next_action: "修 12/20 构建 warning，发下一版实现 slice 排序"
contribution_opportunities:
  - kind: review
    description: "核对 sched_class_above() 覆盖 sched_ext dl server 抢占 fair 场景"
  - kind: testing
    description: "复现/验证 lkp 构建 warning 与 push 行为"
generated_at: "2026-11-14T01:30:00"
source_email_count: 5
related_articles: [sched-20261106-002, sched-20261107-004, sched-20261109-002, sched-20261110-010, sched-20261111-009, sched-20261112-015]
tags: [eevdf, cfs]
---