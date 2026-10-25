---
id: sched-20261025-007
date: 2026-10-25
subject: 'sched_ext: Sync tools headers with scx and fix unsigned enum reads'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261023232102.1124938-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20261023232102.1124938-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
- Andrea Righi
current_version: v1
patch_series:
- version: v1
  msgid: <20261023232102.1124938-1-tj@kernel.org>
  date: 2026-10-24
  summary: 修 __COMPAT_read_enum 符号扩展、同步 scx 头与 autogen 表、删 stale 枚举条目
  review_outcome: Andrea Righi 全系列 Reviewed-by + 1/4 注释 nit
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 1/4 的 pahole < 1.24 kflag 注释 nit，非阻断
  next_action: Tejun 收取进 sched_ext/for-7.5
contribution_opportunities:
- kind: review
  description: 核对 __COMPAT_read_enum 修复与生成表/scx 仓库一致性
- kind: extend
  description: 继续清理 enums.autogen.h 中已不存在的 stale 枚举条目
generated_at: '2026-10-26T09:00:00'
source_email_count: 2
related_articles:
- sched-20261024-003
tags:
- sched_ext
title: 'sched_ext: Sync tools headers with scx and fix unsigned enum reads'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/24/sched-20261024-003-sched-ext-sync-tools-headers-with-scx-and-fix-unsigned-enum.html">sched-20261024-003</a>（v1）：Tejun Heo 发往 sched_ext/for-7.5 的四补丁系列——修 `__COMPAT_read_enum()` 对无符号 4 字节枚举的符号扩展（`SCX_RESCUE_DISABLE` 被读成 `0xffffffffffffffff`）、把 tools/sched_ext/include 共享头与 scx 仓库同步、删 kernel 已不存在的枚举查表条目。属 for-7.5 枚举查表收尾，scx 侧 PR 已合并，高确信合入。
- <a class="article-ref" href="/lkm/2026/10/25/sched-20261025-007-sched-ext-sync-tools-headers-with-scx-and-fix-unsigned-enum.html">sched-20261025-007</a>（今天）：Andrea Righi 给 2-4/4 三枚 *Reviewed-by*，并对 1/4 给 *Reviewed-by* 附一个 nit——pahole < 1.24 从不设 enum kflag、签名枚举在那也被零扩展，建议在注释里提一句。

## 背景与问题
（承接 20261024-003）`__COMPAT_read_enum()` 是无符号 4 字节枚举的兼容读取路径，此前对 unsigned enum 做了符号扩展，使 `SCX_RESCUE_DISABLE` 被读成 `0xffffffffffffffff`；同时 tools/sched_ext/include 共享头与 scx 仓库漂移、autogen 查表残留已删除条目。今日无新背景，进入 review 阶段。

## 技术方案
（承接 20261024-003）四补丁（7 files，+48/−35，均在 tools/sched_ext/）：修 `__COMPAT_read_enum()` 符号扩展、同步 autogen enum 查表、同步 common/compat 头、删 stale 枚举条目。今日无代码变更。

## 版本演进与当前进展
*current_version: v1*（`<20261023232102.1124938-1-tj@kernel.org>`）。当日收到 Andrea Righi 的 review 回帖（`<at3YBauZxfWw8su4@gpd4>`、`<at3YP-bVKwyfVKBT@gpd4>`）。

## Maintainer 意见与讨论焦点
Andrea Righi（sched_ext reviewer）：
- 1/4：*Reviewed-by* + nit——BTF 由 pahole < 1.24 生成时从不设 enum kflag，签名枚举在那也被零扩展；今天无害（`SCX_TASK_CURSOR` 是唯一受影响条目、只作 u32 flag），但建议在注释里说明。
- 2-4/4：*Reviewed-by*。

无反向意见。

## 合入评估
*likelihood=high*。已获 Andrea Righi 全系列 Reviewed-by，符合前序预测（由 Andrea 背书）；scx 侧 PR 已合并。*blocking_issues*：仅 1/4 的注释 nit，非阻断。*next_action*：Tejun 收取进 sched_ext/for-7.5（或先按 Andrea 建议补注释）。

## 效果评估
功能等价性为主：修 unsigned enum 符号扩展、头文件与 scx 仓库对齐。无量化性能数据。

## 我可以参与的点
- *kind: review*：核对签名后的 `__COMPAT_read_enum()` 对 unsigned/有符号枚举语义、以及生成表与 scx 仓库一致性（可接 Andrea 的 nit 补注释）。
- *kind: extend*：继续清理 `enums.autogen.h` 中已不存在的 stale 枚举条目并同步 scx 仓库。

## 参考链接
- cover: https://lore.kernel.org/all/20261023232102.1124938-1-tj@kernel.org/
- Andrea 1/4 回帖: https://lore.kernel.org/all/at3YBauZxfWw8su4@gpd4/
- 前文: <a class="article-ref" href="/lkm/2026/10/24/sched-20261024-003-sched-ext-sync-tools-headers-with-scx-and-fix-unsigned-enum.html">sched-20261024-003</a>
