# sched_ext: Fix NULL sched deref in kfunc sub-sched error paths

## TL;DR

Wanwu Li 发现两个 COMPAT kfunc 包装器（`scx_bpf_select_cpu_and()`、`scx_bpf_dsq_insert_vtime()`）在挂了 sub-sched 时会用 `scx_task_sched(p)` 去 `scx_error()`，而该字段对「已过 `sched_ext_dead()` 的任务」和 idle 任务为 NULL，NULL 会一路传到 `scx_vexit()` 无条件解引用 `sch->exit_info`（偏移 0x398）直接 Oops。本日 Tejun Heo 回复「Applied to sched_ext/for-7.3-fixes with "# v7.1+" added to the stable Cc」，v3 已入 fixes 树并将派生 stable。

## 背景与问题

根因链条在正文里写得很具体：

- 包装器在 root sched 挂了 sub-sched 时拒绝调用：`scx_error(scx_task_sched(p), "__scx_bpf_dsq_insert_vtime() must be used")`。
- `scx_task_sched(p)` 读的是 `p->scx.sched`。它在 `init_scx_entity()` 里被 memset、由 `sched_ext_dead()` 走的 `scx_disable_and_exit_task()` 在任务退出时清空，因此对「已 dead 的任务」和 idle 任务为 NULL；同时它本身是 `rcu_dereference_protected()`，期望持有 @p 的 `pi_lock` 或 rq lock，而两个包装器都没持。
- `scx_error()` → `scx_vexit()` 会无条件解引用 `sch->exit_info`，传 NULL 就崩。
- 可达性：`scx_bpf_select_cpu_and()` 属 select_cpu 组，`scx_kfunc_context_filter()` 对该组开放 `BPF_PROG_TYPE_SYSCALL`；`scx_bpf_dsq_insert_vtime()` 属 enqueue_dispatch 组，`ops.enqueue()` / `ops.dispatch()` 可以带任意 KF_RCU 任务调用它——该组没有 `kf_tasks` 校验，而 `scx_dsq_insert_preamble()` 正是因为 @p 可能是任意任务才用 `scx_task_on_sched()` 判归属。
- 触发不需要特殊构造：从 `bpf_task_from_pid()` 拿到的任务可以在调用落地前退出，僵尸在被回收前对 pid 查找仍然可见；idle 任务则天然为 NULL。

作者在开发过程中真跑出过这个 Oops（v7.2 基线、`BPF_PROG_TYPE_SYSCALL` 程序对已退出未回收任务调用 select_cpu_and 包装器，且挂了 sub-scheduler）：崩溃指令是 `scx_vexit()` 序言 `mov r15,[rdi+0x398]`，RDI=NULL，0x398 即 `sch->exit_info` 偏移；调用栈 `scx_bpf_select_cpu_and+0xab/0xb0` → `__scx_exit+0x4f/0x70` → `scx_vexit+0x25/0xa0`，`CR2: 0000000000000398`。

## 技术方案

最终形态（v3）不引入新的 flag/warn-once 机制，而是「能确定就报错、不能确定就只拒绝」：

```
if (unlikely(!list_empty(&sch->children))) {
	struct scx_sched *tsch = scx_task_sched_rcu(p);

	if (tsch)
		scx_error(tsch, "__scx_bpf_dsq_insert_vtime() must be used");
	return;   /* select_cpu_and 处为 return -EINVAL */
}
```

要点：
- 用 `scx_task_sched_rcu(p)` 取代 `scx_task_sched(p)`，包装器本来就在 `guard(rcu)()` 下，可以直接做 RCU 读取。
- `tsch` 为 NULL（@p 是已过 `sched_ext_dead()` 的任务或 idle 任务）时不再判为调度器出错，只按原样拒绝调用——因为「本来就没有明显错误可报」。
- 两处改动分别在 `kernel/sched/ext/ext.c`（`scx_bpf_dsq_insert_vtime()`）与 `kernel/sched/ext/idle.c`（`scx_bpf_select_cpu_and()`），各 11 行、合计 18 增 4 删。
- 注释同步改写为「read it under RCU as @p's locks aren't necessarily held here」并说明 NULL 情形。
- 标签：`Fixes: a5fa0708cbfd ("sched_ext: Enforce scheduling authority in dispatch and select_cpu operations")`、`Cc: <stable@vger.kernel.org>`、`Suggested-by: Andrea Righi`。

## 版本演进与当前进展

- v1（09-02 23:36，`20260902153640.144791-1-liwanwu@kylinos.cn`）标题只覆盖 `select_cpu_and` 一处，做法是用 `scx_task_sched_rcu()` 并在拿不到时回落到 root scheduler。
- Andrea Righi（09-03 00:14）确认崩溃与方向正确，但指出 `scx_bpf_dsq_insert_vtime()` 同样受影响——SYSCALL 程序调不到它，但 STRUCT_OPS 程序可以在 `ops.enqueue()` / `ops.dispatch()` 里调；作者 00:34 承认「This one is my miss」。
- v2（09-03 01:07，`20260902170751.256434-1-liwanwu@kylinos.cn`）改为两片同修、标题变成现在的 `kfunc sub-sched error paths`；Andrea Righi 02:11 给出 `Reviewed-by`。
- Tejun Heo（09-03 03:37）指出三处描述错误并否掉「拿不到就报错到 root sched」的回落；03:39 又补一句「直接忽略也可以」。
- v3（09-03 14:06，`20260903060626.814951-1-liwanwu@kylinos.cn`）按 Tejun 意见改成「拿不到就只拒绝、不报错」，并修正注释措辞。
- 09-04 01:56 Tejun Heo：`Applied to sched_ext/for-7.3-fixes with "# v7.1+" added to the stable Cc.` 本日按 subject 匹配到 1 封邮件（该 apply 通报）。

## Maintainer 意见与讨论焦点

**Andrea Righi（09-03 00:14，v1）**：`"The reported crash looks valid to me, and using scx_task_sched_rcu() with the root scheduler as fallback also looks correct."` 但紧接着扩了修复面：`"as also pointed out by sashiko, the assumption above doesn't hold for scx_bpf_dsq_insert_vtime(), although SYSCALL programs can't call it, STRUCT_OPS programs can call it from ops.enqueue() and ops.dispatch(). Can you update scx_bpf_dsq_insert_vtime() as well with the same fallback?"` —— v1→v2 的范围扩展完全由这条驱动，v3 的 `Suggested-by` 也给了他。

**Tejun Heo（09-03 03:37，v2）** 四条纠正，是 v2→v3 的唯一驱动：
1. 事实纠正：`"This isn't accurate. p->scx.sched is set for every non-idle task on root enable and on fork regardless of sched class. The only tasks with NULL p->scx.sched are the ones past sched_ext_dead() and the idle tasks."` —— 作者原先「被别的调度器管理的任务为 NULL」的说法是错的，v2 还据此写成 kthread 与 `SCX_SWITCH_ALL=n` 下其它调度类的任务会长期 NULL；Tejun 给的口径是：root enable 与 fork 时对所有非 idle 任务都会赋值，真正的 NULL 只有已过 `sched_ext_dead()` 的任务与 idle 任务。
2. 归属纠正：`"Both of those error out the calling program's scheduler, not @p's. The compat wrappers are the only ones using @p's scheduler and only because they don't have @aux."`
3. 锁措辞纠正：`"@p's locks are held when called from ops.select_cpu() or ops.enqueue(). The ext.c comment's 'aren't necessarily held' is the right wording."`
4. 设计纠正：`"As the fallback only triggers for tasks already past sched_ext_dead() (or idle tasks), tearing down the root scheduler doesn't make sense. How about adding a flag to the root sched and printing a warning once instead?"`，随后 03:39 放宽：`"It'd be fine to just ignore it too. The scx_error() is there to flag cases where things went obviously wrong. I don't think we'd lose anything meaningful by just ignoring it when sch can't be determined."`

**讨论焦点**：争的不是「要不要修」而是「拿不到 @p 的 sched 时该做什么」——报给 root sched（v1/v2 做法，Tejun 认为对一个已 dead 的任务去 tear down root sched 没有意义）、加 flag 只 warn 一次（Tejun 的第一个提议）、还是静默拒绝（Tejun 第二个提议，v3 采纳）。作者选了最小那条路，也顺带避开了给 root sched 增状态。

值得记一笔的语义收获：`p->scx.sched` 的赋值时机（root enable 与 fork，与调度类无关）经维护者之口被澄清，这纠正了作者 v1/v2 的整个可触达性论证。

## 合入评估

likelihood: **likely**（已合入 fixes 树）。

依据：Tejun Heo 09-04 明确 applied 到 `sched_ext/for-7.3-fixes`，并且把 stable Cc 补成 `# v7.1+`；此前已有 Andrea Righi 的 `Reviewed-by`，v3 已把维护者三条纠正全部落实，无遗留异议；补丁带 `Fixes:`、规模 18 增 4 删，属典型 fixes 通道内容。

卡点：
- 只剩流程：`for-7.3-fixes` 需由 Tejun 向主线发 fixes pull。
- `# v7.1+` 是维护者手工补的判定，stable 派发范围以他给的口径为准，而非作者原先的 `Cc: <stable@vger.kernel.org>`。

## 效果评估

邮件中未提供性能数据，这类修复也没有性能维度。功能证据是作者在开发过程中真实复现的 Oops：NULL 指针崩溃地址 `0000000000000398`、崩溃点 `scx_vexit+0x25/0xa0`（`mov r15,[rdi+0x398]`，RDI=NULL）、`CPU: 7 PID: 8201 Comm: kfunc_test_runn`，前提是 `kfunc_subsched_null` 这个调度器与其 sub-scheduler 同时 enable。修复后同一程序路径只返回 `-EINVAL` / 直接 return 而不退出调度器。改动规模：`ext.c` 与 `idle.c` 各 11 行上下文、合计 18 增 4 删。

## 我可以参与的点

- **可直接读的机制点**：`p->scx.sched` 的语义边界（root enable + fork 时赋值；只有 dead 任务与 idle 任务为 NULL；读取需 `pi_lock` 或 rq lock，否则必须走 `scx_task_sched_rcu()`）。这是 sub-sched 引入后新出现的一条约束，任何在内核侧或 BPF 侧碰 `p->scx.sched` 的代码都要按它自检——这类「维护者一句话纠正一个普遍误解」的邮件值得摘录进内部知识库。
- **可复用的自检方向**：本片暴露的是 `scx_error()` / `scx_vexit()` 会无条件解引用 `sch->exit_info` 这个更普遍的前置问题。凡是可能拿到 `scx_sched *` 的路径都值得检查是否有同类无判空解引用；把「NULL 时只拒绝、不报错」定成约定，也可以反过来提给维护者作为统一做法。
- **回合判断（对 OLK-6.6 有直接意义）**：带 `Fixes: a5fa0708cbfd` + `# v7.1+`，是 stable 通道补丁。可操作动作是先确认内部树是否已引入 `CONFIG_EXT_SUB_SCHED` 与 COMPAT 包装器 `scx_bpf_select_cpu_and()` / `scx_bpf_dsq_insert_vtime()`；都没有就没有回合对象，若已有 sub-sched 但缺这个防护，则应把它当作可触发 Oops 的安全级修复优先排。

## 参考链接

- 邮件线程：
  - v1: <https://lore.kernel.org/all/20260902153640.144791-1-liwanwu@kylinos.cn/>
  - v2: <https://lore.kernel.org/all/20260902170751.256434-1-liwanwu@kylinos.cn/>
  - v3（被合入版本）: <https://lore.kernel.org/all/20260903060626.814951-1-liwanwu@kylinos.cn/>
  - Tejun Heo 的四条纠正: <https://lore.kernel.org/all/d819e8358fffc09015feffad57794f7c@kernel.org/>
  - Tejun Heo 的「直接忽略也可以」: <https://lore.kernel.org/all/aph7j7b_rqqqcSwR@slm.duckdns.org/>
  - Tejun Heo 的 apply 通报: <https://lore.kernel.org/all/2edcf44237f7a5e81c6ec97a81b56d5b@kernel.org/>
  - Andrea Righi 要求扩到 dsq_insert_vtime: <https://lore.kernel.org/all/aphLWtCVY1XVME9C@gpd4/>
  - Andrea Righi 的 Reviewed-by: <https://lore.kernel.org/all/aphmwjLkdS4tKpbv@gpd4/>
- 相关文章/系列：
  - [[sched-20260903-004]] sched_ext sub-sched 错误路径 NULL deref（kfunc v3 + select_cpu_and）。
- 相关代码/commit：
  - `a5fa0708cbfd` "sched_ext: Enforce scheduling authority in dispatch and select_cpu operations"
  - `kernel/sched/ext/ext.c` `scx_bpf_dsq_insert_vtime()` / `kernel/sched/ext/idle.c` `scx_bpf_select_cpu_and()`
  - `scx_task_sched()` / `scx_task_sched_rcu()` / `scx_vexit()`

---
id: sched-20260904-011
date: '2026-09-04'
subject: 'sched_ext: Fix NULL sched deref in kfunc sub-sched error paths'
subsystem: sched
type: fix
status: merged_tip
severity: high
thread_root_msgid: 20260902153640.144791-1-liwanwu@kylinos.cn
lore_url: https://lore.kernel.org/all/20260903060626.814951-1-liwanwu@kylinos.cn/
upstream_commit: null
fixes_commit: a5fa0708cbfd
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
  likelihood: likely
  blocking_issues:
  - 无技术卡点，仅剩 for-7.3-fixes 向主线发 fixes pull 的流程
  - stable 派发范围由维护者手工改为 v7.1+，需按该口径而非作者原始 Cc stable
  next_action: 等待 sched_ext fixes pull 通报；若内部树已引入 CONFIG_EXT_SUB_SCHED 与 COMPAT 包装器，按可触发 Oops 的安全级修复优先排队回合。
contribution_opportunities:
- 摘录并核对 p->scx.sched 的赋值/清空时机与锁要求，检查其它直接读 p->scx.sched 的调用点是否满足
- 排查 scx_error()/scx_vexit() 链路上是否还有无判空的 scx_sched 解引用
- 向维护者提议把「无法确定所属 sched 时只拒绝调用」确立为统一约定，而非逐个补丁处理
source_email_count: 1
related_articles:
- sched-20260903-004
tags:
- sched_ext
- crash
---
