# sched_ext: Fix NULL sched deref in kfunc sub-sched error paths

## TL;DR

带 sub-sched 时，COMPAT 包装 `scx_bpf_select_cpu_and()` 与 `scx_bpf_dsq_insert_vtime()` 会用 `scx_error(scx_task_sched(p), ...)` 报错，而 `p->scx.sched` 对「已过 `sched_ext_dead()` 的任务」和 idle 任务是 NULL，于是 `scx_error()` 一路走到 `scx_vexit()` 解引用 `sch->exit_info`，直接 oops（实测崩溃地址 0x398）。
Wanwu Li 的修复是改用 `scx_task_sched_rcu()` 在 RCU 下读该指针。本日走完 v2→v3：Andrea Righi 的 `Reviewed-by` 落在 v2，Tejun Heo 在 v2 上指出提交说明对 `p->scx.sched` 何时为 NULL 的描述不准确、并反对「无法判定时就把 root 调度器 error out」，v3 已按此改为「判不出来就单纯拒绝调用」。截至 09-03 结尾 v3 尚无新 tag。

## 背景与问题

两个 COMPAT 包装在拒绝调用时把错误报告给 `@p` 所属的调度器：`scx_error(scx_task_sched(p), "... must be used")`。可达性来自 `scx_kfunc_context_filter()`：
- `scx_bpf_select_cpu_and()` 属于 `select_cpu` kfunc 组，该组对 `BPF_PROG_TYPE_SYSCALL` 程序开放；
- `scx_bpf_dsq_insert_vtime()` 属于 `enqueue_dispatch` 组，该组没有 `kf_tasks` 校验，`ops.enqueue()` / `ops.dispatch()` 可以带任意 KF_RCU 任务指针调用它——`scx_dsq_insert_preamble()` 之所以用 `scx_task_on_sched()` 检查所有权，正是因为 `@p` 可能是任意任务。
而 `scx_task_sched(p)` 就是 `p->scx.sched`：任务退出时 `scx_disable_and_exit_task()` 会经 `sched_ext_dead()` 清空它，idle 任务则从不经过 SCX 启用路径。此外该访问本身是 `rcu_dereference_protected()`，前提是持有 `@p` 的 `pi_lock` 或 rq lock，而这两个包装都没有持。传 NULL 给 `scx_error()` 会进入 `scx_vexit()` 并解引用 `sch->exit_info` -> 内核 oops。
作者在开发中真跑出一个触发路径：`BPF_PROG_TYPE_SYSCALL` 程序在有 sub-scheduler 附着时对「已退出但未被回收」的任务调用 `select_cpu_and` 包装（僵尸未被 reap 期间其 pid 仍可查找），崩溃点为 `scx_vexit+0x25/0xa0`、`CR2: 0000000000000398`，`Comm: kfunc_test_runn`。

## 技术方案

在包装自带的 `guard(rcu)` 下改用 `scx_task_sched_rcu()` 读取 `@p` 的调度器。v3 的最终语义（按 Tejun 意见收敛）是：
- 能判定所属调度器时，照常 `scx_error()` 该调度器；
- 判定不出时（`@p` 是已过 `sched_ext_dead()` 的任务或 idle 任务），**不再 fault 任何调度器**，只像原来那样拒绝调用——因为此时并没有明显错误可报告。
两个触发点（`scx_bpf_select_cpu_and()`、`scx_bpf_dsq_insert_vtime()`）用同一套 fallback 处理。改动仅 `kernel/sched/ext/ext.c` 与另一文件的小范围（v2 diffstat：`ext.c +9/-2`）。带 `Cc: stable`、`Fixes: a5fa0708cbfd`（"sched_ext: Enforce scheduling authority in dispatch and select_cpu operations"）、v3 起 `Suggested-by: Andrea Righi`。作者也说明这些 COMPAT 包装在弃用宽限期结束后会被移除，但无论移除时间表如何，它们都不该对拿到的任务 oops。

## 版本演进与当前进展

- v1（09-02 15:36，标题为 "... in select_cpu_and sub-sched error path"）只处理 `scx_bpf_select_cpu_and()`。
- Andrea Righi 09-03 00:14 确认崩溃与 fallback 方向都成立，但指出 `scx_bpf_dsq_insert_vtime()` 的假设不成立：SYSCALL 程序调不到它，可 STRUCT_OPS 程序能从 `ops.enqueue()` / `ops.dispatch()` 调用它，要求补同一 fallback。作者 00:34 承认 "This one is my miss"（只从 SYSCALL 拒绝角度推理，忽略了同一 kfunc 组经 struct_ops 的可达性），并致谢 sashiko-bot 的同一提示。
- v2（09-02 17:07）改标题为 "kfunc sub-sched error paths" 并覆盖两个包装；Andrea Righi 09-03 02:11 给 `Reviewed-by`。
- Tejun Heo 09-03 03:37/03:39 提出三处不准确与一个替代方案；v3（09-03 14:06）按此把「fallback 到 root 调度器」改为「判定不出即拒绝」，并补 `Suggested-by: Andrea Righi`。
- 本日为 v3，09-03 内无 v3 的复审回帖。

## Maintainer 意见与讨论焦点

- **Andrea Righi（NVIDIA）**：确认问题真实且方向正确（"The reported crash looks valid to me, and using scx_task_sched_rcu() with the root scheduler as fallback also looks correct"），并给出 v1→v2 的唯一实质缺口（`scx_bpf_dsq_insert_vtime()` 经 struct_ops 可达）；v2 上给 `Reviewed-by: Andrea Righi`。
- **Tejun Heo（sched_ext 维护者）**：v2 上三处技术反驳——
  1. "This isn't accurate. p->scx.sched is set for every non-idle task on root enable and on fork regardless of sched class. The only tasks with NULL p->scx.sched are the ones past sched_ext_dead() and the idle tasks."（即 v2 注释里「由另一个调度器管理」的说法是错的）；
  2. "Both of those error out the calling program's scheduler, not @p's."——混淆了被报错的对象；
  3. "@p's locks are held when called from ops.select_cpu() or ops.enqueue(). The ext.c comment's 'aren't necessarily held' is the right wording."；
  4. 设计上反对把 root 调度器 teardown 作为 fallback："As the fallback only triggers for tasks already past sched_ext_dead() (or idle tasks), tearing down the root scheduler doesn't make sense. How about adding a flag to the root sched and printing a warning once instead?"，随后补充更轻的选择："It'd be fine to just ignore it too ... I don't think we'd lose anything meaningful by just ignoring it when sch can't be determined."
- 作者 v3 采纳了后者（拒绝而非 fault root scheduler），未采用 Tejun 提的 root-sched 标志 + 一次告警方案，这一取舍尚未得到 Tejun 的回应对照。

## 合入评估

likelihood: **possible**。
依据：`Fixes: a5fa0708cbfd` + `Cc: stable`，且是可从 BPF 侧稳定触发的内核 oops（作者附了完整 Oops 与 RIP/CR2），严重性无争议；Andrea Righi 已在 v2 给 `Reviewed-by`；v3 已按维护者意见把语义收敛到最小面（判定不出即拒绝，不再牵连 root 调度器）。
卡点：一是 v3 距离上一版评审只有约 10 小时，09-03 内 Tejun 未对 v3 表态，`Reviewed-by` 仍是 v2 的；二是 v3 偏离了 Tejun 提的「root sched 加标志 + 打印一次告警」方案，改用「静默拒绝」，需要他确认这不会丢掉他想观测的信号；三是本补丁与同作者的 NMI 拒绝系列（[[sched-20260903-003]]）共用 `scx_kfunc_context_filter()` 可达性论证，前者已进 `for-7.4`，本补丁存在基线交叉，可能需要在同一分支上重排。

## 效果评估

邮件中未提供效果数据，但有可核对的崩溃证据：开发过程中实际触发的 Oops 为 `BUG: kernel NULL pointer dereference, address: 0000000000000398`，`RIP: 0010:scx_vexit+0x25/0xa0`，调用链 `scx_bpf_select_cpu_and+0xab/0xb0 -> bpf_prog_430ed61a7b66e03a_run_select_cpu_and -> bpf_prog_test_run_syscall`，`CR2` 恰为 `sch->exit_info` 的偏移 0x398，触发条件为 root + sub-scheduler 同时附着、对未回收僵尸任务调用该包装。修复后同一触发不再进入 `scx_vexit()`（`0x398` 偏移、指令序列 `4c 8b bf 98 03 00 00` 均出自邮件正文）。无人给出 syzbot/sashiko 的命中计数，也未提供性能影响数据。

## 我可以参与的点

1. 复现并验证 v3：用作者描述的 `BPF_PROG_TYPE_SYSCALL` + 未 reap 僵尸 + sub-sched 附着组合，在带 sub-scheduler 的 scx 分层配置下确认修复后既无 oops 也不误伤 root 调度器——这是目前线程里最缺的一步。
2. 就 v3 的取舍表态：`判定不出即静默拒绝` vs Tejun 的 `root sched 标志 + 一次告警`。从可运维性看前者会掩盖一类 BPF 程序 bug，可以给出量化意见（这类误用在真实调度器里出现频率）。
3. 复核同一模式的其它调用点：`scx_error(scx_task_sched(p), ...)` 在非 `guard(rcu)` 上下文里是否还有其它 COMPAT/新 kfunc 使用，避免同类 NULL 解引用遗漏。
4. 回合视角：OLK-6.6 无 sched_ext，直接价值有限；可复用的是「kfunc 里读 `p` 的所属对象必须先确定锁/RCU 前提」这条 review checklist，对自研 BPF 调度扩展的取锁与错误上报路径同样适用。

## 参考链接

- 本补丁各版本：
  - v1（select_cpu_and 标题）：https://lore.kernel.org/all/20260902153640.144791-1-liwanwu@kylinos.cn/
  - v2（获 Reviewed-by）：https://lore.kernel.org/all/20260902170751.256434-1-liwanwu@kylinos.cn/
  - v3（当前）：https://lore.kernel.org/all/20260903060626.814951-1-liwanwu@kylinos.cn/
- 关键回帖：
  - Andrea Righi 要求补 dsq_insert_vtime：https://lore.kernel.org/all/aphLWtCVY1XVME9C@gpd4/
  - Andrea Righi 的 Reviewed-by：https://lore.kernel.org/all/aphmwjLkdS4tKpbv@gpd4/
  - Tejun Heo 的三处反驳：https://lore.kernel.org/all/d819e8358fffc09015feffad57794f7c@kernel.org/
  - Tejun Heo 的「可直接忽略」补充：https://lore.kernel.org/all/aph7j7b_rqqqcSwR@slm.duckdns.org/
- 相关文章/系列：
  - [[sched-20260902-006]] sched_ext select_cpu_and NULL deref（本补丁的 v1 阶段）。
  - [[sched-20260903-003]] NMI 拒绝取锁 kfuncs（同一作者的同一轮审计）。
- 相关代码：
  - `kernel/sched/ext/ext.c` COMPAT 包装与 `scx_error()` / `scx_vexit()` 错误上报路径

---
id: sched-20260903-004
date: '2026-09-03'
subject: 'sched_ext: Fix NULL sched deref in kfunc sub-sched error paths'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: '<20260902153640.144791-1-liwanwu@kylinos.cn>'
lore_url: https://lore.kernel.org/all/20260902153640.144791-1-liwanwu@kylinos.cn/
upstream_commit: null
fixes_commit: 'a5fa0708cbfd'
merged_branch: null
current_version: v3
generated_at: '2026-09-07'
authors:
- Wanwu Li
maintainers_involved:
- Tejun Heo
- Andrea Righi
patch_series:
- "sched_ext: Fix NULL sched deref in kfunc sub-sched error paths"
merge_assessment:
  likelihood: medium
  blocking_issues:
  - "v3 尚无维护者回应，已有的 Reviewed-by 停留在 v2"
  - "v3 采用静默拒绝而非 Tejun 提的 root sched 标志 + 一次性告警，取舍未确认"
  - "与同作者的 NMI 拒绝系列共用可达性论证，存在基线交叉"
  next_action: "等 Tejun Heo 对 v3 表态；社区侧复现 BPF_PROG_TYPE_SYSCALL + 僵尸任务的 oops 以验证修复"
contribution_opportunities:
- "在带 sub-sched 的 scx 分层配置下复现未回收僵尸任务触发路径并验证 v3"
- "就静默拒绝 vs root sched 一次性告警的可运维性给量化意见"
- "排查其它在非 RCU/非持锁上下文中调用 scx_error(scx_task_sched(p), ...) 的 kfunc"
source_email_count: 7
related_articles:
- sched-20260902-006
tags:
- sched_ext
- crash
---
