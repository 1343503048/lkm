# sched dynamic simplify preempt_dynamic v2

# sched: 简化 PREEMPT_DYNAMIC（v2 0/6 与 2/6 收尾）

## 摘要

Mark Rutland 的「简化 PREEMPT_DYNAMIC」系列（v2，6 个 patch）在 08-05 推进，本日可见 v2 0/6（cover）与 2/6（具体 patch）的 review 往返。目标：去掉 PREEMPT_DYNAMIC 里针对各架构的重复的、脆弱的静态跳板（static jump / patching）样板，统一成更薄的通用层，让 arm64 / x86 / riscv 共用一套入口。

要点：
- **v2 0/6**：Mark 在 cover 里说明 v2 相对 v1 的主要变化——把原来分散在 `arch/*/kernel/entry_*.c` 的 preempt 模式切换收敛到 `kernel/sched/core.c` 提供的通用 helper，减少每架构的拷贝代码。
- **2/6**：具体实现「用一个通用 `preempt_dynamic_enable()` 包装替掉各架构的 `__preempt_dynamic_enable()` 变体」。本日 review 集中在该 helper 的参数化（是否需要传入 `key` 与回调）以及和 `static_call` 的初始化顺序，避免早期启动阶段（before `jump_label`/`static_call` 可用）调用导致空指针。

## 技术细节

PREEMPT_DYNAMIC 当前允许在启动后于 `none` / `voluntary` / `full` 之间切换，依赖 `static_key` / `static_call` 改写抢占相关函数指针。各架构自行实现了几乎是同一套的 `preempt_dynamic_enable()`，差异仅在调用哪个 `static_call` 目标。

v2 的简化：
```
// 通用层
void preempt_dynamic_enable(enum preempt_dynamic_mode mode,
                            struct static_call_key *key,
                            void *target);
// 各架构只注册自己的 key/target，不再各自实现 enable 逻辑
```

争议/关注点：
- 早期启动期：static_call 尚未初始化时如果触发模式设置，需保证降级到直接函数指针而非解引用未初始化的 key。Mark 在 2/6 里用一个 `preempt_dynamic_state_init_done` 标志保护。
- Peter 关注 `static_call` 与 `static_key` 两套机制在切换时的顺序，防止出现「key 已翻转但 call 目标未更新」的中间态。

## 影响与风险

- 影响面：所有启用 `PREEMPT_DYNAMIC` 的架构（arm64/x86/riscv 为主）。纯重构，不改变运行时抢占语义。
- 风险：低—中。重构涉及启动早期路径，需在多架构上跑一遍 boot 验证；但逻辑等价。
- 收益：减少每架构拷贝代码，降低后续新增架构的接入成本，也便于统一修复 preempt 模式切换的潜在 bug。

## 评价

属于健康的维护性重构，方向清晰、reviewer（Peter）已介入。合入可能性高，建议等 v2 各架构 ack 后进入 tip/sched/core。

---
subject: "sched dynamic simplify preempt_dynamic v2"
id: sched-20260805-003
date: "2026-08-05"
title: "sched: 简化 PREEMPT_DYNAMIC（v2 0/6 与 2/6 收尾）"
series: "Simplify PREEMPT_DYNAMIC"
type: feature
status: under_review
severity: none
merge_likelihood: high
tags: [preempt, topology]
authors: ["Mark Rutland <mark.rutland@arm.com>"]
reviewers: ["Peter Zijlstra <peterz@infradead.org>"]
related_articles: ["sched-20260804-009"]
emails: ["uid-22078@qq-imap", "uid-22034@qq-imap"]
---
