# sched_ext: Reset runnable_at when a task leaves its scheduler

## TL;DR

Michal Blaszczyk（Google）发往 sched_ext 的两补丁修复：任务在等待中离开 SCHED_EXT 时 `runnable_at` 未重置，watchdog 会把任务在 SCHED_EXT 之外的时间计入「等待时长」，误报 stall 并中止调度器。补丁 1 修复、补丁 2 加 `class_switch_stall` selftest。维护者 Andrea Righi 已复现并给 1/2 `Reviewed-by`，2/2 仅有一条 selftest 超时余量的稳健性建议。

## 背景与问题

sched_ext 的 watchdog 用 `runnable_at` 判断任务「等待过长」。若任务在等待时被切出 SCHED_EXT（其 BPF 调度器在唤醒后仍把它留在 DSQ 上等待），测试场景会把它切到 SCHED_OTHER 睡过三倍 watchdog 超时，再切回并唤醒，调度器继续让它等待——watchdog 若把 SCHED_EXT 之外的时间也计入，会误报 stall 并 abort 调度器。不加补丁 1 时该误报可复现。

## 技术方案

两补丁（`kernel/sched/ext/` + selftests）：

- **1/2 Reset runnable_at when a task leaves its scheduler**：任务离开 sched_ext 时重置 `runnable_at`，使 watchdog 只对 SCHED_EXT 内的等待时间计时。
- **2/2 selftests/sched_ext: Add class_switch_stall test**：新增测试——任务等待时切到 SCHED_OTHER、在 SCHED_EXT 外睡三倍 watchdog 超时、切回并唤醒，调度器继续让它等待（长于 watchdog 间隔但短于超时），watchdog 不应报 stall。

## 版本演进与当前进展

*current_version: v1*。当日新发（封面 `<20261019124146.3582127-1-michalblk@google.com>`），Andrea Righi 已 review。

## Maintainer 意见与讨论焦点

Andrea Righi（sched_ext 维护者）：

- 1/2：「This makes sense to me and I reproduced the issue (thanks for providing a selftest).」`Reviewed-by: Andrea Righi`。
- 2/2：稳健性建议（非 observed 问题，面向高负载 CI VM）——当前值只有约 250ms 的定时器投递/派发/子进程获 CPU 余量，且第一阶段依赖 userspace 在 1s 内把 parked child 切出；建议 watchdog 超时调到 3s、park 时长调到 2s，并相应改 `timeout_ms`。

## 合入评估

*likelihood=high*。修复方向获维护者复现 + Reviewed-by，仅剩 2/2 selftest 超时余量的稳健性调整。*blocking_issues*：2/2 超时/时长参数需按 Andrea 建议微调。*next_action*：作者调整 `class_switch_stall` 的 watchdog timeout=3s、park=2s 后重发，即可进入收取。

## 效果评估

无性能数据，属正确性修复。Andrea 复现了误报问题（「reproduced the issue」），补丁 2 的 selftest 用于证明修复有效；Andrea 同时指出当前 selftest 参数在高负载 CI 上存在约 250ms 余量偏小的稳健性风险。

## 我可以参与的点

- `testing`：在 CI VM（高负载）上跑 `class_switch_stall` 及相关 sched_ext selftest，验证 watchdog 无误报、无脆弱超时。
- `review`：复核 `runnable_at` 重置时机是否覆盖「任务在等待/运行中离开 SCX」的全部路径。

## 参考链接

- 封面信：https://lore.kernel.org/all/20261019124146.3582127-1-michalblk@google.com/
- Andrea 对 3/3(2/2) 的建议：https://lore.kernel.org/all/atYhHvJAxLp01QbT@gpd4/

---
id: sched-20261019-012
subject: "sched_ext: Reset runnable_at when a task leaves its scheduler"
date: 2026-10-19
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261019124146.3582127-1-michalblk@google.com>"
lore_url: "https://lore.kernel.org/all/20261019124146.3582127-1-michalblk@google.com/"
authors: ["Michal Blaszczyk"]
maintainers_involved: ["Andrea Righi"]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261019124146.3582127-1-michalblk@google.com>"
    date: 2026-10-19
    summary: "两补丁：任务离开 SCX 时重置 runnable_at 避免 watchdog 误报 stall + class_switch_stall selftest"
    review_outcome: "Andrea 复现并给 1/2 Reviewed-by；2/2 建议调 watchdog/park 超时余量"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["2/2 selftest 超时/时长参数按 Andrea 建议微调"]
  next_action: "作者调整 class_switch_stall 的 watchdog timeout=3s、park=2s 后重发"
contribution_opportunities:
  - kind: testing
    description: "高负载 CI VM 上跑 class_switch_stall 及 sched_ext selftest，验证无误报/无脆弱超时"
  - kind: review
    description: "复核 runnable_at 重置时机是否覆盖任务离开 SCX 的全部路径"
generated_at: "2026-10-20T01:30:00"
source_email_count: 3
related_articles: []
tags: [sched_ext]
---