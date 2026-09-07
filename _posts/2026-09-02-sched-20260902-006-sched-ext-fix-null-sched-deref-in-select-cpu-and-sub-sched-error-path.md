---
id: sched-20260902-006
date: '2026-09-02'
subject: 'sched_ext: Fix NULL sched deref in select_cpu_and sub-sched error path'
subsystem: sched
type: bug
status: merged_tip
severity: high
thread_root_msgid: <20260902153640.144791-1-liwanwu@kylinos.cn>
lore_url: https://lore.kernel.org/all/20260903060626.814951-1-liwanwu@kylinos.cn/
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.3-fixes
current_version: v3
generated_at: '2026-09-07'
authors:
- Wanwu Li
maintainers_involved:
- Tejun Heo
- Andrea Righi
patch_series:
- 'sched_ext: Fix NULL sched deref in kfunc sub-sched error paths'
merge_assessment:
  likelihood: merged
  blocking_issues:
  - '无：v3 已于 9/4 applied 到 sched_ext/for-7.3-fixes，并由 Tejun 加 # v7.1+ 进 stable Cc'
  - Tejun 否定了「NULL 时退回 root sched 并 scx_error」的语义，改为 root sched 打标记 + warn once（或忽略），该语义是否最优仍可在后续讨论
  next_action: 观察 stable 发布与是否补 selftest 复现用例；跟进 root-sched flag 方案的最终形态
contribution_opportunities:
- 清单化审查 sched_ext 内所有 scx_task_sched(p)/rcu_dereference_protected 解引用点的可达性（SYSCALL
  与 STRUCT_OPS 两类）
- 就 Tejun 的 root-sched flag + warn once 方案给实现或反例
- 补 sched_ext selftest：bpf_task_from_pid 取刚退出任务 + SYSCALL 程序调 select_cpu_and 的复现用例
- '评估自有 sched_ext 部署的威胁模型，决定 # v7.1+ 这条 stable 修复的回合紧急度'
source_email_count: 1
related_articles: []
tags:
- sched_ext
- crash
title: 'sched_ext: Fix NULL sched deref in select_cpu_and sub-sched error path'
layout: article
---

## TL;DR

`scx_bpf_select_cpu_and()` 在「root scheduler 挂了 sub-sched 且参数用法不对」时走
`scx_error(scx_task_sched(p), ...)`，而 `scx_task_sched(p)` 就是 `p->scx.sched`——对不在 sched_ext 上的
任务它是 NULL。`BPF_PROG_TYPE_SYSCALL`（`bpf_prog_test_run`）能拿到这个 wrapper 并传入任意任务
（例如 `bpf_task_from_pid()` 取到已退出未被回收的任务），`scx_error()` → `scx_vexit()` 无条件解引用
`sch->exit_info`，直接把 kernel oops 掉。**作者给出了完整的实机 Oops 栈，不是推测。**
09-02 是 v1 日；v2/v3 在 9/3 发出、范围扩大到所有 kfunc sub-sched 错误路径，
**Tejun Heo 9/4 01:56 "Applied to sched_ext/for-7.3-fixes with '# v7.1+' added to the stable Cc."**
——按 fixes 分支进树并带 stable。

## 背景与问题

`p->scx.sched` 由 `init_scx_entity()` memset 清零、由 `sched_ext_dead()` 走的
`scx_disable_and_exit_task()` 清除，因此任何不在 sched_ext 上的任务（含已退出的任务、idle 任务）
它的值都是 NULL。而且 `scx_task_sched()` 是 `rcu_dereference_protected()`，必须在持有 `@p` 的
pi_lock 或 rq lock 时调用——**`BPF_PROG_TYPE_SYSCALL` 程序两个都不持**。
可达性来自 `scx_kfunc_context_filter()`：它把 select_cpu 这一组 kfunc 开放给 SYSCALL 程序，
程序就能拿任意 `struct task_struct *` 进来。

实机触发（v7.2 内核，sub-scheduler `kfunc_subsched_null` 已启用，SYSCALL 程序对一个「已退出未回收」
的任务调用 wrapper，出错指令是 `scx_vexit()` 序言里的 `mov r15,[rdi+0x398]`，RDI=NULL，
`0x398` 即 `sch->exit_info` 偏移）：

```
BUG: kernel NULL pointer dereference, address: 0000000000000398
RIP: 0010:scx_vexit+0x25/0xa0
 __scx_exit+0x4f/0x70
 scx_bpf_select_cpu_and+0xab/0xb0
 bpf_prog_test_run_syscall+0x130/0x2f0
```

## 技术方案

保留「把错误记在 `@p` 的 scheduler 上」这个归属语义——v1 正文论证了它为什么是对的：
其它 kfunc 错误路径都这么做（`select_cpu_from_kfunc()` 的 cross_task、`scx_kf_arg_task_ok()`），
而真正会走这条路径的其余调用方是 struct_ops 的 select_cpu/enqueue，那里 `@p` 就是调用者自己的任务。
**只改读取方式**：用 `scx_task_sched_rcu()`（wrapper 已有的 `guard(rcu)()` 下合法，不需要 `@p` 的锁），
并在 `@p` 不在 sched_ext 上时 fallback 到 `@sch`——root scheduler 在这里保证非 NULL，
而这恰好就是原来会变成 NULL 的那一支。

`scx_bpf_dsq_insert_vtime()` 有同样的错误路径，v1 作者当时判断它"not reachable with a NULL @p"
（SYSCALL 程序在其 kfunc set 上被拒，且 `@p` 总是调用者自己的调度器）——**这个判断是错的**，
Andrea Righi 指出 STRUCT_OPS 程序可以从 `ops.enqueue()`/`ops.dispatch()` 调它，于是 v2 把标题从
`... in select_cpu_and sub-sched error path` 改成 `... in kfunc sub-sched error paths` 并覆盖该函数。

## 版本演进与当前进展

- v1 `74452`（9/2 23:36）→ Andrea `74645`（9/3 00:14）指出 `scx_bpf_dsq_insert_vtime()` 的缺口 →
  作者 `74707`（00:34）"This one is my miss..." → **v2 `74871`（9/3 01:07，扩大范围并改标题）** →
  Andrea `74952`（02:11）**Reviewed-by: Andrea Righi** → Tejun `75131`（03:37）与 `75110`（03:39）
  提出事实性纠正与新方案 → **v3 `75994`（9/3 14:06）** → **Tejun `77890`（9/4 01:56）applied**。
- 上一轮「v2 是否已发出」的保守说法可以撤掉：v2 确已发出且范围扩大。
- 进的是 `sched_ext/for-7.3-fixes`（修复分支），Tejun 还手动往 stable Cc 里加了 `# v7.1+`，
  说明影响范围被认定为 v7.1 起。

## Maintainer 意见与讨论焦点

- **Andrea Righi**（`74645`）：抓可达性漏角的评审，原文
  "the assumption above doesn't hold for `scx_bpf_dsq_insert_vtime()`, although SYSCALL programs can't
  call it, STRUCT_OPS programs can call it from `ops.enqueue()` and `ops.dispatch()`. Can you update
  `scx_bpf_dsq_insert_vtime()` as well with the same fallback?" 并在 v2 上给 `Reviewed-by`。
- **Tejun Heo** 的三条（`75131`/`75110`）都是「事实纠正 + 设计方向」：
  1. 纠正作者对 `p->scx.sched` 何时为 NULL 的理解："This isn't accurate. p->scx.sched is set for every
     non-idle task on root enable and on fork regardless of sched class. The only tasks with NULL
     p->scx.sched are the ones past sched_ext_dead() and the idle tasks."；
  2. 指出错误归属语义用错对象："Both of those error out the calling program's scheduler, not @p's..."；
  3. 否定 fallback 的行为："As the fallback only triggers for tasks already past sched_ext_dead() (or
     idle tasks), tearing down the root scheduler doesn't make sense. **How about adding a flag to the
     root sched and printing a warning once instead?**"，并补 "It'd be fine to just ignore it too..."。
  → 结论：v2 的「NULL 时退回 root sched 并 scx_error」被换成「root sched 上打标记、只 warn 一次
  （或干脆忽略）」，v3 按此实现后进树。这是很典型的「修复正确但语义选错」被维护者当场改写。

## 合入评估

**likelihood: likely（事实已完成）**——v3 已进 `sched_ext/for-7.3-fixes` 且带 stable（`# v7.1+`）。
当日无卡点；讨论只影响实现形态，不影响是否收。

## 效果评估

效果就是消除一个可从 BPF 测试路径稳定触发的整机 Oops（作者有实机栈）。它同时暴露了 sched_ext 的
一个结构性风险面：**`scx_kfunc_context_filter()` 为测试方便放开的 SYSCALL 可达集，等于把内核
API 暴露给「可传任意 task_struct 的任意程序」**，因此每个 `p->scx.sched` 解引用点都需要单独论证
可达性——同一作者在 [[sched-20260902-004]] 里做的 NMI 审计是同一类问题。
无性能影响（多一次 RCU 安全读）。

## 我可以参与的点

- 这类「可达性论证」型修复门槛低、收益高：把 sched_ext 里其它 `scx_task_sched(p)` /
  `rcu_dereference_protected` 使用点做一次清单化审查，特别是从 SYSCALL/STRUCT_OPS 都能到的 kfunc。
- 对 Tejun 提的「root sched 加 flag + warn once」给出实现或反例（例如会不会掩盖真正的
  scheduler bug），这决定 stable 里的行为。
- 回背侧：`# v7.1+` 说明这是近期内核的问题；若在跑 sched_ext 的产品内核，应先确认
  `bpf_prog_test_run` + sub-sched 是否对本地威胁模型有意义，再决定是否紧急回合。
- 复现脚本本身有价值：`bpf_task_from_pid()` 拿一个刚退出的任务 + SYSCALL 程序调 select_cpu_and
  即可复现，可作为 sched_ext selftest 的补充用例。

## 参考链接

- v1：https://lore.kernel.org/all/20260902153640.144791-1-liwanwu@kylinos.cn/
- v2：https://lore.kernel.org/all/20260902170751.256434-1-liwanwu@kylinos.cn/
- v3（进树版本）：https://lore.kernel.org/all/20260903060626.814951-1-liwanwu@kylinos.cn/
- Andrea 的缺口指认与 Reviewed-by：https://lore.kernel.org/all/aphLWtCVY1XVME9C@gpd4/ 、
  https://lore.kernel.org/all/aphmwjLkdS4tKpbv@gpd4/
- Tejun 的意见：https://lore.kernel.org/all/d819e8358fffc09015feffad57794f7c@kernel.org/ 、
  https://lore.kernel.org/all/aph7j7b_rqqqcSwR@slm.duckdns.org/ ；
  applied：https://lore.kernel.org/all/2edcf44237f7a5e81c6ec97a81b56d5b@kernel.org/
- 相关：[[sched-20260902-004]]、[[sched-20260903-004]]、[[sched-20260904-011]]
