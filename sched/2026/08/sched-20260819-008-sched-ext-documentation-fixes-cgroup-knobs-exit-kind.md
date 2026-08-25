# Liang Luo 修两处 sched-ext 文档：cgroup-v2.rst 里 `cpu.max`/`cpu.max.burst`/`cpu.idl...


## TL;DR
Liang Luo 修两处 sched-ext 文档：cgroup-v2.rst 里 `cpu.max`/`cpu.max.burst`/`cpu.idle` 应说明也作用于实现了对应回调的 BPF 调度器；sched-ext.rst 示例 `ei->type` 应为 `ei->kind`。纯文档，合入概率高。

## 背景与问题
- `Documentation/admin-guide/cgroup-v2.rst` 中 `cpu.max`/`cpu.max.burst`/`cpu.idle` 仅写 "affects only processes under the fair-class scheduler"，但 sched_ext 通过 `cgroup_set_bandwidth` / `cgroup_set_idle` 回调把这些 knobs 透传给 BPF 调度器，措辞与已更新的 `cpu.weight` 不一致，BPF 用户难以发现这些通知点。
- `Documentation/scheduler/sched-ext.rst` 的 `ops.exit()` 示例读 `ei->type`，但 `struct scx_exit_info` 从未有 `type` 字段——退出原因自该结构体引入起就是 `ei->kind`。照抄示例的调度器会编译失败（`error: no member named 'type'`）。Fixes `fa48e8d2c7b5`。

## 技术方案
- cgroup-v2.rst：三处描述加 "and a BPF scheduler with the `cgroup_set_bandwidth` / `cgroup_set_idle` callback depending on what the callback actually does"。
- sched-ext.rst：`exit_type = ei->type;` → `exit_type = ei->kind;`。

## 版本演进与当前进展
v1（2026-08-19）两封独立补丁同天发出，暂无 reviewer 正式回复。

## Maintainer 意见与讨论焦点
暂无正式回复。与同日 sched_ext 带宽文档讨论（article 010）同源：社区倾向用文档而非运行时警告来说明 "BPF 调度器可能不实现某些 knob"。

## 合入评估
合入可能性 high：纯文档修正，定位准确（含 Fixes 标签），无功能风险。

## 效果评估
无性能数据（文档）。

## 我可以参与的点
- 可作为 reviewer 给出 ack；或检查 sched-ext.rst 是否还有其它过时字段引用。

## 参考链接
- lore thread: 未获取到
- Fixes: fa48e8d2c7b5

---
id: sched-20260819-008
date: 2026-08-19
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<unknown>"
lore_url: "未获取到"
authors: [Liang Luo]
maintainers_involved: [Tejun Heo, Changwoo Lee]
current_version: v1
patch_series:
  - version: v1
    msgid: "<unknown>"
    date: 2026-08-19
    summary: "sched-ext 文档两连修：(1) 把 cpu.max / cpu.max.burst / cpu.idle 的描述从'仅影响 fair-class'改为'也影响实现了 cgroup_set_bandwidth / cgroup_set_idle 回调的 BPF 调度器'（与 cpu.weight 措辞对齐）；(2) 修正 sched-ext.rst 中 ops.exit() 示例的 ei->type -> ei->kind（struct scx_exit_info 从未有 type 字段，自引入起就是 kind），Fixes fa48e8d2c7b5。"
    review_outcome: "v1 刚发出，暂无 reviewer 正式回复。"
upstream_commit: null
fixes_commit: "fa48e8d2c7b5 (\"sched_ext: Documentation: scheduler: Document extensible scheduler class\")"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["纯文档，需 sched_ext 维护者 ack"]
  next_action: "等待 Tejun/Changwoo 收下。"
contribution_opportunities:
  - kind: review
    description: "可帮忙 ack 这两处文档修正。"
generated_at: "2026-08-20T00:30:00"
source_email_count: 2
related_articles: ["sched-20260818-004", "sched-20260818-005"]
tags: [sched_ext, cgroup, documentation]
---
