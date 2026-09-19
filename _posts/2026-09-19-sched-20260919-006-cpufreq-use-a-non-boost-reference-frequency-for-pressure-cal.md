---
id: sched-20260919-006
date: '2026-09-19'
subject: 'cpufreq: Use a non-boost reference frequency for pressure calculation'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260915065747.1671965-1-wujianyong@hygon.cn>
lore_url: https://lore.kernel.org/all/20260915065747.1671965-1-wujianyong@hygon.cn/
authors:
- Jianyong Wu
maintainers_involved:
- Rafael J. Wysocki
current_version: v1
patch_series:
- version: v1
  msgid: <20260915065747.1671965-1-wujianyong@hygon.cn>
  date: '2026-09-15'
  summary: 用非 boost 参考频率计算 pressure，避免 boost 开关干扰负载均衡
  review_outcome: Rafael 提出窄化 intel_pstate 回退的替代方案，待作者验证
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Rafael 主张修复不应绑 boost，提出窄化 scope 的替代方案待验证
  next_action: 作者/Ricardo 测试 Rafael 的 intel_pstate 窄化补丁并回复
contribution_opportunities:
- kind: testing
  description: 在 intel_pstate 混合核与 HYGON 平台对比两种方案的 pressure 行为
- kind: review
  description: 评估两条技术路线的调度语义差异
generated_at: '2026-09-20T09:00:00'
source_email_count: 1
related_articles:
- sched-20260918-010
tags:
- cpufreq
- load_balance
title: 'cpufreq: Use a non-boost reference frequency for pressure calculation'
layout: article
---

## TL;DR
增量更新：Jianyong Wu 的 cpufreq CPU pressure 参考频率修复本日被 Rafael J. Wysocki 指出方向性偏差——Rafael 认为问题的本质是"在 `arch_scale_freq_ref()` 为零时仍施加了 pressure"，与 boost 本身关系不大，并贴出一版更窄的替代补丁（把回退限于 `intel_pstate` 非对称容量场景），请作者与 Ricardo 帮忙测试。

## 背景与问题
背景见 sched-20260918-010：cpufreq 的 CPU pressure 计算此前在 `arch_scale_freq_ref()` 为零时回退到 `policy->cpuinfo.max_freq`，导致 boost 开关时 pressure 无谓变化，干扰负载均衡（cache-aware scheduling 无法按预期聚合 LLC 任务）。

## 技术方案
原修复（见 sched-20260918-010）：改用"非 boost 参考频率"计算 pressure。本日 Rafael 提出另一条路线：问题实质在于调度器假设 `arch_scale_freq_ref()` 为零时 pressure 应为零，而被质疑的 commit 违反了这个假设——所以不应把修复绑到 boost 上。替代补丁（未测试）把 `cpufreq_update_pressure()` 里的 `max_freq` 回退改为仅当驱动提供 `scale_freq_ref` 回调时才回退（`if (!max_freq && cpufreq_driver->scale_freq_ref) max_freq = cpufreq_driver->scale_freq_ref(policy);`），并在 `intel_pstate` 里新增 `intel_pstate_scale_freq_ref()`：仅当 `cpu->capacity_perf` 非零（即有非对称容量/混合核）时返回 `cpuinfo.max_freq`，否则返回 0——即把回退范围限定到"intel_pstate 配非对称容量"这一触发场景。

## 版本演进与当前进展
- v1（2026-09-15，`<20260915065747.1671965-1-wujianyong@hygon.cn>`）："非 boost 参考频率"方案（见 sched-20260918-010）。
- 本日 Rafael Wysocki（`<5135696.31r3eYUQgx@rafael.j.wysocki>`）提出窄化 scope 的替代方案，请作者（Jianyong Wu）与 Ricardo 测试。

## Maintainer 意见与讨论焦点
- **Rafael J. Wysocki**（cpufreq 维护者）：明确"这其实与 boost 关系不大，让它依赖 boost 帮助不大"；指出改动的最初动机是 intel_pstate 跑非对称容量时的行为不当，建议把修复限定到该场景（"completely untested"的示例补丁）。
- 分歧/未决：两条技术路线（boost 参考频率 vs 窄化 intel_pstate 回退）尚未收敛，作者尚未回应 Rafael 的替代方案。

## 合入评估
likelihood=medium。维护者对当前 fix 的方向提出替代主张，作者需回应/验证后才能继续。blocking_issues：Rafael 认为修复不应绑 boost、主张窄化 scope，需作者测试并回应替代补丁。next_action：作者（或 Ricardo）测试 Rafael 的 `intel_pstate` 窄化补丁，回复哪种方案更合适。

## 效果评估
本日无新增测试数据。Rafael 的替代补丁明确标注"completely untested"，并请作者与 Ricardo 验证。

## 我可以参与的点
- kind=testing：在 intel_pstate（尤其混合核/非对称容量平台）与 HYGON 平台上对比两种方案对 pressure 计算与 LLC 聚合行为的影响，把结果回帖。
- kind=review：评估"非 boost 参考频率"与"窄化 intel_pstate 回退"两条路线对 schedutil/cache-aware LB 的语义差异。

## 参考链接
- lore（原 patch）: https://lore.kernel.org/all/20260915065747.1671965-1-wujianyong@hygon.cn/
- lore（Rafael 替代方案）: https://lore.kernel.org/all/5135696.31r3eYUQgx@rafael.j.wysocki/
