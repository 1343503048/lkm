---
id: sched-20261027-013
date: 2026-10-27
subject: 'sched_ext: Sync tools headers with scx and fix unsigned enum reads'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <20261023232102.1124938-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20261023232102.1124938-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
- Andrea Righi
current_version: v2
patch_series:
- version: v1
  msgid: <20261023232102.1124938-1-tj@kernel.org>
  date: 2026-10-24
  summary: 4 patches：修符号扩展 + 同步头 + 删 stale 条目
  review_outcome: Andrea 三枚 Reviewed-by + 1/4 nit
- version: v2
  msgid: <20261026173339.584908-1-tj@kernel.org>
  date: 2026-10-27
  summary: 1/4 发 v2（注释注明 pahole 行为），1-4 全部合入 for-7.5
  review_outcome: Applied to sched_ext/for-7.5
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.5
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入 for-7.5，等待随 sched_ext pull 进主线
contribution_opportunities: []
generated_at: '2026-10-28T09:00:00'
source_email_count: 2
related_articles:
- sched-20261024-003
- sched-20261025-007
tags:
- sched_ext
title: 'sched_ext: Sync tools headers with scx and fix unsigned enum reads'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/24/sched-20261024-003-sched-ext-sync-tools-headers-with-scx-and-fix-unsigned-enum.html">sched-20261024-003</a>（v1，4 patches）：Tejun Heo 发往 sched_ext/for-7.5 的系列——修 `__COMPAT_read_enum()` 对无符号 4 字节枚举的符号扩展（`SCX_RESCUE_DISABLE` 被读成 `0xffffffffffffffff`）、同步 tools/sched_ext/include 共享头与 scx 仓库、删 kernel 已不存在的枚举查表条目。
- <a class="article-ref" href="/lkm/2026/10/25/sched-20261025-007-sched-ext-sync-tools-headers-with-scx-and-fix-unsigned-enum.html">sched-20261025-007</a>：Andrea Righi 给 2-4/4 三枚 `Reviewed-by`，对 1/4 附一个 nit（pahole < 1.24 从不设 enum kflag）。
- <a class="article-ref" href="/lkm/2026/10/27/sched-20261027-013-sched-ext-sync-tools-headers-with-scx-and-fix-unsigned-enum.html">sched-20261027-013</a>（今天）：Tejun Heo 把 1/4 的 v2（注释注明 pahole 行为）发回，并 `Applied 1-4 to sched_ext/for-7.5`，补上 Andrea 的 `Reviewed-by`。系列**已合入** for-7.5。

## 背景与问题
（承接 20261024-003）`__COMPAT_read_enum()` 是无符号 4 字节枚举的兼容读取路径，此前对 unsigned enum 做了符号扩展，使 `SCX_RESCUE_DISABLE` 被读成 `0xffffffffffffffff`；同时 tools/sched_ext/include 共享头与 scx 仓库漂移、autogen 查表残留已删除条目。

## 技术方案
（承接 v1）四补丁（均在 tools/sched_ext/）：修 `__COMPAT_read_enum()` 符号扩展（按 BTF kflag 决定 sign/zero-extend）、同步 autogen enum 查表、同步 common/compat 头、删 stale 枚举条目。v2 只在 1/4 的注释里注明「pahole < 1.24 从不设 kflag，签名枚举在那里也被零扩展」。

## 版本演进与当前进展
*current_version: v2*（1/4 发 v2，其余保持 v1）。今日 1-4/4 全部 `Applied to sched_ext/for-7.5`。

## Maintainer 意见与讨论焦点
Andrea Righi `Reviewed-by`（全部四枚）；Tejun Heo 作为 sched_ext 维护者自取合入。无分歧。

## 合入评估
*likelihood=merged*。已合入 sched_ext/for-7.5（*merged_branch=sched_ext/for-7.5*）。

## 效果评估
无性能数据。正确性修复（enum 读取）与头文件同步。

## 我可以参与的点
当前阶段已合入，暂无明显参与空间。

## 参考链接
- v2 1/4: https://lore.kernel.org/all/20261026173339.584908-1-tj@kernel.org/
- v1 cover: https://lore.kernel.org/all/20261023232102.1124938-1-tj@kernel.org/
