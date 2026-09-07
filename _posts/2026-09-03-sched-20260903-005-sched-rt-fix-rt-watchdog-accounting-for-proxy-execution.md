---
id: sched-20260903-005
date: '2026-09-03'
subject: 'sched/rt: Fix RT watchdog accounting for proxy execution'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20260903111247.3538976-1-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20260903111247.3538976-1-sh_def@163.com/
upstream_commit: null
fixes_commit: 7de9d4f94638
merged_branch: null
current_version: v1
generated_at: '2026-09-07'
authors:
- Hui Su
maintainers_involved: []
patch_series:
- 'sched/rt: Fix RT watchdog accounting for proxy execution'
merge_assessment:
  likelihood: possible
  blocking_issues:
  - 09-03 内零回帖、零 tag，RT 侧维护者未确认 rt.timeout 生命周期
  - __schedule() 快路径新增两处无条件判断，可能被要求收拢
  - 依赖 rq->donor/rq->curr 拆分基线，需与 proxy execution 主线推进顺序协调
  next_action: 补一份补丁前后 rt.timeout 与 SIGXCPU 投递对象的数值对照并回帖
contribution_opportunities:
- 用 SCHED_FIFO/SCHED_RR donor 复现并量化 rt.timeout 归属差异
- 核对 __schedule() 新增判断在 prev==next、balance 提前返回等路径上的覆盖
- 确认 try_to_block_task() 中 idle 任务进入该判断时的取值
source_email_count: 1
related_articles:
- sched-20260903-001
tags:
- rt
- proxy_execution
- sched/core
title: 'sched/rt: Fix RT watchdog accounting for proxy execution'
layout: article
---

## TL;DR

代理执行下 `task_tick_rt()` 是替调度上下文 `rq->donor` 跑的，但运行时间记在 `rq->curr` 上，于是 `RLIMIT_RTTIME` 的 `rt.timeout` 累计与 posix CPU 定时器状态更新都落在了错误的任务上。Hui Su 的单补丁把 `watchdog()` 改传 `rq->curr`，并为「非 RT 执行任务借用 RT donor」的情形定义了 `rt.timeout` 的重置时机。
本日刚发出（19:12），09-03 内无任何回帖，也没有 tag；属代理执行上下文一致性修补簇，与同日 001/008 同一作者、同一个 `Fixes` 提交。

## 背景与问题

`task_tick_rt()` 针对调度上下文 `rq->donor` 被调用，而真正执行的是 `rq->curr`。RT watchdog 通过它的 task 参数查找 `RLIMIT_RTTIME` 并更新该任务的 `rt.timeout` 与 `posix_cputimers` 状态；但运行时间记账按 `rq->curr` 收费，且 `run_posix_cpu_timers()` 在 tick 之后检查的是 `current`。三者不一致时，watchdog 的状态更新跟随的是 donor 而非实际执行者：非 RT 任务替 RT donor 执行时会消耗 donor 的 `rt.timeout`（错误地逼近 `SIGXCPU`），而真正消耗了 CPU 时间的执行任务却不被记账。

## 技术方案

- `kernel/sched/rt.c` `task_tick_rt()`：`watchdog(rq, p)` 改为 `watchdog(rq, rq->curr)`——一行修改。
- `kernel/sched/core.c` 增加两处 `rt.timeout` 重置，使 timeout 生命周期同时绑定执行上下文与调度上下文：
  1. `try_to_block_task()`：`sched_proxy_exec() && !rt_prio(p->prio) && rt_prio(rq->donor->prio)` 时置 `p->rt.timeout = 0`，即非 RT 执行任务在借用 RT donor 期间阻塞时结束该 RT 代理区间；
  2. `__schedule()` 中 `rq_set_donor()` 之后：`sched_proxy_exec() && !rt_prio(next->prio) && !rt_prio(rq->donor->prio) && next->rt.timeout` 时清零，即以非 RT 调度上下文被选中时结束上一个 RT 代理区间。
作者明确该设计 handles nested proxy chains / preserves the timeout across scheduler preemption，且原生 RT 任务行为不变。改动量 `core.c +13`、`rt.c 1 行`，带 `Fixes: 7de9d4f94638`（`sched: Start blocked_on chain processing in find_proxy_task()`），无 `Cc: stable`。

## 版本演进与当前进展

- 本日单 patch 首发（v1），无封面、无版本迭代。
- 09-03 内未收到任何回帖，未获 `Acked-by`/`Reviewed-by`，未进入任何分支。
- 属「代理执行执行上下文修正」主线：同日 001（NUMA/cache tick）与 008（cgroup cputime）同作者、同一 `Fixes` 提交；001 已有的 Intel/AMD 复审资源是这条线最可能的评审来源。

## Maintainer 意见与讨论焦点

未获取到维护者意见：该 patch 于 09-03 19:12 发出，截至当日邮件缓存结束无人回帖，缓存中也无本线程的后续讨论。
可作为参照的是同一作者 001 系列本日的讨论走向：Tim Chen 关心的是「哪个上下文才是正确归属」，Chen Yu 关心的是提交说明中论证是否与既有结论（`rq->curr->mm` 才是真正在 CPU 上使用的那个）一致。本 patch 的争议面恰恰在同类问题上：`rt.timeout` 何时该重置——作者给出的规则横跨 `try_to_block_task()` 与 `__schedule()` 两处，尚无 RT 侧维护者（如 Quentin Perret / Peter Zijlstra / Daniel Bristot de Oliveira）确认该生命周期是否覆盖嵌套代理链与抢占的全部组合。

## 合入评估

likelihood: **possible**。
依据：缺陷本身无争议——`RLIMIT_RTTIME` 记错对象会导致对正确任务漏发 `SIGXCPU`、对 donor 误发；带指向已合入 tip 提交的 `Fixes` 标签；改动面极小且以 `sched_proxy_exec()` 严格门控，非代理执行路径行为不变；作者给了可复现的行为差分（见效果评估）。
卡点：一是线程内零评审，`watchdog()` 参数改动会牵连 `rt.timeout` 的对外语义，需要 RT 维护者明确认可；二是两处 `rt.timeout = 0` 的插入点对 `__schedule()` 快路径增加了无条件判断（虽由 static key 级别的 `sched_proxy_exec()` 保护），可能被要求合并到一处或改为在 donor 切换钩子内完成；三是与同作者 008 一样依赖 `rq->donor`/`rq->curr` 拆分基线，需要与 proxy execution 主线的推进顺序协调。

## 效果评估

邮件中未提供性能数据，但给了明确的行为差分：使用 SCHED_FIFO 与 SCHED_RR 作为 donor 的代理执行复现程序下，**未打补丁的内核把 `rt.timeout` 记到 donor，打过补丁的内核记到执行任务并向其投递 `SIGXCPU`**。
覆盖面亦已实跑：嵌套代理链、阻塞、非 RT 上下文切换、调度器抢占与 donor 取消都被执行过。缺少的是数值化验证（如 `RLIMIT_RTTIME` 阈值与实际 CPU 时间的一致性对照表）与对 `posix_cpu_timers` 侧的观测数据。

## 我可以参与的点

1. 首个回帖的价值最高：在 `CONFIG_SCHED_PROXY_EXEC=y` 下用 `SCHED_FIFO`/`SCHED_RR` donor + 非 RT mutex owner 复现，给出 `rt.timeout` 在补丁前后的对照数值（`/proc/<pid>/sched`、`RLIMIT_RTTIME` 触发时刻），可直接补上作者缺的量化证据。
2. 可复核的具体代码点：`__schedule()` 里新增判断位于 `rq_set_donor()` 之后、`picked:` 之前，值得核对在 `prev == next`（未发生切换）与 `balance` 提前返回等路径上是否都会经过；另外 `try_to_block_task()` 的 `!rt_prio(p->prio) && rt_prio(rq->donor->prio)` 判断在 `p` 即 idle 任务时的取值需要确认。
3. 与 008 的耦合：`rt.timeout` 归属改了之后，cgroup CPU 统计与 `RLIMIT_RTTIME` 的观测口径是否仍一致，可作为一条 review 意见提出。
4. 回合视角：OLK-6.6 无 proxy execution，本 patch 不可回合；但若 6.6 上有自研的「A 任务替 B 任务执行」机制（如某些 RT 增强/绑核代理方案），这条 `watchdog()` 归属 + `rt.timeout` 生命周期设计可直接作为 review 清单。

## 参考链接

- 本补丁：https://lore.kernel.org/all/20260903111247.3538976-1-sh_def@163.com/
- 相关文章/系列：
  - [[sched-20260903-001]] 代理执行下执行上下文 tick 处理（同作者、同 `Fixes` 提交）。
  - [[sched-20260903-008]] cgroup cputime 归属调度上下文（同作者，同属上下文一致性簇）。
- 相关代码：
  - `kernel/sched/rt.c` `task_tick_rt()` / `watchdog()`
  - `kernel/sched/core.c` `try_to_block_task()` / `__schedule()` 的 `rt.timeout` 重置点
