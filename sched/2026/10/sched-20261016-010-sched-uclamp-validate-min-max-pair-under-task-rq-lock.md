# sched/uclamp: Validate min/max pair under task_rq_lock()

## TL;DR
Hui Su 修复 `sched_setattr()` 中 UCLAMP_MIN/MAX 的校验竞态：两次不同的 `sched_setattr()` 调用可以在拿锁前各自基于同一份旧值通过校验，最终留下 `min > max` 的非法 `uclamp_req`。补丁把「任务相关」的 min/max 配对校验移到 `task_rq_lock()` 之后（更新已串行化），并拒绝一起提交的反向对。作者用 x86_64 QEMU/KVM 复现了旧代码的竞态（第 20 轮即出现双方 setter 都成功），修复后 10 万轮每轮只有一个 setter 返回 `-EINVAL`。

## 背景与问题
`sched_setattr()` 可分别更新 UCLAMP_MIN 与 UCLAMP_MAX。若两次调用在取 `task_rq_lock()` 之前都针对同一份旧 `uclamp_req` 做校验，两者都能通过，最终留下 `min > max` 的 `uclamp_req`，破坏 uclamp 钳制语义。uclamp static key 一旦使能就不会再关，所以要避免在使能时引入非法状态。`Fixes: a509a7cd7974 ("sched/uclamp: Extend sched_setattr() to support utilization clamping")`。

## 技术方案
单补丁（`kernel/sched/syscalls.c`，+40/−11）：把依赖任务当前值的 min/max 配对校验（`uclamp_validate_pair()`，带 `lockdep_assert_held(&p->pi_lock)`）放到 `task_rq_lock()` 之后；保留标量范围检查与 `sched_uclamp_enable()`（在调度锁之前，因为使能 uclamp 可能阻塞）；在使能前拒绝一起提交的反向对。

## 版本演进与当前进展
v1 刚发出（<20261016062629.2102883-1-sh_def@163.com>），暂无 review 意见。

## Maintainer 意见与讨论焦点
暂无维护者表态。

## 合入评估
*likelihood=medium*。修复点真实、带复现与测试，但当日无 review；uclamp 属维护者重点关注的接口。*blocking_issues*：暂无 review。*next_action*：等 uclamp 维护者 review。

## 效果评估
作者测试数据：
- x86_64 QEMU/KVM 复现：旧代码第 20 轮即出现 min=900/max=800 双方 setter 都成功；修复后 10 万轮每轮恰好一个 setter 返回 `-EINVAL`，`bad_pair=0`、`unexpected_errno=0`。
- x86_64 `make -j12 bzImage`（`CONFIG_UCLAMP_TASK=y` + `CONFIG_PROVE_LOCKING=y` + `CONFIG_CPU_FREQ_GOV_SCHEDUTIL=y`）通过。

## 我可以参与的点
- *testing*：在真实任务并发热更新 UCLAMP_MIN/MAX 的负载下验证修复后再无 min>max 出现，并确认对 uclamp 使能路径无回归。

## 参考链接
- patch：https://lore.kernel.org/all/20261016062629.2102883-1-sh_def@163.com/

---
id: sched-20261016-010
date: 2026-10-16
subject: "sched/uclamp: Validate min/max pair under task_rq_lock()"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261016062629.2102883-1-sh_def@163.com>"
lore_url: "https://lore.kernel.org/all/20261016062629.2102883-1-sh_def@163.com/"
authors: ["Hui Su"]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261016062629.2102883-1-sh_def@163.com>"
    date: 2026-10-16
    summary: "min/max 配对校验移到 task_rq_lock() 之后，拒绝反向对"
    review_outcome: "暂无 review"
upstream_commit: null
fixes_commit: "a509a7cd7974"
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["暂无 review"]
  next_action: "等 uclamp 维护者 review"
contribution_opportunities:
  - kind: testing
    description: "真实并发更新 UCLAMP_MIN/MAX 负载下验证修复有效且使能路径无回归"
generated_at: "2026-10-17T01:30:00"
source_email_count: 1
related_articles: []
tags: [uclamp, cfs]
---