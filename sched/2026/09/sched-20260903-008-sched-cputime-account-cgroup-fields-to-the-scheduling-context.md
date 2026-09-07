# sched/cputime: Account cgroup fields to the scheduling context

## TL;DR

代理执行下 cgroup 的 CPU 统计被劈成两半：调度器运行时间记账把 cgroup 时间记到 donor，而 tick 与 vtime 更新 cgroup 字段时用的是执行任务。当 donor 与执行任务分属不同 cgroup 时，`cpu.stat` 的 usage 落到 donor 的 cgroup、user/system 落到执行任务的 cgroup，同一份时间被记到两个组。
Hui Su 的单补丁（本日 19:07 发出）把 cgroup 字段统一按**调度上下文**记账，同时让 per-CPU cpustat 继续按执行上下文记账，并新增 per-rq 的 cputime owner（`rq->cputime_donor`）处理 vtime 的延迟归属与跨边界残留。改动 197 行，是本日三件代理执行上下文修正里最大的一件。09-03 内无回帖。

## 背景与问题

代理执行把调度上下文（`rq->donor`）与执行上下文（`rq->curr`）分开后，两条记账路径对上下文的选择不一致：调度器运行时间记账把 cgroup 时间记给 donor，而 tick 与 vtime 记账在更新 cgroup 字段时使用的是执行任务。
作者在补丁里给出了修复前的实测现象：构造 donor 与执行任务分处不同 cgroup 的复现程序，可以观察到 **donor 的 cgroup 凭空获得 usage 时间，而执行任务的 cgroup 获得 system 时间**。对依赖 `cpu.stat` 做配额、计费或容量规划的 cgroup 用户，这是直接的统计错误。

## 技术方案

核心是把「谁拥有这段 CPU 时间」拆成两个独立问题，而不是统一到一个上下文上：
- **cgroup 字段按调度上下文记账**：新增 `cgroup_account_task()`，在 `sched_proxy_exec()` 开启时返回 `this_rq()->cputime_donor`，否则返回 `p`；原 `task_group_account_field()` 里的 per-CPU `kernel_cpustat` 累加被拆成独立的 `account_cpustat_field()`，因此 **per-CPU cpustat 仍跟随执行任务**，只有 cgroup 字段跟随调度上下文。CPU 侧 cpustat 的分类仍按执行任务，cgroup 字段的分类按记账 owner，`nice_usec` 同样遵循这一划分。
- **per-rq cputime owner**：保留 `rq->cputime_donor`，使延迟的虚拟 cputime 记账落到真正拥有该区间的调度上下文；`init_idle()` 初始化它，`finish_task_switch()` 调 `sched_cputime_switch()`，`__schedule()` 在 `prev == next` 时调 `sched_cputime_donor_changed()`。
- **异步 donor 重置的边界延迟**：唤醒可能在持有某个 rq lock 时重置 `rq->donor`。若该重置是远端的或发生在任务上下文之外，`proxy_reset_donor()` 走 `sched_cputime_donor_defer()`，把 cputime 边界推迟到目标 CPU 下次进入调度器，以避免访问远端/中断上下文的 vtime 与 per-CPU cpustat 状态；推迟期间对旧 cputime owner 持引用。
- **vtime 残留**：通用 vtime residuals 在代理边界处强制 flush，防止一个区间跨两个调度上下文。
- 明确不动的部分：per-task、thread-group 与 force-idle 记账保持不变。
辅助说明：改动集中在 `kernel/sched/cputime.c`（+189）、`core.c`（+17）、`sched.h`（+8），大部分新逻辑由 `CONFIG_SCHED_PROXY_EXEC` 与 `sched_proxy_exec()` 双重门控。

## 版本演进与当前进展

- 本日单 patch 首发（v1），带 `Fixes: aa4f74dfd42b`（"sched: Fix runtime accounting w/ split exec & sched contexts"），无 `Cc: stable`。
- 09-03 内无回帖、无 tag、未进入任何分支。
- 属「代理执行执行上下文修正」主线：同日 [[sched-20260903-001]]（NUMA/cache tick，已迭代到 v2 并有 Intel/AMD 实质评审）与 [[sched-20260903-005]]（RT watchdog）同作者、同基线；三者里本补丁体量最大（197 行）而评审进度最慢。

## Maintainer 意见与讨论焦点

未获取到维护者意见：补丁于 09-03 19:07 发出，当日缓存内无人回帖；尤其值得注意的是 **Tejun Heo（cgroup 维护者）当天没有对 cgroup 统计语义的这一改动表态**，而同作者的 [[sched-20260903-003]]、[[sched-20260903-014]] 两个 sched_ext 补丁当天都已拿到他的处理结果，说明他当日在线。
可预见的讨论焦点（依据补丁自身内容，而非回帖）：
- cgroup `cpu.stat` 的 usage/user/system 首次被明确定义为「调度上下文」口径，而 `/proc/<pid>/stat` 与 per-CPU cpustat 仍是「执行上下文」口径。这种同一时间双口径的划分是否要在 `Documentation/admin-guide/cgroup-v2.rst` 里写清，作者未提。
- 延迟边界方案里「持旧 owner 引用 + 推迟到目标 CPU 下次进入调度器」是全套改动中最需要并发评审的部分：它引入了一个新的生命周期，而 `proxy_reset_donor()` 本身已有 `WARN_ON_ONCE(rq->donor == rq->curr)` 前置。

## 合入评估

likelihood: **possible**。
依据：问题定义清晰且有实测差分（usage 与 system 落到不同 cgroup），带指向已合入 tip 提交的 `Fixes` 标签；作者用 `CONFIG_SCHED_PROXY_EXEC` + `sched_proxy_exec()` 双重门控，明确声明 per-task/thread-group/force-idle 记账不变，所以对非代理执行配置零风险——这大幅降低了合入阻力。
卡点：一是 197 行改动全部落在 cputime/vtime 这个历史上极易出并发问题的区域，而线程内目前零评审；二是 cgroup 侧维护者（Tejun Heo）尚未确认「cgroup 字段按调度上下文」这一新口径，该口径会直接影响 cgroup v2 的对外统计契约，属于必须拿到 ack 的部分；三是 `deferred cputime boundary + 持旧 owner 引用` 是一个新的生命周期，需要 Peter Zijlstra/Thomas Gleixner 侧确认 vtime 序列与引用释放顺序无窗；四是与同作者另外两个上下文修正补丁共享基线，很可能被要求作为一个簇统一排队。

## 效果评估

邮件中未提供性能数据。功能验证为三种配置组合下的实测/构建：
- `CONFIG_SCHED_PROXY_EXEC=y` + `CONFIG_VIRT_CPU_ACCOUNTING_GEN=y` 下跑代理执行 cgroup 复现程序；
- `CONFIG_SCHED_PROXY_EXEC=y` + `CONFIG_VIRT_CPU_ACCOUNTING=n`；
- `CONFIG_SCHED_PROXY_EXEC=n` + `CONFIG_VIRT_CPU_ACCOUNTING_GEN=y` 构建通过。
修复前复现给出的定性结果是 donor cgroup 增长 usage、执行 cgroup 增长 system。缺少的是修复后同一复现的数值对照（例如两个 cgroup 的 usage/user/system 加和是否等于总执行时间），这正是最容易被补上的一块证据。

## 我可以参与的点

1. 与用户主线（cpuset/cgroup）直接相关，是今天最值得介入的一条：可以给出「cgroup 字段跟随调度上下文、per-CPU cpustat 跟随执行上下文」这一划分对 cgroup v2 用户可见语义的影响评估，并追问是否需要同步 `Documentation/admin-guide/cgroup-v2.rst`。这类意见来自 cgroup 侧使用者比来自调度器侧更有分量。
2. 可跑的验证：在开 `PROXY_EXEC` 的内核上构造 donor/执行任务分属两个 cgroup 的场景，量化补丁前后 `cpu.stat` 的 usage/user/system 以及 `cat /proc/stat` 的守恒性（两 cgroup 之和 == 总执行时间），把结果贴回线程。
3. 可复核的代码点：`sched_cputime_donor_defer()` 的推迟路径——旧 cputime owner 的引用在目标 CPU 长时间不调度（如 `nohz_full` 上纯内核工作负载）时会不会长期不释放；以及 `cgroup_account_task()` 用 `this_rq()` 取值在中断上下文中是否总能拿到有效 donor。
4. 回合视角：若 OLK-6.6 引入任何「替执行」类机制，本补丁给出的结论——运行时间归属、cgroup 字段归属、vtime 边界三者必须分别定义并在边界处 flush——是必须抄的清单；但 diff 本身依赖 `rq->donor`、`cputime_donor`、`CONFIG_VIRT_CPU_ACCOUNTING_GEN` 三者，6.6 上不可直接回合。

## 参考链接

- 本补丁：https://lore.kernel.org/all/5733b51108eda90c1bda98a68d58b5e6ccbc24ec.1788433334.git.sh_def@163.com/
- 相关文章/系列：
  - [[sched-20260903-001]] 代理执行下执行上下文 tick 处理（同作者、同一主线，进度最快）。
  - [[sched-20260903-005]] RT watchdog 记账归属（同作者、同簇）。
- 相关代码：
  - `kernel/sched/cputime.c` `task_group_account_field()` / `cgroup_account_task()` / vtime 边界
  - `kernel/sched/core.c` `proxy_reset_donor()` / `finish_task_switch()` / `init_idle()`

---
id: sched-20260903-008
date: '2026-09-03'
subject: 'sched/cputime: Account cgroup fields to the scheduling context'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<5733b51108eda90c1bda98a68d58b5e6ccbc24ec.1788433334.git.sh_def@163.com>'
lore_url: https://lore.kernel.org/all/5733b51108eda90c1bda98a68d58b5e6ccbc24ec.1788433334.git.sh_def@163.com/
upstream_commit: null
fixes_commit: 'aa4f74dfd42b'
merged_branch: null
current_version: v1
generated_at: '2026-09-07'
authors:
- Hui Su
maintainers_involved: []
patch_series:
- "sched/cputime: Account cgroup fields to the scheduling context"
merge_assessment:
  likelihood: medium
  blocking_issues:
  - "线程内零评审，197 行全部落在 cputime/vtime 并发敏感区"
  - "cgroup 维护者 Tejun Heo 未确认 cgroup 字段按调度上下文这一新对外口径"
  - "deferred cputime boundary + 持旧 owner 引用是新增生命周期，未经评审"
  - "与同作者另两个上下文补丁共享基线，可能被要求成簇排队"
  next_action: "从 cgroup 侧就新统计口径与文档影响提问，并补一份补丁前后 cpu.stat 守恒性数值对照"
contribution_opportunities:
- "评估 cgroup 字段按调度上下文对 cgroup v2 用户可见语义的影响并追问文档更新"
- "量化补丁前后 donor/执行两个 cgroup 的 usage/user/system 守恒性"
- "复核 sched_cputime_donor_defer() 在 nohz_full 长期不调度时旧 owner 引用的释放时机"
source_email_count: 1
related_articles:
- sched-20260903-001
tags:
- sched/core
- cgroup
- proxy_execution
---
