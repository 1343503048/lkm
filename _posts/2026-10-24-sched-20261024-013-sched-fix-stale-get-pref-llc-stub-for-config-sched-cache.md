---
id: sched-20261024-013
date: 2026-10-24
subject: 'sched: fix stale get_pref_llc() stub for !CONFIG_SCHED_CACHE'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <20261019064157.29885-2-laoar.shao@gmail.com>
lore_url: https://lore.kernel.org/all/20261019064157.29885-2-laoar.shao@gmail.com/
authors:
- Yafang Shao
maintainers_involved:
- Peter Zijlstra
current_version: v3
patch_series:
- version: v3
  msgid: <20261019064157.29885-2-laoar.shao@gmail.com>
  date: 2026-10-19
  summary: 更新 !CONFIG_SCHED_CACHE 下过期的 get_pref_llc() 桩
  review_outcome: 三位 Reviewed-by；Peter 收取进 sched/urgent
upstream_commit: cac037a85c1971ec75c4d3edf5a28af9ec2a089c
fixes_commit: b636fef85bda
merged_branch: tip/sched/urgent
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: stable 7.2.x 回合
contribution_opportunities:
- kind: review
  description: 确认拆分后补丁签名与 stable 回合版本号无误
generated_at: '2026-10-25T01:00:00'
source_email_count: 1
related_articles:
- sched-20261022-014
tags:
- cfs
title: 'sched: fix stale get_pref_llc() stub for !CONFIG_SCHED_CACHE'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-017-sched-fix-stale-get-pref-llc-stub-for-config-sched-cache.html">sched-20261021-017</a> / <a class="article-ref" href="/lkm/2026/10/22/sched-20261022-014-sched-fix-stale-get-pref-llc-stub-for-config-sched-cache.html">sched-20261022-014</a>：Yafang Shao 的 bpf-next RFC v3 系列中的 1/5 补丁——修正 `!CONFIG_SCHED_CACHE` 构建下 `get_pref_llc()` 桩函数过期（与实际签名不符）的问题；已获 Gregory Price、Chen Yu、Tim Chen 三位 Reviewed-by，一致建议拆出单独提交并 `Cc: stable # v7.2.x`。
- <a class="article-ref" href="/lkm/2026/10/24/sched-20261024-013-sched-fix-stale-get-pref-llc-stub-for-config-sched-cache.html">sched-20261024-013</a>（今天）：Peter Zijlstra 将补丁合入 **tip/sched/urgent**（commit `cac037a85c19`），`Fixes: b636fef85bda`，`Cc: stable #v7.2.x`。系列正式合入。

## 背景与问题
（承接 20261021-017）`get_pref_llc()` 的 `!CONFIG_SCHED_CACHE` 桩实现与其新签名失配（stale），在关闭 SCHED_CACHE 的构建下会编译/语义异常。该修复混在 bpf-next RFC 系列里、评审一致要求拆分。被修 commit `b636fef85bda`（"sched/cache: Introduce task_struct->sched_cache_grp to fix UAF"）已进 stable，本修复需跟随回合。今日无新背景，为合入确认。

## 技术方案
（承接前序）单补丁：把 `!CONFIG_SCHED_CACHE` 下过期的 `get_pref_llc()` 桩（仍持旧的 `struct mm_struct *` 参数）更新为与实函数签名一致的 `struct sched_cache_group *grp`。已合入版本 diff（fair.c +1/-1）确认了该签名修正。

## 版本演进与当前进展
*current_version: v3*。今日进展：合入 tip/sched/urgent（commit `cac037a85c1971ec75c4d3edf5a28af9ec2a089c`）。

## Maintainer 意见与讨论焦点
Peter Zijlstra 今日将补丁合入 sched/urgent，提交消息记录：`Reviewed-by: Gregory Price (Meta)`、`Reviewed-by: Chen Yu`、`Reviewed-by: Tim Chen`、`Cc: <stable@vger.kernel.org> #v7.2.x`。无分歧。

## 合入评估
*likelihood=merged*。已合入 tip sched/urgent，待回合 stable 7.2.x（已带 stable 标签）。*blocking_issues*：无。*next_action*：stable 7.2.x 回合。

## 效果评估
编译正确性修复，无性能数据。

## 我可以参与的点
- *kind: review*：确认拆分后的单补丁签名与 stable 回合版本号无误。

## 参考链接
- tip 提交: https://git.kernel.org/tip/cac037a85c1971ec75c4d3edf5a28af9ec2a089c
- 前文: <a class="article-ref" href="/lkm/2026/10/22/sched-20261022-014-sched-fix-stale-get-pref-llc-stub-for-config-sched-cache.html">sched-20261022-014</a> / <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-017-sched-fix-stale-get-pref-llc-stub-for-config-sched-cache.html">sched-20261021-017</a>
