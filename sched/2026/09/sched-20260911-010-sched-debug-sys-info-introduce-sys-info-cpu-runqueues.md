# sched/debug, sys_info: Introduce SYS_INFO_CPU_RUNQUEUES

## TL;DR
Aaron Tomlin 提出新 patch：给 panic 时的 sys_info 机制新增 cpu_runqueues 开关，panic 时把 per-CPU runqueue 深度与可运行任务直接打进 log_buf，填补「debugfs 有数据但 panic/crash dump 抓不到」的诊断空白。v1 首发，当日无回帖。

## 背景与问题
排查内核 panic 时，per-CPU runqueue 与可运行任务状态对诊断 CPU 饥饿、优先级反转等很有价值；/sys/kernel/debug/sched/debug 能看到，但自动化 panic 或 crash dump 场景拿不到这些内容。把 runqueue 状态直接写入 log_buf 可供事后分析。

## 技术方案
- 新增 SYS_INFO_CPU_RUNQUEUES 位与 panic_sys_info 字符串 token "cpu_runqueues"，用户经 sysctl panic_sys_info 开启；
- kernel/sched/debug.c 新增 sched_show_runqueues()（仿 print_rq()），但只输出 task_on_rq_queued()/task_current() 的任务——与 debugfs 全量 dump 不同，保持 panic 日志精简并防止高线程数系统冲爆 printk ring buffer；
- panic 上下文安全：raw_spin_rq_trylock() + READ_ONCE 回退（拿不到锁标注 " (contended)"）、rcu_read_lock() 保护采样到的 current、省略 cgroup group-path 打印（避免 cgroup_mutex 与 kernfs 遍历）；
- Suggested-by: Rishil Sandip Shah。

## 版本演进与当前进展
*current_version: v1（msgid `<20260911022844.521413-1-atomlin@atomlin.com>`，09-11 10:28 入缓存）*，v1 刚发出、暂无 review 意见。改动面：Documentation/admin-guide/sysctl/kernel.rst、include/linux/sched/debug.h、include/linux/sys_info.h、kernel/sched/debug.c（+70/-13）、lib/sys_info.c。

## Maintainer 意见与讨论焦点
暂无维护者或社区回帖（当日缓存零回复），未获取到任何表态。

## 合入评估
*likelihood=unknown*：无 review 可依据。可参照的事实：作者同日在 sched/isolation 领域活跃，sys_info 框架（lib/sys_info.c 的 SYS_INFO_* 家族）已有多位（blocked_tasks、all_bt 等先例）。*blocking_issues*：panic 路径代码评审标准高（trylock/rcu/printk 洪泛控制都要被细看），尚无维护者意见；与 print_rq() 的代码复用程度（作者选择建模而非复用）可能被问。*next_action*：等待第一轮 review（预计涉及 sched/debug 与 panic/sys_info 两方维护者）。

## 效果评估
暂无效果数据：邮件未附 panic 输出示例的完整样张（diff 上下文可见输出格式），也无高线程数系统上 ring buffer 压力的量化对比；「保持精简、防冲爆」为作者设计主张。

## 我可以参与的点
- kind=testing：在 panic_sys_info=cpu_runqueues 开启的机器上触发 panic（kdump/手动），核对输出完整性、锁争用标注与日志体量，尤其高线程数（数百上千可运行任务）场景是否仍会冲爆 log_buf。
- kind=review：审 panic 上下文的死锁/内存安全论证：trylock 失败路径、rcu_read_lock 内 pr_info 的延迟、省略 cgroup path 是否影响可用性。

## 参考链接
- 补丁：https://lore.kernel.org/all/20260911022844.521413-1-atomlin@atomlin.com/

---
id: sched-20260911-010
subject: 'sched/debug, sys_info: Introduce SYS_INFO_CPU_RUNQUEUES'
date: '2026-09-11'
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: '<20260911022844.521413-1-atomlin@atomlin.com>'
lore_url: 'https://lore.kernel.org/all/20260911022844.521413-1-atomlin@atomlin.com/'
authors:
  - 'Aaron Tomlin'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260911022844.521413-1-atomlin@atomlin.com>'
    date: 2026-09-11
    summary: '新增 SYS_INFO_CPU_RUNQUEUES 与 cpu_runqueues token；sched_show_runqueues() 在 panic 时输出 per-CPU runqueue 摘要（仅 running/queued 任务），trylock + RCU + 省 cgroup path 保证 panic 上下文安全。'
    review_outcome: 'v1 刚发出，当日无回帖。'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - '无任何维护者意见，panic 路径代码评审尚未开始'
  next_action: '等待 sched/debug 与 panic/sys_info 两侧维护者的第一轮 review'
contribution_opportunities:
  - kind: testing
    description: '开启 cpu_runqueues 触发 panic，核对输出、争用标注与高线程数下的日志体量'
  - kind: review
    description: '审 panic 上下文 trylock/RCU/printk 洪泛控制的安全论证'
generated_at: '2026-09-14T11:35:00'
source_email_count: 1
related_articles: []
tags:
  - sched_debug
---
