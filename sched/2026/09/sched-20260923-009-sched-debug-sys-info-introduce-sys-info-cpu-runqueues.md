# sched/debug, sys_info: Introduce SYS_INFO_CPU_RUNQUEUES

## TL;DR
本文为增量更新，完整背景见 sched-20260912-006（v2）。Peter Zijlstra 与 Petr Mladek 终于开始了对这个 panic 期 per-CPU runqueue 摘要补丁的首轮人类评审：Peter 要求给「这些路径必须远离 rq->lock」加上注释/注解、并质疑是否真需要这个功能（kdump 也可只 dump 内核数据结构）；作者 Aaron Tomlin 逐条回应，坚持 `raw_spin_rq_trylock()` 非阻塞路线，并说明面向生产支持（kdump 未配/截断时 dmesg 是唯一诊断物）。likelihood 从 unknown 转 low/unknown。

## 背景与问题
背景见 sched-20260912-006：排查 panic 时 per-CPU runqueue 与可运行任务状态对诊断 CPU 饥饿/优先级反转很有价值，但 debugfs 不进自动化 panic dump。补丁新增 `SYS_INFO_CPU_RUNQUEUES` 与 `panic_sys_info=cpu_runqueues` 开关，`sched_show_runqueues()` 把 runqueue 摘要写进 log_buf。

## 技术方案
方案不变（承 v2）：`sched_show_runqueues()` 只调 `print_rq(NULL, rq, cpu, false, true)`（不调会无条件拿 `rq->lock` 的 `print_cpu()`），`print_rq()` 内仅在 `rcu_read_lock()` 下遍历线程并 `print_task()`，全程不再拿 `rq->lock`；用 `raw_spin_rq_trylock()` 保证非阻塞，争用队列标注 `(contended)`。

## 版本演进与当前进展
- v2（09-12）后，本日进入首轮人类评审（Peter Zijlstra、Petr Mladek），无新版。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**：① 要求给这些路径加注释/注解说明「必须远离 rq->lock」，太容易被人后来加上；② 质疑「拦着你不开 kdump 的是啥」——crash dump 可配置成只 dump 内核数据结构、比全量内存 dump 经济得多；③ 自我定位「mostly I just worry about death by a thousand cuts」，非强烈反对，只是不确定是否真需要。
- **Petr Mladek**（据作者回帖反推）：要求 `print_rq()` 补 banner 行、对 trylock 使用点提出疑问。
- **Aaron Tomlin（作者）**：说明场景是「kdump 未配 / vmcore 截断或失败时，dmesg（pstore/serial）常是唯一存活诊断物」；澄清 `print_rq()` 不调 `print_cfs_stats()`（那是 `print_cpu()` 的、无条件拿 `rq->lock` 的部分）；坚持 trylock 对所有 `__sys_info()` 调用者（NMI hardlockup / hardirq softlockup / khungtaskd，此时 `oops_in_progress=0`）都是必需的，无条件 `raw_spin_rq_lock()` 会自死锁/AB-BA 死锁；`trylock` + `(contended)` 标注已足够；改动严格限于 `kernel/sched/debug.c`、复用 `print_rq()`/`print_task()` 与两个 flag。

## 合入评估
likelihood=low。首轮人类评审刚启动，Peter 对「是否真需要」仍持保留（虽非强烈反对），并新增「rq->lock 路径需加注释防退化」的要求。blocking_issues：Peter 的「是否需要」质疑未消解；需补 rq->lock 路径注释；Andrew（sys_info/lib）侧仍未表态。next_action：作者补注释并进一步论证存在必要性，回应 Peter 的 kdump 经济性论点。

## 效果评估
无 panic 输出样张、无高线程数日志体量对比（承前作）。本日为「是否值得合入」的定性讨论。

## 我可以参与的点
- kind=review：评估「kdump 可只 dump 内核结构」这一论点下，`SYS_INFO_CPU_RUNQUEUES` 在无 kdump 生产环境的不可替代性，帮助作者回应 Peter。
- kind=testing：开启 `panic_sys_info=cpu_runqueues` 触发 panic，核对输出、`(contended)` 标注与高线程数下的 log_buf 体量。

## 参考链接
- lore（Peter Zijlstra 回复）: https://lore.kernel.org/all/20260923083753.GB4121339@noisy.programming.kicks-ass.net/
- lore（作者回应 Peter，含 Petr 意见反推）: https://lore.kernel.org/all/rqph2yaqdxyu4dmwddmdcakiacmyumjh7adxdl2a6ibjc6wwi4@55oxsrrgjuaw/
- lore（作者回应 Petr）: https://lore.kernel.org/all/uccrrdkyufnfhjer5lapd24dastzq7pkc4qhujn3jcbs4nnpxl@fzvxux6wtmef/
- lore（v2 补丁）: https://lore.kernel.org/all/20260912013240.545742-1-atomlin@atomlin.com/

---
id: sched-20260923-009
subject: 'sched/debug, sys_info: Introduce SYS_INFO_CPU_RUNQUEUES'
date: '2026-09-23'
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: '<20260912013240.545742-1-atomlin@atomlin.com>'
lore_url: 'https://lore.kernel.org/all/20260912013240.545742-1-atomlin@atomlin.com/'
authors:
  - 'Aaron Tomlin'
maintainers_involved:
  - 'Peter Zijlstra'
current_version: v2
patch_series:
  - version: v1
    msgid: '<20260911022844.521413-1-atomlin@atomlin.com>'
    date: '2026-09-11'
    summary: '新增 SYS_INFO_CPU_RUNQUEUES；sched_show_runqueues() panic 时输出 per-CPU runqueue 摘要'
    review_outcome: 'KTR 报 __rcu sparse 告警'
  - version: v2
    msgid: '<20260912013240.545742-1-atomlin@atomlin.com>'
    date: '2026-09-12'
    summary: '经 rcu_dereference() 访问 rq->curr 消除 sparse 告警'
    review_outcome: 'Peter/Petr 首轮人类评审：需补 rq->lock 路径注释，Peter 质疑必要性'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - 'Peter 对存在必要性的质疑未消解'
    - '需补 rq->lock 路径注释防退化'
    - 'Andrew（sys_info 侧）未表态'
  next_action: '作者补注释并论证无 kdump 场景的不可替代性'
contribution_opportunities:
  - kind: review
    description: '评估无 kdump 生产环境下该功能的不可替代性，帮助回应 Peter'
  - kind: testing
    description: '触发 panic 核对输出、contended 标注与日志体量'
generated_at: '2026-09-24T09:00:00'
source_email_count: 3
related_articles:
  - sched-20260912-006
  - sched-20260911-010
tags:
  - sched_debug
---