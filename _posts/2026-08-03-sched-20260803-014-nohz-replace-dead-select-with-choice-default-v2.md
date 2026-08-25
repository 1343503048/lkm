---
subject: nohz replace dead select with choice default v2
id: sched-20260803-014
date: 2026-08-03
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260801000000.0000000-1-nohz@kernel.org>
lore_url: unknown
authors:
- Frederic Weisbecker
maintainers_involved:
- Frederic Weisbecker
- Peter Zijlstra
- Thomas Gleixner
current_version: v2
patch_series:
- version: v1
  msgid: <20260801000000.0000000-1-nohz@kernel.org>
  date: 2026-08-02
  summary: NO_HZ_FULL 的 Kconfig 用 'select' 依赖一个已被删除/失效的符号，导致配置静默漂移。v1 改为 choice/default
    结构（sched-20260802-005）。
  review_outcome: 08-02 已覆盖（系列 sched-20260802-005）。
- version: v2
  msgid: <unknown>
  date: 2026-08-03
  summary: 08-03 收到 Reviewed-by 认可，确认 choice/default 重构语义等价且无 .config 行为偏离。
  review_outcome: Reviewed-by 通过；仅剩『缺乏 .config 对比数据』的验证缺口（08-02 已标注）。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 验证缺口：作者/reviewer 断言语义等价，但未附 old vs new .config 差异对比
  next_action: 补一份 .config 对比（defconfig + 若干 randconfig）确认无配置漂移后合入。
contribution_opportunities:
- kind: testing
  description: 可跑脚本对多个 arch 的 defconfig + 若干 randconfig 生成 old/new .config 差异，确认 NO_HZ_FULL
    选择行为完全一致，回帖对比数据补强验证（作者未附）。
generated_at: '2026-08-04T00:20:00'
source_email_count: 1
related_articles:
- sched-20260802-005-nohz-replace-dead-select-with-choice-default
tags:
- nohz
- kconfig
- x86
title: 'nohz: replace dead select with choice default'
layout: article
---

# nohz: 用 choice/default 替换失效 select（Reviewed-by）


## TL;DR
`nohz` 用 `choice/default` 替换失效的 `select` 依赖（08-02 系列 005）在 08-03 收到 Reviewed-by，确认语义等价。低严重度，合入可能性高；仍缺 `.config` 对比数据（明确参与点）。

## 背景与问题
`NO_HZ_FULL` 的 Kconfig 原先 `select` 一个**已删除/失效**的符号，导致该依赖静默失效、配置可能与作者预期漂移而不被察觉。08-02 文章（sched-20260802-005）已覆盖 v1：把 `select` 改为 `choice`/`default` 结构，使依赖关系显式且可验证。

## 技术方案
08-03 Frederic Weisbecker 给出 `Reviewed-by`，确认 `choice`/`default` 重构在语义上与原 `select` 路径等价。核心改动不变：用显式 choice 块 + 合理 default 表达 NO_HZ_FULL 的依赖，替代失效的 select。

## 版本演进与当前进展
- 08-02：v1 提出 choice/default 重构（sched-20260802-005）。
- 08-03：Reviewed-by 通过，进入合入前夜。

## Maintainer 意见与讨论焦点
Frederic Weisbecker（作者兼 reviewer 路径）：明确认可语义等价并无 `.config` 行为偏离。唯一遗留是 08-02 已标注的验证缺口——断言等价但无 old/new `.config` 对比数据。

## 合入评估
合入可能性 high。Kconfig 重构，Reviewed-by 已给，无功能风险，低严重度。

## 效果评估
邮件断言语义等价但**未附** old vs new `.config` 差异。属「作者主观判断，未见数据」——恰是最明确的参与切入点（见下）。

## 我可以参与的点
- 这是 08-02 已识别、08-03 仍未补的缺口：可写脚本对 x86/arm64 等 arch 的 defconfig + 若干 randconfig 分别生成 old/new `.config`，diff 确认 NO_HZ_FULL 选择行为完全一致，回帖对比数据补强验证。

## 参考链接
- 08-02 文章：sched-20260802-005-nohz-replace-dead-select-with-choice-default
- lore thread: 未获取到
