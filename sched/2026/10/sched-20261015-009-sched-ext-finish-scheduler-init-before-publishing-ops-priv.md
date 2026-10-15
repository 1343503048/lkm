# sched_ext: finish scheduler init before publishing ops priv

## TL;DR
Binbin Deng 修复 sched_ext 注册路径的 publish-before-init 竞态：`scx_alloc_and_add_sched()` 在初始化 scheduler 的 kobject、链表、子调度器 kset、以及消费 BPF arena 引用**之前**就 `rcu_assign_pointer(ops->priv, sch)` 发布了指针；BPF kfuncs 经 `scx_prog_sched()` 在 RCU 下解引用 `ops->priv`，注册尚未完成时程序就能读到未初始化字段。补丁把发布推迟到所有易失败的初始化和 arena 建立成功之后。带 `Fixes: 105dcd005be2 ("sched_ext: Introduce scx_prog_sched()")` 与 `Cc: stable@vger.kernel.org`，仅代码审计发现、未见运行时触发。

## 背景与问题
`sched_ext` 的 struct_ops 注册路径：attachment 期间若一个 sched_ext 程序 reach 到解析 scheduler 的 kfunc，`scx_prog_sched()` 的读者会在 RCU 下解引用 `ops->priv`。一旦指针被发布，程序就能用到创建路径尚未初始化的字段（kobject/kset、sibling 链表、arena 引用）。作者经静态分析辅助审计发现（Coccinelle 规则给出候选点，LLM 辅助（GLM-5.3）代码审查确认读者/写者路径），未在运行时观察到。

## 技术方案
单补丁（kernel/sched/ext/ext.c，+8/−7）：把 `rcu_assign_pointer(ops->priv, sch)` 从当前位置（`INIT_LIST_HEAD(&sch->sibling)` 之后）后移到 `sch->kobj.kset = scx_kset`、`INIT_LIST_HEAD(...)`、arena 消费（`cmd->arena_map` 转移给 scheduler）等易失败初始化完成之后，确保发布时字段已就绪。

## 版本演进与当前进展
v1 刚发出（<20261015081431.46628-1-18983559317@163.com>），无 review 意见。

## Maintainer 意见与讨论焦点
暂无维护者表态。潜在关注点：发布后移是否覆盖所有读者（`scx_prog_sched()` 及其它 kfunc 的 RCU 读者），以及 arena 引用转移的时序正确性，需 Tejun Heo / sched_ext 维护者确认。作者带 `Cc: stable`，暗示他认为是可 backport 的竞态修复。

## 合入评估
*likelihood=medium*。逻辑自洽、缺陷真实（publish-before-init 违反 RCU 发布语义），但仅静态分析发现、无运行时证据，需维护者确认读者路径覆盖。*blocking_issues*：暂无 review；静态分析结论未经运行时验证。*next_action*：等 sched_ext 维护者 review，确认所有 RCU 读者都受益于发布后移。

## 效果评估
暂无效果数据。作者明确标注「未在运行时观察，仅代码审查发现」。

## 我可以参与的点
- *review*：核对 `scx_alloc_and_add_sched()` 发布点后移后，所有 `scx_prog_sched()` 读者（含子调度器路径）是否都能读到完整初始化后的 scheduler。
- *testing*：构造一个在注册进行中就 reach kfunc 的 struct_ops 程序，验证旧代码可触发未初始化字段、新代码安全。

## 参考链接
- patch：https://lore.kernel.org/all/20261015081431.46628-1-18983559317@163.com/

---
id: sched-20261015-009
date: 2026-10-15
subject: "sched_ext: finish scheduler init before publishing ops priv"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261015081431.46628-1-18983559317@163.com>"
lore_url: "https://lore.kernel.org/all/20261015081431.46628-1-18983559317@163.com/"
authors: ["Binbin Deng"]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261015081431.46628-1-18983559317@163.com>"
    date: 2026-10-15
    summary: "把 ops->priv 发布推迟到 scheduler 初始化与 arena 建立完成之后"
    review_outcome: "暂无 review"
upstream_commit: null
fixes_commit: "105dcd005be2"
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["暂无 review；静态分析结论未经运行时验证"]
  next_action: "等 sched_ext 维护者 review，确认所有 RCU 读者覆盖"
contribution_opportunities:
  - kind: review
    description: "核对发布点后移后所有 scx_prog_sched() 读者都能读到完整初始化"
  - kind: testing
    description: "构造注册期间 reach kfunc 的程序，验证修复有效性"
generated_at: "2026-10-16T01:05:00"
source_email_count: 1
related_articles: []
tags: [sched_ext]
---