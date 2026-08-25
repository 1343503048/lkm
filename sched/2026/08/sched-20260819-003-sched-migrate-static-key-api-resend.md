# sched/migrate static key api resend


## TL;DR
Hongyan Xia 把调度子系统里残留的 deprecated raw `static_key` API 统一迁移到新的 `static_branch_*` API（含 `sched_feat` 数组用 union 包装 true/false 两种类型），无功能变化。RESEND 已拆成独立补丁、paravirt 部分拿到 Ack。纯清理，合入概率高。

## 背景与问题
raw `struct static_key` 与 `static_key_true/false()` 已被废弃；`__cfs_bandwidth_used`、`paravirt_steal_*`、`sched_feat` 数组仍直接用旧 API。属于代码质量/API 现代化改进，非 bug。

## 技术方案
- `core.c`：`preempt_dynamic_key_{enable,disable}` 宏改为 `preempt_dynamic_branch_{enable,disable}`，并迁移 `sk_dynamic_*` 到 `static_branch_*`。
- `fair.c`：`__cfs_bandwidth_used` 的 `static_key_{enable,disable}` 改 `static_branch_*`。
- `debug.c` / `sched.h`：`sched_feat_keys[]` 从 `struct static_key` 改为 `union sched_feat_key`（含 `key_true`/`key_false`），因新 API 对 true/false 是不同类型；`sched_feat_enable/disable` 改用 `static_branch_enable/disable_cpuslocked`。
- paravirt：`paravirt_steal_rq_enabled` / `paravirt_steal_enabled` 迁移，已获 Juergen Gross Acked-by。

## 版本演进与当前进展
RESEND（2026-08-19）相较初版：将原系列拆成独立补丁（更易 review），并把 `sk_dynamic_*` 也一并迁移到新 API。`paravirt_steal` 补丁已有 Juergen Gross 的 Acked-by。

## Maintainer 意见与讨论焦点
无反对意见。`sched_feat` 那封技术上最棘手（true/false 两种 key 类型需用 union 包装），作者已在 commit message 说明取舍。

## 合入评估
合入可能性 high：纯非功能清理，且 paravirt 部分已 ack。无阻塞，等 maintainer 收尾。

## 效果评估
无功能变化，无性能数据（作者明确 "No functional change"）。

## 我可以参与的点
- 可作为 reviewer 确认拆分后各补丁正确性（尤其 union 包装的 sched_feat 改动）。

## 参考链接
- lore thread: 未获取到

---
id: sched-20260819-003
date: 2026-08-19
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<unknown>"
lore_url: "未获取到"
authors: [Hongyan Xia]
maintainers_involved: [Peter Zijlstra, Ingo Molnar]
current_version: RESEND
patch_series:
  - version: RESEND
    msgid: "<unknown>"
    date: 2026-08-19
    summary: "将调度子系统中直接使用的 raw static_key / static_key_{true,false}() 及 __cfs_bandwidth_used、paravirt_steal、sched_feat 数组统一迁移到新的 static_branch_* API（STATIC_KEY_TRUE_INIT / STATIC_KEY_FALSE_INIT、static_branch_enable/disable）。无功能变化。RESEND 把原系列拆成独立补丁便于 review，并额外迁 sk_dynamic_* 到新 API。"
    review_outcome: "paravirt_steal 那封已获 Juergen Gross Acked-by；其余为 RESEND 拆分，暂无明显反对。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["纯清理，需 maintainer 收尾 ack"]
  next_action: "等待 Peter/Ingo 收下 RESEND 拆分后的各补丁。"
contribution_opportunities:
  - kind: review
    description: "可帮忙 ack/review 拆分后的各独立补丁（core.c / fair.c / debug.c / paravirt 部分）。"
generated_at: "2026-08-20T00:30:00"
source_email_count: 3
related_articles: []
tags: [sched/core, sched/fair, preempt]
---
