# sched: Account cgroup CPU time to the execution context

## TL;DR

代理执行下 `cgroup_account_cputime()` 把 CPU 时间记到 donor，而 per-task / thread-group / cgroup 的 user/system 字段已记到实际执行任务，donor 与执行任务分属不同 cgroup 时用量会被算到别的组。Hui Su 的 v2 沿用 Tejun Heo 的意见，改成 cgroup CPU usage 跟随执行上下文（`rq->curr`），实际只有 `kernel/sched/fair.c` 的 1 行改动；Tejun 已给出带条件的 Acked-by（「Provided John is okay with going this way」）。

## 背景与问题

`aa4f74dfd42b`（"sched: Fix runtime accounting w/ split exec & sched contexts"）让 per-task 与 thread-group 的运行时间记账跟随真正执行的任务，但 cgroup CPU usage 仍按 donor 记。当 donor 与执行任务在不同 cgroup 时，一个任务的执行时间被算进它并不属于的那个 cgroup。

作者最初的 v1 走的是反方向：把 tick/vtime 的 cgroup user/system 字段也改到调度上下文（donor），并为 vtime 引入 per-rq 的 cputime owner、延迟边界与 donor 生命周期引用，改动 197 行、涉及 `core.c` / `cputime.c` / `sched.h`。这个方向被 Tejun Heo 否掉，理由是用户态看到的 user/sys 是从 `usage_usec` 摊出来的，同一份数据内部必须先自洽，而线程一级的报表已跟随执行上下文，cgroup 没有理由偏离。

## 技术方案

- v2 只改 `kernel/sched/fair.c` 的 `update_se()`：删除 `struct task_struct *donor = task_of(se);`，把 `cgroup_account_cputime(donor, delta_exec)` 换成 `cgroup_account_cputime(running, delta_exec)`，其中 `running = rq->curr`。净变化 1 行新增 / 3 行删除。
- 调度状态（`rq->donor`、EEVDF 队列归属、slice 与 vruntime）仍留在 donor，只有 cgroup CPU usage 的记账目标改成执行上下文；这样 cgroup 的 usage 与 user/system 字段口径一致。
- v1 中的 per-rq cputime owner、延迟边界处理、donor 生命周期引用在 v2 全部删除，被 Tejun 的方案取代。
- 补丁带 `Fixes: aa4f74dfd42b` 与 `Suggested-by: Tejun Heo <tj@kernel.org>`。

## 版本演进与当前进展

- v1（09-03，`5733b51108eda90c1bda98a68d58b5e6ccbc24ec.1788433334.git.sh_def@163.com`，标题为 `sched/cputime: Account cgroup fields to the scheduling context`）：把 cgroup 字段记到调度上下文，同时把 per-CPU cpustat 记账与 cgroup 字段记账拆开，另加 vtime 残差在代理边界冲刷。09-04 01:30 Tejun 明确反对这一方向。
- 09-04 10:37 作者接受，并指出自己此前把问题描述成「用户可见的 cpu.stat 不一致」说得过头（`cputime_adjust()` 本来就会把 user/system 拆分对总量做配平）。
- v2（本日 11:47，`20260904034707.268416-1-sh_def@163.com`）：反转为「cgroup CPU usage 跟随执行上下文」，改动从 197 行缩到 4 行。Changes since v1 三条：按 Tejun 意见重做方向；删掉 owner/边界/生命周期机制；重做 reproducer 的预期。
- 09-04 14:37 Tejun 给出条件性 `Acked-by: Tejun Heo <tj@kernel.org>`，条件是 John 也认可该方向。本日匹配 5 封邮件。

## Maintainer 意见与讨论焦点

**Tejun Heo（cgroup 维护者，决定性意见）**
- 01:30 否掉 v1 方向："When these numbers are presented to the userspace, the user/sys split is calculated out of usage_usec, so at least the presented numbers should be coherent no matter what. I don't think it makes sense for cgroup's usage times to deviate from how thread's get reported. Threads follow execution context. All cgroup numbers should too." 并给出未来出口：若担心 `usage_usec` 与带宽控制结果不一致，可以「show donation time separately」，但 "let's worry about that later"。
- 14:27 重申立场并留待他人："cgroup accounting deviating from task accounting doesn't seem to make sense to me but I haven't thought too much about proxy execution, so let's hear what John has to say."
- 14:37 对 v2："Provided John is okay with going this way: Acked-by: Tejun Heo <tj@kernel.org>. The diff looks so much better."

**Hui Su（作者）**：10:37 承认对不一致性的描述过强，说明 v1 是跟随 `aa4f74dfd42b` 里 `cgroup_account_cputime()` 记到 donor 的既有行为去补齐 tick/vtime 侧，接受改用执行上下文方向。

**讨论焦点**：唯一实质分歧是「代理执行期间这段时间在语义上属于谁」——Tejun 的选择是记账口径统一跟随执行上下文，把 donor 语义留给调度状态；被点名的 "John"（正文中未给出姓氏）尚未表态，这是当前唯一的悬置项。此外「donation time 单独呈现」被明确推迟，未来若要给 cpu.stat 增加捐赠时间字段，会另开讨论。

## 合入评估

likelihood: **likely**。

依据：cgroup 侧维护者 Tejun Heo 已给出 Acked-by；补丁带 `Fixes:`，是对 `aa4f74dfd42b` 引入的行为缺口的直接修正；改动只有 1 行、方向与既有 per-task / tg 记账一致，不新增机制；作者给出了 cgroup v2、RT donor、cgroup v1 cpuacct、`sched_proxy_exec=off` 对照组四类验证。

卡点：
- Tejun 的 Acked-by 是条件式的——需要他点名的 John 认可该方向，缓存中未见该回复。
- 依赖 proxy execution 的调度器侧接受度：Peter Zijlstra / Ingo Molnar 本日未参与该线程，缓存中未获取到表态。
- 语义变更对用户态可见（受代理执行影响的 cgroup 的 `cpu.stat usage_usec` 会变大/变小），若上游要求，可能补一条 Documentation 或 cgroup 变更说明；邮件中未讨论这点。

## 效果评估

邮件正文给出的是 reproducer 级验证数据（v2 changelog，非性能基准）：

- cgroup v2 代理执行 reproducer：执行任务 runtime +1.483s；donor 所在 cgroup A 的 usage +0；执行任务所在 cgroup B 的 usage +1.629s。
- RT donor reproducer：执行任务 runtime +0.991s；donor cgroup A usage +125us；执行 cgroup B usage +0.991s。
- cgroup v1 cpuacct：usage 记到执行者所在 cgroup。
- `sched_proxy_exec=off` 对照组通过；`CONFIG_SCHED_PROXY_EXEC` / `CONFIG_CGROUPS` / `CONFIG_CGROUP_CPUACCT` 构建矩阵通过；`W=1 kernel/sched/fair.o`、`checkpatch --strict`、`git diff --check` 通过。

未提供：对带宽控制（CFS quota）判定结果的量化影响，以及代理执行规模场景下的开销数据。

## 我可以参与的点

- **直接命中主线工作**：这是对 cgroup CPU 用量口径的语义变更。可以复核的具体点：`update_se()` 中 `entity_is_task(se)` 分支下 `running = rq->curr` 的取值时机（代理执行中 `rq->curr` 可能刚被 `proxy_reset_donor()` 改掉），以及非任务 se 分支仍按 donor `se->sum_exec_runtime += delta_exec` 是否与 cgroup 口径自洽。
- **cpu.max 交互**：Tejun 提到「usage_usec 与带宽控制结果可能不一致」这一担忧被推迟。如果有兴趣，可以在 `CONFIG_CFS_BANDWIDTH` + 代理执行下测 `cpu.max` 的限流行为与 `usage_usec` 是否匹配，给后续「show donation time separately」的讨论攒数据。
- **回合检查**：OLK-6.6 若已回合 `aa4f74dfd42b`（或其等价补丁），本补丁应一并回合，否则受代理执行影响的 cgroup 用量归属会与上游不一致；若未回合 proxy execution，则不需要。
- **测试补充**：作者已有单任务级 reproducer，可帮忙补一个多 cgroup、带 RT/deadline donor 混合的长稳用例，确认 `cpuacct`（v1）与 `cpu.stat`（v2）在两种层级布局下都不串账。

## 参考链接

- 邮件线程：
  - v2 补丁: <https://lore.kernel.org/all/20260904034707.268416-1-sh_def@163.com/>
  - Tejun Heo 的条件性 Acked-by: <https://lore.kernel.org/all/appnKwylGK3QUIJ3@slm.duckdns.org/>
  - Tejun Heo 否掉 v1 方向的首评: <https://lore.kernel.org/all/apmuywWz3c0keI2i@slm.duckdns.org/>
  - Tejun Heo 留待 John 表态: <https://lore.kernel.org/all/appk0wG9RlWojNLJ@slm.duckdns.org/>
  - 作者接受意见的回帖: <https://lore.kernel.org/all/20260904023705.106589-1-sh_def@163.com/>
  - v1（反向方案）: <https://lore.kernel.org/all/5733b51108eda90c1bda98a68d58b5e6ccbc24ec.1788433334.git.sh_def@163.com/>
- 相关文章/系列：
  - [[sched-20260903-008]] 同一问题的 v1 方案（把 cgroup 字段记到调度上下文），已被本 v2 取代。
- 相关代码/commit：
  - `kernel/sched/fair.c` `update_se()`
  - `aa4f74dfd42b` "sched: Fix runtime accounting w/ split exec & sched contexts"
  - `kernel/sched/cputime.c`（v1 曾改动，v2 未触及）

---
id: sched-20260904-003
date: '2026-09-04'
subject: 'sched: Account cgroup CPU time to the execution context'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: 20260904034707.268416-1-sh_def@163.com
lore_url: https://lore.kernel.org/all/20260904034707.268416-1-sh_def@163.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: '2026-09-07'
authors:
- Hui Su
maintainers_involved:
- Tejun Heo
patch_series:
- 'sched: Account cgroup CPU time to the execution context'
merge_assessment:
  likelihood: high
  blocking_issues:
  - 等待 Tejun 点名的 John 认可「cgroup usage 跟随执行上下文」这一方向
  - 缓存中未见调度器侧维护者（Peter Zijlstra / Ingo Molnar）表态
  - 用户可见语义变更未附带文档说明的讨论
  next_action: 跟进 John 的回复；若无异议，本补丁可作为 sched/urgent 或 cgroup 树的修复排队。
contribution_opportunities:
- 复核 update_se() 中 rq->curr 与 proxy_reset_donor() 的时序，确认 cgroup 记账目标不会漂
- 在 CONFIG_CFS_BANDWIDTH + 代理执行下测 usage_usec 与 cpu.max 限流的一致性，为 donation time 展示做数据准备
- 补多 cgroup、RT/deadline donor 混合的长稳用例，覆盖 cgroup v1 cpuacct 与 v2 cpu.stat
- 评估 OLK 回合必要性：仅在已回合 aa4f74dfd42b 的前提下需要一并回合
source_email_count: 5
related_articles:
- sched-20260903-008
tags:
- sched/core
- cgroup
- proxy_execution
---
