# selftests/sched_ext: Handle CPU hotplug write failures

## TL;DR

Tianyi Chen 修 sched_ext selftest 的 CPU hotplug 测试缺陷：写 CPU 状态失败时丢弃返回值，导致测试可能无限等待。纯测试树修复，severity 低，合入可能性高。

## 背景与问题

`toggle_online_status()` 会记录 CPU 状态变更失败，但把 write 的返回值丢弃了。结果 hotplug 测试可能在「一次失败的写操作从未触发的调度器退出」上无限等待，掩盖了真实失败。

## 技术方案

返回 write 结果；当必需的 CPU 状态变更失败时，同时停止两个 hotplug 测试，并在这些路径上释放已获取的调度器资源，让既有 cleanup 回调重试恢复 CPU1；正常 CPU 恢复失败时同样使测试失败。

## 版本演进与当前进展

v1 首次发出，无 review 意见。作者已在双 vCPU VM 中验证：用 strace 向 10 次 CPU 状态 write 注入 EIO，修复后测试返回 1、CPU1 在线且 sched_ext 在 cleanup 后禁用；原始测试在前两次 write 任一失败时 3 秒内无法结束。把 online 文件设为只读也能产生失败而不挂起。

## Maintainer 意见与讨论焦点

v1 刚发出，暂无维护者意见。

## 合入评估

属于 selftest 健壮性修复，`Fixes: a5db7817af78`，无争议点，`likelihood=high`，预计进 sched_ext 测试树。

## 效果评估

作者给出明确测试结果（注入 EIO 后修复测试返回 1、不挂起），属测试正确性验证，无性能数字。

## 我可以参与的点

- 在更多虚拟化/真实硬件配置下复现注入 EIO 的 hotplug 失败路径，确认 cleanup 恢复 CPU1 的可靠性（testing）。

## 参考链接

- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260906-002
date: '2026-09-06'
subject: 'selftests/sched_ext: Handle CPU hotplug write failures'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: null
lore_url: null
upstream_commit: null
fixes_commit: a5db7817af78
merged_branch: null
current_version: v1
generated_at: '2026-09-07T00:10:00'
authors:
- Tianyi Chen
maintainers_involved:
- Tejun Heo
patch_series:
- version: v1
  msgid: null
  date: 2026-09-06
  summary: selftests/sched_ext 的 toggle_online_status() 记录了 CPU 状态变更失败日志却丢弃了 write 返回值，导致 hotplug 测试可能在一次从未触发的调度器退出上无限等待。改为返回 write 结果，在必需的 CPU 状态变更失败时同时停止两个 hotplug 测试，并释放已获取的调度器资源、由既有 cleanup 回调重试恢复 CPU1。
  review_outcome: v1 刚发出，暂无 review 意见
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 Tejun 合入 sched_ext 测试树
contribution_opportunities:
- kind: testing
  description: 在双 vCPU VM 中用 strace 向各 CPU 状态 write 注入 EIO，确认修复后测试返回 1 且 CPU1 在线、sched_ext 在 cleanup 后禁用
source_email_count: 1
related_articles:
- sched-20260906-001
tags:
- sched_ext
---
