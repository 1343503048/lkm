---
id: sched-20261010-006
date: '2026-10-10'
subject: 'sched_ext: Fix use-after-free of a destroyed user DSQ by a deferred reenqueue'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20261009220001.196762128-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20261009220001.196762128-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20261009220001.196762128-1-tj@kernel.org>
  date: '2026-10-10'
  summary: 宽限期前取消 pending reenq 请求，保住 exit_dsq() 的冲刷假设
  review_outcome: Applied 到 sched_ext/for-7.3-fixes；Hui Su KASAN 实测 Tested-by
upstream_commit: null
fixes_commit: 84b1a0ea0b7c
merged_branch: sched_ext/for-7.3-fixes
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 随 sched_ext for-7.3-fixes pull 进主线并回合 stable v7.1+
contribution_opportunities:
- kind: testing
  description: 在非 x86 或真实物理机复跑 DSQ lifetime 测试与 sched_ext selftests
generated_at: '2026-10-11T09:00:00'
source_email_count: 3
related_articles: []
tags:
- sched_ext
- crash
title: 'sched_ext: Fix use-after-free of a destroyed user DSQ by a deferred reenqueue'
layout: article
---

## TL;DR
同日，**Tejun Heo 直接发出修复 Hui Su 报告的 DSQ use-after-free 的 for-7.3-fixes 补丁**——deferred reenqueue 可能在 RCU 宽限期之后仍读取已释放的用户 DSQ（`run_deferred()` 在宽限期内开始、晚于 RCU 回调 detach 请求再读已释放 DSQ 的 id）。修复改为在宽限期**之前**取消 pending 请求：释放 DSQ 的 irq work 逐 CPU unlink 请求、`schedule_dsq_reenq()` 在 id 失效后不再排队。带 `Fixes: 84b1a0ea0b7c`、`Cc: stable v7.1+`；Hui Su 在 KVM+KASAN 下实测通过并给 Tested-by。**已 applied 到 sched_ext/for-7.3-fixes**（`Reported-and-tested-by: Hui Su`）。

## 背景与问题
deferred reenqueue（`scx_bpf_dsq_reenq()`，`84b1a0ea0b7c` 引入）下，请求留在其 CPU 的 deferred 列表直到 `run_deferred()` 取走；而释放 DSQ 的 RCU 回调假设宽限期已把请求冲刷掉，`exit_dsq()` 因此**不持 deferred 列表锁**检查 per-CPU 节点。但宽限期只等待「在途读者」，不等「未决的 `run_deferred()`」——一个在宽限期开始后才启动的 `run_deferred()` 可以在回调查看之前 detach 请求、随后读取已释放 DSQ 的 id。这就是 Hui Su 报告的 KASAN slab-use-after-free。

## 技术方案
单补丁（`kernel/sched/ext/ext.c` +25/-3）：

- 在宽限期之前取消 pending 请求：释放 DSQ 的 `free_dsq_irq_workfn()` 逐 CPU、在 per-CPU deferred 列表锁下 `list_del_init()` 每个请求；
- `schedule_dsq_reenq()` 在同样的锁下检查到 `dsq->id == SCX_DSQ_INVALID` 时直接返回，不再排队；
- 只有宽限期开始前就已启动的 `run_deferred()` 能持有请求，而它运行在 IRQ 关闭态，因此宽限期会等它结束，回调之后再无任何东西碰 DSQ。
- 结果：`exit_dsq()` 的「宽限期已冲刷」假设重新成立，其 `WARN_ON_ONCE`（丢失调度的保护）继续有效。

## 版本演进与当前进展
*current_version: v1*（作为独立 for-7.3-fixes 修复，`<20261009220001.196762128-1-tj@kernel.org>`）。当日进展：

- Tejun 自回帖（`<6100f6f22f41f99811b8c1433685e9be@kernel.org>`）：Applied 到 sched_ext/for-7.3-fixes，并按 Hui Su 的测试把 tag 更新为 `Reported-and-tested-by: Hui Su`。
- Hui Su 回帖（`<23f74656850cf78261d84fd18bfc7870@163.com>`）：x86_64 KVM + KASAN，sched_ext selftests 全过，定向 DSQ lifetime 测试在补丁后无 slab-use-after-free；给 `Tested-by`。

## Maintainer 意见与讨论焦点
- **Tejun Heo**（维护者+作者）：在 Hui Su 的 v3「Serialize user DSQ destruction」方向之外，选择「在宽限期前取消 pending 请求」的更简方案（见 <a class="article-ref" href="/lkm/2026/10/10/sched-20261010-007-sched-ext-serialize-user-dsq-destruction-against-deferred-re.html">sched-20261010-007</a> 的关联讨论），理由是让 `exit_dsq()` 的假设成立、保住 `WARN` 对丢失调度的捕获。
- **Hui Su**（原报告者）：实测通过并 Tested-by。
- 无 NAK、无剩余争议；方向已由维护者自己定案并应用。

## 合入评估
*likelihood=high*。维护者本人发出、已 applied 到 `sched_ext/for-7.3-fixes`、带 `Fixes:` 与 `Cc: stable v7.1+`、原报告者 KASAN 实测背书——随 7.3-rc 周期进主线并回合 stable 只是流程问题。*blocking_issues*：无（待 pull）。*next_action*：随 sched_ext for-7.3-fixes 的 pull 进主线，并随 stable v7.1+ 回合。

## 效果评估
Hui Su 的实测：x86_64 KVM + KASAN 下 sched_ext selftests 全过，定向 DSQ lifetime 测试在补丁后不再报 slab-use-after-free（补丁前该测试稳定复现 UAF）。

## 我可以参与的点
- 在非 x86（如 arm64 或真实物理机）复跑 DSQ lifetime 测试与 sched_ext selftests；
- 跟踪该 `Cc: stable v7.1+` 修复在 stable 分支的回合情况。

## 参考链接
- patch: https://lore.kernel.org/all/20261009220001.196762128-1-tj@kernel.org/
- Hui Su 的 v3（关联）: https://lore.kernel.org/all/20261008024753.4096008-1-sh_def@163.com/
- Tejun applied: https://lore.kernel.org/all/6100f6f22f41f99811b8c1433685e9be@kernel.org/
- Hui Su Tested-by: https://lore.kernel.org/all/23f74656850cf78261d84fd18bfc7870@163.com/
