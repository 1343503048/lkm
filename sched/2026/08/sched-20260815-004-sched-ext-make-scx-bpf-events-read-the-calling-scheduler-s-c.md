# sched_ext: Make scx_bpf_events() read the calling scheduler's counters

## TL;DR
Tejun Heo 提交 2 个 sched_ext 小修：让 `scx_bpf_events()` 读取"调用程序所属调度器"的事件计数器（此前误读 root 调度器），并修正注释为规范 kerneldoc。属正确性修复，合入概率高。

## 背景与问题
`scx_bpf_events()` 一直读取 root 调度器的事件计数器。当一个 sub-scheduler 程序查询自身事件时，会静默拿到 root 的计数器，且没有 BPF 可见的接口能读到自己的（只有 per-scheduler 的 sysfs `events` 文件可读）。

## 技术方案
- patch 1：修复 `scx_bpf_dsq_reenq()` 兼容层（旧问题延续处理，见 010 系列）。
- patch 2：给 `scx_bpf_events()` 加 `KF_IMPLICIT_ARGS`，通过 `scx_prog_sched(aux)` 从调用程序解析所属调度器；未关联程序走 usual 的 `scx_prog_sched()` 解析（pre-sub-attach 兼容 root 或零计数）。同时把畸形注释改为规范 kerneldoc，并修正 `__sz` 拼写。

## 版本演进与当前进展
v2 同日演进（封面 41296 标注 `[PATCH 1/2]`/`[PATCH 2/2]`，后续有 v2 修订）。暂无外部 review 意见。

## Maintainer 意见与讨论焦点
v1/v2 刚发出，暂无 review 意见（作者为维护者）。

## 合入评估
合入可能性高。`scx_bpf_events` 改为 `KF_IMPLICIT_ARGS` 会改 kfunc 签名，但因是隐式参数、且 resolved via aux，对 BPF 程序不可见，风险低，预期由 Tejun 直接 apply。

## 效果评估
修复 sub-scheduler 读到错误（root）计数器这一正确性 bug；无性能数据讨论。

## 我可以参与的点
- 在 sub-scheduler 场景下验证 `scx_bpf_events()` 现返回自身计数器。

## 参考链接
- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
subject: "sched_ext: Make scx_bpf_events() read the calling scheduler's counters"
id: sched-20260815-004
date: 2026-08-15
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<uid-41296@qq-imap>"
lore_url: "未获取到"
authors: [Tejun Heo]
maintainers_involved: [Tejun Heo]
current_version: v2
patch_series:
  - version: v1
    msgid: "<uid-41296@qq-imap>"
    date: 2026-08-15
    summary: "2 个 patch：scx_bpf_dsq_reenq 兼容修正 + scx_bpf_events() 改为读取调用程序所属调度器的计数器。"
    review_outcome: "v1 刚发出，暂无 review 意见；v2 仍在同日后续讨论中。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: [scx_bpf_events 改动涉及 KF_IMPLICIT_ARGS 签名变化，需确认 BPF 校验器/compat 路径]
  next_action: "等待 Tejun 自身 apply（维护者即作者）。"
contribution_opportunities:
  - kind: testing
    description: "子调度器（sub-scheduler）场景下验证 scx_bpf_events() 现在返回自身计数器而非 root 的。"
generated_at: "2026-08-16T00:10:00"
source_email_count: 2
related_articles: []
tags: [sched_ext]
---
