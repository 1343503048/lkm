# Documentation: power/cpuidle: Fix repeating phrase

## TL;DR

Norsyazwina Fazrul 提交的 cpuidle 文档修订（去掉一处重复措辞）获 Rafael Wysocki 应用为 7.4 material。属纯文档打磨，无技术风险。

## 背景与问题

`Documentation/admin-guide/pm/cpuidle.rst` 里存在一处重复/赘述的措辞，读起来冗余。作者提交单枚文档补丁清理。

## 技术方案

纯文本修订：删除重复短语，无代码改动、无行为影响。

## 版本演进与当前进展

v1 提交后，09-26 Rafael Wysocki（`<CAJZ5v0jepvJLOVFWypNPsRYcbQtqbQFSFjDLTU+CrHAGGZzfww@mail.gmail.com>`）回复 "Applied as 7.4 material, thanks!"，直接应用。

## Maintainer 意见与讨论焦点

- **Rafael Wysocki**（电源管理维护者）：无异议，直接应用为 7.4 材料。无分歧。

## 合入评估

已应用（*likelihood=merged*），目标 7.4。*blocking_issues*：无。*next_action*：无，等待 7.4 窗口随分支进入主线。

## 效果评估

文档修订，无可量化运行时效果。

## 我可以参与的点

已应用，当前阶段暂无明显参与空间。

## 参考链接

- Rafael 应用回帖: https://lore.kernel.org/all/CAJZ5v0jepvJLOVFWypNPsRYcbQtqbQFSFjDLTU+CrHAGGZzfww@mail.gmail.com/
- 原补丁: https://lore.kernel.org/all/20260915220105.14655-1-norsyazwina.fazrul@gmail.com/

---
id: sched-20260926-010
date: 2026-09-26
subject: "Documentation: power/cpuidle: Fix repeating phrase"
subsystem: sched
type: fix
status: merged_tip
severity: none
thread_root_msgid: "<20260915220105.14655-1-norsyazwina.fazrul@gmail.com>"
lore_url: "https://lore.kernel.org/all/CAJZ5v0jepvJLOVFWypNPsRYcbQtqbQFSFjDLTU+CrHAGGZzfww@mail.gmail.com/"
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: "2026-09-27T01:20:00"
authors:
  - "Norsyazwina Fazrul"
maintainers_involved:
  - "Rafael Wysocki"
patch_series:
  - version: v1
    msgid: "<20260915220105.14655-1-norsyazwina.fazrul@gmail.com>"
    date: 2026-09-15
    summary: "删除 cpuidle 文档重复措辞"
    review_outcome: "09-26 Rafael 应用为 7.4 material"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "等待 7.4 窗口随分支进入主线"
contribution_opportunities: []
source_email_count: 1
related_articles: []
tags:
  - idle
---