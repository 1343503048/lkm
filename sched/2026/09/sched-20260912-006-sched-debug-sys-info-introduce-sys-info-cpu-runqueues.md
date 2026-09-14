# sched/debug, sys_info: Introduce SYS_INFO_CPU_RUNQUEUES

## TL;DR
Aaron Tomlin 的 panic 期 per-CPU runqueue 摘要补丁当日完成 v1→v2：kernel test robot 报出 rq->curr 的 __rcu sparse 告警，作者当天致谢（收件 Andrew、Peter）并以 rcu_dereference() 修复发出 v2。人类维护者评审仍未开始。本文为增量更新，v1 分析见 sched-20260911-010。

## 背景与问题
排查内核 panic 时 per-CPU runqueue 与可运行任务状态对诊断 CPU 饥饿、优先级反转很有价值，但 debugfs 内容不会进入自动化 panic/crash dump。补丁新增 SYS_INFO_CPU_RUNQUEUES 与 panic_sys_info 的 cpu_runqueues 开关，sched_show_runqueues()（仿 print_rq()，只输出 running/queued 任务）把 runqueue 摘要直接写进 log_buf。

## 技术方案
（承 sched-20260911-010：trylock + READ_ONCE 回退与 " (contended)" 标注、rcu_read_lock() 保护采样、省略 cgroup path。）v2 相对 v1 的唯一变化：sched_show_runqueues() 中经 rcu_dereference() 访问 rq->curr，消除 microblaze randconfig（W=1 构建）下的 sparse __rcu 地址空间告警（kernel/sched/debug.c 多处 incorrect type in argument/assignment）。

## 版本演进与当前进展
current_version: v2（msgid `<20260912013240.545742-1-atomlin@atomlin.com>`，09-12 09:32 入缓存）。

- v1（09-11）→ kernel test robot 09-12 04:45 报 sparse 告警（akpm-mm/mm-everything 基线，microblaze-randconfig-r132）；
- 09-12 09:00：作者回帖（Hi Andrew, Peter）致谢机器人并预告 v2；
- 09-12 09:32：v2 发出，仅修 __rcu 告警，无功能变化。

## Maintainer 意见与讨论焦点
人类维护者（Andrew、Peter 已被作者点名收件）仍未回复；当日全部推进来自 KTR 告警与作者响应。无分歧记录；panic 路径的 trylock/RCU/printk 洪泛控制论证（v1 分析中列出的评审点）尚待第一轮人类评审。

## 合入评估
likelihood=unknown：构建卫生问题已快速清理，但评审未开始。blocking_issues：零人类 review；panic_sys_info 位分配（0x100）与既有位的冲突检查未见讨论。next_action：等 Andrew（sys_info/lib）与 Peter（sched/debug）两侧的首轮意见。

## 效果评估
暂无效果数据（承 v1：无 panic 输出样张、无高线程数日志体量对比）。

## 我可以参与的点
- kind=testing：开启 panic_sys_info=cpu_runqueues 触发 panic，核对输出、争用标注与高线程数下的 log_buf 体量（承 v1 的验证点，v2 依旧适用）。
- kind=review：v2 后复核 rcu_dereference() 的使用是否落在 rcu_read_lock() 临界区内（panic 上下文的 RCU 读侧语义）。

## 参考链接
- v2 补丁：https://lore.kernel.org/all/20260912013240.545742-1-atomlin@atomlin.com/
- KTR sparse 告警：https://lore.kernel.org/all/202609120421.J3jtss6v-lkp@intel.com/
- 作者致谢回帖：https://lore.kernel.org/all/duj4ijalt7aef7523les6sfqsf7ryhq5quwjoekrtkigws6iyb@2i7ufubk23ws/
- v1 补丁：https://lore.kernel.org/lkml/20260911022844.521413-1-atomlin@atomlin.com/

---
id: sched-20260912-006
subject: 'sched/debug, sys_info: Introduce SYS_INFO_CPU_RUNQUEUES'
date: '2026-09-12'
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: '<20260912013240.545742-1-atomlin@atomlin.com>'
lore_url: 'https://lore.kernel.org/all/20260912013240.545742-1-atomlin@atomlin.com/'
authors:
  - 'Aaron Tomlin'
maintainers_involved: []
current_version: v2
patch_series:
  - version: v1
    msgid: '<20260911022844.521413-1-atomlin@atomlin.com>'
    date: 2026-09-11
    summary: '新增 SYS_INFO_CPU_RUNQUEUES；sched_show_runqueues() panic 时输出 per-CPU runqueue 摘要。'
    review_outcome: 'KTR 报 rq->curr __rcu sparse 告警（microblaze randconfig）；作者当天确认修复方向。'
  - version: v2
    msgid: '<20260912013240.545742-1-atomlin@atomlin.com>'
    date: 2026-09-12
    summary: '经 rcu_dereference() 访问 rq->curr 消除 sparse 告警，无功能变化。'
    review_outcome: '人类维护者（Andrew/Peter 已点名）仍未回复。'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - '零人类 review，panic 路径安全性论证未经评审'
  next_action: '等 Andrew 与 Peter 两侧首轮意见'
contribution_opportunities:
  - kind: testing
    description: '开启 cpu_runqueues 触发 panic 验证输出与高线程数日志体量'
  - kind: review
    description: '复核 v2 的 rcu_dereference 临界区边界'
generated_at: '2026-09-14T12:40:00'
source_email_count: 3
related_articles:
  - 'sched-20260911-010'
tags:
  - sched_debug
---
