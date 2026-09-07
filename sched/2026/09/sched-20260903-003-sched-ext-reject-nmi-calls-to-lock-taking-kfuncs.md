# sched_ext: Reject NMI calls to lock-taking kfuncs

## TL;DR

仍会取锁的 sched_ext kfunc 若从 NMI 里被调用，会在「被中断上下文已持有该锁」的 CPU 上自旋到死，表现为整机 hard lockup。Wanwu Li 的做法是把 `scx_bpf_kick_cpu()` 已有的 `in_nmi()` 拒绝抽成公共 helper `scx_kf_allowed_ctx()`，让所有暴露给 `BPF_PROG_TYPE_TRACING` 的取锁 kfunc 统一在入口拒绝 NMI。
这个系列已经落地：Tejun Heo 本日（09-03 07:05）回复 **v3 已 applied 到 `sched_ext/for-7.4`**，并附两处由他做的调整。同一天作者又按 Tejun 在 v2 上的意见发出后续 2 patch 系列，补上 `scx_locked_rq()` 与 idle 搜索 nodemask 两个残留问题。

## 背景与问题

`e06ece82d7b0`（"sched_ext: Report NMI kicks with scx_error()"）已经让 `scx_bpf_kick_cpu()` 拒绝 NMI 调用，其封面说明了可达性：属于 "any" 类别的 sched_ext kfunc "are callable from tracing progs that can attach to functions running in NMI"，从那里发起的不巧调用 "could deadlock the machine"。那次修复把 error/exit 路径改成无锁（`f883dbb64ca5` 使 `scx_error()` 在 NMI 下安全），因此**关闭的是每个 kfunc 的 error 路径，而不是 kfunc 成功路径上自己的取锁**。
`scx_kfunc_context_filter()` 暴露给 `BPF_PROG_TYPE_TRACING` 的取锁 kfunc 因此仍有同一隐患：NMI 落在一个已持有该锁的 CPU 上时，kfunc 的 raw spinlock 会永远自旋并把该 CPU 硬锁死。

## 技术方案

新增 `scx_kf_allowed_ctx()` 统一入口守卫，复用 `scx_bpf_kick_cpu()` 已有的 `in_nmi()` 检查——该检查现与其 cid 对应物 `scx_bpf_kick_cid()` 通过 `scx_kick_cpu()` 共享——使规则只声明一次、覆盖面可从一个地方审计。被纳入守卫的 kfunc 及其锁：
- `scx_bpf_destroy_dsq()` -> `dsq->lock`
- `scx_bpf_dsq_reenq()` -> rq 的 `deferred_reenq_lock`
- `scx_bpf_cpuperf_set()` / `scx_bpf_cidperf_set()` -> `rq->lock`
- `scx_bpf_sub_grant()` / `scx_bpf_sub_revoke()` -> pshard lock（经由共享的 `sub_cap_preamble()`）
- `bpf_iter_scx_dsq_next()` / `bpf_iter_scx_dsq_destroy()` -> `dsq->lock`；拒绝点放在本身无锁的 `bpf_iter_scx_dsq_new()`，于是 NMI 下 `next()`/`destroy()` 成为 no-op 且 `kit->dsq` 留为 NULL。
定位是**防御性**的：目前不存在需要在 NMI 里重排队、迭代 DSQ、设性能目标或授予 sub-cap 的场景，守卫防的是有 bug 或恶意的 BPF 程序把 "any" 类 kfunc 变成整机 hard lockup。因为 `scx_error()` 已 NMI-safe，拒绝这条 abort 路径本身不会再造成死锁。

## 版本演进与当前进展

- v1 09-01（`<20260901095652.1009104-1-liwanwu@kylinos.cn>`）→ v2 09-02 → v3 09-02 17:36 → **09-03 07:05 由 Tejun Heo applied 到 `sched_ext/for-7.4`**。
- 09-03 05:51 Tejun 在 v2 上追加一条意见：把 `in_nmi()` 判断直接加进 `scx_locked_rq()` 让它在 NMI 下返回 NULL，从而把三个调用者一起引到无锁路径；并指出那处 "probably needs to be irqsave'd"，因为 `preempt_disable()` 不屏蔽中断而 idle kfuncs 可从中断上下文调用。
- 作者 09-03 09:46 回帖接受，并于 11:29 发出后续系列 `[PATCH 0/2] sched_ext: two more context-safety fixes found in the NMI kfunc audit`：patch 1 `Make scx_locked_rq() return NULL from NMI`，patch 2 `Protect the idle-search scratch nodemask with irqsave`（`per_cpu_unvisited` 掩码原先只有 `preempt_disable()` 保护），改动 `kernel/sched/ext/idle.c` 与 `kernel/sched/ext/internal.h`。
- 本日无合入 tip 主线的迹象，落在 sched_ext 自己的 for-7.4 分支。

## Maintainer 意见与讨论焦点

- **Tejun Heo（sched_ext 维护者）— 已 accept**：09-03 07:05 写明 "Applied to sched_ext/for-7.4 with the following changes"，并逐项说明他改了什么：
  1. 澄清他在 v2 上说的 "No need to wrap" 指的是函数签名的换行，不是去掉包装，因此恢复了 `static __always_inline bool __scx_kf_allowed_ctx(struct scx_sched *sch, const char *who)` + `#define scx_kf_allowed_ctx(sch) __scx_kf_allowed_ctx((sch), __func__)` 的内联函数 + 宏包装形式；
  2. 修正提交说明最后一段的事实错误："struct_ops don't run in task context (e.g. ops.tick() runs from the tick interrupt). They just never run in NMI." —— 即正确说法是 struct_ops 从不在 NMI 运行，而不是它们在任务上下文运行。
- Tejun 同日在 v2 上的另一条意见（把 `in_nmi()` 下推到 `scx_locked_rq()` + 需要 irqsave）没有进入本补丁，被他明确留给 follow-up；作者当天照做，未拖延。
- Andrea Righi 与 Tejun 在 09-02 对 v1/v2 的早期意见已体现在版本推进中；本日线程内没有第三方反对意见。

## 合入评估

likelihood: **likely**（事实上已进入 `sched_ext/for-7.4` 分支）。
依据：维护者本人在 09-03 明确 applied，并附了他自己做的两处修改，等价于带 maintainer 改动的接受；补丁是纯入口守卫、不改语义，且建立在 `e06ece82d7b0` 与 `f883dbb64ca5` 已铺好的 NMI 安全前提上。
卡点：只剩下游同步——该分支尚未进入 tip 主线，7.4 合并窗口的最终拉取由 Peter Zijlstra/Ingo 决定；另外本补丁的守卫清单依赖 `scx_kfunc_context_filter()` 当前的暴露集合，将来新增取锁 kfunc 时容易漏加，这一点作者用「集中到一处 helper、可单点审计」来缓解但没有强制机制。残留的 `scx_locked_rq()` 与 nodemask 两处问题由后续 2 patch 系列承接，本线程内不闭合。

## 效果评估

邮件中未提供效果数据（无 benchmark、无 syzbot/sashiko 复现计数）。作者给的是可达性论证与硬锁死的故障模型：NMI 落在已持 `dsq->lock` / `rq->lock` / pshard lock 的 CPU 上时 raw spinlock 永久自旋。修复效果按维护者接受时的表述衡量：把「任何类别 kfunc 被 NMI 调用」转成一次干净的 `scx_error()` abort 而非 machine-wide hard lockup。是否在真实系统上观测到过该 NMI 路径，邮件正文中未提及。

## 我可以参与的点

1. 跟进后续 2 patch 系列（`scx_locked_rq()` 返回 NULL + idle 搜索 nodemask 改 irqsave）的复审：Tejun 点名要求的两点正在那里闭合，谁先实测谁就能拿到 tag。
2. 可复核的具体代码点：`bpf_iter_scx_dsq_new()` 在 NMI 下 leave `kit->dsq` 为 NULL 后，`next()`/`destroy()` 的 no-op 路径是否被所有现有 scx 调度器安全处理（iter 的 NULL dsq 语义）。
3. 可为 sched_ext 加一条自检：枚举 `scx_kfunc_context_filter()` 放行的全部 kfunc，静态核对每个取锁者是否都过 `scx_kf_allowed_ctx()`，把「单点可审计」变成真正的 CI 检查。
4. 回合视角：OLK-6.6 无 sched_ext，本补丁不可移植；可移植的是同一条判据——任何从 NMI/中断可达的路径上不得取 rq 级 raw spinlock，可用它复核 6.6 里自研调度扩展的 kfunc 类入口。

## 参考链接

- 本补丁各版本：
  - v1：https://lore.kernel.org/all/20260901095652.1009104-1-liwanwu@kylinos.cn/
  - v2：https://lore.kernel.org/all/20260902023124.1422942-1-liwanwu@kylinos.cn/
  - v3（被 applied）：https://lore.kernel.org/all/20260902093611.52651-1-liwanwu@kylinos.cn/
- 关键回帖：
  - Tejun Heo 在 v2 上提出 scx_locked_rq()/irqsave 意见：https://lore.kernel.org/all/d84b31727f04e1ed0d40042ba1c09e61@kernel.org/
  - Tejun Heo applied 到 sched_ext/for-7.4：https://lore.kernel.org/all/27793d61e70c3d4df415729e1d150ad0@kernel.org/
- 后续系列（本日发出）：[PATCH 0/2] sched_ext: two more context-safety fixes found in the NMI kfunc audit，https://lore.kernel.org/all/20260903032953.659847-1-liwanwu@kylinos.cn/
- 相关文章/系列：
  - [[sched-20260902-004]] 本系列初版评审记录。
- 相关代码：
  - `kernel/sched/ext.c` kfunc 上下文过滤与 `scx_kf_allowed_ctx()`；`kernel/sched/ext/idle.c`

---
id: sched-20260903-003
date: '2026-09-03'
subject: 'sched_ext: Reject NMI calls to lock-taking kfuncs'
subsystem: sched
type: fix
status: merged_tip
severity: high
thread_root_msgid: '<20260901095652.1009104-1-liwanwu@kylinos.cn>'
lore_url: https://lore.kernel.org/all/20260901095652.1009104-1-liwanwu@kylinos.cn/
upstream_commit: null
fixes_commit: null
merged_branch: 'sched_ext/for-7.4'
current_version: v3
generated_at: '2026-09-07'
authors:
- Wanwu Li
maintainers_involved:
- Tejun Heo
patch_series:
- "sched_ext: Reject NMI calls to lock-taking kfuncs"
merge_assessment:
  likelihood: merged
  blocking_issues:
  - "sched_ext/for-7.4 尚未进入 tip 主线，最终拉取由 sched 维护者决定"
  - "后续 scx_locked_rq()/irqsave 两点在另一 2 patch 系列中，本线程不闭合"
  next_action: "跟进 for-7.4 是否被拉入 tip，并复审同作者的 follow-up 2 patch 系列"
contribution_opportunities:
- "实测 scx_locked_rq() 返回 NULL + per_cpu_unvisited nodemask irqsave 的 follow-up 补丁"
- "核对 bpf_iter_scx_dsq_new() 在 NMI 下留 kit->dsq 为 NULL 时 next()/destroy() 的安全性"
- "写一条静态检查：枚举 scx_kfunc_context_filter() 放行的取锁 kfunc 是否都过 scx_kf_allowed_ctx()"
source_email_count: 3
related_articles:
- sched-20260902-004
tags:
- sched_ext
---
