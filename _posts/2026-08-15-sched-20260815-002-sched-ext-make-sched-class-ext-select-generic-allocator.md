---
subject: 'sched_ext: Make SCHED_CLASS_EXT select GENERIC_ALLOCATOR'
id: sched-20260815-002
date: 2026-08-15
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <uid-41417@qq-imap>
lore_url: 未获取到
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <uid-41417@qq-imap>
  date: 2026-08-15
  summary: 让 SCHED_CLASS_EXT 选择 GENERIC_ALLOCATOR，修复 hppa 等架构构建时 gen_pool_* 未定义引用。
  review_outcome: Bradley Morgan 给出 Reviewed-by；Tejun 已 apply 到 sched_ext/for-7.3。
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.3
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入，等待进入主线 next 树。
contribution_opportunities:
- kind: discussion
  description: 讨论邮件中顺带提到 hppa 已于 2021 退役但仍需适配，可关注是否将来在 SCX 泛化中再简化。
generated_at: '2026-08-16T00:10:00'
source_email_count: 3
related_articles: []
tags:
- sched_ext
- sched/core
title: 'sched_ext: Make SCHED_CLASS_EXT select GENERIC_ALLOCATOR'
layout: article
---

## TL;DR
Tejun Heo 让 `SCHED_CLASS_EXT` 显式 `select GENERIC_ALLOCATOR`，修复部分架构（如 hppa）构建时 `gen_pool_create/for_each_chunk/destroy` 未定义引用的问题。已 apply 到 `sched_ext/for-7.3`，属小修。

## 背景与问题
`SCHED_CLASS_EXT`（sched_ext 调度类）用到了 generic allocator（`gen_pool_*`），但未在 Kconfig 中 `select GENERIC_ALLOCATOR`。在 hppa 等未默认启用该符号的架构上，构建 `build_policy.o` 时报：
```
build_policy.o: undefined reference to `gen_pool_create'
build_policy.o: undefined reference to `gen_pool_for_each_chunk'
build_policy.o: undefined reference to `gen_pool_destroy'
```

## 技术方案
在 sched_ext 对应的 Kconfig 项中加入 `select GENERIC_ALLOCATOR`，确保依赖的 generic allocator 符号一定被构建。属于典型"缺依赖声明"修复。

## 版本演进与当前进展
v1 单 patch。Bradley Morgan 在 review 中戏谑提到 hppa 已退役但仍需适配，并给出 `Reviewed-by: Bradley Morgan <include@grrlz.net>`。Tejun 回复 "Applied to sched_ext/for-7.3"。

## Maintainer 意见与讨论焦点
- Bradley Morgan 认可 patch，附带一句关于 hppa 是否值得维护的闲谈（非技术反对）。
- Tejun 直接合入，无修改意见。

## 合入评估
已合入 `sched_ext/for-7.3`，等待进入主线。无悬空问题。

## 效果评估
构建期链接错误修复，无运行时行为变化。

## 我可以参与的点
当前阶段暂无明显参与空间，可持续观察后续版本。

## 参考链接
- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到
