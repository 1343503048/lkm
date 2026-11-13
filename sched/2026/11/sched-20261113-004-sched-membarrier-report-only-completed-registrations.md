# sched/membarrier: Report only completed registrations

## TL;DR
Mathieu Desnoyers 的 RFC 系列（16 补丁）修复之二：`MEMBARRIER_CMD_GET_REGISTRATIONS` 目前只要注册的任一状态位置位就上报，导致只注册了 sync core 或 rseq 的进程被误报为也注册了 `PRIVATE_EXPEDITED`（进而 `MEMBARRIER_CMD_PRIVATE_EXPEDITED` 返回 -EPERM），-ENOMEM 失败的注册也被同样上报。CRIU checkpoint/restore 会据此恢复出原进程从未发出过的注册。修复为只上报"ready"位已置的注册。

## 背景与问题
`MEMBARRIER_CMD_GET_REGISTRATIONS` 返回进程发出过的注册命令。每个注册有两个状态位：开始注册时置起一个，"ready"在完成时置起另一个。当前实现只要任一位置起就上报该注册。

sync core 与 rseq 注册也会置起 `MEMBARRIER_STATE_PRIVATE_EXPEDITED`（但**不置**其 ready 位）——因为它们需要与 `MEMBARRIER_CMD_PRIVATE_EXPEDITED` 相同的调度屏障。于是只发出过 `MEMBARRIER_CMD_REGISTER_PRIVATE_EXPEDITED_RSEQ` 的进程，会被误报为也发出过 `MEMBARRIER_CMD_REGISTER_PRIVATE_EXPEDITED`，而该命令对它实际返回 -EPERM。一个因 -ENOMEM 失败的注册也会被同样上报。

用户态拿到错误的注册掩码。该命令是为 CRIU 加的：checkpoint 时保存进程注册、restore 时恢复；恢复出的进程会带着原进程从未发出的注册。信任该掩码的程序发 `MEMBARRIER_CMD_PRIVATE_EXPEDITED` 会拿到 -EPERM。

## 技术方案
只在该注册的"ready"位置起时才上报——把状态数组从「两个状态位 OR 后匹配」改为只匹配各 `*_READY` 位。行为变化：`MEMBARRIER_CMD_GET_REGISTRATIONS` 不再为只发过 sync core / rseq 注册的进程上报 `PRIVATE_EXPEDITED`；其余命令结果不变。

正文含 `Fixes: 544a4f2ecd45` 并 Cc stable。

## 版本演进与当前进展
RFC 02/16 刚发出（系列共 16 补丁，本窗口仅见 01、02 两封）。尚未有对本文的回复。

## Maintainer 意见与讨论焦点
当日无针对本补丁的回复。改动小、语义清晰（只上报完成的注册），且带 CRIU 场景的实际影响说明。

## 合入评估
RFC 发布，尚未有维护者表态。语义正确性有 CRIU 恢复场景支撑，属低风险修复，但需随整组 RFC 等待评审。

## 效果评估
正文未给 benchmark；影响为「用户态注册掩码行为改变」，属语义修复而非性能优化。作者说明：除 sync core / rseq 注册的 PRIVATE_EXPEDITED 误报被修正外，其余命令结果不变。

## 我可以参与的点
- **review**：核对 `ready_states` 数组与 `registration_cmds` 数组的一一对应是否覆盖全部四种注册命令。
- **testing**：用 CRIU checkpoint/restore 验证只注册 sync core / rseq 的进程恢复后掩码正确、`PRIVATE_EXPEDITED` 不再被误报。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261113131903.157186-3-mathieu.desnoyers@efficios.com/

---
id: sched-20261113-004
subject: "sched/membarrier: Report only completed registrations"
date: 2026-11-13
subsystem: sched
type: bug
status: rfc
severity: medium
thread_root_msgid: "<20261113131903.157186-3-mathieu.desnoyers@efficios.com>"
lore_url: "https://lore.kernel.org/all/20261113131903.157186-3-mathieu.desnoyers@efficios.com/"
authors: [Mathieu Desnoyers]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261113131903.157186-3-mathieu.desnoyers@efficios.com>"
    date: 2026-11-13
    summary: "GET_REGISTRATIONS 只上报 ready 位已置的注册，修正 sync core / rseq 的 PRIVATE_EXPEDITED 误报"
    review_outcome: "RFC 刚发出，暂无回复"
upstream_commit: null
fixes_commit: "544a4f2ecd45"
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: "等待维护者对 RFC 系列的评审"
contribution_opportunities:
  - kind: review
    description: "核对 ready_states 与 registration_cmds 数组对应关系覆盖全部注册命令"
  - kind: testing
    description: "用 CRIU checkpoint/restore 验证修复后注册掩码正确"
generated_at: "2026-11-14T01:30:00"
source_email_count: 2
related_articles: []
tags: [membarrier]
---