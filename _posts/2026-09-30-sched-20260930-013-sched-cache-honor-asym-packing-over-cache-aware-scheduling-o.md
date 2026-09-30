---
id: sched-20260930-013
date: '2026-09-30'
subject: 'sched/cache: Honor asym packing over cache aware scheduling on hybrid system'
subsystem: sched
type: regression
status: under_review
severity: high
thread_root_msgid: <221f8b0345328c4b26b65daff4d3eec56a32b06d.1790617047.git.tim.c.chen@linux.intel.com>
lore_url: https://lore.kernel.org/all/221f8b0345328c4b26b65daff4d3eec56a32b06d.1790617047.git.tim.c.chen@linux.intel.com/
authors:
- Tim Chen
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <221f8b0345328c4b26b65daff4d3eec56a32b06d.1790617047.git.tim.c.chen@linux.intel.com>
  date: '2026-09-29'
  summary: 在 can_migrate_llc_task()/llc_balance() 让 asym packing 优先于 cache-aware
  review_outcome: 09-30 Tim 与 Kayra 收敛到给放行加 env->idle 前置，Tim 认可并给片段
upstream_commit: null
fixes_commit: 23b2b5ccc45c
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 需作者把 env->idle 前置落进 cleaned-up 版再投 sched/urgent
  - 尚未见 Peter 收取
  next_action: 作者按 env->idle 方案更新补丁，发 cleaned-up 版进 sched/urgent
contribution_opportunities:
- kind: review
  description: 确认 can_migrate_llc_task 与 llc_balance 两处放行口径（env->idle）一致
- kind: testing
  description: 在 big/little + cache-aware 平台验证加 env->idle 后仍消除编译负载回归且无新 LLC 抖动
generated_at: '2026-10-01T01:00:00'
source_email_count: 4
related_articles:
- sched-20260929-003
tags:
- load_balance
- topology
- regression
title: 'sched/cache: Honor asym packing over cache aware scheduling on hybrid system'
layout: article
---

> **subject**：`sched/cache: Honor asym packing over cache aware scheduling on hybrid system`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-003-sched-cache-honor-asym-packing-over-cache-aware-scheduling-o.html">sched-20260929-003</a>：Tim Chen 针对「cache-aware 调度在 AMD big/little 混合平台性能回退」的修复补丁——让 asym packing 在「要把任务迁到更高优先级空核」时优先于 cache-aware（迁到更高性能空核比 cache 共置更划算），带 `Fixes:`、双 `Tested-by`、`Cc: stable # 7.2.x`；Kayra 指出注释与实现的语义不一致（未检查 idle 就放行）。
- <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-013-sched-cache-honor-asym-packing-over-cache-aware-scheduling-o.html">sched-20260930-013</a>（今天）：Kayra 与 Tim 就「是否应给 `sched_asym()` 的 cache-aware 放行加 `env->idle` 前置」往返讨论，Tim 认可「这是有效的点」并给出加 `env->idle && sched_asym(...)` 条件的具体补丁片段——补丁朝「与 asym packing 迁移前置一致」的方向细化。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-003-sched-cache-honor-asym-packing-over-cache-aware-scheduling-o.html">sched-20260929-003</a>）这是「Cache-aware scheduling does not work well with amd big/little cores」讨论串的收口补丁：asym packing 想把任务放到最高优先级 CPU，cache-aware 想把进程任务共置到同一 LLC，两者放置策略相反；补丁让 asym packing 在迁向更高优先级空核时胜出。今日的增量聚焦 Kayra 前一天指出的语义问题：`sched_use_asym_prio()` 在不检查 core 是否完全空闲时就返回 true，`sched_asym()` 便可能在不满足「空闲」前置时放行 cache-aware 的 LLC 迁移限制。

## 技术方案

（承接）Tim Chen 今日确认「idle CPU 实际已在设 `asym_packing` 时作为前置条件被检查」（`if (env->idle && sgs->sum_h_nr_running && sched_group_asym(...)) sgs->group_asym_packing = 1;`），并给出把 `can_migrate_llc_task()` 第一段改成加 `env->idle` 检查的具体片段：

```c
if (cpu < 0 || cpus_share_cache(src_cpu, dst_cpu))
    return mig_unrestricted;

/* Prioritize asym packing over cache awareness */
if (env->idle && sched_asym(env->sd, dst_cpu, src_cpu))
    return mig_unrestricted;
```

方向：让 cache-aware 放行与 asym packing 迁移前置（idle 空核）保持一致，避免「非空闲时也被放行」的语义漏洞。

## 版本演进与当前进展

v1（`<221f8b0345328c4b26b65daff4d3eec56a32b06d.1790617047.git.tim.c.chen@linux.intel.com>`）仍为最新版本。当日增量：Kayra 贴出 `sched_use_asym_prio()` 与 `is_core_idle()` 代码、Tim 给出加 `env->idle` 条件的修改片段并认可。

## Maintainer 意见与讨论焦点

- **Tim Chen**（作者）：确认 idle 前置已在 `group_asym_packing` 设置处被检查；认为 Kayra 提议「给 cache-aware 放行加 `env->idle` 检查以匹配 asym packing 迁移前置」是有效点，并给出具体补丁片段。
- **Kayra Cizmeci**：先贴 `sched_use_asym_prio()`/`is_core_idle()` 说明无 SMT 时 `sched_use_asym_prio()` 在不检查空闲即返回 true 的情形；后又自我修正「若没有其他兄弟且我空闲，那我的兄弟家族也是空闲」。
- 无 NAK；讨论收敛到「补丁应补 `env->idle` 前置」这一具体改动，尚未见 Peter 的收取或 cleaned-up 版发布。

## 合入评估

*likelihood=high*。`Fixes:` 指向、两位 `Tested-by`（含最初报告者 Klaus Kusche）、`Cc: stable # 7.2.x`，今日又明确了 Kayra 语义问题的修法（加 `env->idle`）。*blocking_issues*：需作者把 `env->idle` 前置落进补丁（cleaned-up 版）再投 `sched/urgent`；尚未见 Peter 收取。*next_action*：作者按 `env->idle` 方案更新补丁，发 cleaned-up 版进 sched/urgent。

## 效果评估

本补丁无新增 benchmark 数字；回归本身（full-LTO 构建显著变慢）与此前讨论串证据见 <a class="article-ref" href="/lkm/2026/09/27/sched-20260927-005-cache-aware-scheduling-does-not-work-well-with-amd-big-littl.html">sched-20260927-005</a>（Klaus 复测 wallclock 优于所有 cache-aware 版本且不差于关掉 cache-aware 的基线）。今日无新量化。

## 我可以参与的点

- `review`：确认加 `env->idle` 后 `can_migrate_llc_task()` 放行条件与 `llc_balance()` 中 asym packing 路径的一致性，避免两处放行口径不一致。
- `testing`：在 big/little + cache-aware 平台验证「加 env->idle」后的补丁仍消除编译负载回归、且无新的 LLC 抖动。

## 参考链接

- lore（补丁，v1）: https://lore.kernel.org/all/221f8b0345328c4b26b65daff4d3eec56a32b06d.1790617047.git.tim.c.chen@linux.intel.com/
- Tim 今日回复: https://lore.kernel.org/all/7790ab6c5da3aeac42f6878f0a167c6cddebb354.camel@linux.intel.com/
- Kayra 今日回复: https://lore.kernel.org/all/20260929182137.196669-1-kayracizmeci@gmail.com/
- 相关讨论串: <a class="article-ref" href="/lkm/2026/09/27/sched-20260927-005-cache-aware-scheduling-does-not-work-well-with-amd-big-littl.html">sched-20260927-005</a>
