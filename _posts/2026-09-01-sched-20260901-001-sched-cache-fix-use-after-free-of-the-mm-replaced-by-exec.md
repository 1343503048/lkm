---
subject: 'sched/cache: Fix use-after-free of the mm replaced by exec'
id: sched-20260901-001
date: '2026-09-01'
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: <apXzDjnvOm9GfTLK@v4bel>
lore_url: https://lore.kernel.org/all/apXzDjnvOm9GfTLK@v4bel/
authors:
- Hyunwoo Kim
- Tim Chen
- Chen Yu
maintainers_involved:
- Tim Chen
- Chen Yu
- Peter Zijlstra
current_version: v2
patch_series:
- version: v1
  msgid: null
  date: '2026-08-31'
  summary: 轮转 rq 锁排除并发读者；混入一个无关 hunk
  review_outcome: 作者自己承认无关 hunk；讨论后倾向改用 RCU
- version: v2
  msgid: <apXzDjnvOm9GfTLK@v4bel>
  date: '2026-09-01'
  summary: 在 exec_mm_put_old() 前调用新增 sched_cache_exec_done() 做 synchronize_rcu()，覆盖所有关抢占的读者；3
    文件 +17 行；Fixes df0d98475954 + Cc stable
  review_outcome: Tim Chen 认为完整 grace period 落在 exec 路径不可接受，主张改用 sc_stat 与 mm 解耦 +
    refcount + call_rcu（prctl 系列前 2 片）；Chen Yu 确认解耦实现；Hyunwoo 已验证那 2 片可防住本 UAF；Peter
    Zijlstra 被点名后本日未回复
upstream_commit: null
fixes_commit: df0d98475954
merged_branch: null
merge_assessment:
  likelihood: possible
  blocking_issues:
  - 修复路线未定：v2 的 synchronize_rcu() 被 Tim Chen 认为会在 exec 路径引入一个完整 grace period 的延迟
  - 替代路线（sc_stat 与 mm 解耦）目前仍是 RFC 状态的 prctl 系列前 2 片，未单独作为 fix 发出
  - Tim Chen 已当场向 Peter Zijlstra 征求意见，本日无回复
  next_action: Peter Zijlstra 或 Tim Chen 明确选定路线：直接收 v2 走 stable，或把 prctl 前 2 片拆成独立
    fix 系列并带 Reported-by/Tested-by
contribution_opportunities:
- kind: testing
  description: 在 exec 密集型负载 + KASAN 下验证 prctl 系列前 2 片，回帖补 Tim Chen 明确索要的 Tested-by
- kind: backport
  description: 自查 OLK 分支是否含 df0d98475954 引入的 account_mm_sched()/mm->sc_stat 路径；若有，先用
    v2 的 sched_cache_exec_done() 最小止血，再决定是否跟进 sc_stat 解耦重构
- kind: new_patch
  description: 把 anon_pipe_write 唤醒撞 execve 的竞争整理成自包含确定性复现脚本，量化 exec 路径 synchronize_rcu()
    的实际延迟代价
source_email_count: 7
related_articles:
- sched-20260831-009
- sched-20260831-008
tags:
- load_balance
- crash
- perf
generated_at: '2026-09-07'
title: 'sched/cache: Fix use-after-free of the mm replaced by exec'
layout: article
---

## TL;DR

Hyunwoo Kim 报告并修复 cache-aware 调度统计（`mm->sc_stat`）在 exec 换 mm 时的 slab-use-after-free：`account_mm_sched()` 在 rq 锁下读的 `p->mm` 没有任何生命周期保护，exec 路径可以把它释放掉。v2 用 `synchronize_rcu()` 兜底并 `Cc: stable`，但 Tim Chen 主张改用「把 `sc_stat` 从 mm 里解耦出来 + refcount + `call_rcu()`」的重构（即 prctl 系列前 2 片），Hyunwoo 当天已确认那两片能防住本 UAF。修复路线尚未定，Peter Zijlstra 当天未表态。

## 背景与问题

`account_mm_sched()` 读 `p->mm` 并更新 `mm->sc_stat`（cache-aware 负载均衡的 per-mm 统计）。问题出在唤醒路径：当 waker 不能用 wakelist 时，`ttwu_queue()` 会拿**目标** rq 的锁并下沉到 `update_curr()`，此时传给 `account_mm_sched()` 的是那台 CPU 上正在跑的任务，而不是被唤醒的任务。作者指出：

> The rq lock and rq->cpu_epoch_lock it holds have nothing to do with the lifetime of the mm.

若该任务正好在 `execve()`：`exec_mmap()` 把 `tsk->mm`/`tsk->active_mm` 指向新 mm，`setup_new_exec()` 里的 `exec_mm_put_old()` 丢掉旧 mm；`mmput()` → `__mmdrop()` → `mm_destroy_sched()` 对 `sc_stat.pcpu_sched` 做 `free_percpu()`，`free_mm()` 归还 `mm_struct`。已经读过旧指针的人继续读写已释放的 per-cpu 区域和 `mm_struct`，并按条件写 `sc_stat.cpu`。

已有修复 `9f23469401b0`（"sched/cache: Fix potential NULL mm pointer access"）认为 `active_mm` 的引用足以保证结构存活——对其他 detach mm 的路径成立（它们拿 `mmgrab_lazy_tlb()`），但 exec 会重新指派 `active_mm`，于是只剩 `bprm->old_mm` 里的 `mm_users` 引用，而释放它的正是那条路径。

复现是**可触发**的，邮件带 KASAN 日志：`BUG: KASAN: slab-use-after-free in update_se+0xe6e/0xf70`，分配对象为 `mm_struct`（size 1688），释放方为 `setup_new_exec()`，触发方为 `anon_pipe_write()` → `try_to_wake_up()` → `enqueue_task_fair()`。作者用 `sc-direct-set` 任务把竞争跑了出来。

## 技术方案

- **v1**：在 exec 换 mm 处通过轮转 rq 锁来排除读者（同时混进一个无关 hunk）。
- **v2**（当前）：改为 `fs/exec.c:exec_mm_put_old()` 里调用新增的 `sched_cache_exec_done()`，内部 `synchronize_rcu()`，然后才 `mmput(old_mm)`。论证是：`account_mm_sched()` 持 rq 锁、抢占关闭，本身即 RCU 读侧临界区；等在 `tsk->mm` 赋值之后，已拿到旧指针的读者必然在 grace period 结束前完成，之后的读者看到的是新 mm。改动 3 个文件 `+17/-0`（`fs/exec.c`、`include/linux/sched.h`、`kernel/sched/fair.c`），带 `Fixes: df0d98475954 ("sched/cache: Introduce infrastructure for cache-aware load balancing")`、`Suggested-by: Chen Yu`、`Cc: stable@vger.kernel.org`。
- **被提出、可能取代 v2 的备选方案**（Tim Chen）：`synchronize_rcu()` 虽避开 rq 锁，但要等一个完整 grace period，落在 exec 路径上不可接受。他主张把 `sc_stat` 从 `mm` 中解耦成独立结构，自己带引用计数与 RCU 管理，任务通过 `task->sc_stat` 直接访问而不再经 `task->mm->sc_stat`——"Then we will know sc_stat exists in account_mm_sched() execution as long as a task points to it"。这正是 Tim 的 `[RFC PATCH 0/7] sched/cache: Per-task control of cache aware scheduling via prctl` 系列前 2 个补丁做的事。
- Chen Yu 补充确认：解耦后 sched_group 生命周期由引用计数管理，释放走非阻塞的 `call_rcu()` 而非 `synchronize_rcu()`。
- 另一个被放弃的方向是「在 rq 锁里做保护」：Tim 认为 rq lock 方案延迟比 `synchronize_rcu()` 小，但他自己更倾向解耦，因为 exec 路径不增加延迟。

## 版本演进与当前进展

- **v1**（msgid 未在本日缓存中，作者自链 `https://lore.kernel.org/all/apPb-Dr4nPYuHQOK@v4bel/`）：轮转 rq 锁 + 一个无关 hunk。被指出后作者回 "Duh.. that one is unrelated. My mistake."，并认可 RCU 写法更干净，承诺发 v2。
- **v2**（2026-09-01 05:33，`<apXzDjnvOm9GfTLK@v4bel>`）：去掉无关 hunk；改用 `synchronize_rcu()` 覆盖所有关抢占的读者；加 `Cc: stable`。
- **同日讨论走向**：Tim 04:25 提出解耦方案并要求「优先考虑先把 prctl 系列头两片和进来」；Hyunwoo 05:44 回应 "It is a real, triggerable issue … If you add a Reported-by: tag for this UAF to the patch, I am fine with handling it that way."；Tim 06:10 请对方验证并愿追加 Tested-by；Chen Yu 11:00 读完解耦实现确认走 `call_rcu()`；Hyunwoo 18:44 结论：**"I confirmed that patches 1 and 2 of your series prevent this UAF."**
- 状态：under_review。v2 是一个可独立合入的稳定修复，但维护者层面的共识倾向用重构根治。

## Maintainer 意见与讨论焦点

- **Tim Chen（Intel，cache-aware 维护方向）**：明确不认可 `synchronize_rcu()` —— "it could introduce a long delay of a full grace period that will be undesirable"，并认为解耦 `sc_stat` 才是正解（"the best solution without adding latency in the exec path"），同时指出解耦能顺带降低这块代码的维护成本。他**当场向 Peter 征求意见**："Wonder what is Peter's opinion?"——本日截止无回复，这是最大的未决点。
- **Chen Yu（Intel）**：偏技术核对，读完 prctl 前 2 片后确认生命周期管理方式（refcount + 非阻塞 `call_rcu()`），没有提出反对。
- **Hyunwoo Kim（报告者/作者）**：坚持这是真实可触发的问题（不接受"理论问题"的定性），但对修复归属足够开放——只要重构补丁带上 `Reported-by` 即可接受该路线。他同时提醒解耦是 "a fairly large change"。
- 未解决的分歧：**稳定性回合（`Cc: stable` 的小修复）与新引入的重构之间的取舍**。v2 只 17 行，能立刻进 stable；解耦方案要引动 `task_struct`/`mm_struct` 结构和 prctl 系列，风险与收益都更大。另外，Tim 请求的验证结论（"patches 1&2 fix it"）在 09-01 当晚才拿到，prctl 系列本身仍只是 RFC。

## 合入评估

`likelihood = possible`。判断依据：问题真实且有 KASAN 证据、`Fixes:` 指向 `df0d98475954`、`Cc: stable`，作为独立修复的技术门槛很低，所以**存在一条明确的近期合入路径**（直接收 v2）。卡点是路线未定：Tim（该子模块最活跃的 Intel 维护者之一）不想要 exec 路径上的 `synchronize_rcu()`，希望由 prctl 系列前 2 片承载修复，而那个系列当天还是 RFC 且未获 ack；Peter Zijlstra 被点名后未表态。要推进需要其中之一发生：Peter/Tim 明确接受 v2 作为 fix 先走 stable、重构随后；或者 Tim 把 prctl 前 2 片从 RFC 里拆出来单独发 fix 版（他自己已提议 "We should probably prioritize to merge the first couple of patches from that series now"，并已向 Hyunwoo 索要 `Reported-by`，说明这条路已经在准备中）。

## 效果评估

有确定的失效证据（KASAN slab-use-after-free，读写 `mm_struct` 内 400 字节偏移处、以及已释放的 per-cpu 区域），但没有性能数据。方案对比中的关键论断——`synchronize_rcu()` 会拖慢进程启动、rq-lock 方案延迟更低、解耦方案不增加 exec 延迟——均为**维护者主观判断，未见测试数据**。修复对正确性的影响面：`sc_stat.epoch`/`sc_stat.cpu` 与 per-cpu runtime 累加，属于 cache-aware 负载均衡的输入，出错时表现为迁移决策被脏数据污染，而非立即可见的崩溃（UAF 本身则可能崩溃）。

## 我可以参与的点

- **回合自查（最直接）**：若 OLK 分支已带 `df0d98475954` 引入的 sched/cache 基础设施与 `account_mm_sched()`，同一 UAF 就在自己代码里。可先在分支上按 v2 的 `sched_cache_exec_done()` 做最小化止血，再决定是否跟随上游重构，避免后续与 `task->mm->sc_stat` 的解耦大改冲突。
- **验证 prctl 系列前 2 片**：Hyunwoo 已给出结论，但 Tim 明确请求过 `Tested-by`。在 exec 密集型负载（`fork+exec` 高压、shell 遍历、容器 init）+ KASAN 下跑那两片并回帖，是一条低成本、社区明确在等的贡献。
- **给出更小的确定性复现**：当前复现依赖 `anon_pipe_write()` 唤醒撞上 `execve()`，可以把它整理成自包含压测脚本回帖，帮 Peter 判断是否需要在 nohz_full/高频 exec 场景下额外评估 grace period 代价。
- 关注 Tim 是否把前 2 片拆成独立 fix 系列发出——拆出来后 `merge_assessment` 会立刻转向 likely。

## 参考链接

- v2 补丁（`synchronize_rcu()` 版）: https://lore.kernel.org/all/apXzDjnvOm9GfTLK@v4bel/
- v1（作者自链，正文中给出）: https://lore.kernel.org/all/apPb-Dr4nPYuHQOK@v4bel/
- Tim Chen 提出解耦方案并请求验证: https://lore.kernel.org/all/a1a0bc24108e68656041dc17824d6b88b4120058.camel@linux.intel.com/
- Chen Yu 确认 refcount + call_rcu: https://lore.kernel.org/all/apY_vvPExYP6qMZS@three-body/
- Hyunwoo Kim 确认 prctl 1&2 可防住: https://lore.kernel.org/all/apasjygjnsg1n6em@v4bel/
- 承载修复方向的 prctl 系列 cover（Tim 在邮件中给出的链接）: https://lore.kernel.org/lkml/cover.1787955777.git.tim.c.chen@linux.intel.com/
- tip-bot commit: 未获取到（尚未合入）
- stable backport: 未获取到（v2 带 `Cc: stable`，等待合入后才会出现）
