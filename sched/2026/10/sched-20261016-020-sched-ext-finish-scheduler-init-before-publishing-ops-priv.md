# sched_ext: finish scheduler init before publishing ops priv

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261015-009：Binbin Deng 修复 sched_ext 注册路径的 publish-before-init 竞态——`scx_alloc_and_add_sched()` 在 scheduler 初始化完成**之前**就 `rcu_assign_pointer(ops->priv, sch)` 发布指针，BPF kfuncs 可在 RCU 下读到未初始化字段；补丁把发布推迟到初始化完成之后（仅静态分析发现）。
- sched-20261016-020（今天）：Andrea Righi 回帖质疑——「这个窗口里我看不到任何 kfunc 能访问未初始化字段；旧新发布点之间也没有可失败操作；这个改动到底防的是什么失败？」，要求作者先给 reproducer 或具体代码路径。

## 背景与问题
（承接 20261015-009）原补丁主张 `ops->priv` 发布过早，BPF kfuncs 经 `scx_prog_sched()` 在 RCU 下解引用可能读到未初始化字段。Andrea 今天的质疑是：子调度器 kset 在任一发布点之后才创建，且旧新发布点之间没有可失败操作，看不到实际可触发的失败路径。

## 技术方案
（承接 20261015-009）无代码变更；作者需提供 reproducer 或具体代码路径，证明发布点后移确实防止了某种失败，否则补丁可能不被接受。

## 版本演进与当前进展
v1（2026-10-15）→ 今天 Andrea 要求提供证据。作者尚未回应。

## Maintainer 意见与讨论焦点
Andrea Righi（sched_ext reviewer）：「Please always provide a reproducer or a clear, concrete code path to the reported failure before sending a fix.」——未直接否定修复，但要求作者补齐触发证据，否则视为未论证。

## 合入评估
*likelihood=medium*。缺陷逻辑上自洽（publish-before-init 违反 RCU 发布语义），但 Andrea 要求补 reproducer/代码路径。*blocking_issues*：作者未提供 reproducer 或具体触发路径，reviewer 质疑改动必要性。*next_action*：作者回应 Andrea，给出具体可触发的代码路径或承认是预防性修复。

## 效果评估
无量化数据（作者自述仅静态分析发现、未在运行时观察）。

## 我可以参与的点
- *review*：核对 `scx_alloc_and_add_sched()` 发布点后移后所有 `scx_prog_sched()` 读者路径，判断旧新发布点之间是否存在可被 BPF kfunc 观察到的未初始化字段。

## 参考链接
- Andrea 的回复：https://lore.kernel.org/all/atEFSsTO9eT_O9ql@gpd4/
- 原补丁：https://lore.kernel.org/all/20261015081431.46628-1-18983559317@163.com/

---
id: sched-20261016-020
date: 2026-10-16
subject: "sched_ext: finish scheduler init before publishing ops priv"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261015081431.46628-1-18983559317@163.com>"
lore_url: "https://lore.kernel.org/all/20261015081431.46628-1-18983559317@163.com/"
authors: ["Binbin Deng"]
maintainers_involved: ["Andrea Righi"]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261015081431.46628-1-18983559317@163.com>"
    date: 2026-10-15
    summary: "把 ops->priv 发布推迟到 scheduler 初始化与 arena 建立完成之后"
    review_outcome: "Andrea Righi 要求补 reproducer/具体代码路径"
upstream_commit: null
fixes_commit: "105dcd005be2"
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["作者未提供 reproducer 或具体触发路径，reviewer 质疑改动必要性"]
  next_action: "作者回应 Andrea，给出具体可触发路径或承认是预防性修复"
contribution_opportunities:
  - kind: review
    description: "核对发布点后移后所有 scx_prog_sched() 读者路径是否存在可被观察的未初始化字段"
generated_at: "2026-10-17T01:30:00"
source_email_count: 1
related_articles: ["sched-20261015-009"]
tags: [sched_ext]
---