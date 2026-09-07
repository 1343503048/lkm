---
id: sched-20260906-006
date: '2026-09-06'
subject: 'tcp: Skip cond_resched() in inet_csk_listen_stop() under BPF context'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: null
lore_url: null
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: '2026-09-07T00:10:00'
authors:
- bot+bpf-ci@kernel.org
- Jiayuan Chen
maintainers_involved:
- Alexei Starovoitov
- Daniel Borkmann
- Peter Zijlstra
patch_series:
- version: v1
  msgid: null
  date: null
  summary: 首次提出在 BPF 上下文下跳过 inet_csk_listen_stop() 中的 cond_resched()。
  review_outcome: v1 review 意见（未在本日邮件中获取到细节）
- version: v2
  msgid: null
  date: 2026-09-06
  summary: bpf v2 2/3：在 inet_csk_listen_stop() 的 cond_resched() 处，当处于 BPF 迭代上下文（rcu_read_lock
    下）时跳过该可能导致睡眠的检查，避免 invalid context BUG。
  review_outcome: v2 刚发出，暂无明确 NAK
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 跨子系统（net/bpf 与 sched）修复，需网络与 BPF 维护者共同认可；cond_resched 跳过是否影响既有 RCU/抢占语义需确认
  next_action: 等待 net/bpf 维护者 review；确认跳过 cond_resched 在 BPF 迭代上下文下的安全性
contribution_opportunities:
- kind: testing
  description: 用 BPF 程序对仍带 accept 队列子连接的 listener 调用 bpf_sock_destroy()，确认不再触发 sleeping-function-from-invalid-context
    BUG
source_email_count: 3
related_articles: []
tags:
- sched/core
- preempt
title: 'tcp: Skip cond_resched() in inet_csk_listen_stop() under BPF context'
layout: article
---

## TL;DR

Jiayuan Chen 的 bpf v2 修复：在 BPF 迭代上下文（rcu_read_lock 下）调用 `bpf_sock_destroy()` 命中带子连接的 listener 时，`inet_csk_listen_stop()` 内的 `cond_resched()` 会触发 invalid-context BUG。本日 patch 在 BPF 上下文下跳过该 `cond_resched()`。属跨子系统修复，涉及调度原语 `cond_resched()` 的调用语义，纳入本摘要跟踪。

## 背景与问题

`bpf_sock_destroy()` 从 tcp iterator 中、在 `rcu_read_lock()` 下运行。若目标 sock 是一个 accept 队列里仍有子连接的 listener，`tcp_abort()` 会进入 `inet_csk_listen_stop()`，其中的 `cond_resched()` 在原子/RCU 上下文里触发：
`BUG: sleeping function called from invalid context at net/ipv4/inet_connection_sock.c:1523`，伴随 `RCU nest depth: 1` 与多个 held locks。这是调度原语 `cond_resched()` 在不应睡眠的上下文被调用的典型 sleep-in-atomic 问题。

## 技术方案

在 `inet_csk_listen_stop()` 的 `cond_resched()` 处，识别「当前处于 BPF 迭代上下文」时跳过该调用，避免在 RCU/原子上下文中尝试可能睡眠的调度点。即：仅在非 BPF 上下文保留原有的 `cond_resched()` 让出点。

## 版本演进与当前进展

- v1：首次提出在 BPF 上下文下跳过 `cond_resched()`（本日邮件未含 v1 细节）。
- v2（2026-09-06，bpf v2 2/3）：延续该思路，作为 bpf 系列第 2/3 片发出，暂无明确 NAK。

## Maintainer 意见与讨论焦点

本日邮件中尚未出现网络/BPF 维护者的明确 review 结论。关键争议点（待确认）是：在 BPF 迭代上下文跳过 `cond_resched()` 是否会影响既有 RCU/抢占语义，以及是否应在更上层（tcp iterator）规避而非在 `inet_csk_listen_stop()` 内打补丁。

## 合入评估

`likelihood=medium`。修复本身定位清晰，但属于 net/bpf 与 sched 交叉修复，需要网络与 BPF 维护者共同认可；且 `cond_resched()` 是调度核心原语，跳过其调用需谨慎论证安全性。

## 效果评估

作者给出明确复现栈（invalid context BUG，RCU nest depth=1），属可复现的崩溃类问题；修复后该路径不再触发睡眠检查。暂无性能数字。

## 我可以参与的点

- 在仍带 accept 队列子连接的 listener 上用 BPF 程序调用 `bpf_sock_destroy()`，确认 BUG 不再复现（testing）。

## 参考链接

- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到
