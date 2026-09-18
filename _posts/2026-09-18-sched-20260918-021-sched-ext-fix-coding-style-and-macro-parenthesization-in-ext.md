---
id: sched-20260918-021
date: '2026-09-18'
subject: 'sched_ext: Fix coding style and macro parenthesization in ext and cid'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260918143844.1279-1-rahadbhuiya2021@gmail.com>
lore_url: https://lore.kernel.org/all/20260918143844.1279-1-rahadbhuiya2021@gmail.com/
authors:
- rahadbhuiya
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260918143844.1279-1-rahadbhuiya2021@gmail.com>
  date: '2026-09-18'
  summary: checkpatch 风格清理与宏括号化
  review_outcome: 本日无回复
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: 等待 Tejun 审阅纯风格清理补丁
contribution_opportunities:
- kind: review
  description: 核对宏括号化是否完整覆盖各展开场景
generated_at: '2026-09-19T09:00:00'
source_email_count: 1
related_articles: []
tags:
- sched_ext
- cleanup
title: 'sched_ext: Fix coding style and macro parenthesization in ext and cid'
layout: article
---

## TL;DR
新贡献者 rahadbhuiya 提交 sched_ext 编码风格清理：把 SPDX 注释改成 C++ 风格、给两个宏定义加括号避免优先级副作用、修正结构体初始化括号位置、删除分号前空格、补空行。纯格式清理，无功能变化，本日无回复。

## 背景与问题
`kernel/sched/ext/` 下存在若干 checkpatch 风格问题（per Documentation/process/license-rules.rst 等），包括：
- SPDX 注释应为 C++ 风格 `//`（ext.c 与 cid.c）。
- `SCX_CID_TOPO_NEG` 与 `scx_enabling_sub_sched` 宏定义缺少括号，存在优先级副作用隐患。
- `scx_tg_online()` 结构体初始化大括号位置、`scx_bypass()` 分号前空格、`scx_alloc_and_add_sched()` 局部变量声明后缺空行。

## 技术方案
- `kernel/sched/ext/cid.c`：SPDX 注释改 C++ 风格；`SCX_CID_TOPO_NEG` 用 `((struct scx_cid_topo){...})` 包裹。
- `kernel/sched/ext/ext.c`：SPDX 注释改 C++ 风格；`scx_enabling_sub_sched` 改为 `((struct scx_sched *)NULL)`；修复结构体初始化/空格/空行。共 14 增 12 删。

## 版本演进与当前进展
- v1（09-18，`<20260918143844.1279-1-rahadbhuiya2021@gmail.com>`）：首版，本日无回复。

## Maintainer 意见与讨论焦点
- 本日无维护者回复。独立提交者为新贡献者（无实名），纯格式清理类补丁。

## 合入评估
likelihood=medium。无功能风险、符合风格规范；但这类纯风格补丁能否合入取决于 sched_ext 维护者（Tejun）是否愿意收取碎片化清理。blocking_issues：无阻塞；等待维护者 review。next_action：等待 Tejun 审阅；若被要求合并/精简条目，按意见调整。

## 效果评估
无性能数据；纯编码风格清理，无行为变化。

## 我可以参与的点
- kind=review：核对宏括号化是否完整覆盖所有展开场景（尤其 `SCX_CID_TOPO_NEG` 在条件/赋值上下文中的展开安全性）。

## 参考链接
- lore（patch）: https://lore.kernel.org/all/20260918143844.1279-1-rahadbhuiya2021@gmail.com/
