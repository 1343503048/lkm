# sched/fair: Fix cgroup::idle preemption

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261106-003：Peter Zijlstra 发出 3 补丁系列修复 cgroup SCHED_IDLE 任务组的抢占问题：patch 1 用 guard 清理 `sched_group_set_idle()`、patch 2 把 `cfs_rq::idle` 改为「祖先 tg::idle 之和」、patch 3（RFC）携带 Vincent 的 `sched/eevdf: Fix sched idle task group preemption`。Kayra 指出 patch 2 有任务组创建竞态并追问 `se_is_idle()`；Peter 补上判定。
- sched-20261107-005：Peter 发出 patch 2 v2（并入竞态修正）；Kayra 给 patch 2 v2 与 patch 3 RFC 双 Reviewed-by；Vincent 给 patch 1 Reviewed-by。
- sched-20261109-006：Vincent 给 patch 2 v2 补上 Reviewed-by，至此 patch 1/2 均已获 Vincent + Kayra 双维护者评审，patch 3 仍为 RFC。
- sched-20261110-011（今天）：**Josh Don 补上 patch 1/2 的 Reviewed-by，但对 patch 3（RFC）提出实质设计质疑**——`se_is_idle()` 现在检查「任何 idle 祖先」会导致嵌套场景抢占判定错误（普通任务与 SCHED_IDLE 任务同处 idle cgroup 时普通任务不再抢占 SCHED_IDLE），给出两个具体例子与两种修法；Kayra 也追问「是否要保留 idle 祖先组之间的 idle 差异」。

## 背景与问题

（承接 sched-20261106-003 / 20261107-005 / 20261109-006）cgroup SCHED_IDLE 任务组的抢占语义：`cfs_rq::idle` 此前只反映本组自身 idle 状态、未聚合祖先，导致嵌套 idle 判定错误。Peter 用「`cfs_rq::idle` = 祖先 tg::idle 之和」修复，并为 patch 3 的 EEVDF 抢占优化打底。今日 Josh Don 的质疑直指 patch 3 里 `se_is_idle()` 的「检查任何祖先」语义。

## 技术方案

patch 2（`Make cfs_rq::idle the sum of ancestor tg::idle`）把 `cfs_rq::idle` 改为祖先 tg::idle 之和；patch 1（`Use guard in sched_group_set_idle()`）用 guard 清理。今日 Josh 对两者都给 Reviewed-by。

焦点在 patch 3（RFC `Fix sched idle task group preemption`）：Josh 指出 `se_is_idle()` 现在「检查任何 idle 祖先」并不正确，给两个反例——例 1：普通任务与 SCHED_IDLE 任务都在 idle cgroup 内，`se_is_idle()` 对两个 se 都返回 true，于是普通任务不再抢占 SCHED_IDLE 任务（期望行为是相对 SCHED_IDLE 普通任务并非 idle）；例 2：`root → cgrp A(idle) → {cgrp B, cgrp C(idle)} → {task_1, task_2}`，task_1 应抢占 task_2，但 matching_se 是 cgrp B/C 且都显示 idle。Josh 给出两种修法：① 用现有 `se_is_idle()` 决定能否快路径跳过 `find_matching_se()`，但找到 matching se 后改用更聚焦的 helper 直接比较这两个实体本身（任务比较 idle policy、组比较 `tg_is_idle()`）；② 找到 matching se 后直接比较 `->idle` 值（一个比另一个大（至多 1）即相对 idle），但任务 vs 组的处理略乱。Kayra 追问：是否真的想保留 idle 祖先组之间的 idle 差异。

## 版本演进与当前进展

*current_version: v2（patch 2，2026-11-07 发出）*。今日：Josh 补 patch 1/2 Reviewed-by，并对 patch 3 提出需改 `se_is_idle()` 判定方式的实质意见；Kayra 追加语义追问。patch 3 仍未定型。

## Maintainer 意见与讨论焦点

- **Josh Don（Google，sched 核心贡献者）**：patch 1/2 Reviewed-by；patch 3 提出设计级异议（se_is_idle 祖先检查导致嵌套抢占错误）+ 两种修法。
- **Kayra Cizmeci**：追问「是否要保留 idle 祖先组之间的 idle 差异」，隐含对 patch 3 语义的进一步澄清诉求。
- 无 NAK。patch 1/2 已收敛可收，patch 3 的 `se_is_idle()` 语义需 Peter 回应 Josh 的两例。

## 合入评估

*likelihood=high*（对 patch 1/2）。patch 1/2 已获 Vincent + Kayra + Josh 三方评审，可独立收取；patch 3 仍 RFC、且刚被 Josh 指出具体反例需修订。*blocking_issues*：① patch 2 是否补 Fixes 标签待定（Kayra 此前建议）；② patch 3 的 `se_is_idle()` 判定需按 Josh 意见改。*next_action*：Peter 收取 patch 1/2；patch 3 回应 Josh 的两例并修订 `se_is_idle()` 用法。

## 效果评估

无量化性能数据，属抢占语义正确性修复。Vincent 此前确认 patch 2 可避免 `find_matching_se()` 无谓调用（微观优化，未见 benchmark）。

## 我可以参与的点

- **review**：就 Josh 提出的两种修法（聚焦 helper vs 比较 `->idle` 值）评估哪个更稳（尤其任务 vs 组、嵌套多层的边界）——这是 patch 3 能否定型的关键开放问题。

## 参考链接

- Josh 对 patch 3 的质疑: https://lore.kernel.org/all/CABk29Nujsg7FNY4yJ3Yd0maT0GEtvxacUWvTDiT5HD=-YVqTvg@mail.gmail.com/
- Josh 对 patch 1 的 Reviewed-by: https://lore.kernel.org/all/CABk29NvMcBSO_Eu3VN5Au1QjZHcFESmNWCqmD0fEwydmctUL=w@mail.gmail.com/
- Josh 对 patch 2 的 Reviewed-by: https://lore.kernel.org/all/CABk29Nuee4RVMcWGtZk4geGMigx-dTkiWUhex1LuUv-N_ub-8A@mail.gmail.com/

---
id: sched-20261110-011
date: '2026-11-10'
subject: "sched/fair: Fix cgroup::idle preemption"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<CABk29Nujsg7FNY4yJ3Yd0maT0GEtvxacUWvTDiT5HD=-YVqTvg@mail.gmail.com>"
lore_url: "https://lore.kernel.org/all/CABk29Nujsg7FNY4yJ3Yd0maT0GEtvxacUWvTDiT5HD=-YVqTvg@mail.gmail.com/"
authors: [Peter Zijlstra, Vincent Guittot]
maintainers_involved: [Josh Don, Vincent Guittot]
current_version: v2
patch_series:
  - version: v2
    msgid: "<20261107113639.GK2668200@noisy.programming.kicks-ass.net>"
    date: '2026-11-07'
    summary: "patch 2 v2 把 cfs_rq::idle 改为祖先 tg::idle 之和，并入竞态修正"
    review_outcome: "Josh 补 Reviewed-by；patch 3 被 Josh 指出现嵌套抢占反例"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - "patch 2 是否补 Fixes 标签待定"
    - "patch 3 的 se_is_idle() 判定需按 Josh 意见改"
  next_action: "Peter 收取 patch 1/2；patch 3 回应 Josh 两例并修订"
contribution_opportunities:
  - kind: review
    description: "评估 Josh 的两种修法（聚焦 helper vs 比较 idle 值）在嵌套多层下的正确性"
generated_at: "2026-11-11T09:00:00+08:00"
source_email_count: 4
related_articles: [sched-20261106-003, sched-20261107-005, sched-20261109-006]
tags: [cgroup, cfs, eevdf]
---