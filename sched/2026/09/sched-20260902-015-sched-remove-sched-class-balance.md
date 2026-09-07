# sched: Remove sched_class::balance()

## TL;DR

9/2 该主题只有两条实质往返，都不是「该不该删 `balance()`」，而是补丁本身的可评审性：Tejun Heo 回
7/7 指出 **diffstat 里有 `kernel/sched/fair.c | 47` 但正文没有任何 fair.c 改动**；回同系列 2/7 指出
`opt_update_rq_clock()` 把 `RQCF_UPDATED` 当「已经更新过」的判据是错的，sibling rq 的 flag 不保证被清，
后续 `pick_task()` 会带着很旧的 rq clock 跑。Peter Zijlstra 当晚 22:32 直接认账并给出修法
（"We should clear clock_update_flags on unlock, rather than on lock."）。删回调的方向从 8/19 起就没被
任何人质疑，但 Peter 自己在 8/22 就说过 "the patches need to be redone, they're a bit of a mess"，
1/7 正文里还留着 `XXX words on forward progress go here` 占位。**合入评估应从原稿的「中/高」下调为
「likely，但必须等一次重投」**：卡点不是争议，是漏发 hunk + clock 判据错误 + 作者自认待重做。
9/3–9/7 缓存内该主题零新邮件。

## 背景与问题

`sched_class::balance()` 是 `__schedule()`/`pick_next_task()` 路径上按调度类反向遍历的均衡钩子。
Peter 在 7/7 正文里给的删除理由很具体：自从 `50653216e4ff ("sched: Add support to pick functions to take
rf")` 之后，`balance()` 和 `pick_task()` 功能重叠——两者都会 drop `rq->lock` 去搬任务；更糟的是
core-sched 下 `prev_balance()` 只对**单个** rq 调用，造成 "missed balance opportunities"。
`prev_balance()` 从 `rq->donor->sched_class` 起按类往下走、找到一个可运行任务就停，与 `pick_task()`
只差起点（一个从顶类、一个从 prev 的类），因此 prev 是 RT 时会多 visit 一次 `balance_dl()`，prev 是
fair 时 `balance_dl()` 和 `balance_rt()` 都会被 visit 一次。Peter 论证这无害，
因为 `need_pull_{dl,rt}_task()` 会做正确的事，于是把 `balance_{rt,dl}()` 移进 `pick_task_{rt,dl}()`，
删掉回调本身。

真正的技术难点是**前向进展保证**：均衡从「一次性有界遍历」变成「pick 过程中随时可能 break lock 重试」后，
重试次数失去上界。这正是 8/20 Tejun 与 Peter 的分歧核心——Tejun 说明 SCX 只在确实有任务要迁移进本地 DSQ
时才 drop rq lock，"if nothing has changed since the last time, there won't be a task to migrate and thus
no lock drop"，BPF 自定义 DSQ 方法也都嵌在 rq lock 内执行；Peter 担心 fair 侧做不到（拉不到任务时每次重试
都会再试一次），并提出自己的 hack："keeping a retry count, and simply setting 'rf = NULL' after a few
cycles, to inhibit any further balancing and forcing progress"，代价是所有 `pick_task()` 必须能处理 `!rf`。

## 技术方案

7/7 本体（UID 63355，8/28 发出）删除的内容：`prev_balance()`（core.c 23 行）、`struct sched_class` 的
`int (*balance)(struct rq *rq, struct rq_flags *rf)` 成员（sched.h 5 行）、`balance_idle()`、
`balance_stop()`；`balance_rt()`/`balance_dl()` 返回值改 void，并前置进 pick：

    static struct task_struct *pick_task_rt(struct rq *rq, struct rq_flags *rf)
    {
            rq_modified_begin(rq, &rt_sched_class);
            balance_rt(rq, rf);
            if (rq_modified_above(rq, &rt_sched_class))
                    return RETRY_TASK;

整体挂在 `[PATCH 0/7] sched: core-sched fixes and balancing` 下，其余 6 补丁为：1/7 self recursion
修复（本地保存 `seq = ++rq->core->core_task_seq`，检测 sibling CPU 竞争多 pick 踩坏 core 级选队状态导致的
NULL deref，并把 `idle_sched_class.pick_task(rq_i, rf)` 改成传 `NULL`）、2/7 时间戳简化（新增
`opt_update_rq_clock()`、循环里改用 `struct rq_flags rf_i = *rf` 副本、循环后显式
`rq->clock_update_flags |= RQCF_UPDATED`）、3/7 `sched/core: Allow newidle for core-sched`、
4/7 `sched/rt: Add early exit on balance path`、5/7 `sched/fair: Reflow pick_task_fair() / newidle`、
6/7 `sched/fair: Push sched_balance_newidle() unlock down`。

**原稿对系列形态的判断有误**：不存在「当日同时有 0/2 和 7/7 两种形态、Peter 中途把系列拆开」。
实际情况是 6/24 有 `[PATCH 0/2]` 前身，8/28 扩容为 0/7，封面自述 "Previous 'version' is at [1], but this
one is vastly expanded, so I didn't really bother keeping count."，且整条线起源于 "all this started with me
breaking core-scheduling"，外加 "TJ had a few patches fixing core-sched for ext（which, if/when this lands,
can be simplified again）"。0/2 的回帖全部在 8/19–8/22，9/2 当天只有 0/7 的两条线。

## 版本演进与当前进展

- 6/24：`[PATCH 0/2] sched: Remove sched_class::balance()` 首投（该 msgid 只在后续邮件的 `references`
  头中出现，缓存内无正文记录，故不单独给链接）。
- 7/2：Aaron Lu 报告该改动引发 panic（"The test caused a panic with below msg"）。
- 8/19–8/20：Tejun/Peter 往返前向进展与 SCX lock-drop 语义；Tejun 认可 `core_seq` 方案
  （"if core_seq tracks competing multi-picks, SCX no longer needs to track lock drops which was kinda ugly"）。
- 8/20 晚：Peter 向 Aaron 索要复现方法（"What test do you run? I think all I have is the prctl selftest thing."）。
- 8/21：K Prateek Nayak 给出常规用例 `coresched new -t pid -- perf bench sched messaging -p -l 100000 -g 8`
  （"a full run without any splats as a pass"）；Aaron 补上备份脚本，`./test.sh` 即可触发，
  且 "the problem can be triggered no matter quota is set or not"（原测试机已回收）。
- 8/22：Peter 确认 `queue.git/sched/hackery` 能活过 Prateek 的用例、准备跑 Aaron 的，同时明确
  "the patches need to be redone, they're a bit of a mess"。
- 8/28：以 0/7 重发，封面声称 "these patches survive both Aaron's test case [4] and Prateek's [5]"。
  系列**不带 vN 编号**（作者刻意不计数），故 frontmatter `current_version` 置 null。
- 9/2：Tejun 两笔意见（7/7 缺 fair.c hunk、2/7 clock 判据错），Peter 认错并给出修法。
- 9/3–9/7：缓存内零新邮件，无重投。
- 标签面：全缓存检索该主题所有邮件，**无 `Fixes:`、无 `Cc: stable`、无任何 `Reviewed-by`/`Acked-by`/`Tested-by`**。

## Maintainer 意见与讨论焦点

- **Tejun Heo（sched_ext 维护者）** 9/2 07:47 回 7/7：`"diffstat has fair.c ... but the patch body doesn't
  have any fair.c changes."` 7/7 声称 `fair.c | 47 ++++...---` 而正文只到 `stop_task.c` 为止——这是发布事故，
  评审无法基于它继续。
- **Tejun Heo** 9/2 13:38 回 2/7：先认可抽象方向（`"Yeah, I think this really needs sth like this"`），
  再指出用法错：`"I don't think this is correct. A sibling rq wouldn't necessarily have RCQF_UPDATED cleared
  from whenever it scheduled / ticked the last time, so the following pick_task() can run with pretty stale
  rq clock."` 同时点掉 1/7/2/7 一起引入的 `WARN_ON_ONCE(p == RETRY_TASK)` + `goto restart` 简化。
  （引文中的 `RCQF_UPDATED` 是 Tejun 原邮件的笔误。）
- **Peter Zijlstra** 9/2 22:32：`"Ah, indeed. We should clear clock_update_flags on unlock, rather than on
  lock. Thanks!"` —— 无条件接受，修复点从「读侧判断」移到「解锁侧清零」。
- **Tejun Heo** 8/20：为本系列的前提（去掉 ext 的 lock-drop 追踪）背书，并逐条回答 Peter 的两个担忧：
  SCX 不会为「尝试」而 drop lock；BPF 方法全部嵌在 rq lock 内。同时反问 `pick_task(rq_i, NULL)` 的语义是否
  就是「idle pick 在 seq 校验之后不许再 drop rq lock」。
- **Aaron Lu / K Prateek Nayak**：不是意见方，而是回归门槛的提供方——两个崩溃用例 + `perf bench sched
  messaging` 的 no-splat 判据，是 Peter 封面用来声明系列可用的依据。
- 全程无 NAK、无第二种反对声音；争议全部集中在实现细节与前向进展保证，不在接口删除本身。

## 合入评估

**likely（但要等一次重投）**。理由：删 `balance()` 的唯一实质异议者（sched_ext 侧）已经在为它背书，
Peter 主推、体量小（7/7 净 -63 行）、依赖的 newidle/rt 早退补丁同批在手，Aaron 与 Prateek 的崩溃用例已被
作者声明通过。阻塞项按优先级：

1. 7/7 漏发 `fair.c` hunk——本轮评审被直接判空，Tejun 的意见至今未被补发版本回应。
2. 2/7 的 `RQCF_UPDATED` 判据要在 unlock 时清零，Peter 已认错但新Posting 未到；2/7 与 7/7 同系列强依赖。
3. 作者自认 "the patches need to be redone"，1/7 仍留 `XXX words on forward progress go here`——前向进展
   这一核心论证没写完，fair 侧 `rf == NULL` 的 retry 上界方案（"Let me continue pondering if there is
   anything saner than simply clearing rf"）未定。
4. 无 `Fixes:`、无 stable、无第三方 tag，需完整 core-sched 回归才有排队理由。

## 效果评估

7/7 与 2/7 线程内**没有任何性能或规模数据**，原稿「不该有数据」的说法不成立：这是核心 pick 路径的重写，
作者与测试方都给了量化判据，只是判据是正确性而非性能。可引用的只有：`queue.git/sched/hackery` 活过
`coresched new -t pid -- perf bench sched messaging -p -l 100000 -g 8`；Aaron 的 nop+bandwidth 脚本
（带/不带 quota 均可触发原 panic）被声明通过。结构性收益是可静态核实的：删除一次
`for_active_class_range()` 类遍历、`struct sched_class` 少一个函数指针、净 -63 行；RT/DL 的均衡入口改由
`rq_modified_begin()/rq_modified_above()` 与 `RETRY_TASK` 驱动，是否引入额外 restart 无人测量。
Tejun 提到的收益（sched_ext 可去掉 ugly 的 lock-drop 追踪）要等系列落地后才可量化。

## 我可以参与的点

- **拿现成用例做独立回归**（最低成本、最直接有用）：在 SMT + core-sched 机器上跑 Prateek 的
  `coresched new -t pid -- perf bench sched messaging -p -l 100000 -g 8` 与 Aaron 的 `test.sh`
  （CPU hog + 带宽 quota，quota 设不设都试），回报有无 splat。作者自己说 Aaron 的用例只被他「声明通过」。
- **验证 2/7 的修法**：Peter 说改成「解锁时清 `clock_update_flags`」。可以在 `CONFIG_SCHED_DEBUG` 下用
  `update_rq_clock()` 的重复更新告警反向验证：改完后既不该有 stale clock，也不该出现 double update。
- **补前向进展论证**：1/7 的 `XXX` 占位就是留给评审的空位。fair 侧「拉不到本地任务时每次重试都会再拉一次」
  这个具体场景（cpumask 限制、cgroup CPU 配额导致落点受限）谁能给出可证的上界或反例，谁就推进了这个系列。
- **sched_ext 侧收口**：`core_seq` 覆盖竞态的充分性由 Tejun 关心，但缓存内没有 scx 侧的独立确认；
  跑一遍 scx 自测并确认 `pick_task()` 在 `rf == NULL` 下行为可接受，是可直接回帖的内容。
- **RT/DL 早退正确性**：`balance_rt()` 改 void 后是否继续均衡完全取决于 `rq_modified_above()`，
  可构造 `pull_rt_task()` 空转（无可迁移任务）场景，检查不该 RETRY 时是否 RETRY、该 RETRY 时是否漏掉。

## 参考链接

- `[PATCH 7/7] sched: Remove sched_class::balance()` 本体（UID 63355，含动机全文与 diffstat）：https://lore.kernel.org/all/20260828104018.996963405@infradead.org/
- Tejun Heo 指出缺 fair.c hunk（UID 72564，9/2 07:47）：https://lore.kernel.org/all/apdj_iMZ8Rl7wsXK@slm.duckdns.org/
- `[PATCH 2/7] sched/core: Simplify/fix time updates` 本体（UID 63354，`opt_update_rq_clock()`）：https://lore.kernel.org/all/20260828104018.483560652@infradead.org/
- Tejun Heo 的 stale sibling rq clock 意见（UID 72931，9/2 13:38）：https://lore.kernel.org/all/ape2abNdAgRCfEtg@slm.duckdns.org/
- Peter Zijlstra 认错并给出「解锁时清零」（UID 74280，9/2 22:32）：https://lore.kernel.org/all/20260902143209.GC687043@noisy.programming.kicks-ass.net/
- `[PATCH 0/7] sched: core-sched fixes and balancing` 封面（UID 63350，含前身/触发点/测试声明）：https://lore.kernel.org/all/20260828101659.812011872@infradead.org/
- `[PATCH 1/7] sched/core: Fix pick_next_task() self recursion`（UID 63351，`core_task_seq` 与 `XXX` 占位）：https://lore.kernel.org/all/20260828104018.378378994@infradead.org/
- Tejun Heo 解释 SCX 的 lock-drop 语义（8/20，0/2 线）：https://lore.kernel.org/all/aoYCXConRkdx8zKi@slm.duckdns.org/
- Peter Zijlstra 的 retry count + `rf = NULL` hack（8/20）：https://lore.kernel.org/all/20260820071852.GJ1247881@noisy.programming.kicks-ass.net/
- K Prateek Nayak 给出 `coresched` + `perf bench sched messaging` 判据（8/21）：https://lore.kernel.org/all/3898f82d-e48a-48d5-a13d-54fa5387a203@amd.com/
- Aaron Lu 补上可复现脚本（8/21）：https://lore.kernel.org/all/20260821024335.GA3046103@bytedance.com/
- Peter Zijlstra：hackery 通过 + "the patches need to be redone"（8/22）：https://lore.kernel.org/all/20260822094254.GH687043@noisy.programming.kicks-ass.net/
- Peter Zijlstra 向 Aaron 索要测试方法（8/20，回复 7/2 panic 报告）：https://lore.kernel.org/all/20260820154052.GB4120091@noisy.programming.kicks-ass.net/
- 相关：[[sched-20260902-012]]（同期 `rq->donor` 语义修正，同属 PE 落地后的核心路径收尾）、[[sched-20260902-007]]（同期 fair 侧 `task_h_load` 重做，与本系列 5/7/6/7 改的是同一片 newidle 代码）、[[sched-20260902-002]]（同期 sched/core 清理）

---
id: sched-20260902-015
date: '2026-09-02'
subject: 'sched: Remove sched_class::balance()'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260828104018.996963405@infradead.org>
lore_url: https://lore.kernel.org/all/20260828104018.996963405@infradead.org/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: '2026-09-07'
authors:
- Peter Zijlstra
maintainers_involved:
- Tejun Heo
- Aaron Lu
- K Prateek Nayak
patch_series:
- '[PATCH 0/7] sched: core-sched fixes and balancing'
- '[PATCH 1/7] sched/core: Fix pick_next_task() self recursion'
- '[PATCH 2/7] sched/core: Simplify/fix time updates'
- '[PATCH 3/7] sched/core: Allow newidle for core-sched'
- '[PATCH 4/7] sched/rt: Add early exit on balance path'
- '[PATCH 5/7] sched/fair: Reflow pick_task_fair() / newidle'
- '[PATCH 6/7] sched/fair: Push sched_balance_newidle() unlock down'
- '[PATCH 7/7] sched: Remove sched_class::balance()'
merge_assessment:
  likelihood: high
  blocking_issues:
  - '7/7 diffstat 声称改了 kernel/sched/fair.c（47 行）但正文完全没有 fair.c hunk，本轮评审被 Tejun Heo 判空且尚无补发版本'
  - '同系列 2/7 的 opt_update_rq_clock() 以 RQCF_UPDATED 作“已更新”判据，sibling rq 可能带着 stale clock 进入 pick_task()；Peter 已认但改为“解锁时清零”的新版未到'
  - '作者自述 "the patches need to be redone, they''re a bit of a mess"（8/22），1/7 正文仍留 XXX words on forward progress go here 占位'
  - 'fair 侧“拉不到任务时反复重试”的均衡上界方案（retry count + rf = NULL）未定，前向进展保证缺论证'
  - '无 Fixes: 标签、无 Cc stable、无任何 Reviewed-by/Acked-by/Tested-by，需完整 core-sched 回归才能排队'
  next_action: '等 8/7 或重投版本；在重投前用 Aaron 的 test.sh 与 Prateek 的 coresched+perf bench 用例独立跑一遍 splat 判据，并验证“解锁时清零 clock_update_flags”是否既无 stale 也无 double update'
contribution_opportunities:
- '在 SMT + core-sched 机器上用 coresched new -t pid -- perf bench sched messaging -p -l 100000 -g 8 和 Aaron 的带宽测试脚本做独立回归'
- '在 CONFIG_SCHED_DEBUG 下验证 2/7 改为解锁侧清 clock_update_flags 后不出现 stale clock 与重复更新告警'
- '为移除 balance() 后的前向进展给出可证上界或反例，重点是 fair 在 rf == NULL 时的重试行为'
- '从 sched_ext 侧确认 core_seq 覆盖全部竞态、pick_task() 能处理 rf == NULL，替 Tejun 补上独立结论'
- '构造 pull_rt_task() 空转场景，检查 rq_modified_above() 驱动的新早退既不多 RETRY 也不漏 RETRY'
source_email_count: 20
related_articles: []
tags:
- sched/core
- load_balance
---
