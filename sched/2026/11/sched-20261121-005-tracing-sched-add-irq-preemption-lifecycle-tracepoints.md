# tracing/sched: Add IRQ preemption lifecycle tracepoints

## TL;DR

Karl Mehltretter 的 RFC v2（9 补丁，含 IRQ 抢占生命周期 tracepoint）当日收到 Gabriele Monaco 的 review：质疑一处「调度前禁用抢占前先 trace」的 bookkeeping 注释用途、认为不必手工检查 static key（trace 宏内部已检查）、并追问 tracepoint 里 owner 字段语义（是否只是拿来和 entry 匹配）。系列仍处 RFC 阶段，无维护者表态。

## 背景与问题

该 RFC 为调度/抢占相关路径新增 IRQ 抢占生命周期 tracepoint（`tracing/sched` 方向），用于观测中断抢占上下文的进入/退出。本日缓存只有 Gabriele 对 2/9（tracepoint 定义处）的一封 review，无该 RFC 其余 patch 或 cover 全文，动机细节以补丁主题推断。

## 技术方案

从 Gabriele 的 review 可还原 2/9 大致结构：在 schedule 前禁用抢占的路径上先行 trace 一段（带 bookkeeping 注释），tracepoint 展开处手工检查 static key，并带一个 owner 字段记录首段 switch 的发起者。Gabriele 建议：删掉 bookkeeping 注释、去掉手工 static key 检查（`trace_##_tp()` 展开内部已查）、澄清 owner 是否只用于与 entry 匹配（entry 可能已迁移、未运行或已不在运行）。

## 版本演进与当前进展

*current_version: v2（2026-11-07 发出，`<20261107171252.25090-3-kmehltretter@gmail.com>`，RFC 9 补丁之 2）*。当日无新版本，进展为 Gabriele Monaco 的 review 意见。

## Maintainer 意见与讨论焦点

- **Gabriele Monaco（社区 reviewer，非维护者）**：三点具体问题——bookkeeping 注释的用途、static key 无需手工查、owner 字段语义（是否仅为与 entry 匹配）。
- 无 NAK；属 RFC 早期的可读性/语义澄清，未见调度维护者表态。

## 合入评估

*likelihood=unknown*。RFC 早期，仅收到非维护者的局部 review；tracepoint 命名/字段语义尚需澄清，整体方向未见维护者背书。*blocking_issues*：无维护者表态；tracepoint owner 字段与 bookkeeping 语义待作者澄清。*next_action*：作者回应 Gabriele 三点疑问并说明 tracepoint 设计意图。

## 效果评估

暂无效果数据；tracepoint 类改动，价值在可观测性，未见量化。

## 我可以参与的点

- **discussion**：就 IRQ 抢占生命周期 tracepoint 的字段语义（owner 是「发起者」还是「entry 匹配 key」）与是否有更标准的既有 tracepoint 可复用发表意见。
- **review**：核对 2/9 中「调度前先 trace」的时序是否与 preempt 禁用语义一致。

## 参考链接

- lore thread（Gabriele 对 2/9 的 review）: https://lore.kernel.org/all/6c3fa853697803c63e2b87c7f8a9d4ff2f561820.camel@redhat.com/

---
id: sched-20261121-005
date: '2026-11-21'
subject: "tracing/sched: Add IRQ preemption lifecycle tracepoints"
subsystem: sched
type: discussion
status: rfc
severity: none
thread_root_msgid: "<20261107171252.25090-3-kmehltretter@gmail.com>"
lore_url: "https://lore.kernel.org/all/6c3fa853697803c63e2b87c7f8a9d4ff2f561820.camel@redhat.com/"
authors: [Karl Mehltretter]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v2
    msgid: "<20261107171252.25090-3-kmehltretter@gmail.com>"
    date: '2026-11-07'
    summary: "RFC v2 9 补丁之 2：IRQ 抢占生命周期 tracepoint 定义"
    review_outcome: "Gabriele Monaco 三点 review（注释/static key/owner 语义）"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["无维护者表态", "owner 字段与 bookkeeping 语义待澄清"]
  next_action: "作者回应 Gabriele 三点疑问并说明设计意图"
contribution_opportunities:
  - kind: discussion
    description: "就 IRQ 抢占 tracepoint 的 owner 字段语义与既有 tracepoint 复用发表意见"
  - kind: review
    description: "核对调度前 trace 时序与 preempt 禁用语义一致性"
generated_at: "2026-11-22T01:00:00+08:00"
source_email_count: 91
related_articles: []
tags: [preempt, sched_debug]
---