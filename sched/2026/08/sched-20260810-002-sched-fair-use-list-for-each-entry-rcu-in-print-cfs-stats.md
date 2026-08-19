# sched/fair: Use list_for_each_entry_rcu() in print_cfs_stats()

## TL;DR
Aaron Tomlin 提交 v4（5 patches）「sched/debug per-CPU debugfs 文件 + 调试路径多处 UAF/TOCTOU 修复」。修复了 print_cpu/print_dl_rq/sched_show_numa/print_cfs_stats 多处无锁并发读导致的 UAF 与 TOCTOU，并引入 per-CPU debugfs。合入可能性高。

## 背景与问题
调度 debugfs 处理器（print_cpu、print_dl_rq、sched_show_numa、print_cfs_stats）在输出时多处无锁解引用 `rq->curr`、`rq->rd`、`p->mm`、`leaf_cfs_rq_list`，在任务退出 / CPU 热插拔 / cpuset 重分区并发场景下触发 UAF 或 NULL 解引用。

## 技术方案
- Patch1：rq_attach_root() 写端加 `rcu_assign_pointer(rq->rd, rd)` 发布屏障；print_dl_rq 读端 `READ_ONCE(rq->rd)` + RCU 读临界区。
- Patch2：print_cpu 用 `rcu_dereference(rq->curr)` 在 RCU 读临界区内访问（保留 __rcu）。
- Patch3：sched_show_numa 用 `READ_ONCE(p->mm)` 先取本地副本再检查/解引用，消除 TOCTOU。
- Patch4：print_cfs_stats 引入 `for_each_leaf_cfs_rq_rcu()`（list_for_each_entry_rcu），并加硬迭代上限防 RCU stall。
- Patch5：新增 `/sys/kernel/debug/sched/cpu/cpu<N>/debug` per-CPU 文件，离线 CPU 读返回 -ENODEV。

## 版本演进与当前进展
当前 v4（5 patches）。v1→v4 逐步补齐 RCU 标注、writer 端屏障、TOCTOU 修复与迭代上限。v4 8/10 发出。

## Maintainer 意见与讨论焦点
Peter 要求更清晰动机；Zhan 建议离线 CPU 返回 -ENODEV。v4 已吸收这些意见。剩余焦点在迭代上限取值与 RCU 标注风格。

## 合入评估
合入可能性 high。属明确的并发安全修复，风险低。

## 效果评估
暂无 benchmark；修复的是潜在的崩溃/数据竞争，正向安全收益。

## 我可以参与的点
- 评审 print_cfs_stats 迭代上限取值；
- 在 CPU 热插拔+debugfs 并发读取场景做复现/回归验证。

## 参考链接
- lore v3: https://lore.kernel.org/lkml/20260808235522.380038-1-atomlin@atomlin.com/
- lore v4: https://lore.kernel.org/lkml/20260810095822...-1-atomlin@atomlin.com/

---
subject: "sched/fair: Use list_for_each_entry_rcu() in print_cfs_stats()"
id: sched-20260810-002
date: 2026-08-10
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20260808235522.380038-1-atomlin@atomlin.com>"
lore_url: "https://lore.kernel.org/lkml/20260808235522.380038-1-atomlin@atomlin.com/"
authors: [Aaron Tomlin]
maintainers_involved: [Peter Zijlstra, Juri Lelli, Ingo Molnar, Vincent Guittot, Zhan Xusheng]
current_version: v4
patch_series:
  - version: v1
    msgid: "<20260728020309.6169-1-atomlin@atomlin.com>"
    date: 2026-07-28
    summary: "首次引入 per-CPU debugfs 文件，并保护 print_cpu() 对 rq->curr 的无锁解引用。"
    review_outcome: "Peter/Zhan 建议围绕大型 SMP 拓扑的定向交互式调试重新框定动机，并对离线 CPU 返回 -ENODEV。"
  - version: v2
    msgid: "<20260728205238.18447-1-atomlin@atomlin.com>"
    date: 2026-07-28
    summary: "v2 把 print_dl_rq 无锁 rd 访问也纳入 RCU 保护，引入 for_each_leaf_cfs_rq_rcu()。"
    review_outcome: "Zhan 给出 cpu_online 检查等建议。"
  - version: v3
    msgid: "<20260808235522.380038-1-atomlin@atomlin.com>"
    date: 2026-08-08
    summary: "v3 用 rcu_dereference(rq->curr) 替代 READ_ONCE 以保留 __rcu；新增 writer 端 rcu_assign_pointer()。"
    review_outcome: "v3 发出，尚无最终 ack（本日报 08-09 已记录）。"
  - version: v4
    msgid: "<20260810095822...-1-atomlin@atomlin.com>"
    date: 2026-08-10
    summary: "v4（5 patches）：Patch1 修 print_dl_rq UAF（rq->rd RCU 发布屏障+读取侧 READ_ONCE）；Patch2 修 print_cpu UAF（rcu_dereference(rq->curr)）；Patch3 修 sched_show_numa TOCTOU（READ_ONCE(p->mm)）；Patch4 print_cfs_stats RCU 遍历+迭代上限防 RCU stall；Patch5 per-CPU debugfs 文件。"
    review_outcome: "v4 于 8/10 发出，暂无最终 ack。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待 Peter/Juri 对 RCU 标注与迭代上限取值的最终确认。"
contribution_opportunities:
  - kind: review
    description: "评审 print_cfs_stats RCU 迭代上限的取值是否合理（防止 list churn 下 RCU stall）。"
  - kind: testing
    description: "在开启 SCHED_DEBUG 内核上做 CPU 热插拔/cpuset 重分区同时读 debugfs，复现/验证 UAF 修复。"
generated_at: "2026-08-11T00:15:00"
source_email_count: 6
related_articles: ["sched-20260809-001"]
tags: [sched_debug, sched/core, sched/fair]
---
