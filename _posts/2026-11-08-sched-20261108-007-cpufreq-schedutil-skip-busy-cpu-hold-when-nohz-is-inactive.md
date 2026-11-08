---
id: sched-20261108-007
date: '2026-11-08'
subject: 'cpufreq: schedutil: Skip busy-CPU hold when NOHZ is inactive'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261108145028.2483131-2-thnkslprpt@gmail.com>
lore_url: https://lore.kernel.org/all/20261108145028.2483131-2-thnkslprpt@gmail.com/
authors:
- Avi Weiss
maintainers_involved: []
current_version: v2
patch_series:
- version: v1
  msgid: null
  date: null
  summary: 用 tick_nohz_enabled() 判断 NOHZ 是否启用
  review_outcome: Zhan Xusheng 指出无法覆盖 NOHZ 启用但未激活的情形
- version: v2
  msgid: <20261108145028.2483131-2-thnkslprpt@gmail.com>
  date: '2026-11-08'
  summary: 改用 tick_nohz_is_active()，覆盖 NOHZ 禁用与启用未激活两种情形
  review_outcome: 暂无维护者评审
upstream_commit: null
fixes_commit: b7eaf1aab9f8
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 无维护者评审
  - stable 回合需确认 tick_nohz_is_active 在目标内核可用
  next_action: 等待 schedutil/cpufreq 侧 Ack 后收取并回合 stable
contribution_opportunities:
- kind: testing
  description: 在 nohz=off 或 NOHZ 激活失败平台验证修复前后降频行为
- kind: review
  description: 核对 tick_nohz_is_active 与 tick_nohz_enabled 的覆盖差异是否为本 bug 全部触发面
generated_at: '2026-11-09T09:00:00+08:00'
source_email_count: 1
related_articles: []
tags:
- cpufreq
- nohz
title: 'cpufreq: schedutil: Skip busy-CPU hold when NOHZ is inactive'
layout: article
---

## TL;DR

Avi Weiss 的 v2 单补丁修复 schedutil governor 在 NOHZ 失效场景下的「假忙」误判：`sugov_hold_freq()` 依赖 NOHZ idle-call 计数判断 CPU 近期是否空闲，NOHZ 被禁用或激活失败时计数不推进，CPU 被当作持续繁忙，频率永不下降。修复在 `tick_nohz_is_active()` 为假时跳过 busy-CPU hold。带 `Fixes`/`Cc: stable`，改动 3 行。

## 背景与问题

`sugov_hold_freq()` 用 NOHZ 的 idle-call 计数器判断 CPU 是否近期空闲，决定是否维持当前频率（避免过早降频）。当 NOHZ 被禁用、或虽启用但从未真正激活时，计数器不推进，schedutil 会误判 CPU「持续繁忙」，从而一直 hold 频率、阻止必要的降频。v1 用 `tick_nohz_enabled()` 判断，被 Zhan Xusheng 指出无法覆盖「NOHZ 已启用但从未激活」的情况，v2 改用 `tick_nohz_is_active()`。

## 技术方案

在 `sugov_hold_freq()` 的 `uclamp_rq_is_capped()` 检查之后、正式维持频率之前，插入早退（`kernel/sched/cpufreq_schedutil.c` +3）：

```c
 	if (uclamp_rq_is_capped(cpu_rq(sg_cpu->cpu)))
 		return false;
 
+	if (!tick_nohz_is_active())
+		return false;
+
 	/*
 	 * Maintain the frequency if the CPU has not been idle recently, as
 	 * reduction is likely to be premature.
```

`tick_nohz_is_active()` 同时覆盖「NOHZ 被禁用」与「启用但未激活」两种情形，比 `tick_nohz_enabled()` 更完整。

## 版本演进与当前进展

*current_version: v2（2026-11-08 发出）*。

- v1：用 `tick_nohz_enabled()`。
- v2：改用 `tick_nohz_is_active()`，回应 Zhan Xusheng 的 review 意见，覆盖 NOHZ 启用但未激活的场景。

## Maintainer 意见与讨论焦点

当日缓存未见 cpufreq 维护者（Viresh/Rafael）回帖；可见反馈来自 Zhan Xusheng 对 v1 的意见（改用 `tick_nohz_is_active()`）。无 NAK。

## 合入评估

*likelihood=medium*。改动小、有 `Fixes: b7eaf1aab9f8` 与 `Cc: stable`、v2 已按 review 收敛，但当日无维护者 Ack。*blocking_issues*：① 无维护者评审；② 需确认 `tick_nohz_is_active()` 的语义在目标稳定内核上可用（stable 回合）。*next_action*：等待 schedutil/cpufreq 侧 Ack，随后收取并回合 stable。

## 效果评估

补丁说明偏机理，未附频率曲线/功耗数据。效果判断为作者主观分析：修复后 NOHZ 失效场景下不再阻止降频（作者判断，未见测试数据）。

## 我可以参与的点

- **testing**：在 `nohz=off` 或 NOHZ 激活失败的平台上验证修复前后 schedutil 的降频行为。
- **review**：核对 `tick_nohz_is_active()` 相对 `tick_nohz_enabled()` 的覆盖差异是否正是本 bug 的全部触发面。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261108145028.2483131-2-thnkslprpt@gmail.com/
- Fixes commit: b7eaf1aab9f8（"cpufreq: schedutil: Avoid reducing frequency of busy CPUs prematurely"）
