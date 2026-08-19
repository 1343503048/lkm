# preempt: Introduce HAS_SEPARATE_PREEMPT_RESCHED_BITS

# preempt: 引入 HAS_SEPARATE_PREEMPT_RESCHED_BITS


## TL;DR
`preempt` 引入 `HAS_SEPARATE_PREEMPT_RESCHED_BITS`，允许架构把 PREEMPT 与 NEED_RESCHED 位拆分存储，缓解 TIF 位紧张。Peter Zijlstra 要求合并前两 patch，s390 已给 Reviewed-by。合入可能性高。

## 背景与问题
`TIF_NEED_RESCHED` 与 `TIF_PREEMPT` 等抢占相关标志挂在 thread_info flags 上，而各架构 thread_info 的位空间紧张。某些架构希望把 PREEMPT 标志和 NEED_RESCHED 放在**不同的 word/byte** 上（例如用专门的抢占位域），以便用普通 load-store 而非原子 set-bit 来更新，减少原子操作开销。当前 Kconfig 不支持这种分离。

## 技术方案
新增 `HAS_SEPARATE_PREEMPT_RESCHED_BITS` Kconfig 选项。启用后，架构可以把抢占相关位拆到独立存储。s390 侧据此实现：仅 `set_thread_flag()` / `arch_set_task_state()` 写 TIF，可安全使用 load-store 而非 set-bit 原子操作（Heiko Carstens 确认）。v2 还包含 s390 的 HARDIRQ 相关位调整（16495/16879 同主题）。

## 版本演进与当前进展
当前 v2（2026-08-03）。Peter Zijlstra 的 review 要求：把前两个 patch 合并为一个（`move TIF_NEED_RESCHED_LAZY` 之类的拆分重构合并表述）。s390 维护者 Heiko Carstens 已给 `Reviewed-by`。

## Maintainer 意见与讨论焦点
- Peter Zijlstra：明确「合并 patch 1+2」（实现整洁性）。
- Heiko Carstens (s390)：确认分离位后只有有限的 TIF 写点，可安全用 load-store，给出 Reviewed-by。

属于纯架构/基础设施重构，无行为分歧。

## 合入评估
合入可能性 high。技术障碍已清除（仅剩 patch 合并整理），且关键架构 maintainer 已认可。

## 效果评估
邮件未给基准数字。属架构基础设施重构，效果在于「减少原子位操作 / 缓解 TIF 位紧张」，需架构 maintainer 自测验证，无量化数据公开。

## 我可以参与的点
- 可审阅 x86 等 TIF 位同样紧张的架构是否适配该 Kconfig，提出 arch 侧 review 或测试。

## 参考链接
- lore thread: 未获取到

---
subject: "preempt: Introduce HAS_SEPARATE_PREEMPT_RESCHED_BITS"
id: sched-20260803-007
date: 2026-08-03
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<unknown>"
lore_url: "unknown"
authors: [Boqun Feng]
maintainers_involved: [Peter Zijlstra, Thomas Gleixner, Heiko Carstens]
current_version: v2
patch_series:
  - version: v2
    msgid: "<unknown>"
    date: 2026-08-03
    summary: "引入 HAS_SEPARATE_PREEMPT_RESCHED_BITS Kconfig，允许架构把 PREEMPT 与 NEED_RESCHED 标志分开保存在不同的 word/byte。Peter Zijlstra 要求把前两个 patch 合并；s390 侧 Heiko Carstens 给出实现 Reviewed-by。"
    review_outcome: "Peter Zijlstra：合并 patch 1+2。Heiko Carstens (s390)：Reviewed-by（确认仅 set_thread_flag()/arch_set_task_state() 写 TIF 可安全使用 load-store 而非 set-bit）。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["仅剩 patch 1+2 合并的整理，无技术障碍"]
  next_action: "按 PeterZ 合并前两 patch 发 v3，配合 s390 Reviewed-by 即可合入相关架构分支。"
contribution_opportunities:
  - kind: review
    description: "可审阅其他需要分开 PREEMPT/NEED_RESCHED 位的架构（如 x86 在 TIF 位紧张下的场景）是否也受益于该 Kconfig，提出相应 arch 适配 review。"
generated_at: "2026-08-04T00:20:00"
source_email_count: 1
related_articles: []
tags: [preempt, arch]
---
