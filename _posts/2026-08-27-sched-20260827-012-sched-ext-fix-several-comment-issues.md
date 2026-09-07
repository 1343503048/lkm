---
id: sched-20260827-012
date: '2026-08-27'
subject: 'sched_ext: Fix several comment issues'
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: <20260827091411.973621-1-liwanwu@kylinos.cn>
lore_url: https://lore.kernel.org/all/20260827091411.973621-1-liwanwu@kylinos.cn/
authors:
- Wanwu Li
- Zhan Xusheng
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260827091411.973621-1-liwanwu@kylinos.cn>
  date: 2026-08-27
  summary: 修正 sched_ext 中三处过时/拼错的函数名注释（4 站点）
  review_outcome: Zhan Xusheng Reviewed-by，并指出 changelog 少计一处站点
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 sched_ext 维护者收取
contribution_opportunities: []
generated_at: '2026-09-07T22:05:00'
source_email_count: 2
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Fix several comment issues'
layout: article
---

## TL;DR
Wanwu Li 修正 sched_ext 注释里三处过时/错误的函数名引用（`__setschduler_prio()`→`__setscheduler_class()`、`scx_iter_scx_dsq_new()`→`bpf_iter_scx_dsq_new()`、`scx_next_task_scx()`→`set_next_task_scx()`）。Zhan Xusheng 当日给出 **Reviewed-by** 并逐条核对了新名字与注释语义的匹配性，还提醒 changelog 漏计了一处站点——纯注释修复里 review 质量相当高的一篇，合入只差维护者收。

## 背景与问题
sched_ext 注释中残留了拼错的（`__setschduler_prio`）和从未存在过的函数名（`scx_iter_scx_dsq_new`、`scx_next_task_scx`），会误导按名字 grep 源码的读者。改动范围 `kernel/sched/ext/ext.c` 与 `internal.h`，4 行。

## 技术方案
机械改名。无取舍可谈。

## 版本演进与当前进展
v1（`<20260827091411.973621-1-liwanwu@kylinos.cn>`）当日即获 Zhan Xusheng Reviewed-by（`<20260827095635.535908-1-zhanxusheng1024@gmail.com>`），无 v2 需求。

## Maintainer 意见与讨论焦点
- Zhan Xusheng 不仅 grep 验证旧拼写只剩被改的这几处，还核对了注释声称的调用关系：`__setscheduler_class()` 确实返回 sched_class（core.c:7608）、`task_should_scx()` 经 7617 与 sched_fork 路径 4862 到达、`internal.h:439` 文档的 @running 回调确由 `set_next_task_scx()` 触发。
- 唯一"意见"是给 changelog 的：diff 修了 4 个站点而 changelog 列了 3 个改名——`__setschduler_prio` 与 `__setscheduler_prio` 是同一个陈旧名字的两种拼法。无争议。

## 合入评估
**likely**。纯注释、已带 Reviewed-by、无人反对。`next_action`：sched_ext 维护者（Tejun）收队列即可。

## 效果评估
无效果数据（无需）。

## 我可以参与的点
当前阶段暂无明显参与空间；可作为"高质量小 review 的范本"借鉴——Zhan 那种把注释语义逐条对到代码行的核对方式，正是社区缺的。

## 参考链接
- lore: https://lore.kernel.org/all/20260827091411.973621-1-liwanwu@kylinos.cn/
- Reviewed-by: https://lore.kernel.org/all/20260827095635.535908-1-zhanxusheng1024@gmail.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到
