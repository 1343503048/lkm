---
id: sched-20260925-017
date: 2026-09-25
subject: 'sched_ext: Use fetching atomics for cmask instead of a cmpxchg loop'
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: <20260925134828.2012199-4-puranjay@kernel.org>
lore_url: https://lore.kernel.org/all/20260925134828.2012199-4-puranjay@kernel.org/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v3
generated_at: '2026-09-26T01:15:00'
authors:
- Puranjay Mohan
maintainers_involved:
- Alexei Starovoitov
patch_series:
- version: v2
  msgid: <20260924160354.531101-4-puranjay@kernel.org>
  date: 2026-09-24
  summary: 改注释：不再引用 x86 JIT 拒绝，改为说明 arm64 无 LSE 拒绝所有 arena RMW
  review_outcome: Alexei 指出循环不成立，建议换 __sync_fetch_and_or/and；pw-bot cr
- version: v3
  msgid: <20260925134828.2012199-4-puranjay@kernel.org>
  date: 2026-09-25
  summary: 把 cmask cmpxchg 循环换成原生 fetching 原子，删除 CMASK_CAS_TRIES 与错误路径
  review_outcome: 待 Alexei 复审
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Alexei 尚未对 v3 最终 ack；需随 bpf-next 系列 1/3、2/3 一起合入
  next_action: 等 Alexei 对 v3 的 review/ack
contribution_opportunities:
- kind: testing
  description: 在 arm64（无 LSE）与 riscv（无 Zacas）上构建并跑 sched_ext cmask 路径，验证替换后的可移植性
- kind: review
  description: 确认 __sync_fetch_and_or/and 在 BPF arena 语义下与 cmask u64 word 对齐、无符号/宽度陷阱
source_email_count: 4
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Use fetching atomics for cmask instead of a cmpxchg loop'
layout: article
---

## TL;DR

Puranjay Mohan 的 bpf-next 系列 3/3（sched_ext 的 cmask 位图原子操作）：v2 只是改注释（去掉「x86 JIT 拒绝 arena 上的 BPF_OR/AND|FETCH」这个已过时的说法），Alexei Starovoitov 复审指出这个 cmpxchg 循环根本不是可移植性兜底、不同架构各拒绝各的，建议直接换 `__sync_fetch_and_or/and`；作者据此发 v3，把循环换成原生 fetching 原子并删掉 `CMASK_CAS_TRIES` 及错误路径（-71/+8）。

## 背景与问题

`sched_ext` 的 BPF 侧 cmask 助手（`cid.bpf.h`）用有界 cmpxchg 循环实现 `cmask_set/clear` 与 `test_and_*`。注释给出的理由是「x86 BPF JIT 拒绝 arena 指针上的 `BPF_OR|BPF_FETCH` 和 `BPF_AND|BPF_FETCH`」。但这个理由已经失效：`bpf_jit_supports_insn()` 现在什么都不拒绝。更糟的是，循环声称的可移植性兜底本身也不成立——拒绝 arena 上 fetching OR/AND 的 JIT，同样会拒绝 CMPXCHG（如 arm64 无 LSE 时拒绝所有 arena read-modify-write，循环照样跑不了）；riscv 无 Zacas 时反过来只拒绝 CMPXCHG 而接受 fetching 指令，循环反而更差。

## 技术方案

v3 直接用原生 `__sync_fetch_and_or/and`（BPF 侧 `BPF_OR|BPF_FETCH` / `BPF_AND|BPF_FETCH`）实现 cmask 原子操作，删除 `CMASK_CAS_TRIES` 宏和只有循环存在时才可能触达的错误路径。diffstat：tools/sched_ext/include/scx/cid.bpf.h 共 8 insertions(+), 71 deletions(-)。

## 版本演进与当前进展

- v2 3/3（2026-09-24，`<20260924160354.531101-4-puranjay@kernel.org>`）：仅改注释措辞（从「x86 JIT 拒绝」改为「并非所有 JIT 都接受……arm64 无 LSE 拒绝所有 arena RMW」）。
- Alexei 复审（`<DLNOU1DBG2W4.1SHS4ZHDHYUM3@gmail.com>`）：指出 arm64/riscv 的实际情况、循环不成立，问「patch 1 之后能否把 cmask 原子换成 `__sync_fetch_and_or/and` 并去掉 CMASK_CAS_TRIES」；pw-bot 标 `cr`。
- v3 3/3（2026-09-25，`<20260925134828.2012199-4-puranjay@kernel.org>`）：按 Alexei 意见把循环换成 fetching 原子、删 CMASK_CAS_TRIES 与错误路径。

## Maintainer 意见与讨论焦点

Alexei Starovoitov（bpf 维护者）实质主导了方向：他纠正了作者的架构错误认知（arm64 无 LSE 连 CMPXCHG 都拒绝、riscv 无 Zacas 反过来），并明确建议换成 `__sync_fetch_and_or/and`。作者接受并发 v3。无 NAK；等待 Alexei 对 v3 的最终 ack。

## 合入评估

*likelihood=medium*。方向已由维护者敲定、v3 照做，但作为 bpf-next 系列 3/3，需 Alexei 对 v3 最终 ack 且随整个系列（1/3、2/3）一起合入。*blocking_issues*：Alexei 尚未对 v3 表态；系列前两枚是否同步就绪未知。*next_action*：等 Alexei 对 v3 的 review/ack。

## 效果评估

无运行时数据；这是把误导性注释与不成立的兜底循环替换为更简洁且架构覆盖面更广的原生原子操作（riscv 无 Zacas 场景从「不能用」变「能用」）。暂无效果数据。

## 我可以参与的点

- `testing`：在 arm64（无 LSE）与 riscv（无 Zacas）上构建并跑 sched_ext cmask 路径，验证 fetching 原子替换后的可移植性声明。
- `review`：确认 `__sync_fetch_and_or/and` 在 BPF arena 语义下与 cmask 位宽（u64 word）对齐、无符号/宽度陷阱。

## 参考链接

- v3 3/3 补丁: https://lore.kernel.org/all/20260925134828.2012199-4-puranjay@kernel.org/
- Alexei 复审: https://lore.kernel.org/all/DLNOU1DBG2W4.1SHS4ZHDHYUM3@gmail.com/
- v2 3/3 补丁: https://lore.kernel.org/all/20260924160354.531101-4-puranjay@kernel.org/
