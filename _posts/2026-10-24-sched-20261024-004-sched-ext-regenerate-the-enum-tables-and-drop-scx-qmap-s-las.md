---
id: sched-20261024-004
date: 2026-10-24
subject: 'sched_ext: Regenerate the enum tables and drop scx_qmap''s last compat lookup'
subsystem: sched
type: fix
status: merged_tip
severity: none
thread_root_msgid: <20261023000348.2726436-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20261023000348.2726436-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
- Andrea Righi
current_version: v1
patch_series:
- version: v1
  msgid: <20261023000348.2726436-1-tj@kernel.org>
  date: 2026-10-23
  summary: 重新生成 autogen 枚举头 + 加 SCX_RESCUE_DISABLE 查表并删 compat 查询
  review_outcome: Andrea Righi 双补丁 Reviewed-by
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.5
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 随 for-7.5 窗口合入 tip；可继续做成 stale 枚举清理
contribution_opportunities:
- kind: extend
  description: 清理 enums.autogen.h 中已不存在的 stale 枚举并同步 scx 仓库 SCX_RESCUE_DISABLE
generated_at: '2026-10-25T01:00:00'
source_email_count: 1
related_articles:
- sched-20261023-007
tags:
- sched_ext
title: 'sched_ext: Regenerate the enum tables and drop scx_qmap''s last compat lookup'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/23/sched-20261023-007-sched-ext-regenerate-the-enum-tables-and-drop-scx-qmap-s-las.html">sched-20261023-007</a>：Tejun Heo 发往 sched_ext/for-7.5 的两补丁小系列——`scx_qmap` compat 移除遗留了一处 `__COMPAT_ENUM_OR_ZERO("scx_consts","SCX_RESCUE_DISABLE")` 查表，但该枚举在 kernel 内部 `enum scx_consts` 里、用户态只能从 BTF 读且查表没列它。patch 1 重新生成 autogen 枚举头补 presence marker 与 ABI 值，patch 2 把 `SCX_RESCUE_DISABLE` 加进查表并删 compat 查询。当日 Andrea Righi 对两补丁给 Reviewed-by。
- <a class="article-ref" href="/lkm/2026/10/24/sched-20261024-004-sched-ext-regenerate-the-enum-tables-and-drop-scx-qmap-s-las.html">sched-20261024-004</a>（今天）：Tejun 回帖确认 **Applied 1-2 to sched_ext/for-7.5**，并追加 Andrea Righi 的 Reviewed-by 标签。系列已合入 sched_ext/for-7.5 分支。

## 背景与问题
（承接 20261023-007）这是对「scx_qmap: Drop the compat code」系列的跟进：`scx_qmap` 的 `-B 0` 分支此前用 `__COMPAT_ENUM_OR_ZERO` 读 `SCX_RESCUE_DISABLE`，而该枚举位于 kernel 内部 `enum scx_consts`、枚举查表未列出它，导致无法像其他枚举那样在调度器 open 时从 BTF 统一读取。今日无新背景，为合入确认。

## 技术方案
（承接 20261023-007）两补丁：patch 1 从当前 `vmlinux.h` 重新生成 `enum_defs.autogen.h` 与 `enums_abi.autogen.h`（补新枚举 presence marker 与 ABI 值）；patch 2 把 `SCX_RESCUE_DISABLE` 加进查表、`scx_qmap.c` 的 `-B 0` 分支改用 `skel->rodata->__SCX_RESCUE_DISABLE` 读取并删 compat 查询。今日无代码变更，为收取确认。

## 版本演进与当前进展
*current_version: v1*（`<20261023000348.2726436-1-tj@kernel.org>`，10-23）。今日进展：Tejun 合入。

## Maintainer 意见与讨论焦点
Tejun Heo 今日确认「Applied 1-2 to sched_ext/for-7.5 with the following tags added: Reviewed-by: Andrea Righi」。Andrea 此前还提醒可同步 scx 仓库的 `SCX_RESCUE_DISABLE` 并清理 stale 枚举（`SCX_RQ_BAL_PENDING` 等），属非阻塞建议。无分歧。

## 合入评估
*likelihood=merged*。已合入 sched_ext/for-7.5 分支（Tejun 自有树）。*blocking_issues*：无。*next_action*：随 for-7.5 窗口合入 tip；可继续做成 Andrea 建议的 stale 枚举清理。

## 效果评估
功能等价性验证：`-B 0` 仍禁用 rescue、默认值不变（纯查表机制替换，无量化数据）。

## 我可以参与的点
- *kind: extend*：按 Andrea 建议，提交后续补丁清理 `enums.autogen.h` 中已不存在的 stale 枚举（`SCX_RQ_BAL_PENDING` 等）并同步 scx 仓库的 `SCX_RESCUE_DISABLE`。

## 参考链接
- 系列 cover: https://lore.kernel.org/all/20261023000348.2726436-1-tj@kernel.org/
- Tejun 今日「Applied 1-2」确认: https://lore.kernel.org/all/4aa1f2d3a43d67ffcbba4eff0719e963@kernel.org/
- 前文: <a class="article-ref" href="/lkm/2026/10/23/sched-20261023-007-sched-ext-regenerate-the-enum-tables-and-drop-scx-qmap-s-las.html">sched-20261023-007</a>
