# sched: dynamic: Simplify PREEMPT_DYNAMIC

# sched: 简化 PREEMPT_DYNAMIC（v2）

## TL;DR
在 08-03-007 引入 `HAS_SEPARATE_PREEMPT_RESCHED_BITS` 的基础上，Mark Rutland 进一步简化 PREEMPT_DYNAMIC 的静态键选择与重写逻辑（6 笔 patch），收敛架构分支。这是 08-03-007 的延续，合入可能性 high。

## 背景与问题
PREEMPT_DYNAMIC 允许运行时在 none/voluntary/full 间切换抢占模型，依赖静态键重写。其选择与重写逻辑在各架构分支中较为分散，且与 08-03-007 新增的「分开 PREEMPT/NEED_RESCHED 位」基础设施未充分整合。

## 技术方案
v2 在 `HAS_SEPARATE_PREEMPT_RESCHED_BITS` 之上，把动态抢占的静态键选择/重写逻辑收敛到统一路径，减少架构分支与重复。6 笔 patch 覆盖核心选择逻辑与各 arch 适配。

## 版本演进与当前进展
- 08-03：引入 HAS_SEPARATE_PREEMPT_RESCHED_BITS（08-03-007）。
- 08-04：v2 进一步简化 PREEMPT_DYNAMIC，6 笔 patch。

## Maintainer 意见与讨论焦点
Mark Rutland 主导，Peter Zijlstra / Thomas Gleixner 尚未在 08-04 回帖。预期为纯基础设施收敛，无方向反对。

## 合入评估
合入可能性 high。基础设施重构，需架构 maintainer 确认分支收敛无行为差异。

## 效果评估
无基准；属抢占基础设施整洁性/收敛，效果以「减少架构分支、无行为回归」衡量。

## 我可以参与的点
- 审阅 v2 对 x86/arm64 PREEMPT_DYNAMIC 静态键重写路径的收敛是否引入行为差异，回帖架构侧 review。

## 参考链接
- 08-03 文章：sched-20260803-007-preempt-introduce-has_separate_preempt_resched_bits

---
subject: "sched: dynamic: Simplify PREEMPT_DYNAMIC"
id: sched-20260804-009
date: 2026-08-04
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<unknown>"
lore_url: "unknown"
authors: [Mark Rutland]
maintainers_involved: [Peter Zijlstra, Thomas Gleixner]
current_version: v2
patch_series:
  - version: v2
    msgid: "<unknown>"
    date: 2026-08-04
    summary: "基于 08-03-007 的 HAS_SEPARATE_PREEMPT_RESCHED_BITS，进一步简化 PREEMPT_DYNAMIC：把动态抢占的静态键选择/重写逻辑收敛，减少架构分支。6 笔 patch。"
    review_outcome: "Mark Rutland 主导，延续 08-03-007 的基础设施重构方向；Peter Zijlstra / Thomas Gleixner 尚未在 08-04 回帖。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["需架构 maintainer 对各 arch 分支收敛的确认"]
  next_action: "等待 PeterZ / tglx 对动态抢占简化的最终认可。"
contribution_opportunities:
  - kind: review
    description: "可审阅 v2 对 x86/arm64 等架构 PREEMPT_DYNAMIC 静态键重写路径的收敛是否引入了行为差异，回帖架构侧 review。"
generated_at: "2026-08-05T00:25:00"
source_email_count: 1
related_articles: ["sched-20260803-007-preempt-introduce-has_separate_preempt_resched_bits"]
tags: [preempt, arch]
---
